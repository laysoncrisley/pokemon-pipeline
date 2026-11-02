-- Pergunta: quais tipos têm, em média, os Pokémon mais fortes em cada atributo?
-- Grão: 1 linha por tipo. Pokémon de tipo duplo conta nos dois tipos.
-- Origem: refined.pokemon_type JOIN refined.pokemon.
CREATE OR REPLACE TABLE marts.mart_stats_por_tipo AS
SELECT
    t.type_name,
    COUNT(*)                         AS qtd_pokemon,
    ROUND(AVG(p.hp), 2)              AS media_hp,
    ROUND(AVG(p.attack), 2)          AS media_attack,
    ROUND(AVG(p.defense), 2)         AS media_defense,
    ROUND(AVG(p.special_attack), 2)  AS media_special_attack,
    ROUND(AVG(p.special_defense), 2) AS media_special_defense,
    ROUND(AVG(p.speed), 2)           AS media_speed,
    ROUND(AVG(p.total_stats), 2)     AS media_total_stats
FROM refined.pokemon_type AS t
JOIN refined.pokemon AS p ON p.pokemon_id = t.pokemon_id
GROUP BY t.type_name
ORDER BY media_total_stats DESC, t.type_name;
