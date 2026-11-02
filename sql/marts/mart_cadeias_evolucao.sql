-- Pergunta: quantos Pokémon cada cadeia de evolução tem e qual o maior total_stats dela?
-- Grão: 1 linha por evolution_chain_id. Só conta os membros dentro dos ids 1 a 151.
-- Origem: refined.species JOIN refined.pokemon.
CREATE OR REPLACE TABLE marts.mart_cadeias_evolucao AS
SELECT
    s.evolution_chain_id,
    COUNT(*)                                  AS qtd_pokemon,
    MAX(p.total_stats)                        AS maior_total_stats,
    STRING_AGG(p.name, ', ' ORDER BY p.pokemon_id) AS membros
FROM refined.species AS s
JOIN refined.pokemon AS p ON p.pokemon_id = s.species_id
GROUP BY s.evolution_chain_id
ORDER BY s.evolution_chain_id;
