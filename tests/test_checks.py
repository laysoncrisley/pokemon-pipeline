"""A conferência só vale se for capaz de reprovar: estes testes provocam o erro de propósito."""
import pytest

from src import build, checks


def _resultado(conferencias, descricao):
    return next(item for item in conferencias if item.descricao.startswith(descricao))


def test_contagens_do_dado_inventado_batem(con_inventado):
    conferencias = checks.conferir_refined(con_inventado)
    assert _resultado(conferencias, "refined.pokemon_type").ok
    assert _resultado(conferencias, "refined.pokemon_ability").ok
    assert _resultado(conferencias, "Golpes ANTES").obtido == 7
    assert _resultado(conferencias, "Golpes DEPOIS").obtido == 4


def test_filha_orfa_reprova_o_anti_join(con_inventado):
    con_inventado.execute("INSERT INTO refined.pokemon_type VALUES (1234, 1, 'fogo')")
    conferencias = checks.conferir_refined(con_inventado)
    assert not _resultado(conferencias, "Anti-join refined.pokemon_type").ok
    assert not _resultado(conferencias, "refined.pokemon_type: linhas").ok


def test_mart_pokedex_com_menos_de_151_linhas_reprova(con_inventado):
    build.construir_marts(con_inventado)
    resultado = _resultado(checks.conferir_marts(con_inventado), "mart_pokedex: linhas")
    assert (resultado.obtido, resultado.esperado, resultado.ok) == (1, 151, False)


def test_payload_alterado_na_raw_e_detectado(con_inventado, raw_inventado):
    (raw_inventado / "pokemon" / "9001.json").write_text('{"id": 9001}', encoding="utf-8")
    conferencias = checks.conferir_raw(con_inventado, raw_inventado)
    assert _resultado(conferencias, "raw.pokemon: payload").obtido == 1


def test_validar_para_quando_algo_nao_bate():
    with pytest.raises(checks.ErroDeConferencia, match="contagem x"):
        checks.validar([checks.Conferencia("contagem x", obtido=1, esperado=2)])


def test_registro_sem_esperado_nao_reprova():
    checks.validar([checks.Conferencia("só registro", obtido=99)])


def test_relatorio_mostra_o_erro(tmp_path):
    caminho = tmp_path / "conferencia.md"
    checks.gravar_relatorio([checks.Conferencia("contagem x", obtido=1, esperado=2)], "2026-01-01", caminho)
    conteudo = caminho.read_text(encoding="utf-8")
    assert "| contagem x | 2 | 1 | ERRO |" in conteudo
    assert "2026-01-01" in conteudo
