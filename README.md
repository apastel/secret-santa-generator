# secret-santa-generator
Figure out who gets who for your Secret Santa group!

Just provide a list of names and exclusions (people they shouldn't be matched with) and the tool will generate a PDF to be given to each participant which contains the name of who they are the Secret Santa of.

## Setup (pip/venv)

This project uses a standard Python packaging workflow and can be set up with a virtual environment and pip.

```bash
# Create a virtual environment and activate it
python -m venv .venv
source .venv/bin/activate

# Upgrade pip and install the package in editable mode with development extras
python -m pip install -U pip
python -m pip install '.[pdf]'
python -m pip install -e '.[dev,pdf]'

# Run tests
pytest

# Run the CLI to see the pairings in the console
secret-santa

# Specify an outdir to generate PDFs and hide console output
secret-santa --outdir .
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
