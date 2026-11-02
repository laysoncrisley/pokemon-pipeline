"""Ponto de entrada: python run_pipeline.py [--refresh]"""
import argparse
import sys

import duckdb

from src import build, checks, config, extract, load_raw


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Pipeline Pokémon: extract -> raw -> refined -> marts -> checks")
    parser.add_argument("--refresh", action="store_true", help="ignora o cache e baixa tudo de novo da API")
    args = parser.parse_args()

    print("[1/4] extract: PokeAPI -> data/raw")
    resumo = extract.executar(refresh=args.refresh)
    print(f"      {resumo['baixados']} baixados, {resumo['cache']} do cache, {resumo['total']} no total")

    config.WAREHOUSE_DB.parent.mkdir(parents=True, exist_ok=True)
    with duckdb.connect(str(config.WAREHOUSE_DB)) as con:
        print("[2/4] raw: data/raw -> schema raw")
        for tabela, linhas in load_raw.executar(con).items():
            print(f"      {tabela}: {linhas} linhas")

        print("[3/4] refined: schema raw -> schema refined")
        for arquivo in build.construir_refined(con):
            print(f"      {arquivo}")

        print("[4/4] checks: contagens entre camadas")
        try:
            checks.executar(con)
        except checks.ErroDeConferencia as erro:
            sys.exit(str(erro))
        print(f"      relatório em {config.CONFERENCIA_PATH.relative_to(config.ROOT).as_posix()}")


if __name__ == "__main__":
    main()
