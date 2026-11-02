"""Ponto de entrada: python run_pipeline.py [--refresh]"""
import argparse
import sys

from src import extract


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Pipeline Pokémon: extract -> raw -> refined -> marts -> checks")
    parser.add_argument("--refresh", action="store_true", help="ignora o cache e baixa tudo de novo da API")
    args = parser.parse_args()

    print("[1/1] extract: PokeAPI -> data/raw")
    resumo = extract.executar(refresh=args.refresh)
    print(f"      {resumo['baixados']} baixados, {resumo['cache']} do cache, {resumo['total']} no total")


if __name__ == "__main__":
    main()
