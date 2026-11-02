"""Executa os .sql reais de sql/marts sobre dados inventados em DuckDB :memory:.

Todos os valores esperados foram calculados à mão a partir da tabela abaixo.

 id nome  hp  atk def spa spd spe total tipos        categoria habitat chain capture
  1 a1    10  20  30  40  50  60   210  fogo/voador  comum     forest  1     100
  2 a2    20  30  40  50  60  70   270  fogo         comum     forest  1     200
  3 a3   100 100 100 100 100 100   600  agua         lendário  rare    2       3
  4 a4   100 100 100 100 100 100   600  agua/voador  mítico    (nulo)  3       5
 5-12 a5..a12: hp = total = 110, 120, ... 180, demais 0; normal; comum; sea; chain 5; capture 200
"""
import duckdb
import pytest

from src import build, config

MARTS = [
    "mart_cadeias_evolucao",
    "mart_fraquezas_por_tipo",
    "mart_habilidades_mais_comuns",
    "mart_habitat",
    "mart_lendarios_vs_comuns",
    "mart_resumo_geral",
    "mart_stats_por_tipo",
    "mart_top10_total_stats",
]


@pytest.fixture(scope="module")
def con():
    conexao = duckdb.connect(":memory:")
    conexao.execute(
        """
        CREATE SCHEMA refined;
        CREATE TABLE refined.pokemon (
            pokemon_id INTEGER, name VARCHAR, height_m DECIMAL(5, 1), weight_kg DECIMAL(6, 1),
            base_experience INTEGER, hp INTEGER, attack INTEGER, defense INTEGER,
            special_attack INTEGER, special_defense INTEGER, speed INTEGER, total_stats INTEGER
        );
        CREATE TABLE refined.species (
            species_id INTEGER, name VARCHAR, is_legendary BOOLEAN, is_mythical BOOLEAN,
            capture_rate INTEGER, base_happiness INTEGER, habitat VARCHAR, color VARCHAR,
            growth_rate VARCHAR, generation VARCHAR, evolution_chain_id INTEGER
        );
        CREATE TABLE refined.pokemon_type (pokemon_id INTEGER, slot INTEGER, type_name VARCHAR);
        CREATE TABLE refined.pokemon_ability (pokemon_id INTEGER, ability_name VARCHAR, is_hidden BOOLEAN, slot INTEGER);
        CREATE TABLE refined.pokemon_move (pokemon_id INTEGER, move_name VARCHAR, learn_method VARCHAR, min_level INTEGER);
        CREATE TABLE refined.type_damage (attacking_type VARCHAR, defending_type VARCHAR, multiplier DOUBLE);
        """
    )

    pokemons = [
        (1, "a1", 10, 20, 30, 40, 50, 60, 210),
        (2, "a2", 20, 30, 40, 50, 60, 70, 270),
        (3, "a3", 100, 100, 100, 100, 100, 100, 600),
        (4, "a4", 100, 100, 100, 100, 100, 100, 600),
    ] + [(i, f"a{i}", 60 + 10 * i, 0, 0, 0, 0, 0, 60 + 10 * i) for i in range(5, 13)]
    for id_, nome, hp, atk, dfs, spa, spd, spe, total in pokemons:
        conexao.execute(
            "INSERT INTO refined.pokemon VALUES (?, ?, 1.0, 1.0, 50, ?, ?, ?, ?, ?, ?, ?)",
            [id_, nome, hp, atk, dfs, spa, spd, spe, total],
        )

    especies = [
        (1, False, False, 100, "forest", 1),
        (2, False, False, 200, "forest", 1),
        (3, True, False, 3, "rare", 2),
        (4, False, True, 5, None, 3),
    ] + [(i, False, False, 200, "sea", 5) for i in range(5, 13)]
    for id_, lendario, mitico, captura, habitat, cadeia in especies:
        conexao.execute(
            "INSERT INTO refined.species VALUES (?, ?, ?, ?, ?, 70, ?, 'cor', 'medio', 'generation-i', ?)",
            [id_, f"a{id_}", lendario, mitico, captura, habitat, cadeia],
        )

    tipos = [(1, 1, "fogo"), (1, 2, "voador"), (2, 1, "fogo"), (3, 1, "agua"), (4, 1, "agua"), (4, 2, "voador")]
    tipos += [(i, 1, "normal") for i in range(5, 13)]
    conexao.executemany("INSERT INTO refined.pokemon_type VALUES (?, ?, ?)", tipos)

    habilidades = [
        (1, "comum", False, 1), (2, "comum", False, 1), (3, "comum", False, 1), (4, "comum", True, 3),
        (1, "segunda", False, 2), (2, "segunda", False, 2),
        (3, "abc-oculta", True, 3),
    ]
    habilidades += [(5, f"h{i:02d}", False, i) for i in range(1, 15)]  # 14 habilidades empatadas em 1
    conexao.executemany("INSERT INTO refined.pokemon_ability VALUES (?, ?, ?, ?)", habilidades)

    golpes = [(1, "tackle", "level-up", 1), (1, "leer", "level-up", 5), (2, "tackle", "machine", 0)]
    conexao.executemany("INSERT INTO refined.pokemon_move VALUES (?, ?, ?, ?)", golpes)

    danos = [
        ("agua", "fogo", 2.0), ("voador", "fogo", 0.5), ("fogo", "fogo", 0.5), ("normal", "fogo", 0.0),
        ("fogo", "agua", 0.5),
        ("fogo", "voador", 2.0), ("agua", "voador", 2.0),
    ]
    conexao.executemany("INSERT INTO refined.type_damage VALUES (?, ?, ?)", danos)

    build.construir_marts(conexao)
    yield conexao
    conexao.close()


