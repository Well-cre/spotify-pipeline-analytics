import duckdb
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
