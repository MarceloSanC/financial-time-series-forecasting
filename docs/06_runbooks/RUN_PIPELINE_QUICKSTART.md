# Primeiros Passos

Guia rapido para configurar e rodar o pipeline localmente (Windows).

## Pre-requisitos
- Windows 10/11
- Python 3.12+
- Git (opcional)
- `make` (recomendado)
- pyenv (opcional, para padronizar versao local)

## Setup

1. Clone o repositorio:
```bash
git clone https://github.com/MarceloSanC/tcc-sentiment-analysis.git
cd tcc-sentiment-analysis
```

2. Instale `make` (winget):
```powershell
winget install GnuWin32.Make
```

3. Configure permissao de script e bootstrap:
```powershell
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
.\setup.ps1
```

4. Crie a venv (se necessario) e rode setup novamente:
```powershell
python -m venv .venv
.\setup.ps1
```

5. Instale dependencias:
```bash
make install
```

## Sanity Check
```bash
make lint
make test
```

## Padronizacao com pyenv (opcional)
```bash
pyenv install 3.12.10
pyenv local 3.12.10
```

## Proximos Passos
- Pipeline completo: `docs/06_runbooks/RUN_DATASET.md`
- Treino: `docs/06_runbooks/RUN_TRAINING.md`
- Inferencia: `docs/06_runbooks/RUN_INFERENCE.md`
- Analytics quality gate: `docs/06_runbooks/RUN_REFRESH_ANALYTICS.md`
- Tracking de implementacao: `docs/05_checklists/CHECKLISTS.md`
