from pathlib import Path

import duckdb
from rich.console import Console
from rich.panel import Panel

from pipeline.ingestion import ingest_csv
from pipeline.marts import execute_marts
from pipeline.reporting import render_gold_report
from pipeline.transformation import transform_to_silver


def main() -> None:
    console = Console()
    project_root = Path(__file__).resolve().parent
    dataset_path = project_root / "data" / "dataset.csv"

    console.print(
        Panel.fit(
            "Spotify | Pipeline analítico local com DuckDB",
            border_style="cyan",
        )
    )
    if not dataset_path.is_file():
        console.print(
            f"[bold red]CSV não encontrado: {dataset_path}. "
            "Coloque o dataset em data/dataset.csv.[/bold red]"
        )
        raise SystemExit(1)

    connection = duckdb.connect(":memory:")
    try:
        ingest_csv(connection, dataset_path)
        console.print("[green]Bronze: CSV carregado sem conversão de valores.[/green]")

        transform_to_silver(
            connection,
            project_root / "sql" / "silver" / "transform_tracks.sql",
        )
        silver_count = connection.execute(
            "SELECT COUNT(*) FROM spotify_silver"
        ).fetchone()[0]
        console.print(f"[green]Silver: {silver_count:,} registros refinados.[/green]")

        gold_views = execute_marts(
            connection,
            project_root / "sql" / "marts",
        )
        render_gold_report(connection, gold_views, console)
    finally:
        connection.close()


if __name__ == "__main__":
    main()
