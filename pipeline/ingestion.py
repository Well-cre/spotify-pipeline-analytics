from pathlib import Path

import duckdb


def ingest_csv(
    connection: duckdb.DuckDBPyConnection,
    csv_path: Path,
) -> None:
    """Carrega o CSV sem inferir ou converter os valores das colunas."""
    if not csv_path.is_file():
        raise FileNotFoundError(f"Arquivo CSV não encontrado: {csv_path}")

    connection.execute(
        """
        CREATE OR REPLACE TABLE spotify_raw AS
        SELECT *
        FROM read_csv(?, header = true, all_varchar = true)
        """,
        [str(csv_path)],
    )
