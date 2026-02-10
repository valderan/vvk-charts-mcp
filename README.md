# vvk-charts-mcp

Modern Python MCP server for rendering charts and diagrams (line, bar, pie, scatter, area) with text labels, custom themes, and export to PNG/SVG/base64.

## Features

- MCP tools for `line`, `bar`, `pie`, `scatter`, and `area` charts
- Modern Plotly-based visual styling with full theme customization
- Handles large datasets and multi-series inputs
- Export formats: `png`, `svg`, `base64` (PNG + SVG)
- Interactive CLI test client with ready-to-run templates

## Install from GitHub (uvx)

```bash
uvx install git+https://github.com/valderan/vvk-charts-mcp.git
```

## Run MCP server

```bash
uvx run vvk-charts-mcp
```

## Run interactive test client

```bash
uvx run vvk-charts-cli
```

The CLI asks:

- what chart template to draw
- where to save files
- which output formats to generate
- output size and file name

## AI presets (skill and agent)

Repository includes two reusable AI presets in `ai/`:

- `ai/vvk-charts-skill.md` - skill instructions focused on MCP chart payloads
- `ai/vvk-charts-agent.md` - chart-specialized agent profile

Use either one depending on your workflow preference.

## OpenCode setup (detailed)

### 1) Add this MCP server to OpenCode

Create or edit `opencode.json` (global or project-level) and add:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "vvkcharts": {
      "type": "local",
      "enabled": true,
      "command": [
        "uvx",
        "--from",
        "git+https://github.com/valderan/vvk-charts-mcp.git",
        "vvk-charts-mcp"
      ]
    }
  }
}
```

### 2) Install as an OpenCode skill

OpenCode expects skills at `.opencode/skills/<name>/SKILL.md` and `name` must match directory.

```bash
mkdir -p .opencode/skills/vvk-charts-mcp
cp ai/vvk-charts-skill.md .opencode/skills/vvk-charts-mcp/SKILL.md
```

How to use:
- Ask OpenCode for chart tasks and mention `vvkcharts` tools when needed.
- The model can load the skill through the built-in `skill` tool.

### 3) Install as an OpenCode agent

```bash
mkdir -p .opencode/agents
cp ai/vvk-charts-agent.md .opencode/agents/vvk-charts.md
```

How to use:
- In chat, call it with `@vvk-charts ...`.
- Or switch/cycle agents in OpenCode UI and select `vvk-charts`.

### 4) Verify in OpenCode

- Run `opencode` in this project.
- Confirm `vvkcharts_*` tools are visible.
- Ask: `Build a monthly revenue line chart and save as png in ./output using vvkcharts`.

## Codex setup (detailed)

Codex environments differ by host app. Use this process in Codex-compatible clients that support MCP tool registration.

### 1) Register MCP server

Add an MCP server entry using this command:

```bash
uvx --from git+https://github.com/valderan/vvk-charts-mcp.git vvk-charts-mcp
```

If your client uses JSON config (common pattern), the MCP section typically looks like:

```json
{
  "mcpServers": {
    "vvkcharts": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/valderan/vvk-charts-mcp.git",
        "vvk-charts-mcp"
      ]
    }
  }
}
```

### 2) Use the skill file in Codex-style instructions

Codex does not use OpenCode `SKILL.md` discovery. Use `ai/vvk-charts-skill.md` as a prompt template:
- copy its content into your project-level AI instructions file, or
- paste it into your workspace/system instructions panel.

### 3) Use the agent file in Codex-style profile

Use `ai/vvk-charts-agent.md` as your chart-focused agent prompt:
- create a dedicated profile/preset in your Codex client,
- paste the file content as its system instructions,
- select that profile when generating charts.

### 4) Verify in Codex

- Ask for a chart task that explicitly uses MCP, for example:
  - `Use vvkcharts tools to generate a bar chart and save it to ./output/sales-q1.png`.
- Confirm the output file exists and matches requested format.

## MCP tools

- `create_line_chart`
- `create_bar_chart`
- `create_pie_chart`
- `create_scatter_chart`
- `create_area_chart`

All tools support:

- custom `theme`
- chart `title`
- `width` / `height`
- output `format`
- optional save location (`output_path`)

## Local development

```bash
uv sync
uv run ruff check .
```

## Repository

- https://github.com/valderan/vvk-charts-mcp
