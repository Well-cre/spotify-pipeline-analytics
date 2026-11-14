# 🎧 Spotify Terminal Analytics Pipeline

Pipeline de Engenharia de Dados desenvolvido em Python moderno, utilizando arquitetura em camadas (Medallion Architecture), banco analítico embutido (DuckDB) e uma interface de terminal interativa rica (`rich`). O projeto consome o dataset público do Spotify para gerar indicadores analíticos acionáveis de áudio e popularidade.

---

## 📌 1. Fonte dos Dados
* **Dataset:** [Spotify Tracks Dataset](https://www.kaggle.com/datasets/maharshipandya/spotify-tracks-dataset) (disponível no Kaggle por *Maharshi Pandya*).
* **Licença:** [CC0: Public Domain](https://creativecommons.org/publicdomain/zero/1.0/) (Permite uso público, modificação e distribuição irrestrita).

---

## 🎵 2. O que é uma Linha do Dataset?
Cada linha (registro) na tabela principal representa **uma faixa (track) musical única** disponibilizada no catálogo do Spotify, contendo mais de 125 gêneros musicais diferentes. Cada registro inclui metadados da música (nome da faixa, artistas, álbum, popularidade de 0 a 100) e atributos técnicos de engenharia de áudio extraídos pela plataforma (como `danceability`, `energy`, `tempo`, `valence`, entre outros).

---

## 🏛️ 3. Arquitetura de Camadas (Medallion Architecture) e Indicadores

O pipeline é estritamente dividido em três camadas lógicas executadas em memória através do DuckDB:

1. **Bronze (Raw):** Ingestão do arquivo CSV bruto (`data/dataset.csv`) exatamente como fornecido pela fonte, sem alterar tipos de dados, nomes de colunas ou valores.
2. **Silver (Refined):** Camada de limpeza e padronização. Executa regras declaradas em arquivo SQL externo (`sql/silver/transform_tracks.sql`) para tratar nulos, padronizar tipos numéricos e remover inconsistências.
3. **Gold (Marts):** Camada de indicadores de negócio. Cada indicador é alimentado exclusivamente por um arquivo `.sql` dedicado localizado na pasta `sql/marts/`.

### Indicadores da Camada Gold (Disponíveis no Menu Interativo):
* **Top 5 Músicas Mais Populares:** Faixas com maior pontuação de popularidade global (`gold_top_musicas.sql`).
* **Popularidade Média por Gênero:** Agrupamento analítico da popularidade média por gênero musical (`gold_media_generos.sql`).
* **Perfil de Áudio por Gênero:** Médias de energia, dançabilidade e atributos técnicos por categoria (`gold_perfil_audio_generos.sql`).
* **Artistas com Mais Faixas:** Contagem e ranking de artistas com maior volume de registros no dataset (`gold_top_artistas.sql`).
* **Músicas Mais Dançáveis:** Ranking focado na métrica de dançabilidade (`gold_mais_dancaveis.sql`).
* **Músicas com Maior Energia:** Ranking focado no nível de energia técnica da faixa (`gold_maior_energia.sql`).

---

## 🛡️ 4. Robustez e Tratamento de Erros
O projeto implementa blocos estruturados de **`try / except`** (especificamente capturando exceções do `duckdb.Error` e falhas críticas no pipeline) com fechamento seguro de conexões no bloco `finally`. Isso garante que caso ocorra um erro de sintaxe em consultas ou falhas de leitura, a aplicação exiba alertas estilizados sem fechar abruptamente o terminal, preservando a experiência de navegação do usuário.

---

## 🚀 5. Como Rodar o Projeto do Ziro (Passo a Passo)

Certifique-se de ter o Python 3.12+ e o gerenciador de pacotes **`uv`** instalados em sua máquina.

### Clonar e Instalar Dependências
```bash
# Clone o repositório
git clone [https://github.com/Well-cre/spotify-pipeline-analytics.git](https://github.com/Well-cre/spotify-pipeline-analytics.git)
cd spotify-pipeline-analytics

# Instale as dependências com o uv
uv sync