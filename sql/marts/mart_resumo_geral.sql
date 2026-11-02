-- Pergunta: qual o retrato geral dos dados em uma linha só?
-- Grão: 1 linha com os KPIs. qtd_lendarios não inclui míticos (Mew).
-- Golpes distintos vale para a regra red-blue; empate no mais forte desempata por pokemon_id.
-- Origem: refined.pokemon JOIN refined.species, refined.pokemon_type, refined.pokemon_ability, refined.pokemon_move.
CREATE OR REPLACE TABLE marts.mart_resumo_geral AS
WITH mais_forte AS (
    SELECT name, total_stats
    FROM refined.pokemon
    ORDER BY total_stats DESC, pokemon_id
    LIMIT 1
),
pokemon_especie AS (
    SELECT
        COUNT(*)                                   AS total_pokemon,
        COUNT(*) FILTER (WHERE s.is_legendary)     AS qtd_lendarios
    FROM refined.pokemon AS p
    JOIN refined.species AS s ON s.species_id = p.pokemon_id
)
SELECT
    e.total_pokemon,
    (SELECT COUNT(DISTINCT type_name) FROM refined.pokemon_type)       AS tipos_distintos,
    (SELECT COUNT(DISTINCT ability_name) FROM refined.pokemon_ability) AS habilidades_distintas,
    (SELECT COUNT(DISTINCT move_name) FROM refined.pokemon_move)       AS golpes_distintos,
    e.qtd_lendarios,
    f.name                                                             AS pokemon_maior_total_stats,
    f.total_stats                                                      AS maior_total_stats
FROM pokemon_especie AS e
CROSS JOIN mais_forte AS f;
