import csv
from io import StringIO
from pathlib import Path

import duckdb
import pytest
from rich.console import Console
from rich.prompt import Prompt

from main import run_menu
from pipeline.ingestion import ingest_csv
from pipeline.marts import execute_marts
from pipeline.reporting import render_gold_chart, render_gold_report
from pipeline.transformation import transform_to_silver


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SILVER_SQL = PROJECT_ROOT / "sql" / "silver" / "transform_tracks.sql"
MARTS_SQL = PROJECT_ROOT / "sql" / "marts"
CSV_COLUMNS = [
    "track_name",
    "artists",
    "album_name",
    "popularity",
    "track_genre",
    "energy",
    "danceability",
    "tempo",
    "valence",
]


@pytest.fixture
def connection():
    database = duckdb.connect(":memory:")
    try:
        yield database
    finally:
        database.close()


def load_raw_csv(connection, tmp_path: Path, records: list[dict[str, str]]) -> None:
    csv_path = tmp_path / "tracks.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(records)
    ingest_csv(connection, csv_path)


def make_track(
    track_name: str,
    artists: str,
    popularity: str,
    track_genre: str = "pop",
    *,
    album_name: str = "album",
    energy: str = "0.5",
    danceability: str = "0.6",
    tempo: str = "120",
    valence: str = "0.7",
) -> dict[str, str]:
    return {
        "track_name": track_name,
        "artists": artists,
        "album_name": album_name,
        "popularity": popularity,
        "track_genre": track_genre,
        "energy": energy,
        "danceability": danceability,
        "tempo": tempo,
        "valence": valence,
    }


def test_bronze_preserva_colunas_e_valores_como_texto(
    connection,
    tmp_path: Path,
) -> None:
    load_raw_csv(
        connection,
        tmp_path,
        [make_track("001", "Artist", "07", energy="0.5000")],
    )

    schema = connection.execute("DESCRIBE spotify_raw").fetchall()
    values = connection.execute(
        "SELECT track_name, popularity, energy FROM spotify_raw"
    ).fetchone()

    assert [column[0] for column in schema] == CSV_COLUMNS
    assert {column[1] for column in schema} == {"VARCHAR"}
    assert values == ("001", "07", "0.5000")


def test_duplicata_por_nome_e_artista_mantem_maior_popularidade(
    connection,
    tmp_path: Path,
) -> None:
    load_raw_csv(
        connection,
        tmp_path,
        [
            make_track("Same Song", "Artist", "70", "first"),
            make_track("Same Song", "Artist", "90", "second"),
            make_track("Same Song", "Different Artist", "80"),
        ],
    )

    transform_to_silver(connection, SILVER_SQL)

    rows = connection.execute(
        """
        SELECT track_name, artists, popularity, track_genre
        FROM spotify_silver
        ORDER BY artists
        """
    ).fetchall()
    assert rows == [
        ("Same Song", "Artist", 90, "second"),
        ("Same Song", "Different Artist", 80, "pop"),
    ]
    assert connection.execute(
        "SELECT typeof(popularity), typeof(energy) FROM spotify_silver LIMIT 1"
    ).fetchone() == ("INTEGER", "DOUBLE")


def test_nulos_recebem_padrao_e_linhas_numericas_invalidas_sao_descartadas(
    connection,
    tmp_path: Path,
) -> None:
    load_raw_csv(
        connection,
        tmp_path,
        [
            make_track("", "", "", "", album_name="", energy="", danceability="", tempo="", valence=""),
            make_track("Out of range", "Artist", "101"),
            make_track("Bad audio", "Artist", "60", energy="invalid"),
            make_track("Bad popularity", "Artist", "invalid"),
        ],
    )

    transform_to_silver(connection, SILVER_SQL)

    assert connection.execute(
        """
        SELECT track_name, artists, album_name, popularity, track_genre,
               energy, danceability, tempo, valence
        FROM spotify_silver
        """
    ).fetchall() == [
        ("Desconhecido", "Desconhecido", "Desconhecido", 0, "Desconhecido", 0.0, 0.0, 0.0, 0.0)
    ]


