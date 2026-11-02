Você vai construir do zero, nesta pasta vazia, um projeto completo de engenharia de dados para o "Desafio Final – Trilha Engenharia de Dados JR". Trabalhe de forma autônoma, sem me pedir confirmação entre etapas, até o projeto estar rodando, testado e commitado. Não pergunte, execute. Se algo falhar, corrija e siga.

## Requisitos obrigatórios do desafio
1. Fonte pública: aqui é a PokeAPI (https://pokeapi.co, docs em https://pokeapi.co/docs/v2), sem chave.
2. Duas tabelas ou mais ligadas por chave, com JOIN de verdade.
3. Três camadas separadas: `raw` (bruto, NADA alterado), `refined` (transformado) e `marts` (indicadores).
4. Cada indicador sai de um arquivo `.sql` próprio.
5. Testes com `pytest` usando dado inventado, sem abrir o banco do projeto e sem chamar a API.
6. Histórico de git com um commit por etapa (nunca tudo num commit só), mensagens em português dizendo o que mudou.
7. Dashboard opcional que lê SÓ da camada marts, sem nenhum cálculo na tela.
8. Cada decisão sobre o dado tem um motivo escrito.
9. README completo (detalhes no fim).

## Stack (não troque)
Python 3.10+, `requests`, DuckDB (arquivo `warehouse/pokemon.duckdb`), pandas, pytest, Streamlit + plotly. Tudo precisa rodar no Windows e no Linux: nada de Makefile, nada de comando só-bash. Ponto de entrada: `python run_pipeline.py`.

## Escopo do dado
Pokémon da 1ª geração: ids 1 a 151. Endpoints:
- `GET /api/v2/pokemon/{id}` → stats, tipos, habilidades, golpes, altura, peso
- `GET /api/v2/pokemon-species/{id}` → is_legendary, is_mythical, capture_rate, base_happiness, habitat, color, growth_rate, generation, evolution_chain
- `GET /api/v2/type/{name}` → só para os tipos que aparecerem nos 151 Pokémon (relações de dano)

ANTES de escrever as transformações, baixe e abra 1 JSON de cada endpoint (ex.: pokemon/1, pokemon-species/1, type/fire) e confira os nomes reais dos campos. Não confie na memória.

## Estrutura de pastas
```
data/raw/pokemon/{id}.json            # resposta da API exatamente como veio
data/raw/pokemon_species/{id}.json
data/raw/type/{name}.json
data/raw/_manifest.json               # url, status, data/hora de cada download
sql/refined/*.sql                     # um arquivo por tabela refined
sql/marts/*.sql                       # um arquivo por indicador
src/__init__.py
src/config.py                         # caminhos, BASE_URL, faixa de ids
src/extract.py                        # baixa da API para data/raw (com cache)
src/load_raw.py                       # carrega os JSONs na camada raw do DuckDB
src/transform.py                      # funções PURAS: recebem dict/lista do JSON e devolvem linhas/DataFrame
src/build.py                          # executa os .sql em ordem
src/checks.py                         # conferência de contagens entre camadas
run_pipeline.py                       # extract -> raw -> refined -> marts -> checks
tests/fixtures/                       # JSONs inventados e pequenos, no formato da API
tests/test_transform.py
tests/test_sql_marts.py
dashboard/app.py
docs/decisoes.md
docs/conferencia.md                   # gerado pelo pipeline
requirements.txt
.gitignore
README.md
```

## Extração (`src/extract.py`)
- `requests.Session` com header `User-Agent: desafio-engenharia-dados-jr`, timeout de 30s, 3 tentativas com espera crescente, `time.sleep(0.2)` entre chamadas (uso justo da API).
- Cache: se o arquivo já existe em `data/raw`, não baixa de novo. Flag `python run_pipeline.py --refresh` força novo download.
- Salva o JSON exatamente como veio (`response.text`), sem reformatar, sem remover campos.
- Grava `_manifest.json` com url, status HTTP e timestamp.
- Os JSONs de `/pokemon` são grandes (sprites e golpes por versão). Coloque `data/raw/` no `.gitignore` e explique no README e em `docs/decisoes.md` que a camada raw é recriada pelo `run_pipeline.py`. Comite apenas `data/raw/.gitkeep`.

## Camada RAW (schema `raw` no DuckDB)
Uma linha por arquivo, payload intocado:
- `raw.pokemon(pokemon_id, payload JSON, source_url, loaded_at)` → 151 linhas
- `raw.pokemon_species(species_id, payload JSON, source_url, loaded_at)` → 151 linhas
- `raw.type(type_name, payload JSON, source_url, loaded_at)`

## Camada REFINED (schema `refined`)
Use as funções de `src/transform.py` para achatar o JSON e grave as tabelas; o que for SQL fica em `sql/refined/`. Tabelas:
1. `refined.pokemon` — 1 linha por Pokémon: pokemon_id, name, height_m, weight_kg, base_experience, hp, attack, defense, special_attack, special_defense, speed, total_stats.
2. `refined.species` — 1 linha por espécie: species_id, name, is_legendary, is_mythical, capture_rate, base_happiness, habitat (nulável), color, growth_rate, generation, evolution_chain_id (extraído da url).
3. `refined.pokemon_type` — 1 linha por (pokemon_id, slot, type_name).
4. `refined.pokemon_ability` — 1 linha por (pokemon_id, ability_name, is_hidden, slot).
5. `refined.pokemon_move` — 1 linha por (pokemon_id, move_name, learn_method, min_level).
6. `refined.type_damage` — 1 linha por (attacking_type, defending_type, multiplier) a partir de `damage_relations` (2.0, 0.5, 0.0; pares ausentes = 1.0, não precisa gravar).

Armadilhas que você precisa tratar e escrever o motivo em `docs/decisoes.md`:
- `height` vem em decímetros e `weight` em hectogramas: converter para metros e kg.
- `moves[].version_group_details` repete o mesmo golpe para várias versões do jogo. Decida um critério (ex.: só o version_group `red-blue`, ou distinto por pokemon+golpe+método) e conte as linhas antes e depois para provar que não duplicou.
- `habitat` pode vir nulo; não invente valor.
- A API devolve os tipos ATUAIS, não os da época da 1ª geração (ex.: Clefairy hoje é Fairy, tipo que nem existia em 1996). Isso é decisão a registrar, não bug a esconder.
- Na lista de tipos, ignore os que não aparecem nos 151 (ex.: `unknown`, `shadow`, `stellar`).
- `pokemon_id` e `species_id` coincidem de 1 a 151: confirme com anti-join antes de usar como chave.

Conferência obrigatória gravada em `docs/conferencia.md` (e impressa pelo pipeline): 151 no raw e no refined.pokemon/species; soma de `len(types)` no raw = linhas em pokemon_type; soma de `len(abilities)` = linhas em pokemon_ability; linhas de golpes antes e depois da regra de deduplicação; anti-join das tabelas filhas contra refined.pokemon = 0. Se algo não bater, pare, corrija e anote o que estava errado.

## Camada MARTS (schema `marts`) — um `.sql` por indicador, com JOIN
Cada arquivo começa com um comentário: pergunta que responde, grão (o que é uma linha) e tabelas de origem.
1. `mart_stats_por_tipo.sql` — por tipo: qtd de Pokémon, média de cada stat e de total_stats (tipo duplo conta nos dois; dizer no README).
2. `mart_top10_total_stats.sql` — ranking com `ROW_NUMBER()` dos 10 Pokémon mais fortes por total_stats, com tipos e se é lendário/mítico.
3. `mart_lendarios_vs_comuns.sql` — compara lendários, míticos e comuns: qtd, média de total_stats, média de capture_rate.
4. `mart_fraquezas_por_tipo.sql` — para cada tipo defensivo: quantos tipos causam 2x nele, quantos causam 0.5x e quantos 0x.
5. `mart_habitat.sql` — por habitat (incluindo "sem informação"): qtd de Pokémon e média de total_stats.
6. `mart_habilidades_mais_comuns.sql` — top 15 habilidades por nº de Pokémon, separando ocultas e normais.
7. `mart_cadeias_evolucao.sql` — por evolution_chain_id: nº de Pokémon na cadeia e maior total_stats.
8. `mart_resumo_geral.sql` — 1 linha com KPIs: total de Pokémon, tipos distintos, habilidades distintas, golpes distintos, nº de lendários e o Pokémon com maior total_stats.

## Testes (pytest)
- `tests/fixtures/`: 3 a 4 JSONs inventados, mínimos, no formato real da API (inclua um Pokémon com 2 tipos, um com habitat nulo e um golpe repetido em duas versões).
- `tests/test_transform.py`: conversão de altura/peso, extração de tipos com slot, extração do evolution_chain_id da url, regra de deduplicação de golpes, habitat nulo continua nulo.
- `tests/test_sql_marts.py`: DuckDB `:memory:`, cria as tabelas refined com dados inventados, executa os `.sql` reais de `sql/marts/` e confere contra valores calculados à mão.
- `tests/test_extract.py`: testa o cache e o salvamento com a chamada HTTP mockada (`unittest.mock`), sem internet.
- Nenhum teste abre `warehouse/pokemon.duckdb` nem acessa a API. Rode `pytest -v` e só siga com tudo verde.

## Dashboard (Streamlit)
`dashboard/app.py`: abre o DuckDB com `read_only=True`, faz apenas `SELECT * FROM marts.<tabela>` e mostra KPIs do resumo, barras de stats por tipo, top 10, lendários vs comuns, heatmap/tabela de fraquezas, habitat e habilidades. Filtros só filtram linhas. Proibido groupby, média, soma ou qualquer cálculo no app. Teste com `streamlit run dashboard/app.py` (suba, confirme que não dá erro, encerre).

## Git — um commit por etapa, nesta ordem
Rode `git init -b main` se ainda não houver repositório.
1. `chore: estrutura inicial do projeto, requirements e .gitignore`
2. `feat(extract): download da PokeAPI com cache e manifest`
3. `feat(raw): carga dos JSONs brutos no DuckDB`
4. `feat(refined): tabelas pokemon e species`
5. `feat(refined): tabelas de tipos, habilidades, golpes e relações de dano`
6. `test: testes de extração e transformação com dado inventado`
7. `feat(marts): indicadores de stats, ranking, lendários e fraquezas`
8. `feat(marts): indicadores de habitat, habilidades, evolução e resumo`
9. `test: testes dos SQL dos marts em DuckDB em memória`
10. `feat(dashboard): painel Streamlit lendo só da camada marts`
11. `docs: README completo, decisões sobre o dado e seção da IA`
Não faça push; eu faço.

## README.md (em português) — precisa ter TUDO isto
- Título e objetivo em 2 linhas.
- **Fonte do dado**: PokeAPI (https://pokeapi.co), API pública e gratuita, sem chave; código e dados do projeto PokeAPI sob licença BSD-3-Clause (https://github.com/PokeAPI/pokeapi). Pokémon é marca registrada da Nintendo/Game Freak/Creatures; uso educacional, sem fins comerciais. Escopo: ids 1–151, data da extração.
- **O que é uma linha de cada tabela** (raw, refined e marts).
- **As três camadas** com diagrama mermaid: `PokeAPI -> data/raw (JSON) -> raw -> refined -> marts -> dashboard`.
- **Indicadores**: tabela com nome, pergunta que responde e arquivo `.sql` de origem.
- **Decisões sobre o dado**: resumo com link para `docs/decisoes.md`.
- **Como rodar do zero**, para Windows (PowerShell) e Linux/Mac:
  ```
  git clone <repo> && cd <pasta>
  python -m venv .venv
  .venv\Scripts\activate        (Windows)   |   source .venv/bin/activate  (Linux/Mac)
  pip install -r requirements.txt
  python run_pipeline.py        # primeira vez baixa da API (~1-2 min)
  pytest -v
  streamlit run dashboard/app.py
  ```
- **Conferência**: contagens antes/depois (copie de `docs/conferencia.md`).
- **Seção "Onde a IA errou ou assumiu algo"**: registre os casos REAIS desta construção — campo com nome diferente do que você supôs, golpes duplicados por versão, unidade de altura/peso, tipos atuais vs originais, contagem que não bateu — e como foi descoberto (quase sempre contando linhas antes e depois). Não invente casos. Termine com um bloco `TODO (autor):` para eu acrescentar o que eu mesmo conferir.

## Critério de pronto (só termine quando tudo for verdade)
- Apagando `warehouse/` e `data/raw/`, `python run_pipeline.py` roda do zero sem erro e imprime as contagens.
- `pytest -v` 100% verde, sem internet.
- O dashboard sobe sem erro.
- `git log --oneline` mostra os 11 commits acima.
- O README cobre todos os itens listados.
No final, me mostre: saída do pipeline, saída do pytest, `git log --oneline` e a lista do que eu preciso preencher à mão.
