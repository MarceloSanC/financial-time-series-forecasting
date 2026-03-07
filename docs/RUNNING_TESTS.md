# 🧪 Executando Testes

O projeto usa `pytest` para testes unitários e de integração.

## Rodar todos os testes

```
make test
```

Saída esperada:
```
----------- coverage: platform win32, python 3.12.0 -----------
Name                              Stmts   Miss  Cover
-------------------------------------------------------
src/entities/news.py                 12      0   100%
src/use_cases/fetch_news_use_case.py 28      0   100%
...
TOTAL                                64      0   100%
```

## Rodar testes específicos

- Por arquivo:
```
python -m pytest tests/unit/use_cases/test_fetch_news_use_case.py -v
```

- Por marcação (ex: testes de integração):
```
pytest tests/integration/ -v
```

## Estrutura de testes

Os testes seguem os princípios de Clean Architecture e DDD,
espelhando a estrutura de `src/`.

### Testes unitários (`tests/unit/`)

Cobrem comportamento isolado, sem dependências externas:

- `entities/`  
  Validação de regras de negócio fundamentais e invariantes.

- `domain/services/`  
  Regras de agregação, cálculo e lógica puramente determinística.

- `use_cases/`  
  Orquestração de fluxo, com dependências mockadas.

- `interfaces/`  
  Testes de contrato para garantir consistência entre camadas.

- `adapters/`  
  Testes unitários com mocks, sem chamadas reais a APIs ou modelos.

- Testes unitários: `tests/unit/` — não usam rede, banco ou modelo pesado
- Todos os testes unitários devem ser executáveis offline.

### Testes de integração (`tests/integration/`)

Validam a integração entre múltiplas camadas do sistema, podendo
envolver acesso a disco ou pipelines completos.

- Testes de integração: `tests/integration/` — usam APIs reais (marcados com `@pytest.mark.integration`)

## Testes recomendados para feature sets (anti-leakage, warmup, schema)

Build de dataset e features derivadas:

```bash
.venv/bin/pytest -q tests/unit/use_cases/test_build_tft_dataset_use_case.py
```

Treino com validacoes de warmup e quality gate:

```bash
.venv/bin/pytest -q tests/unit/use_cases/test_train_tft_model_use_case.py
```

Validacao de contratos de config de treino:

```bash
.venv/bin/pytest -q tests/unit/infrastructure/schemas/test_model_artifact_schema.py
```

Validacao de registry e warmup canonical:

```bash
.venv/bin/pytest -q tests/unit/infrastructure/schemas/test_feature_registry.py tests/unit/infrastructure/schemas/test_feature_validation_schema.py
```
