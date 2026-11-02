-- Grão: 1 linha por (pokemon_id, move_name, learn_method, min_level), só do version_group red-blue.
-- Origem: stg_pokemon_move. A regra de deduplicação fica em transform.linhas_golpe e o
-- motivo em docs/decisoes.md. A chave primária faz a carga falhar se a regra deixar repetição.
CREATE OR REPLACE TABLE refined.pokemon_move (
    pokemon_id   INTEGER NOT NULL,
    move_name    VARCHAR NOT NULL,
    learn_method VARCHAR NOT NULL,
    min_level    INTEGER NOT NULL,
    PRIMARY KEY (pokemon_id, move_name, learn_method, min_level)
);

INSERT INTO refined.pokemon_move
SELECT pokemon_id, move_name, learn_method, min_level
FROM stg_pokemon_move
ORDER BY pokemon_id, min_level, move_name;
