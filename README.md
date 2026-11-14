# Spotify Tracks Data Pipeline

Pipeline local de dados em Python 3.12+ e DuckDB para o dataset público
**Spotify Tracks Dataset**. O fluxo segue a arquitetura Medallion
(Bronze → Silver → Gold), com indicadores analíticos definidos em SQL.

## Fonte e licença dos dados

- **Dataset:** [Spotify Tracks Dataset no Kaggle](https://www.kaggle.com/datasets/maharshipandya/-spotify-tracks-dataset)
- **Autor no Kaggle:** [Maharshi Pandya](https://www.kaggle.com/maharshipandya)
- **Licença informada na página:** Open Database License (ODbL) 1.0 para a
  base de dados; o conteúdo é identificado como © dos autores originais.
  Consulte os [termos da ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/)
  antes de redistribuir a base ou derivados.

O pipeline espera o arquivo CSV em `data/dataset.csv`. A obtenção do arquivo é
manual pela página do Kaggle; extraia o CSV do download e use o nome esperado.

## Camadas e granularidade

| Camada / tabela ou view | O que representa uma linha | Conteúdo |
| --- | --- | --- |
| Bronze — `spotify_raw` | Uma linha original do CSV. Não representa necessariamente uma música única. | Todas as colunas de origem, carregadas como texto para preservar os valores. |
| Silver — `spotify_silver` | Uma combinação única de `track_name` e `artists`. | Nome, artista, álbum, popularidade, gênero e métricas de áudio refinadas. |
| Gold — `gold_top_musicas` | Uma música entre as cinco de maior popularidade na Silver. | `track_name`, `artists`, `popularity` e `track_genre`. |
| Gold — `gold_media_generos` | Um gênero presente na Silver. | `track_genre`, popularidade média e quantidade de músicas (`track_count`). |
| Gold — `gold_perfil_audio_generos` | Um gênero entre os cinco com mais faixas. | Quantidade e médias de energia, dançabilidade, tempo e valência. |
| Gold — `gold_top_artistas` | Um crédito de artista presente na Silver. | Texto de `artists` e quantidade de faixas associadas. |

### Bronze — Raw

`pipeline/ingestion.py` carrega o CSV em `spotify_raw` sem converter os valores
das colunas. Como CSV não define tipos nativos, os campos são mantidos como
texto nesta camada.

### Silver — Refined

`pipeline/transformation.py` executa
[`sql/silver/transform_tracks.sql`](sql/silver/transform_tracks.sql). A tabela
`spotify_silver` contém:

- `track_name`, `artists`, `album_name` e `track_genre`;
- `popularity` como inteiro;
- `energy`, `danceability`, `tempo` e `valence` como números decimais.

Nulos ou textos vazios recebem `Desconhecido` nos campos de texto e `0`/`0.0`
nos campos numéricos. Linhas com valores numéricos inválidos ou `popularity`
fora do intervalo de 0 a 100 são descartadas. Para duplicatas de
`track_name` + `artists`, fica a linha com maior popularidade; em caso de
empate, prevalece a primeira ocorrência no CSV.

### Gold — Marts e indicadores

`pipeline/marts.py` carrega dinamicamente cada arquivo `.sql` de `sql/marts/`
como uma view Gold. O relatório do terminal, renderizado com Rich por
`pipeline/reporting.py`, consulta somente essas views.

- [`01_top_musicas.sql`](sql/marts/01_top_musicas.sql) — **Top 5 músicas** por
  popularidade, com desempate por nome e artista.
- [`02_media_generos.sql`](sql/marts/02_media_generos.sql) — **popularidade
  média por gênero** e quantidade de músicas usada no cálculo.
- [`03_perfil_audio_generos.sql`](sql/marts/03_perfil_audio_generos.sql) —
  **perfil de áudio por gênero**, com médias de energia, dançabilidade, tempo e
  valência para os cinco gêneros com mais faixas.
- [`04_top_artistas.sql`](sql/marts/04_top_artistas.sql) — **créditos de artista
  com mais faixas** na Silver (cada valor de `artists` é contado como um crédito).

## Como executar do zero

Pré-requisitos: Python 3.12 ou superior, `uv` e acesso ao Kaggle para baixar o
dataset. Clone o repositório usando a URL remota fornecida pelo projeto e abra
um PowerShell na pasta raiz. Então:

```powershell
# Crie a pasta de dados e copie para ela o CSV baixado e extraído do Kaggle.
New-Item -ItemType Directory -Force .\data
Copy-Item "$HOME\Downloads\dataset.csv" .\data\dataset.csv

# Crie/sincronize o ambiente e instale as dependências, incluindo pytest.
uv sync --dev

# Execute Bronze -> Silver -> Gold e exiba os indicadores.
uv run main.py

# Abra o menu interativo para escolher um relatório Gold.
uv run menu.py

# Rode os testes unitários, que usam dados inventados.
uv run pytest -q
```

O comando `Copy-Item` presume que o arquivo baixado se chama `dataset.csv` e
está em `Downloads`; ajuste o caminho se necessário. O pipeline encerra com uma
mensagem amigável se `data/dataset.csv` não existir.

## Testes unitários

Execute com `uv run pytest -q`. Os testes em
[`tests/test_pipeline.py`](tests/test_pipeline.py) criam CSVs pequenos com dados
inventados em `tmp_path` e usam conexões DuckDB `:memory:`. Eles não executam
`main.py`, não leem `data/dataset.csv` e não abrem um banco persistido do
projeto.

Os seis testes verificam:

1. Bronze preserva nomes de colunas e valores como texto.
2. Silver remove duplicatas por música/artista, mantendo a maior popularidade.
3. Nulos recebem padrões e valores numéricos inválidos são descartados.
4. Os SQLs dos marts produzem os indicadores Gold esperados.
5. O menu exibe os relatórios disponíveis e renderiza a opção escolhida.
6. A ingestão informa quando o CSV não existe.

## Uso de IA e práticas de código

IA generativa, por meio do Copilot SDK no VS Code, foi utilizada como apoio à
implementação e à documentação. As regras de transformação e os indicadores
descritos aqui seguem a especificação do projeto; a execução foi verificada
com `uv run main.py` e `uv run pytest -q`. A IA não é a fonte dos dados: a fonte
é o dataset publicado no Kaggle.

Os módulos Python são separados por responsabilidade e seguem as convenções de
estilo do PEP 8; as consultas de negócio ficam em arquivos SQL próprios.

### 🤖 A IA entra em todas as etapas — e você confere todas

Nesta implementação, algumas hipóteses e erros foram encontrados na
verificação:

- **Fonte:** o primeiro endereço Kaggle usado retornou 404. Conferindo a página
  canônica, corrigi o link e registrei a licença ODbL 1.0.
- **Testes:** embora o contexto dissesse que pytest já estava instalado,
  `uv run pytest --version` falhou porque a dependência não estava no projeto;
  adicionei-a com `uv add --dev pytest`. A primeira coleta também falhou com
  `ModuleNotFoundError: pipeline`; configurei o caminho de importação e a
  execução final passou com **6 testes**.
- **Contagem:** no CSV real, contei **114.000** linhas na Bronze e **81.344** na
  Silver (diferença de **32.656**). Essa diferença inclui deduplicações e
  descartes por dados inválidos; não a tratei como contagem exclusiva de
  duplicatas.