def linhas(con, tabela):
    consulta = con.execute(f"SELECT * FROM marts.{tabela}")
    colunas = [c[0] for c in consulta.description]
    return [dict(zip(colunas, linha)) for linha in consulta.fetchall()]


def por_chave(con, tabela, chave):
    return {linha[chave]: linha for linha in linhas(con, tabela)}


def test_existe_um_sql_por_indicador():
    assert sorted(a.stem for a in config.SQL_MARTS_DIR.glob("*.sql")) == MARTS


@pytest.mark.parametrize("nome", MARTS)
def test_sql_documenta_pergunta_grao_e_origem_e_usa_join(nome):
    texto = (config.SQL_MARTS_DIR / f"{nome}.sql").read_text(encoding="utf-8")
    comentario = texto.split("CREATE OR REPLACE")[0]
    assert "-- Pergunta:" in comentario
    assert "Grão:" in comentario
    assert "Origem:" in comentario
    assert "JOIN" in texto.split("CREATE OR REPLACE")[1]


def test_stats_por_tipo_conta_tipo_duplo_nos_dois(con):
    tipos = por_chave(con, "mart_stats_por_tipo", "type_name")
    assert {t: l["qtd_pokemon"] for t, l in tipos.items()} == {"fogo": 2, "voador": 2, "agua": 2, "normal": 8}


def test_stats_por_tipo_calcula_as_medias(con):
    tipos = por_chave(con, "mart_stats_por_tipo", "type_name")
    voador = tipos["voador"]  # a1 e a4
    assert voador["media_hp"] == pytest.approx(55)
    assert voador["media_attack"] == pytest.approx(60)
    assert voador["media_defense"] == pytest.approx(65)
    assert voador["media_special_attack"] == pytest.approx(70)
    assert voador["media_special_defense"] == pytest.approx(75)
    assert voador["media_speed"] == pytest.approx(80)
    assert voador["media_total_stats"] == pytest.approx(405)
    assert tipos["fogo"]["media_total_stats"] == pytest.approx(240)
    assert tipos["agua"]["media_total_stats"] == pytest.approx(600)
    assert tipos["normal"]["media_total_stats"] == pytest.approx(145)


def test_top10_ordena_desempata_e_corta(con):
    top = linhas(con, "mart_top10_total_stats")
    assert [l["posicao"] for l in top] == list(range(1, 11))
    assert [l["name"] for l in top] == ["a3", "a4", "a2", "a1", "a12", "a11", "a10", "a9", "a8", "a7"]


def test_top10_junta_tipos_sem_repetir_pokemon_e_traz_categoria(con):
    top = por_chave(con, "mart_top10_total_stats", "name")
    assert len(top) == 10
    assert top["a4"]["tipos"] == "agua/voador"
    assert top["a1"]["tipos"] == "fogo/voador"
    assert (top["a3"]["is_legendary"], top["a3"]["is_mythical"]) == (True, False)
    assert (top["a4"]["is_legendary"], top["a4"]["is_mythical"]) == (False, True)


