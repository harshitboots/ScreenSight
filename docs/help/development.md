# Development

## Set up

```bash
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
.\.venv\Scripts\Activate.ps1     # Windows

pip install -e .
pip install pytest
```

## Run the tests

```bash
pytest tests/ -v
```

| Test file | Covers |
|---|---|
| `test_state.py` | On/off round trip |
| `test_privacy.py` | Blocklist matching, zone scaling |
| `test_diff.py` | Hash stability, change detection |
| `test_core.py` | `capture_once()` with a mocked backend |

## Run the MCP server

```bash
screensight-mcp                          # stdio, as an agent would spawn it
fastmcp dev screensight.mcp_server:mcp   # dev inspector
```

## House rules

- **Every surface calls `core.capture_once()`.** Never call a `capture/*.py` backend
  directly — that's how safety properties silently diverge between surfaces.
- **Native OS tools only** for screenshots, via `subprocess`. No Python screenshot
  libraries; the "no extra app, no extra deps" property is deliberate.
- **`active_window_title()` returning `None` means unverified**, not safe. Callers must
  fail closed.
- **New safety properties go inside `capture_once()`**, in the existing order, so every
  surface inherits them.

See [Architecture](../architecture.md) for the full contract.

---

## Working on the docs

The site is [MkDocs Material](https://squidfunk.github.io/mkdocs-material/). Sources live
in `docs/`, config in `mkdocs.yml`.

```bash
pip install -r requirements-docs.txt

mkdocs serve          # live-reloading preview at http://127.0.0.1:8000
mkdocs build --strict # what CI runs; fails on broken links
```

### Adding a page

1. Create the Markdown file under `docs/`.
2. Add it to the `nav:` tree in `mkdocs.yml` — pages missing from `nav` build but are
   unreachable, and `--strict` will warn.
3. Run `mkdocs build --strict` before pushing.

### Styling

Theme overrides live in `docs/stylesheets/extra.css` — a teal/mint palette, a landing
hero and the card grids. Prefer extending the existing CSS custom properties
(`--ss-*`) over hardcoding colors, so light and dark stay in sync.

### Deployment

`.github/workflows/docs.yml` builds the site on every push to `main` that touches
`docs/`, `mkdocs.yml` or the workflow itself, then publishes to GitHub Pages via
`actions/deploy-pages`. Pull requests get a build-only check — no deploy.

Enable it once per repository: **Settings → Pages → Build and deployment →
Source: GitHub Actions**.
