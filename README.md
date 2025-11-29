# secret-santa-generator
Find out who gets who for your Secret Santa group!

## Setup (pip/venv)

This project uses a standard Python packaging workflow and can be set up with a virtual environment and pip.

```bash
# Create a virtual environment and activate it
python -m venv .venv
source .venv/bin/activate

# Upgrade pip and install the package in editable mode with development extras
python -m pip install -U pip
python -m pip install -e '.[dev,pdf]'

# Run tests
pytest

# Run the CLI
secret-santa
```

Optional feature: export PDF pairings with `reportlab` (install the pdf extras above, or install directly):
```bash
python -m pip install reportlab
```
```

## Customize participants

By default the project uses the example participants file committed at
`resources/participants.json.example` using a new format:

```json
[
	{"name": "Alice", "exclusions": ["Bob"]},
	{"name": "Bob", "exclusions": ["Alice"]},
	{"name": "Charlie", "exclusions": []}
]
```

To customize participants for your local setup, copy the example and edit the copy
(*this file is ignored by git*):

```bash
cp resources/participants.json.example resources/participants.json
# Edit resources/participants.json as needed
```

`resources/participants.json` is ignored by git so you can keep your local
customizations private; the CLI and `load_participants()` function will pick up
your local file automatically. Each participant entry is a JSON object with a
`name` string and `exclusions` array. Any exclusions referencing names not in
the participant list are ignored.

Note: Running the CLI without any participants configured will raise a
FileNotFoundError. Provide a participants file explicitly or set the
`SECRET_SANTA_PARTICIPANTS` env var to a path for the CLI to work.


```bash
python -m pip install reportlab
```

