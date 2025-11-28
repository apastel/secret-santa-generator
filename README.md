# secret-santa-generator
Find out who gets who for your Secret Santa group!

## Setup (PDM)

This project uses PDM for dependency management. To set it up locally:

```bash
# Install PDM if you don't have it
python -m pip install -U pdm

# Install project dependencies
pdm install

# Run tests
pdm run pytest

# Run the CLI
pdm run secret-santa
```

Optional feature: export PDF pairings with `reportlab`:
pdm add --dev reportlab
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
pdm add --dev reportlab
```

