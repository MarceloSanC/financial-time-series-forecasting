---
title: Troubleshooting
scope: Solucao de problemas comuns no setup do ambiente local (PATH, make, venv, Windows, Linux). Catalogo de erros e fixes verificados.
update_when:
  - novo erro recorrente for diagnosticado
  - fix de erro existente mudar
  - dependencia de OS for adicionada/removida
canonical_for: [troubleshooting, common_errors, setup_fixes]
---

# 🛠 Solução de Problemas Comuns

## `make : O termo 'make' não é reconhecido...`

Causa: `make` não está no PATH.

Solução:
```
$env:PATH += ";C:\Program Files (x86)\GnuWin32\bin"
```

Ou execute:
```
.\setup.ps1
```

## `git push` falha com "Authentication failed"

Causa: GitHub não aceita senha; exige token ou SSH.

Solução:
1. Crie um [Personal Access Token](https://github.com/settings/tokens)
2. Use seu usuário + token como senha no `git push`

Ou mude para SSH:
```
git remote set-url origin git@github.com:MarceloSanC/tcc-sentiment-analysis.git
```

## `ModuleNotFoundError: No module named 'src'`

Causa: `src/` não está no `PYTHONPATH`.

Solução:
- Certifique-se de ter rodado:
```
make install
```
- Ou verifique se `pyproject.toml` tem:
```
[tool.pytest.ini_options]
pythonpath = ["src"]
```

## `yfinance` retorna DataFrame vazio

Causa: símbolo incorreto ou período fora do mercado.

Solução:
- Use `PETR4.SA`, não `PETR4`
- Verifique datas úteis (ex: evite fins de semana)