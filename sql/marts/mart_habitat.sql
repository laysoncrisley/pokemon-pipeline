-- Pergunta: quantos Pokémon vivem em cada habitat e qual a força média em cada um?
-- Grão: 1 linha por habitat. Habitat nulo vira a linha 'sem informação', que só existe se houver nulo.
-- Origem: refined.species JOIN refined.pokemon.
CREATE OR REPLACE TABLE marts.mart_habitat AS
SELECT
    COALESCE(s.habitat, 'sem informação') AS habitat,
    COUNT(*)                              AS qtd_pokemon,
    ROUND(AVG(p.total_stats), 2)          AS media_total_stats
FROM refined.species AS s
JOIN refined.pokemon AS p ON p.pokemon_id = s.species_id
GROUP BY COALESCE(s.habitat, 'sem informação')
ORDER BY qtd_pokemon DESC, habitat;
