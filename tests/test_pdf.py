import pytest
from datetime import date
from secret_santa import create_mapping, write_pairing_pdfs


def test_write_pairing_pdfs(tmp_path):
    # Skip test if reportlab is not installed
    pytest.importorskip("reportlab")

    participants = [
        {"name": "Pat", "exclusions": []},
        {"name": "Lee", "exclusions": []},
        {"name": "Sam", "exclusions": []},
    ]
    mapping = create_mapping(participants)
    outdir = tmp_path / "pairings"
    write_pairing_pdfs(mapping, outdir=str(outdir))

    # expect one PDF per giver
    for giver in mapping.keys():
        safe_name = str(giver).replace("/", "_").replace("\\", "_")
        year = date.today().year
        filename = outdir / f"To be opened by {safe_name} - {year}.pdf"
        assert filename.exists()
        # Ensure generated PDF contains the repository URL as a clickable link annotation
        with open(filename, "rb") as fh:
            pdf_bytes = fh.read()
        assert b"https://github.com/apastel/secret-santa-generator" in pdf_bytes
