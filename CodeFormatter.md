# Code Formatting Guide — Agentic TA

This document explains the code formatting tools used in the Agentic TA project, how to install them, and how they work in your daily workflow.

---

## Why We Use Formatting Tools

When multiple developers work on the same codebase, inconsistent code style creates unnecessary noise in pull requests and makes code harder to read. Automated formatters and linters solve this by enforcing a single, consistent style across all Python files — automatically.

Our toolchain has **three** components:

| Tool | What It Does | Why We Need It |
|------|-------------|----------------|
| **Black** | Formats Python code (indentation, line breaks, quotes, etc.) | Eliminates all style debates — same input always produces same output |
| **Ruff** | Lints Python code and sorts imports | Catches bugs, enforces best practices, and organizes import statements |
| **pre-commit** | Runs Black and Ruff automatically on every `git commit` | Prevents unformatted code from entering the repository |

> **Why not isort?** Ruff includes built-in isort functionality (the `I` rule set). A separate isort installation would conflict with Ruff.

---

## One-Time Setup (Every Team Member)

Follow these steps **once** after cloning the repository. This sets up your virtual environment, installs all dependencies, and configures the formatting tools.

### Prerequisites

- Python 3.11 or later installed
- Git installed
- VS Code installed (recommended)

### Step 1: Clone the Repository

```bash
git clone https://github.com/<org>/agentic_ta.git
cd agentic_ta
```

### Step 2: Create a Virtual Environment

A virtual environment isolates this project's packages from your system Python. Each team member creates their own local environment — it is **not** pushed to GitHub (it is listed in `.gitignore`).

```bash
python -m venv .venv
```

### Step 3: Activate the Virtual Environment

You must activate the virtual environment **every time** you open a new terminal.

**Windows (PowerShell):**
```powershell
.venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
.venv\Scripts\activate.bat
```

**macOS / Linux:**
```bash
source .venv/bin/activate
```

When activated, you will see `(.venv)` at the beginning of your terminal prompt.

### Step 4: Install All Dependencies

This single command installs both the project dependencies (FastAPI, etc.) and the development tools (Black, Ruff, pre-commit, pytest):

```bash
pip install -e ".[dev]"
```

> **What does `-e ".[dev]"` mean?**
> - `-e .` installs the project in "editable" mode from `pyproject.toml`
> - `[dev]` also installs the optional development dependencies (formatters, linters, test tools)

### Step 5: Install the Git Hooks

This installs the pre-commit hooks into your local `.git/hooks/` directory:

```bash
pre-commit install
```

You only need to run this **once per machine**. After this, Black and Ruff will run automatically every time you run `git commit`.

### Step 6: Install VS Code Extensions

Open VS Code and install these two extensions:

1. **Black Formatter** by Microsoft (`ms-python.black-formatter`)
2. **Ruff** by Astral Software (`charliermarsh.ruff`)

You can install them from the Extensions panel (`Ctrl+Shift+X`) or by running:

```bash
code --install-extension ms-python.black-formatter
code --install-extension charliermarsh.ruff
```

The project already includes a `.vscode/settings.json` file that configures these extensions to format on save, so **no additional VS Code configuration is needed** on your part.

### Step 7: Verify Your Setup

```bash
# Check that the project dependencies are installed
python -c "import fastapi; print('fastapi', fastapi.__version__)"

# Check that pre-commit is working
pre-commit run --all-files
```

If no Python files exist yet, pre-commit will report "Passed" or "no files to check." That is expected.

### Quick Reference (Copy-Paste)

For convenience, here are all setup commands in one block:

```bash
git clone https://github.com/<org>/agentic_ta.git
cd agentic_ta
python -m venv .venv
# Activate: (Windows PS) .venv\Scripts\Activate.ps1
#           (macOS/Linux) source .venv/bin/activate
pip install -e ".[dev]"
pre-commit install
```

---

## Managing Dependencies

All project dependencies are defined in `pyproject.toml`. This file is pushed to GitHub so that every team member installs the same packages.

### When You Need to Add a New Package

For example, if you need to add `openai`:

```bash
# 1. Add it to pyproject.toml under [project] dependencies:
#    "openai>=1.0.0",

# 2. Install the updated dependencies locally
pip install -e ".[dev]"

# 3. Commit and push pyproject.toml
git add pyproject.toml
git commit -m "Add openai dependency"
git push
```

### When Someone Else Added a New Package

After pulling changes that include an updated `pyproject.toml`:

```bash
# 1. Pull the latest changes
git pull

# 2. Re-install dependencies (only new packages get installed)
pip install -e ".[dev]"
```

> **Tip:** Make it a habit to run `pip install -e ".[dev]"` after every `git pull`. This ensures your local environment always matches what the team expects.

