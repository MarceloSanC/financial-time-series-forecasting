# ?? Primeiros Passos

Este guia explica como configurar e executar o projeto localmente (Windows).

## Pr?-requisitos

- Windows 10/11
- Python 3.12+
- Git (opcional)
- pyenv (opcional, recomendado para padronizar versao local)

## Configura??o

1. Clone o reposit?rio (ou baixe o ZIP):
```
git clone https://github.com/MarceloSanC/tcc-sentiment-analysis.git
cd tcc-sentiment-analysis
```

2. Instale o `make` (via winget):
```
winget install GnuWin32.Make
```

3. Configure o ambiente:
```
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
.\setup.ps1
```

> O script `setup.ps1`:
> - Adiciona `make` ao PATH
> - Verifica Python 3.12+
> - Ativa o ambiente virtual (se `.venv` existir)

4. Crie o ambiente virtual (se ainda n?o existir):
```
python -m venv .venv
.\setup.ps1
```

5. Instale as depend?ncias:
```
make install
```

Pronto! O projeto est? configurado.

## Padronizacao com pyenv (recomendado)

Este repositorio versiona `.python-version` com a versao alvo do projeto.

Se voce usa pyenv:
```
pyenv install 3.12.10
pyenv local 3.12.10
```

Isso reduz divergencias de ambiente antes da migracao completa para Docker.

## Checklist do MVP

Consulte `docs/MVP_CHECKLIST.md` para o roadmap e o status atual.