def test_lendarios_vs_comuns(con):
    categorias = por_chave(con, "mart_lendarios_vs_comuns", "categoria")
    assert set(categorias) == {"lendário", "mítico", "comum"}
    assert categorias["lendário"]["qtd_pokemon"] == 1
    assert categorias["lendário"]["media_total_stats"] == pytest.approx(600)
    assert categorias["lendário"]["media_capture_rate"] == pytest.approx(3)
    assert categorias["mítico"]["media_capture_rate"] == pytest.approx(5)
    assert categorias["comum"]["qtd_pokemon"] == 10
    assert categorias["comum"]["media_total_stats"] == pytest.approx(164)  # 1640 / 10
    assert categorias["comum"]["media_capture_rate"] == pytest.approx(190)  # 1900 / 10


def test_fraquezas_conta_cada_multiplicador(con):
    tipos = por_chave(con, "mart_fraquezas_por_tipo", "defending_type")
    def contagem(nome):
        return tipos[nome]["qtd_causam_2x"], tipos[nome]["qtd_causam_0_5x"], tipos[nome]["qtd_causam_0x"]
    assert contagem("fogo") == (1, 2, 1)
    assert contagem("agua") == (0, 1, 0)
    assert contagem("voador") == (2, 0, 0)


def test_fraquezas_mantem_tipo_sem_nenhuma_relacao(con):
    tipos = por_chave(con, "mart_fraquezas_por_tipo", "defending_type")
    assert (tipos["normal"]["qtd_causam_2x"], tipos["normal"]["qtd_causam_0_5x"], tipos["normal"]["qtd_causam_0x"]) == (0, 0, 0)


def test_habitat_nulo_vira_sem_informacao(con):
    habitats = por_chave(con, "mart_habitat", "habitat")
    assert set(habitats) == {"forest", "rare", "sea", "sem informação"}
    assert habitats["sem informação"]["qtd_pokemon"] == 1
    assert habitats["sem informação"]["media_total_stats"] == pytest.approx(600)
    assert habitats["forest"]["qtd_pokemon"] == 2
    assert habitats["forest"]["media_total_stats"] == pytest.approx(240)
    assert habitats["sea"]["media_total_stats"] == pytest.approx(145)


def test_habilidades_separa_normal_e_oculta(con):
    habilidades = por_chave(con, "mart_habilidades_mais_comuns", "ability_name")
    comum = habilidades["comum"]
    assert (comum["posicao"], comum["qtd_pokemon"], comum["qtd_como_normal"], comum["qtd_como_oculta"]) == (1, 4, 3, 1)
    assert (habilidades["abc-oculta"]["qtd_como_normal"], habilidades["abc-oculta"]["qtd_como_oculta"]) == (0, 1)


def test_habilidades_corta_em_15_e_desempata_pelo_nome(con):
    resultado = linhas(con, "mart_habilidades_mais_comuns")
    assert len(resultado) == 15
    assert [l["ability_name"] for l in resultado[:4]] == ["comum", "segunda", "abc-oculta", "h01"]
    assert resultado[-1]["ability_name"] == "h12"


def test_cadeias_evolucao(con):
    cadeias = por_chave(con, "mart_cadeias_evolucao", "evolution_chain_id")
    assert set(cadeias) == {1, 2, 3, 5}
    assert cadeias[1]["qtd_pokemon"] == 2
    assert cadeias[1]["maior_total_stats"] == 270
    assert cadeias[1]["membros"] == "a1, a2"
    assert cadeias[5]["qtd_pokemon"] == 8
    assert cadeias[5]["maior_total_stats"] == 180


def test_resumo_geral_tem_uma_linha_com_os_kpis(con):
    resumo = linhas(con, "mart_resumo_geral")
    assert resumo == [
        {
            "total_pokemon": 12,
            "tipos_distintos": 4,
            "habilidades_distintas": 17,  # comum, segunda, abc-oculta + 14
            "golpes_distintos": 2,
            "qtd_lendarios": 1,  # a4 é mítico e não entra
            "pokemon_maior_total_stats": "a3",  # empate com a4, menor id vence
            "maior_total_stats": 600,
        }
    ]
