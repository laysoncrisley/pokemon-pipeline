"""Caminhos e parâmetros do projeto. Nada aqui depende de sistema operacional."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

RAW_DIR = ROOT / "data" / "raw"
MANIFEST_PATH = RAW_DIR / "_manifest.json"
WAREHOUSE_DB = ROOT / "warehouse" / "pokemon.duckdb"
SQL_REFINED_DIR = ROOT / "sql" / "refined"
SQL_MARTS_DIR = ROOT / "sql" / "marts"
CONFERENCIA_PATH = ROOT / "docs" / "conferencia.md"

BASE_URL = "https://pokeapi.co/api/v2"
POKEMON_IDS = range(1, 152)  # 1ª geração: 1 a 151

USER_AGENT = "desafio-engenharia-dados-jr"
TIMEOUT_S = 30
TENTATIVAS = 3
ESPERA_BASE_S = 1.0  # espera crescente: 1s, 2s
PAUSA_ENTRE_CHAMADAS_S = 0.2  # uso justo da API

# Critério de deduplicação dos golpes (motivo em docs/decisoes.md)
VERSION_GROUP_GOLPES = "red-blue"
