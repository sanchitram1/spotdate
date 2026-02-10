# spotdate

## Setup

We use [uv](https://docs.astral.sh/uv/) from Astral for dependency management and 
virtual environments.

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

## Getting the data

On the terminal, run this

```bash
# Install the Google Cloud SDK (if they haven't)
brew install --cask google-cloud-sdk  # macOS

# Log in to Google Cloud locally 
# Here, you will sign into a Google Cloud account with your Berkeley email
gcloud auth application-default login

# Install the python lib
uv sync
```

Then run the file

```bash
uv run scripts/sync_data.py
```