import pytest
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
        filename = outdir / f"To be opened by {safe_name} - 2025.pdf"
        assert filename.exists()
