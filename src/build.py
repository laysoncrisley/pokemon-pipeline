"""Monta refined e marts: achata o JSON em Python e executa os .sql em ordem."""
from __future__ import annotations

import json
from pathlib import Path

import duckdb

from src import config, transform


def _payloads(con: duckdb.DuckDBPyConnection, tabela: str) -> list[dict]:
    return [json.loads(linha[0]) for linha in con.execute(f"SELECT payload FROM raw.{tabela} ORDER BY 1").fetchall()]


def registrar_staging(con: duckdb.DuckDBPyConnection) -> dict:
    """Publica o JSON achatado como views stg_* que os .sql de refined consomem."""
    pokemons = _payloads(con, "pokemon")
    especies = _payloads(con, "pokemon_species")
    staging = {
        "stg_pokemon": transform.tabela_pokemon(pokemons),
        "stg_species": transform.tabela_species(especies),
    }
    for nome, tabela in staging.items():
        con.register(nome, tabela)
    return staging


def executar_sql(con: duckdb.DuckDBPyConnection, pasta: Path) -> list[str]:
    """Executa cada .sql da pasta em ordem alfabética. Devolve os nomes executados."""
    arquivos = sorted(pasta.glob("*.sql"))
    for arquivo in arquivos:
        con.execute(arquivo.read_text(encoding="utf-8"))
    return [arquivo.name for arquivo in arquivos]


def construir_refined(con: duckdb.DuckDBPyConnection, pasta: Path = config.SQL_REFINED_DIR) -> list[str]:
    con.execute("CREATE SCHEMA IF NOT EXISTS refined")
    staging = registrar_staging(con)
    try:
        return executar_sql(con, pasta)
    finally:
        for nome in staging:
            con.unregister(nome)
