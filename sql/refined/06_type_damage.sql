-- Grão: 1 linha por (attacking_type, defending_type). Pares ausentes valem 1.0 e não são gravados.
-- Origem: stg_type_damage (damage_relations de raw.type) + refined.pokemon_type.
-- damage_relations cita tipos fora dos 151 (hoje, dark). O filtro mantém os dois lados
-- do par dentro dos tipos que existem no escopo (motivo em docs/decisoes.md).
CREATE OR REPLACE TABLE refined.type_damage (
    attacking_type VARCHAR NOT NULL,
    defending_type VARCHAR NOT NULL,
    multiplier     DOUBLE NOT NULL,
    PRIMARY KEY (attacking_type, defending_type)
);

INSERT INTO refined.type_damage
SELECT attacking_type, defending_type, multiplier
FROM stg_type_damage
WHERE attacking_type IN (SELECT type_name FROM refined.pokemon_type)
  AND defending_type IN (SELECT type_name FROM refined.pokemon_type)
ORDER BY attacking_type, defending_type;
