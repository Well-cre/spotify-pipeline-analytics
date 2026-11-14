from pathlib import Path

import duckdb


def transform_to_silver(
    connection: duckdb.DuckDBPyConnection,
    sql_path: Path,
) -> None:
    """Executa a transformação Silver definida no arquivo SQL."""
    if not sql_path.is_file():
        raise FileNotFoundError(f"SQL da camada Silver não encontrado: {sql_path}")

    connection.execute(sql_path.read_text(encoding="utf-8"))
