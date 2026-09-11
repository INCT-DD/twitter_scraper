# Twitter Scraper

Sistema de coleta de dados da plataforma X (antigo Twitter), desenvolvido para apoiar pesquisas acadêmicas do INCT.DD.

O sistema permite realizar a coleta de publicações de perfis previamente configurados, considerando um período específico, armazenando os dados em PostgreSQL e exportando os resultados para arquivos estruturados.

---

## 1. Visão Geral

O Twitter Scraper foi desenvolvido para automatizar a coleta de publicações de perfis do X, permitindo definir o período de interesse e os perfis que serão processados.

A aplicação utiliza a biblioteca [`twscrape`](https://github.com/vladkens/twscrape) para realizar a coleta dos dados e PostgreSQL para armazenamento das publicações coletadas.

Entre as principais funcionalidades estão:

- Coleta de publicações de perfis configurados;
- Definição do período de coleta;
- Identificação dos perfis por categoria, UF e partido;
- Armazenamento dos dados em PostgreSQL;
- Exportação dos dados em JSON e CSV;
- Gerenciamento de mídias associadas às publicações;
- Controle de duplicidade dos tweets coletados.

### Tecnologias utilizadas

- Python
- twscrape
- PostgreSQL
- psycopg2
- Docker
- python-dotenv
- JSON
- CSV

---

## 2. Arquitetura do Projeto

O projeto foi organizado em diferentes camadas, separando as responsabilidades de coleta, processamento, armazenamento e exportação dos dados.

```text
                    ┌─────────────────┐
                    │     main.py     │
                    │  Interface CLI  │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   pipeline.py   │
                    │   PipelineV2    │
                    └───────┬─────────┘
                            │
                 ┌──────────┴──────────┐
                 ▼                     ▼
       ┌──────────────────┐   ┌──────────────────┐
       │twitter_scraper.py│   │   exporter.py    │
       │      Coleta      │   │ JSON / CSV / fila│
       └─────────┬────────┘   └────────┬─────────┘
                 │                     │
                 ▼                     ▼
       ┌──────────────────┐   ┌──────────────────┐
       │    storage.py    │   │  media_queue.py  │
       │    PostgreSQL    │   │   Fila de mídia  │
       └──────────────────┘   └────────┬─────────┘
                                      │
                                      ▼
                             ┌──────────────────┐
                             │media_downloader.py│
                             │ Download de mídia │
                             └──────────────────┘
```
## Componentes principais

| Arquivo               | Responsabilidade                                                           |
| --------------------- | -------------------------------------------------------------------------- |
| `main.py`             | Interface de execução da coleta e entrada dos parâmetros pelo usuário      |
| `pipeline.py`         | Coordenação do fluxo de coleta, armazenamento e exportação                 |
| `twitter_scraper.py`  | Coleta dos tweets utilizando o `twscrape` e processamento dos dados        |
| `storage.py`          | Conexão e operações de armazenamento no PostgreSQL                         |
| `exporter.py`         | Exportação dos dados em JSON e CSV e encaminhamento das mídias para a fila |
| `media_queue.py`      | Gerenciamento da fila de mídias                                            |
| `media_downloader.py` | Download das mídias associadas aos tweets                                  |
| `main_media.py`       | Execução do processamento relacionado às mídias                            |
| `retry_media.py`      | Realização de novas tentativas de processamento das mídias                 |
| `config.py`           | Carregamento das configurações do banco de dados                           |

## Fluxo geral

De forma simplificada, o funcionamento da aplicação ocorre da seguinte maneira:

Configuração
     │
     ▼
 main.py
     │
     ▼
PipelineV2
     │
     ▼
TwitterScraperV2
     │
     ▼
Coleta dos tweets
     │
     ├──────────────► PostgreSQL
     │
     └──────────────► JSON / CSV
                           │
                           ▼
                      Fila de mídia
                           │
                           ▼
                   Download de mídia

A separação das responsabilidades permite que os componentes de coleta, armazenamento e exportação sejam mantidos de forma independente.

## 3. Instalação e configuração

  ### 3.1 Pré-requisitos

  Antes de executar o projeto, é necessário possuir um ambiente com:
  
  - Python instalado;
  - PostgreSQL disponível;
  - Docker, caso o PostgreSQL seja executado em container;
  - Git para obter o código-fonte do projeto.

  ### 3.2 Clonar o repositório
  
  Clone o repositório:
  
  `git clone https://github.com/INCT-DD/twitter_scraper.git`
  
  Entre na pasta do projeto:
  
  `cd twitter_scraper`

  ### 3.3 Criar ambiente virtual

  Recomenda-se utilizar um ambiente virtual Python:
  
  `python -m venv venv`
  
  No Windows:
  
  `venv\Scripts\activate`

  ### 3.4 Configurar as variáveis do banco

  O arquivo `config.py` utiliza variáveis de ambiente para obter as credenciais do PostgreSQL.

  A configuração esperada é:

  ```text
  DB_HOST=
  DB_PORT=
  DB_NAME=
  DB_USER=
  DB_PASSWORD=
  ```
  
  Essas informações devem ser armazenadas em um arquivo `.env`.

  
  >[Importante:]
  > o arquivo .env não deve ser versionado no Git. Ele está incluído no .gitignore do projeto.
