import re
from pathlib import Path

import duckdb


_MART_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")


def execute_marts(
    connection: duckdb.DuckDBPyConnection,
    sql_directory: Path,
) -> list[str]:
    """Cria dinamicamente as views Gold a partir dos arquivos SQL dos marts."""
    sql_files = sorted(sql_directory.glob("*.sql"))
    if not sql_files:
        raise FileNotFoundError(f"Nenhum arquivo SQL de mart encontrado em {sql_directory}")

    view_names: list[str] = []
    for sql_path in sql_files:
        mart_name = re.sub(r"^\d+_", "", sql_path.stem)
        if not _MART_NAME_PATTERN.fullmatch(mart_name):
            raise ValueError(f"Nome de arquivo de mart inválido: {sql_path.name}")

        query = sql_path.read_text(encoding="utf-8").strip().rstrip(";")
        if not query:
            raise ValueError(f"Arquivo SQL de mart vazio: {sql_path}")

        view_name = f"gold_{mart_name}"
        connection.execute(f"CREATE OR REPLACE VIEW {view_name} AS\n{query}")
        view_names.append(view_name)

    return view_names
