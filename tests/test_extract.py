import json
from unittest import mock

import pytest
import requests

from src import config, extract

CORPO_POKEMON = '{"id":  1,\n"name":"é-acentuado", "types": [{"slot": 1, "type": {"name": "fogo"}}]}'
CORPO_TIPO = '{"name":"fogo"}'


def resposta(status: int = 200, texto: str = CORPO_POKEMON) -> mock.Mock:
    return mock.Mock(status_code=status, text=texto)


def sessao_falsa() -> mock.Mock:
    """Devolve o corpo certo conforme o endpoint, como a API faria."""
    sessao = mock.Mock()
    sessao.get.side_effect = lambda url, timeout: resposta(texto=CORPO_TIPO if "/type/" in url else CORPO_POKEMON)
    return sessao


@pytest.fixture(autouse=True)
def sem_espera():
    with mock.patch("src.extract.time.sleep") as dormir:
        yield dormir


def test_sessao_identifica_o_projeto():
    assert extract.criar_sessao().headers["User-Agent"] == "desafio-engenharia-dados-jr"


def test_salva_exatamente_o_texto_da_resposta(tmp_path):
    extract.executar(raw_dir=tmp_path, ids=[1], sessao=sessao_falsa())
    # Compara bytes: espaços, \n e acento precisam sobreviver sem virar \r\n no Windows.
    assert (tmp_path / "pokemon" / "1.json").read_bytes() == CORPO_POKEMON.encode("utf-8")


def test_baixa_pokemon_species_e_so_os_tipos_presentes(tmp_path):
    sessao = sessao_falsa()
    resumo = extract.executar(raw_dir=tmp_path, ids=[1], sessao=sessao)
    urls = [chamada.args[0] for chamada in sessao.get.call_args_list]
    assert urls == [
        f"{config.BASE_URL}/pokemon/1",
        f"{config.BASE_URL}/pokemon-species/1",
        f"{config.BASE_URL}/type/fogo",
    ]
    assert resumo == {"baixados": 3, "cache": 0, "total": 3}


def test_cache_nao_chama_a_api_de_novo(tmp_path):
    extract.executar(raw_dir=tmp_path, ids=[1], sessao=sessao_falsa())
    sessao = sessao_falsa()
    resumo = extract.executar(raw_dir=tmp_path, ids=[1], sessao=sessao)
    sessao.get.assert_not_called()
    assert resumo == {"baixados": 0, "cache": 3, "total": 3}


def test_refresh_ignora_o_cache_e_sobrescreve(tmp_path):
    extract.executar(raw_dir=tmp_path, ids=[1], sessao=sessao_falsa())
    novo = CORPO_POKEMON.replace("é-acentuado", "versao-nova")
    sessao = mock.Mock()
    sessao.get.side_effect = lambda url, timeout: resposta(texto=novo)
    extract.executar(refresh=True, raw_dir=tmp_path, ids=[1], sessao=sessao)
    assert sessao.get.call_count == 3
    assert "versao-nova" in (tmp_path / "pokemon" / "1.json").read_text(encoding="utf-8")


def test_manifest_registra_url_status_e_horario(tmp_path):
    extract.executar(raw_dir=tmp_path, ids=[1], sessao=sessao_falsa())
    entradas = json.loads((tmp_path / "_manifest.json").read_text(encoding="utf-8"))
    assert {e["arquivo"] for e in entradas} == {"pokemon/1.json", "pokemon_species/1.json", "type/fogo.json"}
    primeira = next(e for e in entradas if e["arquivo"] == "pokemon/1.json")
    assert primeira["url"] == f"{config.BASE_URL}/pokemon/1"
    assert primeira["status"] == 200
    assert primeira["baixado_em"].startswith("20")


def test_cache_mantem_o_registro_do_download_original(tmp_path):
    extract.executar(raw_dir=tmp_path, ids=[1], sessao=sessao_falsa())
    antes = (tmp_path / "_manifest.json").read_text(encoding="utf-8")
    extract.executar(raw_dir=tmp_path, ids=[1], sessao=sessao_falsa())
    assert (tmp_path / "_manifest.json").read_text(encoding="utf-8") == antes


def test_tenta_de_novo_com_espera_crescente(sem_espera):
    sessao = mock.Mock()
    sessao.get.side_effect = [resposta(500), resposta(503), resposta(200)]
    assert extract.baixar(sessao, "http://x").status_code == 200
    assert sessao.get.call_count == 3
    esperas = [chamada.args[0] for chamada in sem_espera.call_args_list]
    assert esperas == [1.0, 2.0]


def test_erro_de_conexao_tambem_tenta_de_novo():
    sessao = mock.Mock()
    sessao.get.side_effect = [requests.ConnectionError("caiu"), resposta(200)]
    assert extract.baixar(sessao, "http://x").status_code == 200


def test_404_falha_sem_repetir():
    sessao = mock.Mock()
    sessao.get.return_value = resposta(404)
    with pytest.raises(extract.ErroDeDownload, match="404"):
        extract.baixar(sessao, "http://x")
    assert sessao.get.call_count == 1


def test_falha_definitiva_nao_deixa_arquivo_para_o_cache(tmp_path):
    sessao = mock.Mock()
    sessao.get.return_value = resposta(500)
    with pytest.raises(extract.ErroDeDownload):
        extract.executar(raw_dir=tmp_path, ids=[1], sessao=sessao)
    assert sessao.get.call_count == config.TENTATIVAS
    assert list((tmp_path).rglob("*.json")) == [tmp_path / "_manifest.json"]
