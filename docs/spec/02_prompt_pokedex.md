Quero mudar o visual do dashboard para um layout estilo Pokédex e atualizar a documentação. Trabalhe sozinho até o fim, sem me pedir confirmação. Não faça push.

## Regras do desafio que continuam valendo
- O dashboard lê SÓ da camada marts (`SELECT * FROM marts.<tabela>`, com filtro por id no máximo). Nenhum cálculo na tela: nada de média, soma, groupby nem conta no app. Tudo o que for exibido precisa vir pronto de um mart.
- O mart novo tem seu próprio arquivo `.sql`, com o comentário de pergunta, grão e origem, e um teste em `tests/test_sql_marts.py` com dado inventado.

## 1. Dados novos
- Em `refined.species`, adicione `genus` (o texto em inglês de `genera[]` onde `language.name = 'en'`, ex.: "Mouse Pokémon"). Pode ser nulo. Teste a extração em `tests/test_transform.py`.
- Em `refined.pokemon`, adicione `artwork_url` (`sprites.other.official-artwork.front_default`) e `sprite_url` (`sprites.front_default`). Ambos podem ser nulos. Teste também.
- Crie `sql/marts/mart_pokedex.sql`, com 1 linha por Pokémon: pokemon_id, name (com a primeira letra maiúscula, feito no SQL), numero_formatado ('#025', feito no SQL), tipo_1, tipo_2 (nulável), height_m, weight_kg, genus, hp, attack, defense, special_attack, special_defense, speed, total_stats, is_legendary, is_mythical, artwork_url, sprite_url, stat_max_escala (o maior stat individual entre os 151, calculado no SQL, para a escala das barras e do radar). Use JOIN entre pokemon, species e pokemon_type.
- Atualize o `src/checks.py` para conferir que `mart_pokedex` tem 151 linhas.

## 2. Layout (`dashboard/app.py`)
Duas abas: **Pokédex** (a primeira, padrão) e **Indicadores** (os gráficos que já existem, sem perder nenhum).

Aba Pokédex, inspirada num cartão de Pokédex:
- Fundo azul claro (#A9D6E5) na página toda e cartões brancos com cantos arredondados (border-radius 16px) e sombra leve, com CSS injetado via `st.markdown(..., unsafe_allow_html=True)`.
- Topo: campo de busca com `st.selectbox` pesquisável, listando os nomes de `mart_pokedex` (padrão: Pikachu), e um botão azul (#2A75BB) escrito "Buscar". O filtro só escolhe a linha.
- Coluna esquerda: um gráfico radar plotly (`Scatterpolar`) com os 6 stats (HP, Attack, Defense, Sp. Atk, Sp. Def, Speed), preenchimento azul-petróleo translúcido e eixo radial de 0 a `stat_max_escala`. Abaixo dele, um cartão branco com barras horizontais para os 6 stats, verde (#4FA37C) sobre trilho azul claro, com o valor ao lado. Pode ser em HTML/CSS; a largura usa o valor e o `stat_max_escala` que vêm do mart.
- Centro: nome grande em negrito, badges arredondados para o tipo 1 e o tipo 2 com a cor oficial de cada tipo (dicionário de cores no app é estilo, não cálculo), badge verde com o `numero_formatado`, a linha "altura m · peso kg" e um cartão branco com o `genus`. Mostre um selo "Lendário" ou "Mítico" quando for o caso.
- Coluna direita: imagem grande do `artwork_url` e, embaixo, o `sprite_url` pequeno. Se a URL for nula ou não carregar, mostre um aviso discreto em vez de quebrar a tela.
- Precisa ficar legível em tela de notebook e não pode ter rolagem horizontal.

## 3. Conferir e documentar
- Rode `python run_pipeline.py` (usando o cache, sem `--refresh`), depois `pytest -v` (tudo verde) e suba o `streamlit run dashboard/app.py` para confirmar que as duas abas abrem sem erro, com Pikachu (25), Mewtwo (150) e um Pokémon de tipo duplo, como Charizard (6).
- Atualize o README: o novo indicador na tabela de indicadores, o grão do `mart_pokedex`, as colunas novas do refined, uma descrição das duas abas do dashboard e a observação de que as imagens vêm das URLs da PokeAPI e precisam de internet para aparecer. Registre também em `docs/decisoes.md` o motivo do `stat_max_escala` vir do SQL.
- Se algo não bateu durante a mudança (contagem, campo com outro nome, imagem nula), acrescente o caso real à seção "Onde a IA errou ou assumiu algo". Não invente casos.

## 4. Commits (um por etapa)
1. `feat(refined): genus, artwork e sprite do Pokémon`
2. `feat(marts): mart_pokedex para o cartão do dashboard`
3. `feat(dashboard): layout estilo Pokédex com radar, barras de stats e artwork`
4. `docs: README e decisões atualizados com a Pokédex`

No final, mostre a saída do pipeline, a do pytest e o `git log --oneline -5`.
