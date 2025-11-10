# Reporting module refresh

This iteration cleans up the HTML reporting stack so it is easier to maintain and debug.

- `src/reporting/render.py` was rewritten with a smaller surface, ASCII-only literals and lazily loaded optional dependencies. The new helpers normalise breakdown rows, compute KPI summaries and keep fallbacks for environments without Jinja or Playwright.
- HTML templates under `src/reporting/templates/` were normalised to ASCII to avoid mojibake and to make diffs readable across editors.
- Added `tests/unit/test_render.py` to exercise the enrichment pipeline, context builder and the public `render_report` entry point.

The context passed to Jinja now includes `canasta_base`, `summary.warnings` and relative links to exports. The legacy HTML fallback produces a concise report so downstream tooling keeps working even without Jinja.
