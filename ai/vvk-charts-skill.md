---
name: vvk-charts-mcp
description: Build and style chart payloads for the vvk-charts-mcp server
license: MIT
compatibility: opencode
metadata:
  domain: data-visualization
  transport: mcp-stdio
---

## What this skill does

- Chooses the most suitable chart type for user intent.
- Produces clean MCP payloads for all tools in `vvk-charts-mcp`.
- Applies modern chart design defaults (readable typography, color contrast, clear labels).
- Helps with exporting charts as `png`, `svg`, or `base64`.

## Tool mapping

- Trend over time -> `create_line_chart`
- Category comparison -> `create_bar_chart`
- Part-to-whole -> `create_pie_chart`
- Correlation/distribution -> `create_scatter_chart`
- Cumulative composition over time -> `create_area_chart`

## Input shaping rules

- Keep `x`/`y` lengths equal per series.
- Use explicit `name` for each series.
- Set `title`, `x_label`, and `y_label` unless user requests a minimal chart.
- Use `theme` for color palette, font, grid, and legend placement.
- If the user requests local files, set `output_path` and `filename`.

## Performance guidance for large data

- Prefer line charts without point markers for dense series.
- Limit annotation text to key points only.
- Avoid pie charts with too many slices; switch to bars if labels become unreadable.
- Consider splitting very large datasets across multiple charts.

## Example payloads

```json
{
  "tool": "create_line_chart",
  "arguments": {
    "title": "Revenue by Month",
    "x_label": "Month",
    "y_label": "Revenue (USD)",
    "format": "png",
    "output_path": "./output",
    "filename": "revenue-monthly",
    "data": [
      {
        "name": "North Region",
        "x": ["Jan", "Feb", "Mar", "Apr"],
        "y": [12000, 13500, 12800, 14900]
      }
    ]
  }
}
```

```json
{
  "tool": "create_scatter_chart",
  "arguments": {
    "title": "Ad Spend vs Revenue",
    "x_label": "Ad Spend",
    "y_label": "Revenue",
    "format": "svg",
    "data": [
      {
        "name": "Campaigns",
        "x": [100, 200, 300, 400],
        "y": [1000, 1800, 2500, 3300]
      }
    ]
  }
}
```
