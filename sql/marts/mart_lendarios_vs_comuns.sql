-- Pergunta: lendários e míticos são mais fortes e mais difíceis de capturar que os comuns?
-- Grão: 1 linha por categoria (lendário, mítico, comum).
-- Origem: refined.pokemon JOIN refined.species.
-- capture_rate maior significa captura MAIS fácil.
CREATE OR REPLACE TABLE marts.mart_lendarios_vs_comuns AS
SELECT
    CASE
        WHEN s.is_mythical THEN 'mítico'
        WHEN s.is_legendary THEN 'lendário'
        ELSE 'comum'
    END                          AS categoria,
    COUNT(*)                     AS qtd_pokemon,
    ROUND(AVG(p.total_stats), 2) AS media_total_stats,
    ROUND(AVG(s.capture_rate), 2) AS media_capture_rate
FROM refined.pokemon AS p
JOIN refined.species AS s ON s.species_id = p.pokemon_id
GROUP BY categoria
ORDER BY media_total_stats DESC;
