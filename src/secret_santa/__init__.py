import json
import random
import secrets
import base64
from typing import Any, Dict, List
import os
from pathlib import Path
from datetime import date
from urllib.parse import urlsplit
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

try:
    import importlib.util

    _HAS_REPORTLAB = importlib.util.find_spec("reportlab") is not None
except Exception:
    _HAS_REPORTLAB = False
    # leave `canvas` and `letter` undefined; the writer function will import them


def _default_project_resource_path(name: str) -> str:
    """Return a path under the repo's `resources/` directory for `name`.

    This resolves two levels up from the installed package path, which
    works for running in the repository and also supports local edits.
    """
    pkg_dir = Path(__file__).resolve().parent
    repo_root = pkg_dir.parent.parent
    return str((repo_root / "resources" / name).resolve())


def load_participants(path: str | None = None) -> List[Any]:
    """Load participants data from JSON.

    If `path` is not provided, the function will check the following in order
    and use the first that exists:
    - `resources/participants.json` (project-local override, ignored by git)
    - `resources/participants.json.example` (committed example)
    - If none is found, raise FileNotFoundError
    """
    # explicit path takes precedence
    if path:
        candidate = Path(path)
        if candidate.exists():
            with candidate.open(encoding="utf-8") as fh:
                return json.load(fh)
        raise FileNotFoundError(f"Participants file not found: {path}")

    local = Path(_default_project_resource_path("participants.json"))
    if local.exists():
        with local.open(encoding="utf-8") as fh:
            return json.load(fh)

    example = Path(_default_project_resource_path("participants.json.example"))
    if example.exists():
        with example.open(encoding="utf-8") as fh:
            return json.load(fh)

    # If we got here, there is no participants file configured.
    raise FileNotFoundError(
        "No participants configuration found. Provide a file via `--participants`, "
        "or add `resources/participants.json`"
    )


def _normalize_participants(participants: List[Any]) -> tuple[list[str], dict[str, set[str]]]:
    """Normalize participants list into a list of names and exclusions map.

    Input format: a list of dicts {"name": str, "exclusions": [str, ...]}.
    Returns: (names, exclusions_map) where exclusions_map[name] is a set.
    """
    names: list[str] = []
    exclusions: dict[str, set[str]] = {}
    for item in participants:
        if isinstance(item, dict):
            name = item.get("name")
            if not isinstance(name, str):
                raise ValueError("Each participant must have a string 'name' field")
            if name in names:
                raise ValueError("Duplicate participant names not supported")
            names.append(name)
            ex = item.get("exclusions") or []
            if not isinstance(ex, (list, tuple)):
                raise ValueError("'exclusions' must be a list of names")
            exclusions[name] = set(str(e) for e in ex)
        elif isinstance(item, str):
            # Allow simple strings (singletons)
            if item in names:
                raise ValueError("Duplicate participant names not supported")
            names.append(item)
            exclusions[item] = set()
        else:
            raise ValueError("Invalid participant entry; expected dict or string")
    if not names:
        raise ValueError("At least one participant is required")
    # Filter exclusions to known names
    for k in exclusions:
        exclusions[k] = {e for e in exclusions[k] if e in names}
    return names, exclusions


def _try_random_permutation_exclusions(
    people: List[str],
    exclusions: Dict[str, set[str]],
    ban_self: bool = True,
    attempts: int = 2000,
) -> Dict[str, str] | None:
    """Try simple random permutations for a valid mapping. Returns dict or None.

    Checks both the original-partner `forbidden` map and the directed
    `prev_forbidden` map (previous year pairings).
    """
    targets = people[:]
    for _ in range(attempts):
        random.shuffle(targets)
        ok = True
        for src, tgt in zip(people, targets):
            if ban_self and src == tgt:
                ok = False
                break
            if src in exclusions and tgt in exclusions[src]:
                ok = False
                break
        if ok:
            return dict(zip(people, targets))
    return None


def _maximum_bipartite_matching(people: List[Any], allowed_targets: Dict[Any, List[Any]]) -> Dict[Any, Any]:
    """Kuhn's algorithm for bipartite matching (left=people, right=targets).

    allowed_targets maps each left node to list of allowed right nodes.
    Returns mapping left->right if perfect matching exists, otherwise empty dict.
    """
    match_r = {}  # right -> left

    def try_khun(u, visited):
        for v in allowed_targets[u]:
            if visited.get(v):
                continue
            visited[v] = True
            if v not in match_r or try_khun(match_r[v], visited):
                match_r[v] = u
                return True
        return False

    for u in people:
        visited = {}
        if not try_khun(u, visited):
            return {}

    # invert match_r to left->right
    result = {left: right for right, left in match_r.items()}
    return result