### Where to Add Dependencies

| Type | Where in `pyproject.toml` | Examples |
|------|--------------------------|----------|
| **Runtime dependencies** | `[project] dependencies` | fastapi, uvicorn, httpx |
| **Dev-only tools** | `[project.optional-dependencies] dev` | black, ruff, pytest |

Dev-only tools are **not** installed in production — they are only installed when you use `pip install -e ".[dev]"`.

---

## Configuration Files

All tool configuration lives in files at the project root. You do **not** need to modify these unless the team agrees on a change.

| File | Purpose |
|------|---------|
| `pyproject.toml` | Project metadata, dependencies, and Black/Ruff settings |
| `.pre-commit-config.yaml` | Defines which tools run on `git commit` (with pinned versions) |
| `.vscode/settings.json` | Enables format-on-save and import sorting in VS Code |

---

## Daily Workflow

### When Writing Code in VS Code

If you installed the extensions and the `.vscode/settings.json` is present:

1. **Write your Python code normally.**
2. **Save the file (`Ctrl+S`).** Black automatically formats it and Ruff sorts imports.
3. That is it. Your code is formatted.

### When Committing Code

1. **Stage your files:** `git add your_file.py`
2. **Commit:** `git commit -m "your message"`
3. **pre-commit runs automatically.** It runs Black and Ruff on all staged Python files.
   - If the tools make changes, the commit is **rejected** and the changes are applied to your working directory.
   - **Re-stage and commit again:**
     ```bash
     git add your_file.py
     git commit -m "your message"
     ```
   - The second commit will pass because the files are now properly formatted.

### Running Tools Manually

You can run the tools manually at any time:

```bash
# Format all Python files with Black
black .

# Lint all Python files with Ruff
ruff check .

# Lint and auto-fix all Python files with Ruff
ruff check . --fix

# Run both tools via pre-commit (same as what happens on commit)
pre-commit run --all-files
```

---

## What Each Tool Does (Details)

### Black — Code Formatter

Black reformats your Python code to follow a consistent style. Examples of what it does:

- Converts single quotes to double quotes
- Adds/removes trailing commas
- Breaks long lines at 88 characters
- Normalizes whitespace and indentation

Black is "opinionated" — it makes most decisions for you. This is intentional. The goal is **zero debate about style**.

### Ruff — Linter and Import Sorter

Ruff checks your code for errors and style issues. Our configuration enables:

- **E rules:** PEP 8 style violations (whitespace issues, etc.)
- **F rules:** Logical errors (undefined names, unused variables, unused imports)
- **I rules:** Import sorting (groups imports into: stdlib → third-party → first-party)
- **W rules:** PEP 8 warnings

When run with `--fix`, Ruff auto-corrects fixable issues (like removing unused imports or sorting import statements).

### pre-commit — Git Hook Manager

pre-commit installs a script into `.git/hooks/pre-commit` that runs before every commit. It executes Black first, then Ruff, on the files you are committing. If either tool fails (or makes changes), the commit is blocked until the issues are resolved.

---

## Troubleshooting

### "command not found: black" (or ruff, or pre-commit)

Make sure your virtual environment is activated:

```bash
# Windows PowerShell
.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate
```

Then verify the tools are installed:

```bash
pip install -e ".[dev]"
```

### pre-commit is not running on commit

You need to install the hooks:

```bash
pre-commit install
```

### Commit was rejected, but I do not see any errors

This usually means Black or Ruff **reformatted your files**. The tools made changes, which means the staged files are now out of date. Re-add and commit:

```bash
git add -u
git commit -m "your message"
```

### VS Code is not formatting on save

1. Verify the extensions are installed: `ms-python.black-formatter` and `charliermarsh.ruff`
2. Verify `.vscode/settings.json` contains the `[python]` section
3. Make sure no user-level settings are overriding the workspace settings
4. Try reloading VS Code (`Ctrl+Shift+P` → "Developer: Reload Window")

### Black and Ruff disagree on formatting

This should not happen with our configuration because both tools use the same `line-length = 88`. If it does happen, run Black first, then Ruff:

```bash
black .
ruff check . --fix
```

This is the same order pre-commit uses.

### I want to skip pre-commit for one commit

Use the `--no-verify` flag. **Use this sparingly** — it defeats the purpose of the hooks:

```bash
git commit --no-verify -m "emergency fix"
```

---

## Updating Tool Versions

Periodically, the team should update the tool versions pinned in `.pre-commit-config.yaml`. Run:

```bash
pre-commit autoupdate
```

This updates the `rev` values to the latest releases. Commit the updated `.pre-commit-config.yaml` and notify the team.
