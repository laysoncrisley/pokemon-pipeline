"""Conferência de contagens entre camadas. Grava docs/conferencia.md e para se algo não bater."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import duckdb

from src import build, config, transform


class ErroDeConferencia(RuntimeError):
    """Alguma contagem não bateu entre as camadas."""


@dataclass
class Conferencia:
    descricao: str
    obtido: int
    esperado: int | None = None  # None: só registra o número, não há o que comparar

    @property
    def ok(self) -> bool:
        return self.esperado is None or self.obtido == self.esperado


def _valor(con: duckdb.DuckDBPyConnection, sql: str) -> int:
    return int(con.execute(sql).fetchone()[0] or 0)


def _anti_join(con: duckdb.DuckDBPyConnection, filha: str, coluna: str, pai: str, coluna_pai: str) -> int:
    return _valor(
        con,
        f"""SELECT COUNT(*) FROM {filha} f
            LEFT JOIN {pai} p ON f.{coluna} = p.{coluna_pai}
            WHERE p.{coluna_pai} IS NULL""",
    )


def _duplicados(con: duckdb.DuckDBPyConnection, tabela: str, colunas: str) -> int:
    return _valor(con, f"SELECT COUNT(*) - (SELECT COUNT(*) FROM (SELECT DISTINCT {colunas} FROM {tabela})) FROM {tabela}")


def _payloads_diferentes_do_disco(con: duckdb.DuckDBPyConnection, tabela: str, pasta: Path) -> int:
    diferentes = 0
    for chave, payload in con.execute(f"SELECT * EXCLUDE (source_url, loaded_at) FROM raw.{tabela}").fetchall():
        if payload != (pasta / f"{chave}.json").read_bytes().decode("utf-8"):
            diferentes += 1
    return diferentes


def conferir_raw(con: duckdb.DuckDBPyConnection, raw_dir: Path = config.RAW_DIR) -> list[Conferencia]:
    total = len(config.POKEMON_IDS)
    return [
        Conferencia("raw.pokemon: linhas", _valor(con, "SELECT COUNT(*) FROM raw.pokemon"), total),
        Conferencia("raw.pokemon_species: linhas", _valor(con, "SELECT COUNT(*) FROM raw.pokemon_species"), total),
        Conferencia("raw.pokemon: id do payload diferente do nome do arquivo",
                    _valor(con, "SELECT COUNT(*) FROM raw.pokemon WHERE CAST(payload->>'$.id' AS INTEGER) <> pokemon_id"), 0),
        Conferencia("raw.pokemon_species: id do payload diferente do nome do arquivo",
                    _valor(con, "SELECT COUNT(*) FROM raw.pokemon_species WHERE CAST(payload->>'$.id' AS INTEGER) <> species_id"), 0),
        Conferencia("raw.pokemon: payload diferente do arquivo em disco",
                    _payloads_diferentes_do_disco(con, "pokemon", raw_dir / "pokemon"), 0),
        Conferencia("raw.pokemon_species: payload diferente do arquivo em disco",
                    _payloads_diferentes_do_disco(con, "pokemon_species", raw_dir / "pokemon_species"), 0),
        Conferencia("raw.type: payload diferente do arquivo em disco",
                    _payloads_diferentes_do_disco(con, "type", raw_dir / "type"), 0),
    ]


def conferir_refined(con: duckdb.DuckDBPyConnection, version_group: str = config.VERSION_GROUP_GOLPES) -> list[Conferencia]:
    pokemons = build.payloads(con, "pokemon")
    tipos = build.payloads(con, "type")
    linhas_golpes = _valor(con, "SELECT COUNT(*) FROM refined.pokemon_move")
    linhas_dano = {tuple(d.values()) for t in tipos for d in transform.linhas_dano(t)}
    recebido = {tuple(d.values()) for t in tipos for d in transform.linhas_dano_recebido(t)}
    nomes_tipos = {t["name"] for t in tipos}
    dano_no_escopo = {d for d in linhas_dano if d[1] in nomes_tipos}
    recebido_no_escopo = {d for d in recebido if d[0] in nomes_tipos}

    return [
        Conferencia("refined.pokemon: linhas (raw.pokemon)",
                    _valor(con, "SELECT COUNT(*) FROM refined.pokemon"),
                    _valor(con, "SELECT COUNT(*) FROM raw.pokemon")),
        Conferencia("refined.species: linhas (raw.pokemon_species)",
                    _valor(con, "SELECT COUNT(*) FROM refined.species"),
                    _valor(con, "SELECT COUNT(*) FROM raw.pokemon_species")),
        Conferencia("refined.pokemon_type: linhas (soma de len(types) no raw)",
                    _valor(con, "SELECT COUNT(*) FROM refined.pokemon_type"),
                    _valor(con, "SELECT SUM(json_array_length(payload, '$.types')) FROM raw.pokemon")),
        Conferencia("refined.pokemon_ability: linhas (soma de len(abilities) no raw)",
                    _valor(con, "SELECT COUNT(*) FROM refined.pokemon_ability"),
                    _valor(con, "SELECT SUM(json_array_length(payload, '$.abilities')) FROM raw.pokemon")),
        Conferencia("Golpes ANTES da regra: linhas de version_group_details no raw",
                    sum(transform.contar_golpes_brutos(p) for p in pokemons)),
        Conferencia(f"Golpes de {version_group} no raw, antes do distinto",
                    sum(transform.contar_golpes_do_grupo(p, version_group) for p in pokemons)),
        Conferencia(f"Golpes DEPOIS da regra: refined.pokemon_move ({version_group})", linhas_golpes),
        Conferencia("refined.pokemon_move: repetidos no grão",
                    _duplicados(con, "refined.pokemon_move", "pokemon_id, move_name, learn_method, min_level"), 0),
        Conferencia("Pokémon sem nenhum golpe na regra",
                    _anti_join(con, "refined.pokemon", "pokemon_id", "refined.pokemon_move", "pokemon_id"), 0),
        Conferencia("Anti-join refined.pokemon sem refined.species",
                    _anti_join(con, "refined.pokemon", "pokemon_id", "refined.species", "species_id"), 0),
        Conferencia("Anti-join refined.species sem refined.pokemon",
                    _anti_join(con, "refined.species", "species_id", "refined.pokemon", "pokemon_id"), 0),
        Conferencia("pokemon_id = species_id com nome diferente",
                    _valor(con, """SELECT COUNT(*) FROM refined.pokemon p
                                   JOIN refined.species s ON p.pokemon_id = s.species_id
                                   WHERE p.name <> s.name"""), 0),
        Conferencia("Anti-join refined.pokemon_type sem refined.pokemon",
                    _anti_join(con, "refined.pokemon_type", "pokemon_id", "refined.pokemon", "pokemon_id"), 0),
        Conferencia("Anti-join refined.pokemon_ability sem refined.pokemon",
                    _anti_join(con, "refined.pokemon_ability", "pokemon_id", "refined.pokemon", "pokemon_id"), 0),
        Conferencia("Anti-join refined.pokemon_move sem refined.pokemon",
                    _anti_join(con, "refined.pokemon_move", "pokemon_id", "refined.pokemon", "pokemon_id"), 0),
        Conferencia("Espécies fora da generation-i",
                    _valor(con, "SELECT COUNT(*) FROM refined.species WHERE generation <> 'generation-i'"), 0),
        Conferencia("Tipos de pokemon_type sem linha em raw.type",
                    _anti_join(con, "refined.pokemon_type", "type_name", "raw.type", "type_name"), 0),
        Conferencia("Relações de dano ANTES do filtro de tipos (sentido *_to)", len(linhas_dano)),
        Conferencia("Relações de dano DEPOIS do filtro: refined.type_damage",
                    _valor(con, "SELECT COUNT(*) FROM refined.type_damage"), len(dano_no_escopo)),
        Conferencia("Relações *_to que não aparecem em *_from, ou o inverso (dentro do escopo)",
                    len(dano_no_escopo ^ recebido_no_escopo), 0),
    ]


def conferir_marts(con: duckdb.DuckDBPyConnection) -> list[Conferencia]:
    """Cada mart precisa fechar com a refined de origem: JOIN errado aparece aqui."""
    total = _valor(con, "SELECT COUNT(*) FROM refined.pokemon")
    return [
        Conferencia("mart_stats_por_tipo: soma de qtd_pokemon (linhas de pokemon_type)",
                    _valor(con, "SELECT SUM(qtd_pokemon) FROM marts.mart_stats_por_tipo"),
                    _valor(con, "SELECT COUNT(*) FROM refined.pokemon_type")),
        Conferencia("mart_top10_total_stats: Pokémon distintos",
                    _valor(con, "SELECT COUNT(DISTINCT pokemon_id) FROM marts.mart_top10_total_stats"), 10),
        Conferencia("mart_lendarios_vs_comuns: soma de qtd_pokemon",
                    _valor(con, "SELECT SUM(qtd_pokemon) FROM marts.mart_lendarios_vs_comuns"), total),
        Conferencia("mart_fraquezas_por_tipo: soma das relações (linhas de type_damage)",
                    _valor(con, "SELECT SUM(qtd_causam_2x + qtd_causam_0_5x + qtd_causam_0x) FROM marts.mart_fraquezas_por_tipo"),
                    _valor(con, "SELECT COUNT(*) FROM refined.type_damage")),
        Conferencia("mart_habitat: soma de qtd_pokemon",
                    _valor(con, "SELECT SUM(qtd_pokemon) FROM marts.mart_habitat"), total),
        Conferencia("mart_habitat: Pokémon na linha 'sem informação' (habitat nulo em refined.species)",
                    _valor(con, "SELECT COALESCE(SUM(qtd_pokemon), 0) FROM marts.mart_habitat WHERE habitat = 'sem informação'"),
                    _valor(con, "SELECT COUNT(*) FROM refined.species WHERE habitat IS NULL")),
        Conferencia("mart_habilidades_mais_comuns: linhas",
                    _valor(con, "SELECT COUNT(*) FROM marts.mart_habilidades_mais_comuns"), 15),
        Conferencia("mart_habilidades_mais_comuns: normal + oculta diferente do total",
                    _valor(con, "SELECT COUNT(*) FROM marts.mart_habilidades_mais_comuns WHERE qtd_como_normal + qtd_como_oculta <> qtd_pokemon"), 0),
        Conferencia("mart_cadeias_evolucao: soma de qtd_pokemon",
                    _valor(con, "SELECT SUM(qtd_pokemon) FROM marts.mart_cadeias_evolucao"), total),
        Conferencia("mart_resumo_geral: total_pokemon",
                    _valor(con, "SELECT total_pokemon FROM marts.mart_resumo_geral"), total),
        Conferencia("mart_pokedex: linhas",
                    _valor(con, "SELECT COUNT(*) FROM marts.mart_pokedex"), len(config.POKEMON_IDS)),
    ]


def data_da_extracao(raw_dir: Path = config.RAW_DIR) -> str:
    entradas = json.loads((raw_dir / config.MANIFEST_PATH.name).read_text(encoding="utf-8"))
    datas = sorted({entrada["baixado_em"][:10] for entrada in entradas})
    return datas[0] if len(datas) == 1 else f"{datas[0]} a {datas[-1]}"


def tabela_markdown(conferencias: list[Conferencia]) -> str:
    linhas = ["| Conferência | Esperado | Obtido | Resultado |", "|---|---:|---:|---|"]
    for item in conferencias:
        esperado = "-" if item.esperado is None else item.esperado
        resultado = "registro" if item.esperado is None else ("OK" if item.ok else "ERRO")
        linhas.append(f"| {item.descricao} | {esperado} | {item.obtido} | {resultado} |")
    return "\n".join(linhas)


def gravar_relatorio(conferencias: list[Conferencia], data_extracao: str, caminho: Path = config.CONFERENCIA_PATH) -> None:
    conteudo = (
        "# Conferência entre camadas\n\n"
        "Arquivo gerado por `python run_pipeline.py` (`src/checks.py`). Não edite à mão.\n\n"
        f"Data da extração da API: {data_extracao}.\n\n"
        f"{tabela_markdown(conferencias)}\n"
    )
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(conteudo, encoding="utf-8", newline="\n")


def imprimir(conferencias: list[Conferencia]) -> None:
    for item in conferencias:
        esperado = "" if item.esperado is None else f" (esperado {item.esperado})"
        marca = "info" if item.esperado is None else ("ok  " if item.ok else "ERRO")
        print(f"      {marca} {item.descricao}: {item.obtido}{esperado}")


def validar(conferencias: list[Conferencia]) -> None:
    erros = [item.descricao for item in conferencias if not item.ok]
    if erros:
        raise ErroDeConferencia("Conferência falhou: " + "; ".join(erros))


def executar(con: duckdb.DuckDBPyConnection) -> list[Conferencia]:
    """Confere, imprime e grava o relatório antes de parar, para o erro ficar registrado."""
    conferencias = conferir_raw(con) + conferir_refined(con) + conferir_marts(con)
    imprimir(conferencias)
    gravar_relatorio(conferencias, data_da_extracao())
    validar(conferencias)
    return conferencias
