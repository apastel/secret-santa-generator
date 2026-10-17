# secret-santa-generator
Figure out who gets who for your Secret Santa group!

Just provide a list of names and exclusions (people they shouldn't be matched with) and the tool will generate a PDF to be given to each participant which contains the name of who they are the Secret Santa of.

![Secret Santa image](./resources/sample.png)

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

# Run the CLI to see the pairings in the console
secret-santa

# Or, specify an outdir to generate PDFs and hide console output
secret-santa --outdir .

# Or, generate PDFs *and* see the console output
secret-santa --outdir . --show

# Generate private-link HTML pages in docs/ for GitHub Pages
secret-santa --html-outdir docs --base-url https://YOUR-USERNAME.github.io/YOUR-REPOSITORY
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

You can also specify the path to your participants file:
```bash
secret-santa --participants /path/to/myfile.json
```

## Publish Personal Links

Generate one randomly named HTML page per participant and print the matching
links locally:

```bash
secret-santa \
		--participants resources/participants.json \
		--html-outdir docs \
		--base-url https://YOUR-USERNAME.github.io/YOUR-REPOSITORY
```

The repository includes a GitHub Actions workflow that publishes `docs/` to
GitHub Pages when changes are pushed to `main`. Enable Pages for the repository
and select **GitHub Actions** as the build and deployment source in its Pages
settings. Commit the generated HTML files and push; after the workflow succeeds,
text each person the URL printed next to their name.

Each page uses a random filename, and its assignment is encrypted with
AES-GCM. The decryption key is in the URL fragment, which is not sent to the
GitHub Pages server or included in the published files. There is no public
assignment index. These are still bearer links, not access-controlled pages:
anyone who receives a complete link can view that assignment. Avoid posting the
printed name-to-link list publicly, and regenerate pages if a link is shared
with the wrong person.

Thus, here's the hierarchical order in which participants are checked for and loaded:
* Path specified by `--participants`
* `./resources/participants.json`
* `./resources/participants.json.example`