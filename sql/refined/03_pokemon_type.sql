-- Grão: 1 linha por (pokemon_id, slot). Origem: stg_pokemon_type (campo types de raw.pokemon).
-- Tipos ATUAIS da API, não os de 1996 (motivo em docs/decisoes.md).
CREATE OR REPLACE TABLE refined.pokemon_type (
    pokemon_id INTEGER NOT NULL,
    slot       INTEGER NOT NULL,
    type_name  VARCHAR NOT NULL,
    PRIMARY KEY (pokemon_id, slot)
);

INSERT INTO refined.pokemon_type
SELECT pokemon_id, slot, type_name
FROM stg_pokemon_type
ORDER BY pokemon_id, slot;
