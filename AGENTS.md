# AGENTS.md

Operational guide for coding agents working in `vvk-charts-mcp`.

## Project Snapshot

- Language: Python (`>=3.10`)
- Packaging: `pyproject.toml` with `hatchling`
- Environment manager: `uv`
- Main package path: `src/vvk_charts_mcp`
- Entry points:
  - `vvk-charts-mcp` -> `vvk_charts_mcp.server:main`
  - `vvk-charts-cli` -> `vvk_charts_mcp.client:main`
- Primary libraries: `mcp`, `plotly`, `plotext`, `pydantic`

## Setup Commands

- Install deps (including dev deps):
  - `uv sync`
- Recreate env from lockfile:
  - `uv sync --frozen`

## Run Commands

- Run MCP server locally:
  - `uv run vvk-charts-mcp`
- Run interactive CLI client:
  - `uv run vvk-charts-cli`

## Build / Lint / Typecheck / Test

- Build package artifacts:
  - `uv build`
- Lint entire repo (Ruff):
  - `uv run ruff check .`
- Auto-fix lint issues where safe:
  - `uv run ruff check . --fix`
- Static type checking:
  - `uv run mypy src`
- Run all tests:
  - `uv run pytest`

## Single-Test Commands (important)

There is currently no `tests/` directory in this repository. Use these commands once tests exist.

- Run one file:
  - `uv run pytest tests/test_example.py`
- Run one test function:
  - `uv run pytest tests/test_example.py::test_specific_case`
- Run one test class:
  - `uv run pytest tests/test_example.py::TestSuite`
- Run tests by keyword expression:
  - `uv run pytest -k "terminal and dashboard"`
- Run with quiet output for agents:
  - `uv run pytest -q`

## Repository Structure

- `src/vvk_charts_mcp/server.py`: MCP tool schema + tool dispatch.
- `src/vvk_charts_mcp/client.py`: interactive local smoke-test client.
- `src/vvk_charts_mcp/charts/`: chart classes (`line`, `bar`, `pie`, `scatter`, `area`).
- `src/vvk_charts_mcp/terminal/`: terminal chart/dashboard rendering + themes.
- `src/vvk_charts_mcp/utils/export.py`: PNG/SVG/base64 export helpers.
- `ai/`: reusable prompts/profiles for chart-focused agents.

## Code Style Rules

These rules are inferred from current source and tool config. Follow existing conventions.

### Imports

- Prefer absolute imports from `vvk_charts_mcp.*`.
- Group imports in this order:
  1) stdlib
  2) third-party
  3) local package imports
- Keep imports at module top unless deferred import is justified.
- Let Ruff (`I` rules) enforce import sorting.

### Formatting

- Line length target: `100` (from Ruff config).
- Use 4-space indentation.
- Keep function signatures and calls vertically aligned when multiline.
- Use double quotes consistently (matches current codebase).

### Typing

- Use modern Python typing syntax (`list[str]`, `dict[str, Any]`, `X | None`).
- Keep type annotations on public functions and significant internals.
- Prefer `Literal` for constrained string options.
- Use `Any` only at boundaries (tool payloads, dynamic external data).

### Naming Conventions

- Modules/files: `snake_case`.
- Classes: `PascalCase`.
- Functions/variables: `snake_case`.
- Constants: `UPPER_SNAKE_CASE`.
- Keep MCP tool names as explicit `create_<kind>_chart` style.

### Data Modeling and Validation

- Parse incoming dict payloads into models early (`DataSeries`, `PieDataSeries`, `ChartTheme`).
- Validate user-controlled options before rendering.
- Raise `ValueError` for invalid argument shapes or unsupported enum-like values.
- Ensure chart data arrays are non-empty where required.

### Error Handling

- At low level, raise clear exceptions (`ValueError`) with actionable messages.
- At MCP boundary (`server.call_tool`), return structured JSON error payloads.
- Avoid silent failures; include reason fields for fallbacks when possible.
- Keep terminal rendering resilient: try preferred engine, then fallback cleanly.

### Chart and Theme Practices

- Preserve theme-driven styling through `ChartTheme` / terminal theme resolvers.
- Do not hardcode one-off colors when a theme color can be used.
- Keep labels/titles explicit on user-facing charts.
- For terminal output intended for chat, prefer plain text output (`raw_output` true).

### API and MCP Tooling

- When adding a tool, update both:
  - `list_tools()` input schema
  - `call_tool()` dispatch logic
- Keep schema defaults aligned with implementation defaults.
- Image tools should return `types.ImageContent` for chat preview and `types.TextContent` for metadata.
- Keep response payloads JSON-serializable.

### Image Save Policy (strict)

- Do not accept or use `output_path`.
- Use only env `OUTPUT_DIR` as save location.
- `save_to_disk` defaults to `false`; in this mode never write files.
- If `save_to_disk=true` and `OUTPUT_DIR` is set, save only into `OUTPUT_DIR`.
- If `save_to_disk=true` and `OUTPUT_DIR` is missing, do not raise error; return preview only.
- For `format=base64` with `save_to_disk=true`, save PNG and return preview.
- When saving succeeds, return full absolute file path in response metadata.

### Testing Guidance

- Add unit tests under `tests/` using `pytest`.
- Prefer focused tests for:
  - payload validation
  - chart construction behavior
  - terminal fallback modes
  - export result shape
- For regression fixes, add a failing test first when practical.

## Agent-Specific Notes

- Make surgical changes; avoid broad refactors unless requested.
- Do not change public tool names without updating docs and schemas.
- Keep README examples in sync when behavior changes.
- If adding config/tooling, prefer `pyproject.toml` over scattered config files.

## Cursor/Copilot Rules Status

- `.cursor/rules/`: not present
- `.cursorrules`: not present
- `.github/copilot-instructions.md`: not present

No repository-specific Cursor or Copilot instruction files were found at this time.
