# Conferência entre camadas

Arquivo gerado por `python run_pipeline.py` (`src/checks.py`). Não edite à mão.

Data da extração da API: 2026-11-02.

| Conferência | Esperado | Obtido | Resultado |
|---|---:|---:|---|
| raw.pokemon: linhas | 151 | 151 | OK |
| raw.pokemon_species: linhas | 151 | 151 | OK |
| raw.pokemon: id do payload diferente do nome do arquivo | 0 | 0 | OK |
| raw.pokemon_species: id do payload diferente do nome do arquivo | 0 | 0 | OK |
| raw.pokemon: payload diferente do arquivo em disco | 0 | 0 | OK |
| raw.pokemon_species: payload diferente do arquivo em disco | 0 | 0 | OK |
| raw.type: payload diferente do arquivo em disco | 0 | 0 | OK |
| refined.pokemon: linhas (raw.pokemon) | 151 | 151 | OK |
| refined.species: linhas (raw.pokemon_species) | 151 | 151 | OK |
| refined.pokemon_type: linhas (soma de len(types) no raw) | 218 | 218 | OK |
| refined.pokemon_ability: linhas (soma de len(abilities) no raw) | 395 | 395 | OK |
| Golpes ANTES da regra: linhas de version_group_details no raw | - | 163908 | registro |
| Golpes de red-blue no raw, antes do distinto | - | 4128 | registro |
| Golpes DEPOIS da regra: refined.pokemon_move (red-blue) | - | 4128 | registro |
| refined.pokemon_move: repetidos no grão | 0 | 0 | OK |
| Pokémon sem nenhum golpe na regra | 0 | 0 | OK |
| Anti-join refined.pokemon sem refined.species | 0 | 0 | OK |
| Anti-join refined.species sem refined.pokemon | 0 | 0 | OK |
| pokemon_id = species_id com nome diferente | 0 | 0 | OK |
| Anti-join refined.pokemon_type sem refined.pokemon | 0 | 0 | OK |
| Anti-join refined.pokemon_ability sem refined.pokemon | 0 | 0 | OK |
| Anti-join refined.pokemon_move sem refined.pokemon | 0 | 0 | OK |
| Espécies fora da generation-i | 0 | 0 | OK |
| Tipos de pokemon_type sem linha em raw.type | 0 | 0 | OK |
| Relações de dano ANTES do filtro de tipos (sentido *_to) | - | 115 | registro |
| Relações de dano DEPOIS do filtro: refined.type_damage | 110 | 110 | OK |
| Relações *_to que não aparecem em *_from, ou o inverso (dentro do escopo) | 0 | 0 | OK |
| mart_stats_por_tipo: soma de qtd_pokemon (linhas de pokemon_type) | 218 | 218 | OK |
| mart_top10_total_stats: Pokémon distintos | 10 | 10 | OK |
| mart_lendarios_vs_comuns: soma de qtd_pokemon | 151 | 151 | OK |
| mart_fraquezas_por_tipo: soma das relações (linhas de type_damage) | 110 | 110 | OK |
| mart_habitat: soma de qtd_pokemon | 151 | 151 | OK |
| mart_habitat: Pokémon na linha 'sem informação' (habitat nulo em refined.species) | 0 | 0 | OK |
| mart_habilidades_mais_comuns: linhas | 15 | 15 | OK |
| mart_habilidades_mais_comuns: normal + oculta diferente do total | 0 | 0 | OK |
| mart_cadeias_evolucao: soma de qtd_pokemon | 151 | 151 | OK |
| mart_resumo_geral: total_pokemon | 151 | 151 | OK |
| mart_pokedex: linhas | 151 | 151 | OK |