def create_mapping(
    participants: List[Any],
    ban_self: bool = True,
) -> Dict[str, str]:
    """Create a one-to-one mapping assigning each person another person.

Input is a list of participants in the new format:
    [{"name": "Alice", "exclusions": ["Bob"]}, ...]

Rules:
- Each person is assigned exactly one target (bijection).
- A person's `exclusions` list contains names they cannot be assigned to.
- Optionally disallow assigning someone to themselves (`ban_self`).

Raises `ValueError` if no valid mapping exists.
    """
    people, exclusions = _normalize_participants(participants)
    # quick randomized attempt
    rand_map = _try_random_permutation_exclusions(
        people, exclusions, ban_self=ban_self
    )
    if rand_map is not None:
        return rand_map

    # build allowed targets per person
    allowed = {}
    for p in people:
        allowed_targets = [
            t
            for t in people
            if (not ban_self or t != p)
            and not (p in exclusions and t in exclusions[p])
        ]
        allowed[p] = allowed_targets

    matching = _maximum_bipartite_matching(people, allowed)
    if not matching:
        raise ValueError("No valid mapping exists for given participants and constraints")
    return matching


def write_pairing_pdfs(
    mapping: Dict[Any, Any], outdir: str = "pairings_pdfs"
) -> dict[str, str]:
    """Write a simple one-page PDF for each giver in `mapping`.

    Each PDF is named `To be opened by {giver}.pdf` and contains a short
    message indicating their assigned recipient.

    This function requires `reportlab`. If ReportLab is not installed the
    function will raise ImportError.
    """
    if not _HAS_REPORTLAB:
        raise ImportError("reportlab is required to generate PDFs; install it in your environment")

    # Import here so static analyzers know we're only referencing them
    # when reportlab is installed.
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    os.makedirs(outdir, exist_ok=True)
    print("\nGenerating PDFs...")
    generated_files: dict[str, str] = {}
    for giver, receiver in mapping.items():
        # make filename safe
        safe_name = str(giver).replace("/", "_").replace("\\", "_")
        year = date.today().year
        filename = os.path.join(outdir, f"To be opened by {safe_name} (Secret Santa {year}).pdf")
        c = canvas.Canvas(filename, pagesize=letter)
        width, height = letter
        title = f"Hello {giver}!"
        c.setFont("Helvetica-Bold", 18)
        c.drawCentredString(width / 2, height - 100, title)

        # Prepare text variables; we draw image first so the text appears on top
        c.setFont("Helvetica", 14)
        text = f"You are {receiver}'s Secret Santa!"
        text_y = height - 140

        # optional image under the assignment text
        try:
            from reportlab.lib.utils import ImageReader
        except Exception:
            ImageReader = None

        # If no explicit image path was provided, look for a local 'santa.png'
        image_path = "./resources/secret-santa.png"
        if image_path and ImageReader is not None:
            try:
                img = ImageReader(image_path)
                img_w_px, img_h_px = img.getSize()
                # scale image to not exceed these limits
                max_w = width * 0.6
                max_h = height * 0.25
                aspect = img_w_px / img_h_px if img_h_px else 1
                img_w = min(max_w, img_w_px)
                img_h = img_w / aspect
                if img_h > max_h:
                    img_h = max_h
                    img_w = img_h * aspect

                # Center the image on the page using lower-left coordinates
                x_left = (width - img_w) / 2
                y_bottom = (height - img_h) / 2
                c.drawImage(
                    image_path,
                    x_left,
                    y_bottom,
                    width=img_w,
                    height=img_h,
                    preserveAspectRatio=True,
                    mask="auto",
                )
            except Exception:
                # If anything goes wrong (image unreadable, etc.) just skip drawing the image
                pass

        # Now draw the assignment text so it appears on top of the image if they overlap
        c.drawCentredString(width / 2, text_y, text)

        # Draw a clickable GitHub repo link centered at the bottom of the page.
        link_text = "apastel/secret-santa-generator"
        repo_url = "https://github.com/apastel/secret-santa-generator"
        from reportlab.lib import colors

        prefix_text = "This file was generated by "
        font_name = "Helvetica-Oblique"
        font_size = 10
        c.setFont(font_name, font_size)

        combined_text = prefix_text + link_text
        # Center the combined text and draw each piece separately so we can style only the repo portion.
        text_width_total = c.stringWidth(combined_text, font_name, font_size)
        x_start = (width - text_width_total) / 2
        y_text = 60
        # Draw prefix in default color
        c.setFillColor(colors.black)
        c.drawString(x_start, y_text, prefix_text)

        # Draw repo name in blue and underline it
        x_repo = x_start + c.stringWidth(prefix_text, font_name, font_size)
        repo_width = c.stringWidth(link_text, font_name, font_size)
        c.setFillColor(colors.blue)
        c.drawString(x_repo, y_text, link_text)
        underline_y = y_text - 2
        c.setLineWidth(0.8)
        c.setStrokeColor(colors.blue)
        c.line(x_repo, underline_y, x_repo + repo_width, underline_y)
        # Reset color to black for any subsequent text
        c.setFillColor(colors.black)

        # clickable area covers the repo text with a small vertical padding
        y_bottom = underline_y - 2
        y_top = y_text + font_size
        c.linkURL(repo_url, (x_repo, y_bottom, x_repo + repo_width, y_top), relative=0)

        c.showPage()
        c.save()
        generated_files[str(giver)] = filename
    print(f"PDF generation complete! Check {os.path.abspath(outdir)} for PDF files.")
    return generated_files


