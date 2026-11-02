-- Grão: 1 linha por (pokemon_id, ability_name, is_hidden, slot).
-- Origem: stg_pokemon_ability (campo abilities de raw.pokemon).
CREATE OR REPLACE TABLE refined.pokemon_ability (
    pokemon_id   INTEGER NOT NULL,
    ability_name VARCHAR NOT NULL,
    is_hidden    BOOLEAN NOT NULL,
    slot         INTEGER NOT NULL,
    PRIMARY KEY (pokemon_id, ability_name, is_hidden, slot)
);

INSERT INTO refined.pokemon_ability
SELECT pokemon_id, ability_name, is_hidden, slot
FROM stg_pokemon_ability
ORDER BY pokemon_id, slot;