def test_arquivos_sql_dos_marts_geram_indicadores_gold(
    connection,
    tmp_path: Path,
) -> None:
    load_raw_csv(
        connection,
        tmp_path,
        [
            make_track(f"Track {index}", f"Artist {index}", str(popularity), genre)
            for index, (popularity, genre) in enumerate(
                [(95, "rock"), (80, "rock"), (70, "jazz"), (60, "jazz"), (50, "pop"), (40, "pop")]
            )
        ],
    )
    transform_to_silver(connection, SILVER_SQL)

    views = execute_marts(connection, MARTS_SQL)

    assert views == [
        "gold_top_musicas",
        "gold_media_generos",
        "gold_perfil_audio_generos",
        "gold_top_artistas",
        "gold_generos_populares",
        "gold_maior_energia",
        "gold_mais_dancaveis",
    ]
    assert connection.execute(
        "SELECT track_name, popularity FROM gold_top_musicas ORDER BY popularity DESC"
    ).fetchall() == [
        ("Track 0", 95),
        ("Track 1", 80),
        ("Track 2", 70),
        ("Track 3", 60),
        ("Track 4", 50),
    ]
    assert connection.execute(
        "SELECT track_genre, average_popularity, track_count "
        "FROM gold_media_generos ORDER BY track_genre"
    ).fetchall() == [
        ("jazz", 65.0, 2),
        ("pop", 45.0, 2),
        ("rock", 87.5, 2),
    ]
    assert connection.execute(
        "SELECT track_genre, track_count, average_energy, average_danceability "
        "FROM gold_perfil_audio_generos ORDER BY track_genre"
    ).fetchall() == [
        ("jazz", 2, 0.5, 0.6),
        ("pop", 2, 0.5, 0.6),
        ("rock", 2, 0.5, 0.6),
    ]
    assert connection.execute(
        "SELECT artists, track_count FROM gold_top_artistas ORDER BY artists LIMIT 2"
    ).fetchall() == [("Artist 0", 1), ("Artist 1", 1)]

    render_gold_report(connection, views, Console(record=True))


def test_menu_apresenta_relatorios_gold_e_exibe_a_escolha(
    connection,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    load_raw_csv(
        connection,
        tmp_path,
        [make_track("Track", "Artist", "80")],
    )
    transform_to_silver(connection, SILVER_SQL)
    views = execute_marts(connection, MARTS_SQL)
    responses = iter(["3", "", "0"])
    monkeypatch.setattr(Prompt, "ask", lambda *args, **kwargs: next(responses))
    output = StringIO()

    run_menu(connection, views, Console(file=output))

    rendered = output.getvalue()
    assert "Top 5 músicas mais populares" in rendered
    assert "Popularidade média por gênero" in rendered
    assert "Perfil de áudio por gênero" in rendered
    assert "Artistas/créditos com mais faixas" in rendered
    assert "Top 10 gêneros por popularidade média" in rendered
    assert "Top 5 músicas com maior energia" in rendered
    assert "Top 5 músicas mais dançáveis" in rendered
    assert "Gráfico de Barras: Gêneros por Popularidade Média" in rendered
    assert "Gold | Perfil Audio Generos" in rendered


def test_grafico_de_barras_renderiza_dados_da_view_gold(
    connection,
    tmp_path: Path,
    capfd: pytest.CaptureFixture[str],
) -> None:
    load_raw_csv(
        connection,
        tmp_path,
        [
            make_track(
                f"Track {index}",
                f"Artist {index}",
                str(100 - index),
                f"genre{index:02}",
            )
            for index in range(11)
        ],
    )
    transform_to_silver(connection, SILVER_SQL)
    execute_marts(connection, MARTS_SQL)
    console_output = StringIO()

    gold_genres = connection.execute(
        """
        SELECT genre
        FROM gold_generos_populares
        ORDER BY media_popularidade DESC
        """
    ).fetchall()
    render_gold_chart(connection, Console(file=console_output))

    chart_output = capfd.readouterr().out
    assert len(gold_genres) == 10
    assert [row[0] for row in gold_genres] == [
        f"genre{index:02}" for index in range(10)
    ]
    assert "Top 10 gêneros por popularidade média" in chart_output
    assert all(f"genre{index:02}" in chart_output for index in range(10))
    assert "genre10" not in chart_output
    assert "█" in chart_output


def test_ingest_csv_informa_quando_arquivo_nao_existe(
    connection,
    tmp_path: Path,
) -> None:
    with pytest.raises(FileNotFoundError, match="Arquivo CSV não encontrado"):
        ingest_csv(connection, tmp_path / "missing.csv")
