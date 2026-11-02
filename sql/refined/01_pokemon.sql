-- Grão: 1 linha por Pokémon. Origem: stg_pokemon (raw.pokemon achatado por src/transform.py).
-- Altura e peso já convertidos para metros e kg. artwork_url e sprite_url são nuláveis: a API pode não ter a imagem.
CREATE OR REPLACE TABLE refined.pokemon (
    pokemon_id      INTEGER PRIMARY KEY,
    name            VARCHAR NOT NULL,
    height_m        DECIMAL(5, 1) NOT NULL,
    weight_kg       DECIMAL(6, 1) NOT NULL,
    base_experience INTEGER,
    hp              INTEGER NOT NULL,
    attack          INTEGER NOT NULL,
    defense         INTEGER NOT NULL,
    special_attack  INTEGER NOT NULL,
    special_defense INTEGER NOT NULL,
    speed           INTEGER NOT NULL,
    total_stats     INTEGER NOT NULL,
    artwork_url     VARCHAR,
    sprite_url      VARCHAR
);

INSERT INTO refined.pokemon
SELECT
    pokemon_id, name, height_m, weight_kg, base_experience, hp, attack,
    defense, special_attack, special_defense, speed, total_stats, artwork_url, sprite_url
FROM stg_pokemon
ORDER BY pokemon_id;
