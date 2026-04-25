---
title: System Overview
scope: Estrutura de diretorios `src/` do projeto e organizacao da Clean Architecture (entities, interfaces, use_cases, adapters, infrastructure). Mapeia onde cada tipo de codigo mora.
update_when:
  - novo diretorio top-level for criado em src/
  - nova camada da Clean Architecture for adicionada
  - convencao de organizacao de codigo mudar
canonical_for: [system_overview, src_structure, clean_architecture, code_layout]
---

# 🗂 Estrutura do Projeto

O projeto segue Clean Architecture. Diretórios principais:

- `src/` — código-fonte
  - `entities/` — modelos de domínio (ex: `News`, `Candle`)
  - `interfaces/` — contratos abstratos (ex: `NewsFetcher`, `DataRepository`)
  - `use_cases/` — lógica de negócio (ex: `FetchNewsUseCase`)
  - `adapters/` — implementações concretas (ex: `FinnhubNewsFetcher`, `YFinanceDataFetcher`)
  - `main.py`, `main_candles.py` — entry points

- `tests/` — testes
  - `unit/` — testes unitários (mocks)
  - `integration/` — testes com APIs reais

- `data/` — dados gerados
  - `raw/` — candles em Parquet, banco SQLite

- `config/` — configuração declarativa (`data_sources.yaml`)

- `docs/` — documentação (este diretório)

- `setup.ps1`, `Makefile`, `pyproject.toml` — automação