-- Pergunta: como é o cartão de Pokédex de cada Pokémon, com tudo o que o painel precisa pronto para exibir?
-- Grão: 1 linha por Pokémon (151 linhas). tipo_2 é nulo em quem tem um tipo só; genus, artwork_url e sprite_url podem ser nulos.
-- stat_max_escala é o maior stat individual entre todos os Pokémon, igual em todas as linhas (motivo em docs/decisoes.md).
-- Origem: refined.pokemon JOIN refined.species JOIN refined.pokemon_type (slot 1 e slot 2).
CREATE OR REPLACE TABLE marts.mart_pokedex AS
SELECT
    p.pokemon_id,
    UPPER(LEFT(p.name, 1)) || SUBSTR(p.name, 2)         AS name,
    '#' || LPAD(CAST(p.pokemon_id AS VARCHAR), 3, '0')  AS numero_formatado,
    t1.type_name                                        AS tipo_1,
    t2.type_name                                        AS tipo_2,
    p.height_m,
    p.weight_kg,
    s.genus,
    p.hp,
    p.attack,
    p.defense,
    p.special_attack,
    p.special_defense,
    p.speed,
    p.total_stats,
    s.is_legendary,
    s.is_mythical,
    p.artwork_url,
    p.sprite_url,
    MAX(GREATEST(p.hp, p.attack, p.defense, p.special_attack, p.special_defense, p.speed)) OVER () AS stat_max_escala
FROM refined.pokemon AS p
JOIN refined.species AS s ON s.species_id = p.pokemon_id
JOIN refined.pokemon_type AS t1 ON t1.pokemon_id = p.pokemon_id AND t1.slot = 1
LEFT JOIN refined.pokemon_type AS t2 ON t2.pokemon_id = p.pokemon_id AND t2.slot = 2
ORDER BY p.pokemon_id;
