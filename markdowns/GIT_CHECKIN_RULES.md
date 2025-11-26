# Git Check-in Rules & Secret-Scanning Guidelines

This document defines **mandatory rules** for committing code to this repository, with a strong focus on **preventing secrets from being checked in**.

---

## 1. Absolutely Never Commit Secrets

- **Never commit real secrets** such as:
  - **API keys**, access tokens
  - **Passwords**, database connection strings
  - **Private keys** (SSH, TLS, JWT signing keys, etc.)
  - **Personal data** that should remain private
- Use **placeholders** in tracked files instead, for example:
  - `GEMINI_API_KEY=REPLACEME`
- Store real values only in:
  - Local, untracked `.env` files
  - Secret managers (Vault, Azure Key Vault, AWS Secrets Manager, etc.)

**If you suspect a secret was committed at any time:**
- Rotate/disable the secret immediately.
- Remove it from history following your org’s incident process.

---

## 2. Required Files and Patterns

- All example env files **must** use placeholders only, e.g.:
  - `.env.example` → `GEMINI_API_KEY=REPLACEME`
- Ensure `.gitignore` includes (examples):
  - `.env`
  - `*.pem`, `*.key`
  - `*.pfx`, `*.p12`
  - `*.crt`
  - Any other local config files that may contain secrets.

---

## 3. Pre-Commit: Secret Scanning and Basic Quality Checks

We recommend using **pre-commit** to enforce checks locally.

### 3.1. Install `pre-commit`

```bash
pip install pre-commit
# or
pipx install pre-commit
```

Then enable it in this repo:

```bash
pre-commit install
```

This will run all configured hooks **on every `git commit`**.

### 3.2. Example `.pre-commit-config.yaml`

Create a file named `.pre-commit-config.yaml` at the repo root with content similar to:

```yaml
repos:
  # Basic hygiene: remove trailing whitespace, fix EoL, etc.
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json

  # Detect secrets using Yelp's detect-secrets
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args:
          # Use a baseline file to track audited findings
          - "--baseline .secrets.baseline"

  # Optional: additional secret scanner (GitLeaks wrapper)
  # - repo: https://github.com/zricethezav/gitleaks
  #   rev: v8.18.0
  #   hooks:
  #     - id: gitleaks
```

Then initialize the baseline for `detect-secrets` (run once, then review):

```bash
detect-secrets scan > .secrets.baseline
# Manually review and audit the baseline before committing it
```

> **Policy:** A commit **must not introduce new, unapproved secret findings**. If a hook fails, fix the root cause instead of bypassing the hook.

---

## 4. Developer Pre-Commit Checklist (Manual)

Before committing, always verify:

- **Secrets**
  - **[ ]** No real API keys, tokens, passwords, or private keys in tracked files
  - **[ ]** Env-like files checked in only as `*.example` with placeholders
  - **[ ]** `.gitignore` excludes local secret-bearing files

- **Code Quality**
  - **[ ]** Code compiles / lints cleanly (or at least no new warnings)
  - **[ ]** Unit tests relevant to your change pass
  - **[ ]** No obvious TODOs or debug prints left in production code

- **Documentation & Comments**
  - **[ ]** Public-facing behavior changes documented (README, API docs, etc.)
  - **[ ]** Comments do not expose sensitive information (internal URLs, tokens)

- **Git Hygiene**
  - **[ ]** Commit is focused: one logical change per commit where reasonable
  - **[ ]** No large generated/binary files unless explicitly required

---

## 5. Commit Message Guidelines

Use clear, descriptive commit messages:

- **Format:**
  - Short summary (≤ 72 chars)
  - Optional longer description with context, rationale, and any caveats

- **Good examples:**
  - `fix: handle missing customer_id in transcript search`
  - `feat: add /api/customers/{id} endpoint`
  - `chore: add pre-commit hooks for secret scanning`

- **Bad examples:**
  - `misc changes`
  - `fix stuff`

---

## 6. Branching & Pull Request Best Practices

- **Branches**
  - Use descriptive names: `feature/ada-violations-report`, `bugfix/customer-null-id`, `chore/secret-scanning`

- **Pull Requests**
  - Keep PRs small and focused
  - Reference related issues / tickets
  - Clearly describe:
    - What changed
    - Why it changed
    - How it was tested

- **Review Expectations**
  - Reviewers should check for:
    - Possible **secret leaks**
    - Security impact (auth, authorization, logging)
    - Tests and documentation

---

## 7. Handling Detected Secrets

If a secret is detected by tooling or manually:

1. **Stop and assess**
   - Determine if the secret is real and active.

2. **Rotate and revoke**
   - Regenerate API keys / tokens.
   - Remove or rotate credentials from affected systems.

3. **Remove from Git history** (if required by policy)
   - Use tools like `git filter-repo` or `git filter-branch` as per your org’s guidelines.

4. **Document the incident**
   - Follow your team’s incident management process.

---

## 8. Local Environment Setup Summary

- Copy `.env.example` → `.env` and fill with **local-only** values.
- Keep `.env` **untracked** (ensure `.gitignore` is correct).
- Never paste secrets into chat logs, screenshots, or commit messages.

By following these rules and enabling pre-commit hooks, we significantly reduce the risk of committing sensitive information and improve the overall quality and security of this codebase.
