"""Funções puras: recebem o dict do JSON da API e devolvem linhas (ou DataFrame).

Nada aqui abre arquivo, banco ou rede. Os motivos de cada regra estão em docs/decisoes.md.
"""
from __future__ import annotations

import re
from typing import Callable, Iterable

import pandas as pd

STATS = ("hp", "attack", "defense", "special-attack", "special-defense", "speed")


def decimetros_para_metros(altura: int) -> float:
    return round(altura / 10, 1)


def hectogramas_para_kg(peso: int) -> float:
    return round(peso / 10, 1)


def extrair_evolution_chain_id(url: str) -> int:
    """A API só traz a url da cadeia: .../evolution-chain/1/ vira 1."""
    encontrado = re.search(r"/evolution-chain/(\d+)/?$", url)
    if encontrado is None:
        raise ValueError(f"url de evolution_chain inesperada: {url}")
    return int(encontrado.group(1))


def extrair_genus(especie: dict) -> str | None:
    """Texto em inglês de genera[]. Sem entrada em inglês, fica nulo em vez de usar outro idioma."""
    return next((item["genus"] for item in especie["genera"] if item["language"]["name"] == "en"), None)


def linha_pokemon(pokemon: dict) -> dict:
    stats = {item["stat"]["name"]: item["base_stat"] for item in pokemon["stats"]}
    sprites = pokemon["sprites"]
    return {
        "pokemon_id": pokemon["id"],
        "name": pokemon["name"],
        "height_m": decimetros_para_metros(pokemon["height"]),
        "weight_kg": hectogramas_para_kg(pokemon["weight"]),
        "base_experience": pokemon["base_experience"],
        "hp": stats["hp"],
        "attack": stats["attack"],
        "defense": stats["defense"],
        "special_attack": stats["special-attack"],
        "special_defense": stats["special-defense"],
        "speed": stats["speed"],
        "total_stats": sum(stats[nome] for nome in STATS),
        "artwork_url": sprites["other"]["official-artwork"]["front_default"],  # pode ser nulo
        "sprite_url": sprites["front_default"],  # pode ser nulo
    }


def linha_species(especie: dict) -> dict:
    habitat = especie["habitat"]
    return {
        "species_id": especie["id"],
        "name": especie["name"],
        "is_legendary": especie["is_legendary"],
        "is_mythical": especie["is_mythical"],
        "capture_rate": especie["capture_rate"],
        "base_happiness": especie["base_happiness"],
        "habitat": habitat["name"] if habitat is not None else None,  # nulo continua nulo
        "color": especie["color"]["name"],
        "growth_rate": especie["growth_rate"]["name"],
        "generation": especie["generation"]["name"],
        "evolution_chain_id": extrair_evolution_chain_id(especie["evolution_chain"]["url"]),
        "genus": extrair_genus(especie),
    }


def linhas_tipo(pokemon: dict) -> list[dict]:
    return [
        {"pokemon_id": pokemon["id"], "slot": item["slot"], "type_name": item["type"]["name"]}
        for item in pokemon["types"]
    ]


def linhas_habilidade(pokemon: dict) -> list[dict]:
    return [
        {
            "pokemon_id": pokemon["id"],
            "ability_name": item["ability"]["name"],
            "is_hidden": item["is_hidden"],
            "slot": item["slot"],
        }
        for item in pokemon["abilities"]
    ]


def contar_golpes_brutos(pokemon: dict) -> int:
    """Linhas que existiriam sem a regra: uma por golpe, versão e método."""
    return sum(len(golpe["version_group_details"]) for golpe in pokemon["moves"])


def contar_golpes_do_grupo(pokemon: dict, version_group: str) -> int:
    """Linhas do version_group antes do distinto."""
    return sum(
        detalhe["version_group"]["name"] == version_group
        for golpe in pokemon["moves"]
        for detalhe in golpe["version_group_details"]
    )


