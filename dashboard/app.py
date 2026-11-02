"""Painel Pokémon: lê só da camada marts.

Regra do projeto: nenhum cálculo aqui. Todo número vem pronto de um SELECT * FROM marts.<tabela>;
os filtros só escolhem linhas ou qual coluna mostrar. Indicador novo nasce em sql/marts.
"""
from pathlib import Path

import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st

BANCO = Path(__file__).resolve().parents[1] / "warehouse" / "pokemon.duckdb"

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


st.set_page_config(page_title="Pokémon 1ª geração", layout="wide")
st.title("Pokémon da 1ª geração")
st.caption("Fonte: PokeAPI. Todos os números vêm da camada marts do DuckDB; o painel não calcula nada.")

if not BANCO.exists():
    st.error("Banco não encontrado. Rode primeiro: python run_pipeline.py")
    st.stop()

resumo = ler_mart("mart_resumo_geral").iloc[0]
stats_por_tipo = ler_mart("mart_stats_por_tipo")
top10 = ler_mart("mart_top10_total_stats")
categorias = ler_mart("mart_lendarios_vs_comuns")
fraquezas = ler_mart("mart_fraquezas_por_tipo")
habitat = ler_mart("mart_habitat")
habilidades = ler_mart("mart_habilidades_mais_comuns")

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