def write_pairing_html(
    mapping: Dict[Any, Any], outdir: str, base_url: str
) -> dict[str, str]:
    """Write one unlisted, randomly named HTML page per participant.

    Returns links keyed by participant name. No index page is written, so the
    assignment list stays local to the person running the generator.
    """
    parsed_url = urlsplit(base_url)
    if (
        parsed_url.scheme not in {"http", "https"}
        or not parsed_url.netloc
        or parsed_url.query
        or parsed_url.fragment
    ):
        raise ValueError("base_url must be an absolute HTTP or HTTPS URL")

    os.makedirs(outdir, exist_ok=True)
    base_url = base_url.rstrip("/")
    generated_links: dict[str, str] = {}

    def encode_urlsafe(value: bytes) -> str:
        return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")

    for giver, receiver in mapping.items():
        token = secrets.token_urlsafe(24)
        filename = f"{token}.html"
        page_path = Path(outdir) / filename
        key = AESGCM.generate_key(bit_length=256)
        nonce = secrets.token_bytes(12)
        ciphertext = AESGCM(key).encrypt(nonce, str(receiver).encode("utf-8"), None)
        nonce_encoded = encode_urlsafe(nonce)
        ciphertext_encoded = encode_urlsafe(ciphertext)
        key_encoded = encode_urlsafe(key)
        page_path.write_text(
            "<!doctype html>\n"
            '<html lang="en">\n'
            "<head>\n"
            '  <meta charset="utf-8">\n'
            '  <meta name="viewport" content="width=device-width, initial-scale=1">\n'
            '  <meta name="robots" content="noindex, nofollow">\n'
            "  <title>Secret Santa</title>\n"
            "  <style>"
            "body{font-family:system-ui,sans-serif;margin:0;min-height:100vh;"
            "display:grid;place-items:center;background:#f3f6f4;color:#20302a}"
            "main{max-width:34rem;padding:3rem 2rem;text-align:center}"
            "h1{font-size:2rem}p{font-size:1.25rem}"
            "</style>\n"
            "</head>\n"
            "<body><main>\n"
            "  <h1>Your Secret Santa assignment</h1>\n"
            '  <p id="assignment">Unlocking your assignment...</p>\n'
            "</main>\n"
            "<script>\n"
            f'const nonce = "{nonce_encoded}";\n'
            f'const ciphertext = "{ciphertext_encoded}";\n'
            "function decode(value) {\n"
            '  const base64 = value.replace(/-/g, "+").replace(/_/g, "/");\n'
            '  return Uint8Array.from(atob(base64 + "=".repeat((4 - base64.length % 4) % 4)), c => c.charCodeAt(0));\n'
            "}\n"
            "async function showAssignment() {\n"
            "  try {\n"
            '    const keyBytes = decode(window.location.hash.slice(1));\n'
            '    const key = await crypto.subtle.importKey("raw", keyBytes, "AES-GCM", false, ["decrypt"]);\n'
            "    const cleartext = await crypto.subtle.decrypt(\n"
            '      {name: "AES-GCM", iv: decode(nonce)}, key, decode(ciphertext));\n'
            '    const recipient = new TextDecoder().decode(cleartext);\n'
            '    document.getElementById("assignment").textContent = "You are " + recipient + "\'s Secret Santa.";\n'
            "  } catch {\n"
            '    document.getElementById("assignment").textContent = "This link is invalid or incomplete.";\n'
            "  }\n"
            "}\n"
            "showAssignment();\n"
            "</script></body>\n"
            "</html>\n",
            encoding="utf-8",
        )
        generated_links[str(giver)] = f"{base_url}/{filename}#{key_encoded}"
    return generated_links


def main(
    participants_path: str | None = None,
    outdir: str | None = None,
    show: bool = False,
    html_outdir: str | None = None,
    base_url: str | None = None,
):
    """Run the mapping generation and optionally write PDFs or HTML pages."""
    participants = load_participants(participants_path)
    mapping = create_mapping(participants)
    generated_links: dict[str, str] | None = None
    if html_outdir:
        if not base_url:
            raise ValueError("base_url is required when html_outdir is provided")
        generated_links = write_pairing_html(mapping, html_outdir, base_url)

    pdfs_generated = False
    if outdir:
        try:
            generated_files = write_pairing_pdfs(mapping, outdir=outdir)
            pdfs_generated = bool(generated_files)
        except ImportError:
            print("ReportLab not installed, skipping PDF generation")

    if generated_links is not None:
        print("\nSecret Santa links:\n")
        for giver, link in generated_links.items():
            print(f"{giver}: {link}")
    elif not pdfs_generated or show:
        print("\nSecret Santa Pairings:\n")
        for k, v in mapping.items():
            print(f"{k} is {v}'s secret Santa")
    if show and generated_links:
        print("\nSecret Santa Pairings:\n")
        for k, v in mapping.items():
            print(f"{k} is {v}'s secret Santa")
    print()
    return mapping


__all__ = [
    "create_mapping",
    "write_pairing_pdfs",
    "write_pairing_html",
    "load_participants",
    "main",
]