def linhas_golpe(pokemon: dict, version_group: str) -> list[dict]:
    """Só os detalhes do version_group pedido, distintos por golpe, método e nível.

    O mesmo golpe em níveis diferentes continua como duas linhas: são dois
    momentos de aprendizado no jogo, não uma repetição.
    """
    distintos = dict.fromkeys(
        (golpe["move"]["name"], detalhe["move_learn_method"]["name"], detalhe["level_learned_at"])
        for golpe in pokemon["moves"]
        for detalhe in golpe["version_group_details"]
        if detalhe["version_group"]["name"] == version_group
    )
    return [
        {"pokemon_id": pokemon["id"], "move_name": nome, "learn_method": metodo, "min_level": nivel}
        for nome, metodo, nivel in distintos
    ]


MULTIPLICADORES_CAUSADOS = {"double_damage_to": 2.0, "half_damage_to": 0.5, "no_damage_to": 0.0}
MULTIPLICADORES_RECEBIDOS = {"double_damage_from": 2.0, "half_damage_from": 0.5, "no_damage_from": 0.0}


def linhas_dano(tipo: dict) -> list[dict]:
    """Usa só o sentido *_to: ler também *_from gravaria cada relação duas vezes."""
    return [
        {"attacking_type": tipo["name"], "defending_type": alvo["name"], "multiplier": multiplicador}
        for campo, multiplicador in MULTIPLICADORES_CAUSADOS.items()
        for alvo in tipo["damage_relations"][campo]
    ]


def linhas_dano_recebido(tipo: dict) -> list[dict]:
    """Mesma relação lida pelo sentido *_from. Serve só para conferir linhas_dano."""
    return [
        {"attacking_type": origem["name"], "defending_type": tipo["name"], "multiplier": multiplicador}
        for campo, multiplicador in MULTIPLICADORES_RECEBIDOS.items()
        for origem in tipo["damage_relations"][campo]
    ]


def _tabela(itens: Iterable[dict], extrair: Callable[[dict], Iterable[dict]], colunas: list[str]) -> pd.DataFrame:
    linhas = [linha for item in itens for linha in extrair(item)]
    # object evita que o pandas troque None por NaN ou infira o tipo pela amostra.
    return pd.DataFrame(linhas, columns=colunas, dtype=object)


COLUNAS_POKEMON = [
    "pokemon_id", "name", "height_m", "weight_kg", "base_experience", "hp", "attack",
    "defense", "special_attack", "special_defense", "speed", "total_stats", "artwork_url", "sprite_url",
]
COLUNAS_SPECIES = [
    "species_id", "name", "is_legendary", "is_mythical", "capture_rate", "base_happiness",
    "habitat", "color", "growth_rate", "generation", "evolution_chain_id", "genus",
]


def tabela_pokemon(pokemons: Iterable[dict]) -> pd.DataFrame:
    return _tabela(pokemons, lambda p: [linha_pokemon(p)], COLUNAS_POKEMON)


def tabela_species(especies: Iterable[dict]) -> pd.DataFrame:
    return _tabela(especies, lambda e: [linha_species(e)], COLUNAS_SPECIES)


def tabela_tipos(pokemons: Iterable[dict]) -> pd.DataFrame:
    return _tabela(pokemons, linhas_tipo, ["pokemon_id", "slot", "type_name"])


def tabela_habilidades(pokemons: Iterable[dict]) -> pd.DataFrame:
    return _tabela(pokemons, linhas_habilidade, ["pokemon_id", "ability_name", "is_hidden", "slot"])


def tabela_golpes(pokemons: Iterable[dict], version_group: str) -> pd.DataFrame:
    return _tabela(
        pokemons,
        lambda p: linhas_golpe(p, version_group),
        ["pokemon_id", "move_name", "learn_method", "min_level"],
    )


def tabela_dano(tipos: Iterable[dict]) -> pd.DataFrame:
    return _tabela(tipos, linhas_dano, ["attacking_type", "defending_type", "multiplier"])
