import base64
import html
import re
from pathlib import Path
from urllib.parse import urlsplit

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from secret_santa import write_pairing_html


def test_write_pairing_html_creates_unlisted_pages_and_links(tmp_path):
    mapping = {"Pat <script>": "Lee & Sam", "Lee": "Pat <script>"}
    base_url = "https://example.github.io/santa/"

    links = write_pairing_html(mapping, str(tmp_path), base_url)

    assert set(links) == set(mapping)
    assert len(list(tmp_path.glob("*.html"))) == len(mapping)
    assert not (tmp_path / "index.html").exists()

    def decode(value):
        return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))

    for giver, link in links.items():
        parsed_link = urlsplit(link)
        filename = parsed_link.path.rsplit("/", 1)[-1]
        assert filename.endswith(".html")
        assert giver not in filename
        page = (tmp_path / filename).read_text(encoding="utf-8")
        assert "noindex, nofollow" in page
        assert mapping[giver] not in page
        assert f"Hello {html.escape(giver)}!" in page
        assert "You will be getting a present for " in page
        assert '<span class="reveal-target"><span id="recipient">hidden</span>' in page
        assert 'id="reveal-button" type="button">Tap to reveal</button>' in page
        assert 'src="secret-santa.png" alt="Secret Santa illustration"' in page
        assert 'document.getElementById("recipient").textContent = recipient;' in page
        nonce_match = re.search(r'const nonce = "([^"]+)";', page)
        ciphertext_match = re.search(r'const ciphertext = "([^"]+)";', page)
        assert nonce_match is not None
        assert ciphertext_match is not None
        decrypted = AESGCM(decode(parsed_link.fragment)).decrypt(
            decode(nonce_match.group(1)), decode(ciphertext_match.group(1)), None
        )
        assert decrypted.decode("utf-8") == mapping[giver]

    image = Path(__file__).parents[1] / "resources" / "secret-santa.png"
    assert (tmp_path / "secret-santa.png").read_bytes() == image.read_bytes()


def test_write_pairing_html_requires_absolute_url(tmp_path):
    import pytest

    with pytest.raises(ValueError, match="absolute HTTP or HTTPS URL"):
        write_pairing_html({"Pat": "Lee"}, str(tmp_path), "relative/path")
