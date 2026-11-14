from pathlib import Path

import duckdb
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from pipeline.ingestion import ingest_csv
from pipeline.marts import execute_marts
from pipeline.reporting import render_gold_report
from pipeline.transformation import transform_to_silver

REPORT_LABELS = {
    "gold_top_musicas": "Top 5 músicas mais populares",
    "gold_media_generos": "Média de energia e dançabilidade por gênero",
    "gold_perfil_audio_generos": "Perfil de áudio por gênero",
    "gold_top_artistas": "Artistas com mais músicas registradas",
    "gold_mais_dancaveis": "Top 5 músicas mais dançáveis",
    "gold_maior_energia": "Top 5 músicas com maior energia",
    "gold_generos_populares": "Top 10 gêneros por popularidade média",
}


def run_menu(
    connection: duckdb.DuckDBPyConnection,
    gold_view_names: list[str],
    console: Console,
) -> None:
    if not gold_view_names:
        raise ValueError("Nenhum relatório Gold foi carregado para o menu.")

    options = {
        str(number): view_name
        for number, view_name in enumerate(gold_view_names, start=1)
    }

    while True:
        console.clear()
        console.print(
            Panel.fit(
                "🎧 [bold cyan]Spotify Terminal Analytics | Menu Principal[/bold cyan]",
                border_style="cyan",
            )
        )
        for number, view_name in options.items():
            label = REPORT_LABELS.get(
                view_name,
                view_name.removeprefix("gold_").replace("_", " ").title(),
            )
            console.print(f"[{number}] 📊 {label}")
        console.print("[0] 🚪 Sair\n")

        choice = Prompt.ask(
            "Digite o número da opção desejada",
            choices=[*options, "0"],
            default="1",
        )

        if choice == "0":
            console.print("[bold yellow]Saindo do sistema. Até logo![/bold yellow]")
            return

        console.print("\n")

        # Tratamento de erro ao renderizar a consulta selecionada
        try:
            render_gold_report(connection, [options[choice]], console)
        except Exception as e:
            console.print(
                Panel.fit(
                    f"[bold red]❌ Erro ao executar o relatório selecionado:[/bold red]\n{e}",
                    border_style="red",
                )
            )

        console.print("\n")
        Prompt.ask(
            "[dim]Pressione Enter para voltar ao menu principal...[/dim]", default=""
        )


def main() -> None:
    console = Console()
    project_root = Path(__file__).resolve().parent
    dataset_path = project_root / "data" / "dataset.csv"

    if not dataset_path.is_file():
        console.print(
            f"[bold red]❌ CSV não encontrado: {dataset_path}. "
            "Coloque o dataset em data/dataset.csv.[/bold red]"
        )
        raise SystemExit(1)

    connection = duckdb.connect(":memory:")

    # Tratamento de erro crítico para todo o pipeline de engenharia de dados
    try:
        console.print(
            "[yellow]⏳ Executando pipeline (Bronze -> Silver -> Gold)...[/yellow]"
        )

        # 1. Camada Bronze
        ingest_csv(connection, dataset_path)

        # 2. Camada Silver
        transform_to_silver(
            connection,
            project_root / "sql" / "silver" / "transform_tracks.sql",
        )

        # 3. Camada Gold
        gold_view_names = execute_marts(
            connection,
            project_root / "sql" / "marts",
        )

        # Inicia o menu interativo
        run_menu(connection, gold_view_names, console)

    except duckdb.Error as db_err:
        console.print(
            Panel.fit(
                f"[bold red]❌ Erro de Banco de Dados (DuckDB):[/bold red]\n{db_err}",
                border_style="red",
            )
        )
        raise SystemExit(1)
    except Exception as e:
        console.print(
            Panel.fit(
                f"[bold red]❌ Erro crítico inesperado no pipeline:[/bold red]\n{e}",
                border_style="red",
            )
        )
        raise SystemExit(1)
    finally:
        connection.close()


if __name__ == "__main__":
    main()
