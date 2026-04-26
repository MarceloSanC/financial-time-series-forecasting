---
title: Governance and Versioning
scope: Documento canonico de governanca de processo. Define fluxo branch/commit/PR, formato de mensagem de commit, politica de versionamento (`pipeline_version`, `schema_version`, `model_version`, `sweep_id`) e politica de reprodutibilidade.
update_when:
  - fluxo de branch/commit/PR mudar
  - formato de mensagem de commit ou template de PR mudar
  - politica de versionamento (qualquer dos IDs) mudar
  - politica de reprodutibilidade for revisada
canonical_for: [governance, versioning_policy, reproducibility_policy, branch_commit_pr_flow, pipeline_version, schema_version, model_version, sweep_id]
---

# Governance and Versioning

This is the canonical governance document for branch workflow, commits, pull
requests, version identifiers, and reproducibility policy.

It replaces:
- `docs/08_governance/VERSIONING_POLICY.md`
- `docs/08_governance/REPRODUCIBILITY_POLICY.md`
- `docs/08_governance/GIT_AND_VERSIONING_GUIDE.md`

## Branch, Commit and PR Flow

Use this flow after a merge or when starting a new task from a clean working
tree.

### 1. Sync and Check State

```bash
git fetch origin --prune
git checkout main
git pull --ff-only origin main
git status
```

Expected state:
- current branch is `main`
- working tree is clean (`nothing to commit, working tree clean`)

### 2. Delete the Old Local Branch

```bash
git branch -d <branch_antiga>
```

If Git says the branch was not merged locally but the GitHub PR was already
merged:

```bash
git fetch origin --prune
git branch -d <branch_antiga>
```

Use `-D` only as a last resort.

### 3. Create the New Branch

Branch naming pattern:

```text
<tipo>/<area>-<objetivo>
```

```bash
git checkout -b <nova_branch>
```

Examples:
- `feature/stage-a-task7-models-tests`
- `fix/models-version-validation`
- `docs/readme-models-endpoints`

### 4. Implement and Review Scope

Check changed files:

```bash
git status --short
```

Review the diff:

```bash
git diff
```

### 5. Commit

Commit format:

```text
<tipo>(<escopo>): <resumo no imperativo>
```

Commands:

```bash
git add <arquivos_do_escopo>
git commit -m "<tipo>(<escopo>): <resumo no imperativo>"
```

Examples:
- `feat(models): add introspection routes for model metadata`
- `test(models): add integration coverage for /models endpoints`
- `docs(readme): add usage examples for models endpoints`

Use scoped commits: each commit should represent one coherent, reviewable
change. Do not include files outside the task scope.

Common commit types:
- `feat`: new feature
- `fix`: bug fix
- `test`: tests or test infrastructure
- `docs`: documentation
- `refactor`: structural change without intended behavior change
- `chore`: configuration, dependencies, generated maintenance
- `ci`: CI workflow changes

### 6. Push the Branch

```bash
git push -u origin <nova_branch>
```

### 7. Prepare the PR

Include:
- context/objective
- main changes
- contract/API impact, if any
- validations executed
- known risk, if any

PR body template:

```md
## Summary
- ...
- ...

## Changes
- ...
- ...

## Validation
- ...
- ...

## Notes
- ...
```

### 8. Create the PR

GitHub Web:
- open the URL suggested by `git push`
- or open `https://github.com/<owner>/<repo>/pull/new/<nova_branch>`

GitHub CLI:

```bash
gh pr create --base main --head <nova_branch> --title "<titulo>" --body-file <arquivo_descricao.md>
```

### 9. Validate Before Merge

Merge readiness checklist:

1. PR scope is correct, with no files outside the task.
2. Base branch is `main`.
3. CI/checks are green.
4. Relevant local tests passed.
5. There are no merge conflicts.
6. There are no blocking unresolved comments.

Useful local commands:

```bash
git status --short
git log --oneline -n 5
```

Useful GitHub commands:

```bash
gh pr view --json number,title,state,mergeable,headRefName,baseRefName
gh pr checks
```

### 10. Clean Up After Merge

After merging on GitHub:

```bash
git checkout main
git pull --ff-only origin main
git branch -d <nova_branch>
git fetch origin --prune
```

### Short Sequence

```bash
git fetch origin --prune
git checkout main
git pull --ff-only origin main
git branch -d <branch_antiga>
git checkout -b <nova_branch>
# implementar
git add <arquivos>
git commit -m "<tipo>(<escopo>): <mensagem>"
git push -u origin <nova_branch>
# abrir PR
```

## Versioning Policy

Version identifiers must make persisted artifacts traceable and reproducible.

### Pipeline Version

Use a pipeline version when a data-processing, training, inference, or analytics
behavior changes in a way that can affect persisted outputs.

Record the pipeline version in run metadata whenever the output may be compared
or audited later.

### Schema Version

Use schema versions for persisted tables and contracts.

Schema version changes are required when:
- a column is added, removed, renamed, or changes type
- nullability or allowed values change
- semantic meaning changes even if the physical type remains the same
- downstream quality checks or consumers must change behavior

### Model Version

Model versions identify trained artifacts and must be immutable once published.

A model version must be traceable to:
- training run metadata
- feature set and config signature
- data/split scope
- model artifact path
- validation metrics and decision context

### Sweep Identifiers

Sweep identifiers must isolate experiment cohorts.

Use stable prefixes for related search spaces and keep final decision artifacts
scoped to the exact cohort used in analysis.

## Reproducibility Policy

Reproducibility is required for any artifact used in model selection, analytics
quality decisions, or project reporting.

### Must Have

- immutable run records
- schema contracts
- quality-gated analytics refresh
- persisted inputs for final decision artifacts
- documented commands and paths for rerun

### Validation

- document the rerun procedure
- use deterministic comparison inputs
- record scope, splits, horizons, and cohort identifiers
- report validations executed locally and in CI

### Scope-Aware Quality Semantics

- Global quality checks validate platform/asset health and historical
  consistency.
- Scoped quality checks validate a specific cohort decision context.
- For statistical winner selection, scoped validation is mandatory and must
  match the same cohort/splits/horizons used in analysis.
- A global failure does not invalidate a scoped purge/rerun operation by itself;
  it indicates unresolved issues outside, or across, the chosen scope.

### Decision Integrity

- Every final decision artifact must record the exact analysis scope.
- Re-running with a new cohort prefix must preserve old cohorts for auditability,
  unless an explicit purge is requested.
- Gold decision artifacts must be reproducible from persisted data only, without
  retraining.
- Pairwise statistical comparison requires exact intersection by
  `target_timestamp`.
- Statistical/model-selection conclusions require explicit cohort scope.

