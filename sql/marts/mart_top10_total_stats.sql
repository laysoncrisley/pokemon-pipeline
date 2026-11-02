-- Pergunta: quais são os 10 Pokémon mais fortes por total_stats, e eles são lendários ou míticos?
-- Grão: 1 linha por Pokémon do ranking (10 linhas). Empate em total_stats desempata por pokemon_id.
-- Origem: refined.pokemon JOIN refined.species JOIN refined.pokemon_type.
-- Os tipos são agregados antes do JOIN para o tipo duplo não repetir o Pokémon no ranking.
CREATE OR REPLACE TABLE marts.mart_top10_total_stats AS
WITH tipos AS (
    SELECT pokemon_id, STRING_AGG(type_name, '/' ORDER BY slot) AS tipos
    FROM refined.pokemon_type
    GROUP BY pokemon_id
),
ranking AS (
    SELECT
        ROW_NUMBER() OVER (ORDER BY p.total_stats DESC, p.pokemon_id) AS posicao,
        p.pokemon_id,
        p.name,
        t.tipos,
        p.total_stats,
        s.is_legendary,
        s.is_mythical
    FROM refined.pokemon AS p
    JOIN refined.species AS s ON s.species_id = p.pokemon_id
    JOIN tipos AS t ON t.pokemon_id = p.pokemon_id
)
SELECT *
FROM ranking
WHERE posicao <= 10
ORDER BY posicao;
