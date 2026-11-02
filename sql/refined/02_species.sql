-- Grão: 1 linha por espécie. Origem: stg_species (raw.pokemon_species achatado por src/transform.py).
-- habitat é nulável de propósito: a API pode não informar e não inventamos valor.
CREATE OR REPLACE TABLE refined.species (
    species_id         INTEGER PRIMARY KEY,
    name               VARCHAR NOT NULL,
    is_legendary       BOOLEAN NOT NULL,
    is_mythical        BOOLEAN NOT NULL,
    capture_rate       INTEGER NOT NULL,
    base_happiness     INTEGER,
    habitat            VARCHAR,
    color              VARCHAR NOT NULL,
    growth_rate        VARCHAR NOT NULL,
    generation         VARCHAR NOT NULL,
    evolution_chain_id INTEGER NOT NULL
);

INSERT INTO refined.species
SELECT
    species_id, name, is_legendary, is_mythical, capture_rate, base_happiness,
    habitat, color, growth_rate, generation, evolution_chain_id
FROM stg_species
ORDER BY species_id;
