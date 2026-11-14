# Spotify Terminal Analytics Pipeline

Pipeline de dados em Python para analisar o dataset público **Spotify Tracks Dataset**. O fluxo
usa DuckDB e arquitetura Medallion (Bronze, Silver e Gold), com indicadores em SQL e relatórios
interativos no terminal por meio de Rich e Plotext.

## Fonte dos dados

- **Dataset:** [Spotify Tracks Dataset no Kaggle](https://www.kaggle.com/datasets/maharshipandya/-spotify-tracks-dataset)
- **Autor indicado na página:** Maharshi Pandya.
- **Licença indicada no Kaggle:** [Open Database License (ODbL) v1.0](https://opendatacommons.org/licenses/odbl/1-0/). O conteúdo mantém os direitos autorais de seus autores originais.
- **Arquivo esperado pelo pipeline:** `data/dataset.csv`.

Baixe o CSV na página do dataset e salve-o nesse caminho. O pipeline não baixa o arquivo
automaticamente. A Bronze lê os registros como texto para preservar os valores originais do CSV.

## O que representa uma linha

| Objeto | Granularidade |
| --- | --- |
| CSV de origem / `spotify_raw` (Bronze) | Um registro do dataset para uma faixa e um gênero. A mesma combinação de faixa e artista pode aparecer em mais de um registro. |
| `spotify_silver` (Silver) | Uma combinação de `track_name` e `artists`. Se houver duplicatas dessa combinação, mantém o registro com maior popularidade. |
| Views Gold | A granularidade varia por indicador e está descrita na tabela de indicadores abaixo. |

Na Silver, faixas sem valores textuais recebem `Desconhecido`; métricas ausentes recebem zero.
Registros com popularidade fora do intervalo de 0 a 100 ou valores numéricos inválidos são
descartados. Os campos de popularidade, energia, dançabilidade, tempo e valência são convertidos
para tipos numéricos.

## Camadas e indicadores

O fluxo executa Bronze → Silver → Gold usando DuckDB em memória (`:memory:`). O banco não é
persistido em disco.

1. **Bronze — Raw:** importa `data/dataset.csv` para `spotify_raw`, sem renomear colunas ou
   transformar os valores.
2. **Silver — Refined:** executa `sql/silver/transform_tracks.sql` para deduplicar, limpar e
   converter os campos analíticos.
3. **Gold — Marts:** carrega dinamicamente cada arquivo `.sql` de `sql/marts/` e cria uma view
   correspondente. Os cálculos dos indicadores ficam nos arquivos SQL, não na apresentação.

| Arquivo SQL | View Gold | Indicador e granularidade |
| --- | --- | --- |
| `01_top_musicas.sql` | `gold_top_musicas` | Até cinco faixas, uma linha por faixa, ordenadas por popularidade. |
| `02_media_generos.sql` | `gold_media_generos` | Uma linha por gênero, com popularidade média e quantidade de faixas. |
| `03_perfil_audio_generos.sql` | `gold_perfil_audio_generos` | Até cinco gêneros, uma linha por gênero, com contagem e médias das métricas de áudio. |
| `04_top_artistas.sql` | `gold_top_artistas` | Até dez valores do campo `artists`, uma linha por valor, ordenados pela quantidade de faixas. |
| `05_generos_populares.sql` | `gold_generos_populares` | Até dez gêneros, uma linha por gênero, com popularidade média e quantidade de faixas. |
| `06_maior_energia.sql` | `gold_maior_energia` | Até cinco faixas com maior energia, uma linha por faixa. |
| `07_mais_dancaveis.sql` | `gold_mais_dancaveis` | Até cinco faixas mais dançáveis, uma linha por faixa. |

O menu Rich oferece os sete relatórios Gold e a opção 8 para visualizar, com Plotext, as barras dos
dez gêneros mais populares. O gráfico consulta `gold_generos_populares`; a opção 0 encerra o menu.

## Requisitos e execução

Requisitos: Python 3.12 ou superior e [uv](https://docs.astral.sh/uv/).

```bash
# Clone o repositório na branch do projeto
git clone --branch feature/melhorias-pipeline https://github.com/Well-cre/spotify-pipeline-analytics.git
cd spotify-pipeline-analytics

# Baixe o CSV do Kaggle e coloque-o em data/dataset.csv

# Crie/sincronize o ambiente e as dependências do projeto
uv sync

# Execute Bronze -> Silver -> Gold e abra o menu de relatórios
uv run main.py
```

Se `data/dataset.csv` não existir, o programa encerra com uma mensagem amigável indicando o
caminho esperado.

## Testes

Execute os testes unitários com:

```bash
uv run pytest -q
```

Os testes usam apenas dados inventados em arquivos temporários (`tmp_path`) e conexões DuckDB em
memória. Eles não leem o CSV real nem um banco de dados do projeto. Cobrem a ingestão Bronze, as
regras de transformação Silver, a criação dos indicadores Gold a partir dos SQLs, o menu, o gráfico
Top 10 e o tratamento de arquivo CSV ausente.

## PEP 8, boas práticas e Ruff

O código mantém as responsabilidades separadas entre ingestão, transformação, marts e
apresentação. A lógica dos indicadores permanece nos SQLs da Gold; os testes exercitam o DuckDB
real em memória, sem mock do banco.

O Ruff está configurado no `pyproject.toml` para Python 3.12, limite de 100 caracteres por linha e
regras `E`/`W` (estilo e avisos), `F` (Pyflakes) e `I` (ordenação de imports). Rode as verificações
com:

```bash
uv run ruff check .
uv run ruff format --check .
```

`ruff format --check` verifica a formatação sem modificar os arquivos.

## Uso da IA e conferência

### 🤖 A IA entra em todas as etapas — e você confere todas

Durante o desenvolvimento, a revisão dos resultados revelou erros e premissas que precisaram ser
conferidos:

- Uma versão anterior desta documentação atribuía licença CC0 ao dataset e usava um endereço
  incorreto. A página do Kaggle foi consultada e a referência foi corrigida para ODbL 1.0.
- O gráfico chegou a usar `plotext.bar`, atributo inexistente na versão 6.1.0 instalada. A API foi
  conferida em execução e o gráfico foi ajustado para a interface `figure`; um teste com 11 gêneros
  inventados verifica que somente os dez primeiros são exibidos.
- Na execução com o dataset, foram conferidas as contagens antes e depois da Silver: 114.000
  registros na Bronze e 81.344 na Silver. A diferença é compatível com as regras de deduplicação e
  validação, em vez de ser tratada como perda silenciosa de dados.

> Um projeto em que a IA não errou nenhuma vez é um projeto em que ninguém conferiu.
