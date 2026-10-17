import json
from pathlib import Path
from click.testing import CliRunner
from secret_santa.__main__ import main as cli_main
from secret_santa import create_mapping


def test_cli_participants_and_outdir(tmp_path):
    # Create a temporary participants JSON file
    participants = [
        {"name": "Pat", "exclusions": []},
        {"name": "Lee", "exclusions": []},
        {"name": "Sam", "exclusions": []},
    ]
    participants_file = tmp_path / "parts.json"
    participants_file.write_text(json.dumps(participants), encoding="utf-8")

    outdir = tmp_path / "out"
    runner = CliRunner()
    result = runner.invoke(cli_main, ["--participants", str(participants_file), "--outdir", str(outdir)])
    assert result.exit_code == 0
    # ensure PDFs are created (click CLI used `outdir` so write_pairing_pdfs attempted)
    # If reportlab is not installed, this test will be skipped by importorskip in the PDF test
    # but we still want to ensure the CLI executed successfully.
    # When an outdir is provided and PDFs were generated, the mapping should NOT be printed to stdout
    assert "Secret Santa Pairings:" not in result.output

    # check PDFs were written
    mapping = create_mapping(participants)
    year = __import__("datetime").date.today().year
    for giver in mapping.keys():
        safe_name = str(giver).replace("/", "_").replace("\\", "_")
        filename = Path(outdir) / f"To be opened by {safe_name} (Secret Santa {year}).pdf"
        assert filename.exists()


def test_cli_outdir_with_show_shows_mapping(tmp_path):
    participants = [
        {"name": "Pat", "exclusions": []},
        {"name": "Lee", "exclusions": []},
        {"name": "Sam", "exclusions": []},
    ]
    participants_file = tmp_path / "parts.json"
    participants_file.write_text(json.dumps(participants), encoding="utf-8")

    outdir = tmp_path / "out"
    runner = CliRunner()
    result = runner.invoke(cli_main, ["--participants", str(participants_file), "--outdir", str(outdir), "--show"])
    assert result.exit_code == 0
    # With --show, the mapping should be printed to stdout even when PDFs are generated.
    assert "Secret Santa Pairings:" in result.output


def test_cli_html_output_prints_personal_links(tmp_path):
    participants = [
        {"name": "Pat", "exclusions": []},
        {"name": "Lee", "exclusions": []},
        {"name": "Sam", "exclusions": []},
    ]
    participants_file = tmp_path / "parts.json"
    participants_file.write_text(json.dumps(participants), encoding="utf-8")
    html_dir = tmp_path / "site"
    base_url = "https://example.github.io/santa"

    result = CliRunner().invoke(
        cli_main,
        [
            "--participants", str(participants_file),
            "--html-outdir", str(html_dir),
            "--base-url", base_url,
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Secret Santa links:" in result.output
    assert result.output.count(f"{base_url}/") == len(participants)
    assert "Secret Santa Pairings:" not in result.output
    assert len(list(html_dir.glob("*.html"))) == len(participants)


def test_cli_requires_html_base_url(tmp_path):
    result = CliRunner().invoke(cli_main, ["--html-outdir", str(tmp_path)])

    assert result.exit_code != 0
    assert "--html-outdir and --base-url must be used together" in result.output
