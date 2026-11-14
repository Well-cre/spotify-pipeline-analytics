import duckdb
import plotext as plt
from rich.console import Console
from rich.table import Table


def render_gold_report(
    connection: duckdb.DuckDBPyConnection,
    view_names: list[str],
    console: Console,
) -> None:
    """Renderiza somente os resultados das views da camada Gold."""
    for view_name in view_names:
        if not view_name.startswith("gold_"):
            raise ValueError(f"O relatório aceita somente views Gold: {view_name}")

        result = connection.execute(f'SELECT * FROM "{view_name}"')
        columns = [description[0] for description in result.description]
        rows = result.fetchall()

        title = view_name.removeprefix("gold_").replace("_", " ").title()
        table = Table(title=f"Gold | {title}", header_style="bold magenta")
        for column in columns:
            table.add_column(column.replace("_", " ").title(), overflow="fold")

        for row in rows:
            table.add_row(*(str(value) if value is not None else "—" for value in row))

        console.print(table)


def render_gold_chart(
    connection: duckdb.DuckDBPyConnection,
    console: Console,
) -> None:
    """Renderiza a popularidade média por gênero da view Gold no terminal."""
    rows = connection.execute(
        """
        SELECT genre, media_popularidade
        FROM gold_generos_populares
        ORDER BY media_popularidade DESC
        """
    ).fetchall()

    if not rows:
        console.print("[yellow]Nenhum dado encontrado para gerar o gráfico.[/yellow]")
        return

    genres = [row[0] for row in rows]
    popularity = [float(row[1]) for row in rows]
    title = f"Top {len(rows)} gêneros por popularidade média"

    figure = plt.figure
    figure.clear()
    figure.title(title)
    figure.draw(
        figure.bar(
            genres,
            popularity,
            orientation="horizontal",
            labeled=True,
        )
    )
    figure.show()
