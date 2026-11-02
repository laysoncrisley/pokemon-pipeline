"""Carrega os JSONs de data/raw na camada raw do DuckDB, sem alterar o conteúdo."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import duckdb

from src import config

# tabela, coluna da chave, tipo da chave, subpasta, recurso na API
TABELAS_RAW = (
    ("pokemon", "pokemon_id", "INTEGER", "pokemon", "pokemon"),
    ("pokemon_species", "species_id", "INTEGER", "pokemon_species", "pokemon-species"),
    ("type", "type_name", "VARCHAR", "type", "type"),
)


def _chave(arquivo: Path, tipo: str):
    return int(arquivo.stem) if tipo == "INTEGER" else arquivo.stem


def executar(con: duckdb.DuckDBPyConnection, raw_dir: Path = config.RAW_DIR) -> dict[str, int]:
    """Recria as tabelas raw. Uma linha por arquivo; devolve linhas por tabela."""
    con.execute("CREATE SCHEMA IF NOT EXISTS raw")
    agora = datetime.now(timezone.utc).replace(tzinfo=None)
    contagens = {}
    for tabela, coluna, tipo, pasta, recurso in TABELAS_RAW:
        con.execute(
            f"""CREATE OR REPLACE TABLE raw.{tabela} (
                {coluna} {tipo} PRIMARY KEY,
                payload JSON NOT NULL,
                source_url VARCHAR NOT NULL,
                loaded_at TIMESTAMP NOT NULL
            )"""
        )
        arquivos = sorted((raw_dir / pasta).glob("*.json"), key=lambda a: _chave(a, tipo))
        linhas = [
            (
                _chave(arquivo, tipo),
                arquivo.read_bytes().decode("utf-8"),
                f"{config.BASE_URL}/{recurso}/{arquivo.stem}",
                agora,
            )
            for arquivo in arquivos
        ]
        if linhas:
            con.executemany(f"INSERT INTO raw.{tabela} VALUES (?, ?, ?, ?)", linhas)
        contagens[f"raw.{tabela}"] = len(linhas)
    return contagens
