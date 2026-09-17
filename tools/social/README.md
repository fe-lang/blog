# Fe social cards

A local, data-driven generator for release threads. The visual language follows
the earlier Fe social cards: violet gradient, white typography, and the Fe logo.
It uses the logo already in `static/` and the Space Grotesk and JetBrains Mono
fonts already in the Apollo theme. No API keys, remote assets, browser, image
service, or network access are needed to render.

## Setup and render

Python 3.10+ and Pillow are required. From the blog repository root:

```sh
git submodule update --init --recursive
python3 -m venv target/social-venv
target/social-venv/bin/python -m pip install -r tools/social/requirements.txt
make social PYTHON=target/social-venv/bin/python
```

If Pillow is already installed, `make social` is sufficient. On the machine
where this was created, use `make social PYTHON=/usr/bin/python3` (the other
`python3` on PATH does not have Pillow).

Output goes to `target/social/release-26-3/`:

- `01-release.png` through `14-read-more.png`: upload-ready 1600 × 1000 RGB PNGs.
- `index.html`: local gallery with tweet copy, image downloads, and alt text.
- `contact-sheet.jpg`: all cards at a glance, for reviewing the visual system.
- `thread.md`: copyable text matched to each PNG, with character counts and alt text.
- `*.alt.txt`: individual image descriptions for the social platform's alt-text field.

Open `index.html` directly in a browser. No server is required. For a local HTTP
preview, run `python3 -m http.server --directory target/social 8000` and open
`http://localhost:8000/release-26-3/`.

The original conversational draft, with German visual ideas, is saved separately
at `social/release-26-3/thread-draft.md`. The campaign JSON is the source of truth
for subsequent edits and renders; `target/social/.../thread.md` is generated from it.

## Edit or create a campaign

Copy `social/release-26-3/campaign.json` into another campaign directory, then edit
its content:

```sh
mkdir -p social/release-26-4
cp social/release-26-3/campaign.json social/release-26-4/campaign.json
make social CAMPAIGN=social/release-26-4/campaign.json
```

Change `series`, `footer`, release links, and the card copy together. Remove or add
cards as needed; numbered output filenames follow the array order. The images
themselves have no page numbers or bottom-right labels.
Each card has a unique filesystem-safe `id`, a `layout`, `title`, `tweet`, and `alt`.
`subtitle` and `note` are optional. `note` is a short footer caveat.

Available layouts and their additional fields:

| Layout | Fields | Use |
| --- | --- | --- |
| `cover` | `headline` (two short lines), `description`, `chips` | Announcement and closing cards |
| `code` | `code`, optional `code_label`, optional `aside` (up to three `{label, text}` objects) | Code excerpts; syntax coloring without programming ligatures |
| `tiles` | Four `items`, each `{label, text}` | Four related improvements |
| `flow` | Two to four `steps`, each `{label, text}`, and `caption` | A sequential workflow |
| `lanes` | Two `rows`, each `{label, left, right}`, and `caption` | Independent mappings, such as storage maps to salts |
| `outcomes` | Up to four `rows`, each `{input, result, ok}` | Outcomes; `ok` chooses mint or pink emphasis |
| `regions` | No extra fields | Fe-specific memory length/capacity schematic |
| `packed` | No extra fields | Fe-specific packed encoding example: u16, Address, bool |

The last two layouts are fixed explanatory schematics, not arbitrary chart
builders. Their labels and geometry live in `render.py`; byte-block widths in
`packed` are schematic, not proportional. Other layouts take their content from
JSON. Use `\n` to choose line breaks; code is never wrapped automatically.

Example of a new code card:

```json
{
  "id": "pointers",
  "layout": "code",
  "title": "Memory gets a type.",
  "subtitle": "First-class pointers: *T",
  "code": "let p = core::ptr::alloc<u256>()\n*p = 42",
  "aside": [{"label": "Typed memory", "text": "Read and write through *T."}],
  "note": "A function-body excerpt.",
  "tweet": "Fe now has first-class typed memory pointers.",
  "alt": "Fe code allocates a u256 pointer and writes 42 through it."
}
```

## Checks and repeatability

The renderer rejects duplicate or unsafe IDs, missing common fields, unknown
layouts, overlong tweets, and overflowing wrapped text or code. Tweet copy is
restricted to ASCII so character counting is unambiguous; URLs count as 23
characters. Image text and alt text can contain Unicode. This is intentionally
not a complete implementation of the platform's Unicode weighting rules.

Keep code excerpts short (typically six lines) and important caveats in the
headline/subtitle or accompanying tweet. Check the full-size images as well as
the contact sheet before posting; automatic checks do not replace visual review
or verifying the Fe examples against the release compiler.

Pixels are deterministic with the same Python, Pillow, and checked-out theme
revision. Rendering uses fixed fonts and a procedural gradient, with no random
seed, current date, or host-installed font fallback. The first version was
validated with Python 3.12 and Pillow 10.2.0. Use the same Pillow version when
comparing exact output hashes; the supported range is intentionally broader.

To render outside `target/`:

```sh
python3 tools/social/render.py social/release-26-3/campaign.json --out /tmp/fe-social
```

The renderer overwrites matching output filenames on reruns but does not delete
unrelated files or old filenames after card IDs change. Use a fresh output
directory after renaming/reordering cards if you need a clean upload directory.

## What belongs in Git

Commit `tools/social/`, `social/<campaign>/`, and the Makefile/README changes.
Generated PNGs, gallery files, and the Python environment live under the already
ignored `target/` directory. A normal Zola build can replace `target/`; rerun
`make social` afterward. Use `--out` when you want exports to survive a site build.

Nothing here publishes, uploads, or deploys. Tweet copy is plain text rather than
Markdown; formatting backticks and the original draft's emoji have been removed
from the generated posting copy.
