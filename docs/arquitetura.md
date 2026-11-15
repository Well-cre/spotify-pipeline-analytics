# Arquitetura do Projeto

Este projeto implementa uma pipeline analítica para o Spotify com arquitetura Medallion
(Bronze, Silver e Gold). O DuckDB processa os dados em memória, e os relatórios são exibidos
em uma interface interativa no terminal.

## Visão geral do fluxo

```text
CSV do Kaggle (data/dataset.csv)
          |
          v
Bronze: spotify_raw
          |
          v
Silver: spotify_silver
          |
          v
Gold: views analíticas
          |
          v
Relatórios no terminal (Rich e Plotext)
```

## Camadas de dados

### 1. Bronze (Raw)

- Lê `data/dataset.csv` e cria a tabela `spotify_raw` no DuckDB.
- Mantém as colunas e os valores do CSV como texto, sem transformação.
- A conexão DuckDB usa `:memory:`; as tabelas existem durante a execução e não são persistidas
  em disco.

### 2. Silver (Refined)

- Cria a tabela `spotify_silver` por meio de `sql/silver/transform_tracks.sql`.
- Normaliza campos textuais vazios para `Desconhecido` e valores numéricos ausentes para zero.
- Converte popularidade para inteiro e energia, dançabilidade, tempo e valência para números.
- Descarta linhas com popularidade inválida ou fora do intervalo de 0 a 100, e com valores
  numéricos inválidos nas métricas de áudio.
- Deduplica por `track_name` e `artists`, mantendo o registro com maior popularidade; em caso
  de empate, mantém o primeiro registro de origem.

### 3. Gold (Data Marts)

- Carrega os arquivos SQL de `sql/marts/` e cria uma view Gold para cada arquivo.
- Os indicadores incluem faixas mais populares, médias e perfil de áudio por gênero, gêneros
  por popularidade média, faixas com maior energia ou dançabilidade e valores do campo
  `artists` com mais faixas registradas.
- As views são consultadas pela interface de terminal construída com Rich e Plotext; não são
  tabelas persistidas.

## Stack tecnológica

- **Linguagem:** Python 3.12+
- **Gerenciamento de pacotes:** `uv`
- **Processamento analítico:** DuckDB
- **Interface e visualização no terminal:** Rich e Plotext
- **Qualidade de código:** Ruff, com limite de 100 caracteres por linha no `pyproject.toml`
- **Testes automatizados:** pytest
- **Documentação:** MkDocs com o tema Material
