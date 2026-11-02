"""Painel Pokémon: lê só da camada marts.

Regra do projeto: nenhum cálculo aqui. Todo número vem pronto de um SELECT * FROM marts.<tabela>;
os filtros só escolhem linhas ou qual coluna mostrar. Indicador novo nasce em sql/marts.
Cores, CSS e rótulos daqui são estilo. A largura das barras de stats é um calc() que o navegador resolve.
"""
import os
import sys
from html import escape
from pathlib import Path

import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# O Streamlit só coloca dashboard/ no sys.path; run_pipeline.py e src/ ficam na raiz.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import run_pipeline
from src import checks, config, extract

BANCO = config.WAREHOUSE_DB

COR_SERIE_1 = "#2a78d6"
COR_SERIE_2 = "#eb6834"
ESCALA_AZUL = ["#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]

METRICAS = {
    "Total de stats": "media_total_stats",
    "HP": "media_hp",
    "Ataque": "media_attack",
    "Defesa": "media_defense",
    "Ataque especial": "media_special_attack",
    "Defesa especial": "media_special_defense",
    "Velocidade": "media_speed",
}

# Rótulo na tela -> coluna de mart_pokedex
STATS_POKEDEX = {
    "HP": "hp",
    "Attack": "attack",
    "Defense": "defense",
    "Sp. Atk": "special_attack",
    "Sp. Def": "special_defense",
    "Speed": "speed",
}

TEXTO_ESCURO = "#1F2933"
TEXTO_CLARO = "#FFFFFF"
# Cor oficial do tipo -> (fundo, texto com o maior contraste sobre esse fundo)
CORES_TIPO = {
    "normal": ("#A8A77A", TEXTO_ESCURO),
    "fire": ("#EE8130", TEXTO_ESCURO),
    "water": ("#6390F0", TEXTO_ESCURO),
    "electric": ("#F7D02C", TEXTO_ESCURO),
    "grass": ("#7AC74C", TEXTO_ESCURO),
    "ice": ("#96D9D6", TEXTO_ESCURO),
    "fighting": ("#C22E28", TEXTO_CLARO),
    "poison": ("#A33EA1", TEXTO_CLARO),
    "ground": ("#E2BF65", TEXTO_ESCURO),
    "flying": ("#A98FF3", TEXTO_ESCURO),
    "psychic": ("#F95587", TEXTO_ESCURO),
    "bug": ("#A6B91A", TEXTO_ESCURO),
    "rock": ("#B6A136", TEXTO_ESCURO),
    "ghost": ("#735797", TEXTO_CLARO),
    "dragon": ("#6F35FC", TEXTO_CLARO),
    "steel": ("#B7B7CE", TEXTO_ESCURO),
    "fairy": ("#D685AD", TEXTO_ESCURO),
}
COR_TIPO_DESCONHECIDO = ("#68707A", TEXTO_CLARO)

CSS = """
<style>
.stApp { background: #A9D6E5; color: #1F2933; }
[data-testid="stHeader"] { background: transparent; }
[data-testid="stMainBlockContainer"] { padding-top: 1.5rem; }
.stApp h1 { font-size: 2.25rem; padding-top: 0; }
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] * { color: #2B4552; }
[data-testid="stMetricValue"] { font-size: 1.5rem; }
.cartao, [data-testid="stForm"], [data-testid="stPlotlyChart"], [data-testid="stMetric"],
[data-testid="stExpander"], [data-testid="stDataFrame"] {
    background: #FFFFFF; border-radius: 16px; box-shadow: 0 2px 8px rgba(31, 41, 51, 0.15);
}
.cartao { padding: 16px; margin-bottom: 16px; }
[data-testid="stForm"] { padding: 16px; }
[data-testid="stMetric"] { padding: 12px 16px; }
[data-testid="stPlotlyChart"], [data-testid="stDataFrame"] { overflow: hidden; }
[data-testid="stExpander"] details { border: none; }
[data-testid="stFormSubmitButton"] button {
    background: #2A75BB; border: none; color: #FFFFFF; font-weight: 700; width: 100%;
}
[data-testid="stFormSubmitButton"] button:hover { background: #1F5C96; color: #FFFFFF; }
.stat { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; font-size: 0.9rem; }
.stat:last-child { margin-bottom: 0; }
.stat-nome { flex: 0 0 56px; }
.stat-trilho { flex: 1; min-width: 0; height: 12px; background: #CFE8F1; border-radius: 6px; overflow: hidden; }
.stat-barra { height: 100%; background: #4FA37C; border-radius: 6px; }
.stat-valor { flex: 0 0 32px; text-align: right; font-weight: 700; font-variant-numeric: tabular-nums; }
.stat-total { margin-top: 12px; padding-top: 8px; border-top: 1px solid #E1E8EC; display: flex;
    justify-content: space-between; font-weight: 700; }
.pokemon-nome { font-size: 2.6rem; font-weight: 800; line-height: 1.15; overflow-wrap: anywhere; margin-bottom: 12px; }
.badges { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 12px; }
.badge { padding: 4px 14px; border-radius: 999px; font-weight: 700; font-size: 0.9rem; }
.badge-tipo { text-transform: capitalize; }
.badge-numero { background: #4FA37C; color: #1F2933; }
.badge-lendario { background: #F4C430; color: #1F2933; }
.badge-mitico { background: #7E57C2; color: #FFFFFF; }
.pokemon-medidas { font-size: 1.15rem; margin-bottom: 16px; }
.pokemon-genus { font-size: 1.1rem; font-weight: 600; text-align: center; }
.imagens { text-align: center; }
.artwork { display: block; width: 100%; max-width: 280px; margin: 0 auto; aspect-ratio: 1; }
.sprite { display: block; width: 96px; height: 96px; margin: 8px auto 0; }
.aviso-imagem { color: #5A6B75; font-size: 0.85rem; padding: 8px; }
.artwork .aviso-imagem { padding-top: 40%; }
</style>
"""


@st.cache_resource(show_spinner=False)
def preparar_banco() -> None:
    """Na primeira sessão do servidor, cria o banco se ele não existir. Sessões simultâneas esperam a mesma execução."""
    if BANCO.exists():
        return
    # Monta em um arquivo à parte: uma queda no meio não deixa um banco incompleto com o nome definitivo.
    temporario = BANCO.with_suffix(".tmp")
    for sobra in BANCO.parent.glob(f"{temporario.name}*"):
        sobra.unlink()
    run_pipeline.executar(banco=temporario)
    os.replace(temporario, BANCO)


def ler_mart(tabela: str) -> pd.DataFrame:
    # Conexão curta e só leitura: o painel aberto não trava o run_pipeline.py.
    with duckdb.connect(str(BANCO), read_only=True) as con:
        return con.execute(f"SELECT * FROM marts.{tabela}").df()


def estilizar(figura, altura: int = 360):
    figura.update_layout(height=altura, margin=dict(l=8, r=32, t=8, b=8), bargap=0.35)
    figura.update_traces(marker_cornerradius=4, selector=dict(type="bar"))
    return figura


def barras(dados: pd.DataFrame, valor: str, categoria: str, rotulo: str, altura: int = 360):
    """Barras horizontais de uma série, na ordem em que as linhas chegam."""
    figura = px.bar(
        dados,
        x=valor,
        y=categoria,
        orientation="h",
        text=valor,
        labels={valor: rotulo, categoria: ""},
        color_discrete_sequence=[COR_SERIE_1],
    )
    figura.update_traces(textposition="outside", cliponaxis=False)
    figura.update_yaxes(categoryorder="array", categoryarray=list(dados[categoria])[::-1])
    return estilizar(figura, altura)


def tabela(dados: pd.DataFrame) -> None:
    with st.expander("Ver tabela"):
        st.dataframe(dados, hide_index=True)


def html_imagem(url, classe: str, descricao: str) -> str:
    """<object> mostra o conteúdo interno se a imagem não carregar, sem depender de JavaScript."""
    aviso = f'<div class="aviso-imagem">{descricao} indisponível</div>'
    if pd.isna(url):
        return f'<div class="{classe}">{aviso}</div>'
    return f'<object class="{classe}" data="{escape(url)}" type="image/png" aria-label="{descricao}">{aviso}</object>'


def html_badge(texto: str, classe: str, estilo: str = "") -> str:
    return f'<span class="badge {classe}" style="{estilo}">{escape(texto)}</span>'


def html_badge_tipo(tipo: str) -> str:
    fundo, cor_texto = CORES_TIPO.get(tipo, COR_TIPO_DESCONHECIDO)
    return html_badge(tipo, "badge-tipo", f"background:{fundo};color:{cor_texto}")


def html_barras_stats(pokemon: pd.Series) -> str:
    linhas = "".join(
        f'<div class="stat"><span class="stat-nome">{rotulo}</span>'
        f'<div class="stat-trilho"><div class="stat-barra" '
        f'style="width:calc(100% * {pokemon[coluna]} / {pokemon["stat_max_escala"]})"></div></div>'
        f'<span class="stat-valor">{pokemon[coluna]}</span></div>'
        for rotulo, coluna in STATS_POKEDEX.items()
    )
    total = f'<div class="stat-total"><span>Total</span><span>{pokemon["total_stats"]}</span></div>'
    return f'<div class="cartao">{linhas}{total}</div>'


def html_identidade(pokemon: pd.Series) -> str:
    badges = [html_badge_tipo(pokemon["tipo_1"])]
    if pd.notna(pokemon["tipo_2"]):
        badges.append(html_badge_tipo(pokemon["tipo_2"]))
    badges.append(html_badge(pokemon["numero_formatado"], "badge-numero"))
    if pokemon["is_legendary"]:
        badges.append(html_badge("Lendário", "badge-lendario"))
    if pokemon["is_mythical"]:
        badges.append(html_badge("Mítico", "badge-mitico"))
    genus = escape(pokemon["genus"]) if pd.notna(pokemon["genus"]) else "Espécie não informada"
    # Só troca o separador decimal da exibição; o valor vem pronto do mart.
    altura = f'{pokemon["height_m"]:.1f}'.replace(".", ",")
    peso = f'{pokemon["weight_kg"]:.1f}'.replace(".", ",")
    return (
        f'<div class="pokemon-nome">{escape(pokemon["name"])}</div>'
        f'<div class="badges">{"".join(badges)}</div>'
        f'<div class="pokemon-medidas">{altura} m · {peso} kg</div>'
        f'<div class="cartao pokemon-genus">{genus}</div>'
    )


def radar_stats(pokemon: pd.Series) -> go.Figure:
    rotulos = list(STATS_POKEDEX)
    valores = [pokemon[coluna] for coluna in STATS_POKEDEX.values()]
    figura = go.Figure(
        go.Scatterpolar(
            # O primeiro ponto repetido só fecha o desenho do polígono.
            r=valores + valores[:1],
            theta=rotulos + rotulos[:1],
            fill="toself",
            fillcolor="rgba(0, 128, 128, 0.35)",
            line=dict(color="#0F766E", width=2),
            marker=dict(size=8, color="#0F766E"),
            hovertemplate="%{theta}: %{r}<extra></extra>",
        )
    )
    figura.update_layout(
        height=280,
        margin=dict(l=48, r=48, t=24, b=24),
        showlegend=False,
        dragmode=False,
        polar=dict(
            bgcolor="#FFFFFF",
            radialaxis=dict(range=[0, pokemon["stat_max_escala"]], gridcolor="#E1E8EC", tickfont=dict(size=10, color="#5A6B75")),
            angularaxis=dict(rotation=90, direction="clockwise", gridcolor="#E1E8EC", tickfont=dict(size=12, color="#1F2933")),
        ),
    )
    return figura


def mostrar_pokedex(pokedex: pd.DataFrame) -> None:
    nomes = list(pokedex["name"])
    with st.form("busca"):
        campo, botao = st.columns([6, 1], vertical_alignment="bottom")
        escolhido = campo.selectbox("Buscar Pokémon", nomes, index=nomes.index("Pikachu"))
        botao.form_submit_button("Buscar")

    pokemon = pokedex[pokedex["name"] == escolhido].iloc[0]
    esquerda, centro, direita = st.columns([1.15, 1, 1.05], gap="medium")
    with esquerda:
        st.plotly_chart(radar_stats(pokemon), config={"displayModeBar": False}, key="radar")
        st.markdown(html_barras_stats(pokemon), unsafe_allow_html=True)
    with centro:
        st.markdown(html_identidade(pokemon), unsafe_allow_html=True)
    with direita:
        artwork = html_imagem(pokemon["artwork_url"], "artwork", "Imagem")
        sprite = html_imagem(pokemon["sprite_url"], "sprite", "Sprite")
        st.markdown(f'<div class="cartao imagens">{artwork}{sprite}</div>', unsafe_allow_html=True)


st.set_page_config(page_title="Pokémon 1ª geração", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)
st.title("Pokémon da 1ª geração")
st.caption("Fonte: PokeAPI. Todos os números vêm da camada marts do DuckDB; o painel não calcula nada.")

try:
    with st.spinner("Preparando os dados pela primeira vez, leva cerca de 2 minutos..."):
        preparar_banco()
except (extract.ErroDeDownload, checks.ErroDeConferencia) as erro:
    # Exceção não entra no cache: o próximo acesso tenta de novo, aproveitando o que já foi baixado.
    st.error(f"Não foi possível preparar os dados. Recarregue a página para tentar de novo.\n\n{erro}")
    st.stop()

resumo = ler_mart("mart_resumo_geral").iloc[0]
stats_por_tipo = ler_mart("mart_stats_por_tipo")
top10 = ler_mart("mart_top10_total_stats")
categorias = ler_mart("mart_lendarios_vs_comuns")
fraquezas = ler_mart("mart_fraquezas_por_tipo")
habitat = ler_mart("mart_habitat")
habilidades = ler_mart("mart_habilidades_mais_comuns")
pokedex = ler_mart("mart_pokedex")

aba_pokedex, aba_indicadores = st.tabs(["Pokédex", "Indicadores"])

with aba_pokedex:
    mostrar_pokedex(pokedex)

with aba_indicadores:
    colunas = st.columns(6)
    colunas[0].metric("Pokémon", int(resumo["total_pokemon"]))
    colunas[1].metric("Tipos", int(resumo["tipos_distintos"]))
    colunas[2].metric("Habilidades", int(resumo["habilidades_distintas"]))
    colunas[3].metric("Golpes (red-blue)", int(resumo["golpes_distintos"]))
    colunas[4].metric("Lendários (sem míticos)", int(resumo["qtd_lendarios"]))
    colunas[5].metric("Maior total de stats", f"{resumo['pokemon_maior_total_stats']} ({int(resumo['maior_total_stats'])})")

    filtro_tipos, filtro_metrica, filtro_top = st.columns([3, 1, 1], vertical_alignment="bottom")
    tipos_escolhidos = filtro_tipos.multiselect(
        "Tipos (stats por tipo e fraquezas)",
        options=sorted(stats_por_tipo["type_name"]),
        default=sorted(stats_por_tipo["type_name"]),
    )
    rotulo_metrica = filtro_metrica.selectbox("Atributo", list(METRICAS))
    so_especiais = filtro_top.checkbox("Top 10: só lendários e míticos")

    st.header("Stats por tipo")
    st.caption("Média por tipo. Pokémon de tipo duplo conta nos dois tipos, por isso a soma das quantidades passa de 151.")
    coluna_metrica = METRICAS[rotulo_metrica]
    stats_filtrado = stats_por_tipo[stats_por_tipo["type_name"].isin(tipos_escolhidos)].sort_values(coluna_metrica, ascending=False)
    if stats_filtrado.empty:
        st.info("Escolha ao menos um tipo no filtro acima.")
    else:
        st.plotly_chart(barras(stats_filtrado, coluna_metrica, "type_name", f"{rotulo_metrica} (média)", altura=480))
        tabela(stats_filtrado)

    esquerda, direita = st.columns(2)

    with esquerda:
        st.header("Top 10 por total de stats")
        top_filtrado = top10[top10["is_legendary"] | top10["is_mythical"]] if so_especiais else top10
        st.plotly_chart(barras(top_filtrado, "total_stats", "name", "Total de stats"))
        st.dataframe(
            top_filtrado[["posicao", "name", "tipos", "total_stats", "is_legendary", "is_mythical"]],
            hide_index=True,
            column_config={
                "posicao": "#",
                "name": "Pokémon",
                "tipos": "Tipos",
                "total_stats": "Total",
                "is_legendary": "Lendário",
                "is_mythical": "Mítico",
            },
        )

    with direita:
        st.header("Fraquezas por tipo defensivo")
        st.caption(
            "Quantos tipos causam cada multiplicador. Só contam atacantes presentes nos 151: "
            "dark fica de fora, então ghost e psychic têm uma fraqueza a menos que no jogo."
        )
        fraquezas_filtrado = fraquezas[fraquezas["defending_type"].isin(tipos_escolhidos)]
        if fraquezas_filtrado.empty:
            st.info("Escolha ao menos um tipo no filtro acima.")
        else:
            matriz = fraquezas_filtrado.set_index("defending_type").rename(
                columns={"qtd_causam_2x": "2x", "qtd_causam_0_5x": "0.5x", "qtd_causam_0x": "0x"}
            )
            figura = px.imshow(
                matriz,
                text_auto=True,
                aspect="auto",
                color_continuous_scale=ESCALA_AZUL,
                labels=dict(x="Multiplicador", y="Tipo defensivo", color="Qtd. de tipos"),
            )
            figura.update_xaxes(side="top", title=None)
            figura.update_yaxes(title=None)
            figura.update_layout(height=620, margin=dict(l=8, r=8, t=8, b=8))
            st.plotly_chart(figura)
        tabela(fraquezas_filtrado)

    st.header("Lendários, míticos e comuns")
    st.caption(
        "Capture rate maior significa captura mais fácil. Grupos muito diferentes em tamanho: "
        "4 lendários, 1 mítico (Mew) e 146 comuns."
    )
    coluna_total, coluna_captura = st.columns(2)
    with coluna_total:
        st.plotly_chart(barras(categorias, "media_total_stats", "categoria", "Total de stats (média)", altura=240))
    with coluna_captura:
        st.plotly_chart(barras(categorias, "media_capture_rate", "categoria", "Capture rate (média)", altura=240))
    tabela(categorias)

    st.header("Habitat")
    st.caption("Nos 151 nenhum habitat vem nulo, então a linha \"sem informação\" não aparece com o dado atual.")
    coluna_qtd, coluna_media = st.columns(2)
    with coluna_qtd:
        st.plotly_chart(barras(habitat, "qtd_pokemon", "habitat", "Quantidade de Pokémon"))
    with coluna_media:
        st.plotly_chart(barras(habitat, "media_total_stats", "habitat", "Total de stats (média)"))
    tabela(habitat)

    st.header("Habilidades mais comuns")
    st.caption(
        "Top 15 por nº de Pokémon. Oito habilidades empatam com 6 Pokémon e só três cabem no corte, "
        "escolhidas por ordem alfabética: rivalry, shed-skin, static, sturdy e unnerve ficam de fora."
    )
    figura_habilidades = px.bar(
        habilidades,
        x=["qtd_como_normal", "qtd_como_oculta"],
        y="ability_name",
        orientation="h",
        labels={"value": "Quantidade de Pokémon", "ability_name": "", "variable": ""},
        color_discrete_map={"qtd_como_normal": COR_SERIE_1, "qtd_como_oculta": COR_SERIE_2},
    )
    figura_habilidades.for_each_trace(
        lambda traco: traco.update(name={"qtd_como_normal": "Normal", "qtd_como_oculta": "Oculta"}[traco.name])
    )
    figura_habilidades.update_yaxes(categoryorder="array", categoryarray=list(habilidades["ability_name"])[::-1])
    figura_habilidades.update_layout(legend=dict(orientation="h", y=1.08, x=0, title=None))
    st.plotly_chart(estilizar(figura_habilidades, altura=520))
    tabela(habilidades)
