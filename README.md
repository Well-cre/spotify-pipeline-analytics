# Spotify Data Pipeline

Pipeline local em Python 3.12+ e DuckDB para o dataset público Spotify Tracks.
O CSV deve estar em `data/dataset.csv`.

## Executar

```powershell
uv run main.py
uv run pytest
```

## Camadas

- **Bronze:** carrega todas as colunas do CSV como texto em `spotify_raw`,
  preservando os valores de origem.
- **Silver:** `sql/silver/transform_tracks.sql` seleciona as colunas analíticas,
  converte popularity e métricas de áudio, substitui nulos por padrões e remove
  registros numéricos inválidos. Popularity fora de 0–100 é descartada.
  Duplicatas por `track_name` e `artists` mantêm a maior popularity; em empate,
  prevalece a primeira linha de origem.
- **Gold:** cada arquivo `.sql` em `sql/marts/` define um indicador carregado
  dinamicamente como view. O relatório Rich lê apenas essas views.