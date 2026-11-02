-- Pergunta: quantos tipos causam 2x, 0.5x e 0x em cada tipo defensivo?
-- Grão: 1 linha por tipo defensivo presente nos 151.
-- Origem: refined.pokemon_type LEFT JOIN refined.type_damage.
-- Só conta atacantes dentro dos 151: dark, por exemplo, não entra (motivo em docs/decisoes.md).
CREATE OR REPLACE TABLE marts.mart_fraquezas_por_tipo AS
WITH tipos AS (
    SELECT DISTINCT type_name FROM refined.pokemon_type
)
SELECT
    t.type_name                                       AS defending_type,
    COUNT(*) FILTER (WHERE d.multiplier = 2.0)        AS qtd_causam_2x,
    COUNT(*) FILTER (WHERE d.multiplier = 0.5)        AS qtd_causam_0_5x,
    COUNT(*) FILTER (WHERE d.multiplier = 0.0)        AS qtd_causam_0x
FROM tipos AS t
LEFT JOIN refined.type_damage AS d ON d.defending_type = t.type_name
GROUP BY t.type_name
ORDER BY qtd_causam_2x DESC, t.type_name;
