import click
from . import main as run_main


@click.command()
@click.option(
    "--participants",
    "participants_path",
    type=click.Path(exists=True, dir_okay=False, path_type=str),
    required=False,
    help="Path to participants JSON file",
)
@click.option(
    "--outdir",
    "outdir",
    type=click.Path(file_okay=False, path_type=str),
    default=None,
    required=False,
    help="Directory to write pairing PDFs (if omitted, PDFs are not written)",
)
def main(participants_path: str | None = None, outdir: str | None = None):
    """Secret Santa CLI.

    Example:
        python -m secret_santa --participants resources/participants.json --outdir pairings_pdfs
    """
    try:
        run_main(participants_path, outdir=outdir)
    except FileNotFoundError as exc:
        click.echo(str(exc), err=True)
        raise SystemExit(2)


if __name__ == "__main__":
    main()
