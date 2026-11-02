-- Pergunta: quais as 15 habilidades presentes em mais Pokémon, como normal e como oculta?
-- Grão: 1 linha por habilidade (15 linhas). Empate em qtd_pokemon desempata pelo nome.
-- Origem: refined.pokemon_ability JOIN refined.pokemon.
CREATE OR REPLACE TABLE marts.mart_habilidades_mais_comuns AS
WITH contagem AS (
    SELECT
        a.ability_name,
        COUNT(DISTINCT p.pokemon_id)                                 AS qtd_pokemon,
        COUNT(DISTINCT p.pokemon_id) FILTER (WHERE NOT a.is_hidden)  AS qtd_como_normal,
        COUNT(DISTINCT p.pokemon_id) FILTER (WHERE a.is_hidden)      AS qtd_como_oculta
    FROM refined.pokemon_ability AS a
    JOIN refined.pokemon AS p ON p.pokemon_id = a.pokemon_id
    GROUP BY a.ability_name
)
SELECT
    ROW_NUMBER() OVER (ORDER BY qtd_pokemon DESC, ability_name) AS posicao,
    ability_name,
    qtd_pokemon,
    qtd_como_normal,
    qtd_como_oculta
FROM contagem
QUALIFY posicao <= 15
ORDER BY posicao;
