"""Garante por construção que nenhum teste usa a internet ou o banco do projeto."""
import json
import shutil
import socket
from pathlib import Path
from unittest import mock

import duckdb
import pytest

from src import build, load_raw

FIXTURES = Path(__file__).parent / "fixtures"
_connect_original = duckdb.connect


def _connect_protegido(database=":memory:", *args, **kwargs):
    if "pokemon.duckdb" in str(database):
        raise AssertionError("teste tentou abrir o banco do projeto")
    return _connect_original(database, *args, **kwargs)


@pytest.fixture(autouse=True)
def isolamento():
    def sem_rede(*args, **kwargs):
        raise AssertionError("teste tentou acessar a rede")

    with mock.patch.object(socket.socket, "connect", sem_rede), mock.patch.object(duckdb, "connect", _connect_protegido):
        yield


@pytest.fixture
def carregar_json():
    def _carregar(nome: str) -> dict:
        return json.loads((FIXTURES / nome).read_text(encoding="utf-8"))

    return _carregar


@pytest.fixture
def raw_inventado(tmp_path) -> Path:
    """Pasta no formato de data/raw, montada só com os JSONs inventados."""
    raiz = tmp_path / "raw"
    for pasta, origem, destino in (
        ("pokemon", "pokemon_9001.json", "9001.json"),
        ("pokemon_species", "species_9001_habitat_nulo.json", "9001.json"),
        ("type", "type_fogo.json", "fogo.json"),
    ):
        (raiz / pasta).mkdir(parents=True)
        shutil.copy(FIXTURES / origem, raiz / pasta / destino)
    return raiz


@pytest.fixture
def con_inventado(raw_inventado):
    """DuckDB em memória com raw e refined criados pelo código real, sobre dado inventado."""
    con = duckdb.connect(":memory:")
    load_raw.executar(con, raw_inventado)
    build.construir_refined(con)
    yield con
    con.close()
