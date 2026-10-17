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
@click.option(
    "--html-outdir",
    "html_outdir",
    type=click.Path(file_okay=False, path_type=str),
    default=None,
    help="Directory for per-person HTML pages to publish with GitHub Pages",
)
@click.option(
    "--base-url",
    "base_url",
    type=str,
    default=None,
    help="Published site URL, e.g. https://username.github.io/repository",
)
@click.option(
    "--show/--no-show",
    "show",
    default=False,
    help="Show the mapping in the console even when `--outdir` is provided",
)
def main(
    participants_path: str | None = None,
    outdir: str | None = None,
    html_outdir: str | None = None,
    base_url: str | None = None,
    show: bool = False,
):
    """Secret Santa CLI.

    Example:
        python -m secret_santa --participants resources/participants.json --outdir pairings_pdfs
    """
    try:
        if bool(html_outdir) != bool(base_url):
            raise click.ClickException("--html-outdir and --base-url must be used together")
        run_main(
            participants_path,
            outdir=outdir,
            show=show,
            html_outdir=html_outdir,
            base_url=base_url,
        )
    except FileNotFoundError as exc:
        click.echo(str(exc), err=True)
        raise SystemExit(2)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc


if __name__ == "__main__":
    main()
