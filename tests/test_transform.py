import pytest

from src import transform


@pytest.fixture
def pokemon(carregar_json):
    return carregar_json("pokemon_9001.json")


def test_altura_em_decimetros_vira_metros(pokemon):
    assert transform.linha_pokemon(pokemon)["height_m"] == 0.7


def test_peso_em_hectogramas_vira_kg(pokemon):
    assert transform.linha_pokemon(pokemon)["weight_kg"] == 6.9


def test_stats_com_hifen_viram_colunas_e_total_soma_os_seis(pokemon):
    linha = transform.linha_pokemon(pokemon)
    assert linha["special_attack"] == 40
    assert linha["special_defense"] == 50
    assert linha["total_stats"] == 10 + 20 + 30 + 40 + 50 + 60


def test_pokemon_com_dois_tipos_gera_duas_linhas_com_slot(pokemon):
    assert transform.linhas_tipo(pokemon) == [
        {"pokemon_id": 9001, "slot": 1, "type_name": "fogo"},
        {"pokemon_id": 9001, "slot": 2, "type_name": "voador"},
    ]


def test_habilidades_mantem_oculta_e_slot(pokemon):
    assert transform.linhas_habilidade(pokemon) == [
        {"pokemon_id": 9001, "ability_name": "chama", "is_hidden": False, "slot": 1},
        {"pokemon_id": 9001, "ability_name": "vento-oculto", "is_hidden": True, "slot": 3},
    ]


@pytest.mark.parametrize(
    "url, esperado",
    [
        ("https://pokeapi.co/api/v2/evolution-chain/42/", 42),
        ("https://pokeapi.co/api/v2/evolution-chain/7", 7),
    ],
)
def test_evolution_chain_id_vem_da_url(url, esperado):
    assert transform.extrair_evolution_chain_id(url) == esperado


def test_url_de_cadeia_inesperada_falha_em_vez_de_inventar_id():
    with pytest.raises(ValueError):
        transform.extrair_evolution_chain_id("https://pokeapi.co/api/v2/pokemon/42/")


def test_golpe_repetido_em_outra_versao_nao_duplica(pokemon):
    linhas = transform.linhas_golpe(pokemon, "red-blue")
    assert [l for l in linhas if l["move_name"] == "tackle"] == [
        {"pokemon_id": 9001, "move_name": "tackle", "learn_method": "level-up", "min_level": 1}
    ]


def test_golpe_em_nivel_ou_metodo_diferente_continua_separado(pokemon):
    linhas = transform.linhas_golpe(pokemon, "red-blue")
    leer = {(l["learn_method"], l["min_level"]) for l in linhas if l["move_name"] == "leer"}
    assert leer == {("level-up", 1), ("level-up", 15), ("machine", 0)}


def test_golpe_que_so_existe_em_outra_versao_fica_de_fora(pokemon):
    nomes = {l["move_name"] for l in transform.linhas_golpe(pokemon, "red-blue")}
    assert "golpe-so-de-outra-versao" not in nomes


def test_contagem_de_golpes_antes_e_depois_da_regra(pokemon):
    assert transform.contar_golpes_brutos(pokemon) == 7
    assert transform.contar_golpes_do_grupo(pokemon, "red-blue") == 5
    assert len(transform.linhas_golpe(pokemon, "red-blue")) == 4


def test_habitat_nulo_continua_nulo(carregar_json):
    assert transform.linha_species(carregar_json("species_9001_habitat_nulo.json"))["habitat"] is None


def test_habitat_preenchido_vira_o_nome(carregar_json):
    assert transform.linha_species(carregar_json("species_9002_com_habitat.json"))["habitat"] == "rare"


def test_species_achata_os_campos_aninhados(carregar_json):
    linha = transform.linha_species(carregar_json("species_9002_com_habitat.json"))
    assert linha["is_legendary"] is True
    assert linha["color"] == "blue"
    assert linha["growth_rate"] == "slow"
    assert linha["generation"] == "generation-i"
    assert linha["evolution_chain_id"] == 7


def test_dano_le_so_o_sentido_to(carregar_json):
    assert transform.linhas_dano(carregar_json("type_fogo.json")) == [
        {"attacking_type": "fogo", "defending_type": "voador", "multiplier": 2.0},
        {"attacking_type": "fogo", "defending_type": "fogo", "multiplier": 0.5},
        {"attacking_type": "fogo", "defending_type": "dark", "multiplier": 0.5},
    ]


def test_refined_real_preserva_habitat_nulo_no_banco(con_inventado):
    assert con_inventado.execute("SELECT habitat FROM refined.species").fetchall() == [(None,)]


def test_refined_real_grava_metros_e_kg(con_inventado):
    linha = con_inventado.execute("SELECT CAST(height_m AS VARCHAR), CAST(weight_kg AS VARCHAR) FROM refined.pokemon").fetchone()
    assert linha == ("0.7", "6.9")


def test_refined_real_descarta_tipo_fora_do_escopo_nos_dois_lados(con_inventado):
    linhas = con_inventado.execute(
        "SELECT attacking_type, defending_type, multiplier FROM refined.type_damage ORDER BY defending_type"
    ).fetchall()
    assert linhas == [("fogo", "fogo", 0.5), ("fogo", "voador", 2.0)]


def test_refined_real_grava_golpes_sem_duplicar(con_inventado):
    assert con_inventado.execute("SELECT COUNT(*) FROM refined.pokemon_move").fetchone()[0] == 4
