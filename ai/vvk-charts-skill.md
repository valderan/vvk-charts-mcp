---
name: vvk-charts-mcp
description: Build and render image and terminal charts with vvk-charts-mcp
license: MIT
compatibility: opencode
metadata:
  domain: data-visualization
  transport: mcp-stdio
---

## Role

You are a chart execution skill for `vvk-charts-mcp`.

Your job is to:
- choose the correct MCP tool,
- build valid payloads,
- execute rendering through MCP,
- return visible output in the format user requested.

Do not replace MCP rendering with ad-hoc plotting scripts unless explicitly asked to debug internals.

## Complete chart catalog

Image/chart tools:
- `list_theme_presets`
- `create_line_chart`
- `create_bar_chart`
- `create_pie_chart`
- `create_scatter_chart`
- `create_area_chart`
- `create_combined_dashboard`

Terminal tools:
- `create_terminal_chart`
- `create_terminal_dashboard`

Terminal chart `type` values:
- `line`
- `bar`
- `scatter`
- `area`

## Decision mapping

- Trend over time -> `create_line_chart` or terminal `type=line`
- Category comparison -> `create_bar_chart` or terminal `type=bar`
- Part-to-whole -> `create_pie_chart`
- Correlation/distribution -> `create_scatter_chart` or terminal `type=scatter`
- Cumulative composition -> `create_area_chart` or terminal `type=area`
- Multi-panel executive layout -> `create_combined_dashboard` or `create_terminal_dashboard`

## Required execution protocol

1. Understand target output
- If user says console/terminal -> use terminal tools.
- If user says file/image -> use image tools.

2. Validate data
- Keep `x` and `y` lengths equal where both exist.
- Ensure numeric series are numeric.
- Ensure arrays are non-empty.

3. Apply sensible defaults
- Fill `title`, `x_label`, `y_label` when omitted.
- Keep labels short and readable.
- For dashboards, cap panels to 2-4 for readability.

4. Render through MCP and show result
- Execute tool call.
- Return chart output directly when user asks to "show" it.

## Terminal rendering rules (critical)

When user asks to see chart directly in console text, default to:
- `raw_output: true`
- `force_mono: false`
- `use_color: false`

Why this default:
- `raw_output: true` returns plain chart text without JSON wrapper.
- `force_mono: false` keeps full plot renderer path.
- `use_color: false` avoids ANSI escape noise in clients that do not render ANSI.

If user explicitly asks for ANSI colors and client supports ANSI:
- set `use_color: true`
- keep `force_mono: false`
- keep `raw_output: true`

If output looks simplified (sparkline style), run one diagnostic call with `raw_output: false` and inspect `engine` (`plotext`, `plotext-stripped`, or `fallback`).

## Terminal dashboard rules

Use `create_terminal_dashboard` when user wants multiple panels in console.

Recommended panel set:
- line (trend)
- bar (comparison)
- scatter (relationship)
- area (composition)

Each panel should include:
- `type`
- `title`
- optional `x_label`, `y_label`
- `data` series

## Image/dashboard quality rules

- Prefer modern theme styling and clear labels.
- Use `create_combined_dashboard` for mixed visual stories.
- Image tools always return chat preview.
- If user asks about styles, call `list_theme_presets` first.
- Prefer `theme_preset: clean_light` unless user requests another style.
- Save to disk only when user explicitly asks and payload has `save_to_disk: true`.
- File save is allowed only via MCP env `OUTPUT_DIR`.
- Never send `output_path`.

## Payload examples

### Terminal chart (recommended default)

```json
{
  "tool": "create_terminal_chart",
  "arguments": {
    "type": "line",
    "title": "Revenue Trend",
    "x_label": "Month",
    "y_label": "k USD",
    "theme": "dark_corporate_cli",
    "raw_output": true,
    "force_mono": false,
    "use_color": false,
    "data": [
      {
        "name": "Revenue",
        "x": ["Jan", "Feb", "Mar", "Apr", "May"],
        "y": [120, 132, 148, 160, 178]
      }
    ]
  }
}
```

### Terminal dashboard

```json
{
  "tool": "create_terminal_dashboard",
  "arguments": {
    "title": "Terminal Executive Dashboard",
    "raw_output": true,
    "force_mono": false,
    "use_color": false,
    "panels": [
      {
        "type": "line",
        "title": "Revenue Trend",
        "x_label": "Month",
        "y_label": "k USD",
        "data": [
          {
            "name": "Revenue",
            "x": ["Jan", "Feb", "Mar", "Apr"],
            "y": [120, 132, 148, 160]
          }
        ]
      },
      {
        "type": "bar",
        "title": "ROI by Channel",
        "x_label": "Channel",
        "y_label": "%",
        "data": [
          {
            "name": "ROI",
            "x": ["Search", "Social", "Email", "Affiliate"],
            "y": [136, 112, 121, 95]
          }
        ]
      }
    ]
  }
}
```

### Combined image dashboard

```json
{
  "tool": "create_combined_dashboard",
  "arguments": {
    "title": "Executive Marketing Dashboard",
    "rows": 2,
    "cols": 2,
    "format": "png",
    "save_to_disk": true,
    "filename": "combined_showcase",
    "panels": [
      {
        "type": "line",
        "row": 1,
        "col": 1,
        "title": "Revenue Trend",
        "x_label": "Month",
        "y_label": "k USD",
        "data": [
          {
            "name": "Revenue",
            "x": ["Jan", "Feb", "Mar", "Apr"],
            "y": [120, 132, 148, 160]
          }
        ]
      },
      {
        "type": "pie",
        "row": 1,
        "col": 2,
        "title": "Budget Mix",
        "data": [
          {
            "labels": ["Search", "Social", "Email"],
            "values": [45, 35, 20]
          }
        ]
      }
    ]
  }
}
```
