"""Funções puras: recebem o dict do JSON da API e devolvem linhas (ou DataFrame).

Nada aqui abre arquivo, banco ou rede. Os motivos de cada regra estão em docs/decisoes.md.
"""
from __future__ import annotations

import re
from typing import Callable, Iterable

import pandas as pd

STATS = ("hp", "attack", "defense", "special-attack", "special-defense", "speed")


def decimetros_para_metros(altura: int) -> float:
    return round(altura / 10, 1)


def hectogramas_para_kg(peso: int) -> float:
    return round(peso / 10, 1)


def extrair_evolution_chain_id(url: str) -> int:
    """A API só traz a url da cadeia: .../evolution-chain/1/ vira 1."""
    encontrado = re.search(r"/evolution-chain/(\d+)/?$", url)
    if encontrado is None:
        raise ValueError(f"url de evolution_chain inesperada: {url}")
    return int(encontrado.group(1))


def linha_pokemon(pokemon: dict) -> dict:
    stats = {item["stat"]["name"]: item["base_stat"] for item in pokemon["stats"]}
    return {
        "pokemon_id": pokemon["id"],
        "name": pokemon["name"],
        "height_m": decimetros_para_metros(pokemon["height"]),
        "weight_kg": hectogramas_para_kg(pokemon["weight"]),
        "base_experience": pokemon["base_experience"],
        "hp": stats["hp"],
        "attack": stats["attack"],
        "defense": stats["defense"],
        "special_attack": stats["special-attack"],
        "special_defense": stats["special-defense"],
        "speed": stats["speed"],
        "total_stats": sum(stats[nome] for nome in STATS),
    }


def linha_species(especie: dict) -> dict:
    habitat = especie["habitat"]
    return {
        "species_id": especie["id"],
        "name": especie["name"],
        "is_legendary": especie["is_legendary"],
        "is_mythical": especie["is_mythical"],
        "capture_rate": especie["capture_rate"],
        "base_happiness": especie["base_happiness"],
        "habitat": habitat["name"] if habitat is not None else None,  # nulo continua nulo
        "color": especie["color"]["name"],
        "growth_rate": especie["growth_rate"]["name"],
        "generation": especie["generation"]["name"],
        "evolution_chain_id": extrair_evolution_chain_id(especie["evolution_chain"]["url"]),
    }


def _tabela(itens: Iterable[dict], extrair: Callable[[dict], Iterable[dict]], colunas: list[str]) -> pd.DataFrame:
    linhas = [linha for item in itens for linha in extrair(item)]
    # object evita que o pandas troque None por NaN ou infira o tipo pela amostra.
    return pd.DataFrame(linhas, columns=colunas, dtype=object)


COLUNAS_POKEMON = [
    "pokemon_id", "name", "height_m", "weight_kg", "base_experience", "hp", "attack",
    "defense", "special_attack", "special_defense", "speed", "total_stats",
]
COLUNAS_SPECIES = [
    "species_id", "name", "is_legendary", "is_mythical", "capture_rate", "base_happiness",
    "habitat", "color", "growth_rate", "generation", "evolution_chain_id",
]


def tabela_pokemon(pokemons: Iterable[dict]) -> pd.DataFrame:
    return _tabela(pokemons, lambda p: [linha_pokemon(p)], COLUNAS_POKEMON)


def tabela_species(especies: Iterable[dict]) -> pd.DataFrame:
    return _tabela(especies, lambda e: [linha_species(e)], COLUNAS_SPECIES)
