"""Baixa da PokeAPI para data/raw, com cache em disco e manifest."""
from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

from src import config


class ErroDeDownload(RuntimeError):
    """A API não devolveu 200 depois das tentativas permitidas."""


def criar_sessao() -> requests.Session:
    sessao = requests.Session()
    sessao.headers["User-Agent"] = config.USER_AGENT
    return sessao


def baixar(sessao: requests.Session, url: str) -> requests.Response:
    """GET com retentativa. 404 e afins falham na hora: repetir não muda a resposta."""
    ultimo_erro = ""
    for tentativa in range(1, config.TENTATIVAS + 1):
        try:
            resposta = sessao.get(url, timeout=config.TIMEOUT_S)
        except requests.RequestException as erro:
            ultimo_erro = str(erro)
        else:
            if resposta.status_code == 200:
                return resposta
            ultimo_erro = f"HTTP {resposta.status_code}"
            if resposta.status_code < 500 and resposta.status_code != 429:
                break
        if tentativa < config.TENTATIVAS:
            time.sleep(config.ESPERA_BASE_S * tentativa)
    raise ErroDeDownload(f"{url}: {ultimo_erro}")


def salvar_bruto(caminho: Path, texto: str) -> None:
    """Grava o texto da resposta sem alteração.

    newline="" impede o Windows de trocar \n por \r\n. O arquivo temporário
    evita que uma queda no meio deixe um JSON cortado sendo tratado como cache.
    """
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporario = caminho.with_name(caminho.name + ".tmp")
    with open(temporario, "w", encoding="utf-8", newline="") as arquivo:
        arquivo.write(texto)
    os.replace(temporario, caminho)


def carregar_manifest(caminho: Path) -> dict[str, dict]:
    if not caminho.exists():
        return {}
    entradas = json.loads(caminho.read_text(encoding="utf-8"))
    return {entrada["arquivo"]: entrada for entrada in entradas}


def salvar_manifest(caminho: Path, manifest: dict[str, dict]) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    entradas = [manifest[chave] for chave in sorted(manifest)]
    caminho.write_text(json.dumps(entradas, indent=2, ensure_ascii=False), encoding="utf-8")


def obter(
    sessao: requests.Session,
    url: str,
    caminho: Path,
    manifest: dict[str, dict],
    raw_dir: Path,
    refresh: bool = False,
) -> bool:
    """Garante o arquivo em disco. Devolve True se baixou, False se veio do cache."""
    if caminho.exists() and not refresh:
        return False
    resposta = baixar(sessao, url)
    salvar_bruto(caminho, resposta.text)
    arquivo = caminho.relative_to(raw_dir).as_posix()
    manifest[arquivo] = {
        "arquivo": arquivo,
        "url": url,
        "status": resposta.status_code,
        "baixado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    time.sleep(config.PAUSA_ENTRE_CHAMADAS_S)
    return True


def tipos_presentes(pasta_pokemon: Path) -> list[str]:
    """Só os tipos usados pelos Pokémon baixados: unknown, shadow etc. ficam de fora."""
    tipos: set[str] = set()
    for arquivo in pasta_pokemon.glob("*.json"):
        pokemon = json.loads(arquivo.read_text(encoding="utf-8"))
        tipos.update(item["type"]["name"] for item in pokemon["types"])
    return sorted(tipos)


def executar(
    refresh: bool = False,
    raw_dir: Path = config.RAW_DIR,
    ids=config.POKEMON_IDS,
    sessao: requests.Session | None = None,
) -> dict[str, int]:
    """Baixa pokemon, pokemon-species e type. Devolve a contagem de downloads e de cache."""
    sessao = sessao or criar_sessao()
    manifest_path = raw_dir / config.MANIFEST_PATH.name
    manifest = carregar_manifest(manifest_path)
    baixados = 0
    total = 0
    try:
        for pasta, recurso in (("pokemon", "pokemon"), ("pokemon_species", "pokemon-species")):
            for pokemon_id in ids:
                url = f"{config.BASE_URL}/{recurso}/{pokemon_id}"
                baixados += obter(sessao, url, raw_dir / pasta / f"{pokemon_id}.json", manifest, raw_dir, refresh)
                total += 1
        # A lista de tipos depende dos Pokémon, por isso vem depois deles.
        for nome in tipos_presentes(raw_dir / "pokemon"):
            url = f"{config.BASE_URL}/type/{nome}"
            baixados += obter(sessao, url, raw_dir / "type" / f"{nome}.json", manifest, raw_dir, refresh)
            total += 1
    finally:
        salvar_manifest(manifest_path, manifest)
    return {"baixados": baixados, "cache": total - baixados, "total": total}
