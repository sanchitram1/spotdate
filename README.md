# spotdate

This is a repo for the Analytics Lab Project; IEOR 243 at UC Berkeley. In
general, the idea is to create a music dating application, matching people based
on shared listening histories / music consumption pattern.

## Data

The [data-loading](data-loading/) directory contains all scripts related to open
datasets we gathered / scraped to train our model

## Setup

We use [uv](https://docs.astral.sh/uv/) from Astral for dependency management
and virtual environments.

### 1. Install uv

macOS / Linux:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Windows (PowerShell):

```
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. Create the venv

```bash
uv sync
```

### 3. Activate the venv

```bash
source .venv/bin/activate
```

## Committing and Merging

```bash
uv run ruff format /path/to/directory/or/file
uv run ruff check  /path/to/directory/or/file --fix
```
