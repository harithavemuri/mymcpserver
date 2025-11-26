# MyFeedback MCP Server

This repository contains the **MyFeedback MCP server** and supporting code, including FastAPI endpoints, MCP tools, and sample data for customers and call transcripts.

---

## Pre-commit Hooks & Secret Scanning

This project uses **pre-commit hooks** to:

- Enforce basic code hygiene (trailing whitespace, EOF fixes, JSON/YAML checks).
- **Scan for secrets** (API keys, passwords, tokens, private keys, etc.) before every commit using `detect-secrets`.

### 1. One-time Setup

From the repository root (`MyFeedback`):

```bash
pip install pre-commit detect-secrets
pre-commit install
```

This installs `pre-commit`, the `detect-secrets` CLI, and the Git hook so that all configured checks run automatically on every `git commit`.

### 2. Initialize the Secrets Baseline

We use **Yelp detect-secrets** with a baseline file. Run this once (and whenever you want to rescan).

On **PowerShell (Windows)**, use:

```powershell
detect-secrets scan | Out-File -Encoding utf8 .secrets.baseline
```

If `detect-secrets` is not on PATH, you can instead use:

```powershell
python -m detect_secrets scan | Out-File -Encoding utf8 .secrets.baseline
```

On **bash (Linux/macOS)**, the classic redirection is fine:

```bash
detect-secrets scan > .secrets.baseline
```

Then:

1. Open `.secrets.baseline` and review the findings.
2. Mark any entries that are real secrets and remove/rotate them from the codebase.
3. Commit `.secrets.baseline` along with `.pre-commit-config.yaml` once you are satisfied.

> **Policy:** New commits **must not introduce unapproved secrets**. If a hook fails, fix the underlying issue instead of bypassing the hook.

### 3. What the Hooks Do

Configured in `.pre-commit-config.yaml`:

- **pre-commit-hooks**
  - `trailing-whitespace` – strips trailing spaces.
  - `end-of-file-fixer` – ensures files end with a single newline.
  - `check-yaml` – validates YAML files.
  - `check-json` – validates JSON files.

- **detect-secrets**
  - Scans staged changes for patterns that look like secrets, using `.secrets.baseline` to track known, audited findings.

### 4. Secret Handling Guidelines

- Do **not** commit real API keys, tokens, passwords, or private keys.
- Use placeholders in tracked example files (e.g. `.env.example`):
  - `GEMINI_API_KEY=REPLACEME`
- Keep real values only in:
  - Local, untracked `.env` files (ensure `.env` is in `.gitignore`).
  - Your organization’s secret manager (Vault, Azure Key Vault, AWS Secrets Manager, etc.).

If you suspect a secret was ever committed:

1. Rotate/disable the secret immediately.
2. Remove it from Git history as per your organization’s incident process.

For more detailed rules and recommendations, see:

- `markdowns/GIT_CHECKIN_RULES.md`
