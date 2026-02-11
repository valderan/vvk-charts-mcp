"""Interactive CLI client for manual chart generation checks."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from vvk_charts_mcp.charts import (
    AreaChart,
    BarChart,
    ChartTheme,
    DataSeries,
    LineChart,
    PieChart,
    PieDataSeries,
    ScatterChart,
)
from vvk_charts_mcp.terminal import render_terminal_dashboard
from vvk_charts_mcp.utils.export import export_chart

FormatName = Literal["png", "svg", "base64"]


@dataclass
class Template:
    key: str
    title: str
    chart_type: str
    payload: dict[str, Any]


TEMPLATES: list[Template] = [
    Template(
        key="1",
        title="Monthly Sales Trend",
        chart_type="line",
        payload={
            "title": "Monthly Sales, 2025",
            "x_label": "Month",
            "y_label": "Revenue, USD",
            "data": [
                {
                    "x": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
                    "y": [32000, 38000, 35000, 42000, 47000, 52000],
                    "name": "Online",
                },
                {
                    "x": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
                    "y": [21000, 24000, 26000, 28000, 30000, 34000],
                    "name": "Retail",
                },
            ],
        },
    ),
    Template(
        key="2",
        title="Department KPI Bars",
        chart_type="bar",
        payload={
            "title": "Department KPI Score",
            "x_label": "Department",
            "y_label": "Score",
            "data": [
                {
                    "x": ["Sales", "Support", "Marketing", "R&D", "Finance"],
                    "y": [83, 76, 88, 91, 79],
                    "name": "Q1",
                },
                {
                    "x": ["Sales", "Support", "Marketing", "R&D", "Finance"],
                    "y": [87, 81, 84, 93, 82],
                    "name": "Q2",
                },
            ],
        },
    ),
    Template(
        key="3",
        title="Market Share Pie",
        chart_type="pie",
        payload={
            "title": "Market Share",
            "data": [
                {
                    "labels": ["Product A", "Product B", "Product C", "Product D"],
                    "values": [42, 28, 18, 12],
                    "name": "Products",
                }
            ],
            "hole": 0.45,
        },
    ),
    Template(
        key="4",
        title="Ad Spend vs Revenue Scatter",
        chart_type="scatter",
        payload={
            "title": "Ad Spend Correlation",
            "x_label": "Ad Spend, USD",
            "y_label": "Revenue, USD",
            "data": [
                {
                    "x": [1200, 1500, 1800, 2100, 2500, 2900, 3300],
                    "y": [9400, 11200, 13100, 15300, 17500, 19200, 22000],
                    "name": "Campaigns",
                    "marker": {"size": [10, 12, 15, 11, 16, 18, 20]},
                }
            ],
            "show_line": True,
        },
    ),
    Template(
        key="5",
        title="Traffic Area Stack",
        chart_type="area",
        payload={
            "title": "Website Traffic by Source",
            "x_label": "Week",
            "y_label": "Visits",
            "data": [
                {
                    "x": ["W1", "W2", "W3", "W4", "W5", "W6"],
                    "y": [3200, 3500, 3900, 4100, 4300, 4600],
                    "name": "Organic",
                },
                {
                    "x": ["W1", "W2", "W3", "W4", "W5", "W6"],
                    "y": [1400, 1800, 2000, 2300, 2400, 2500],
                    "name": "Paid",
                },
                {
                    "x": ["W1", "W2", "W3", "W4", "W5", "W6"],
                    "y": [900, 1100, 1200, 1350, 1500, 1650],
                    "name": "Social",
                },
            ],
            "stack": True,
            "opacity": 0.7,
        },
    ),
]


def ask(prompt: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default else ""
    value = input(f"{prompt}{suffix}: ").strip()
    return value or (default or "")


def choose_template() -> Template:
    print("\nChoose a template:")
    for item in TEMPLATES:
        print(f"  {item.key}. {item.title}")

    while True:
        picked = ask("Template number", "1")
        for item in TEMPLATES:
            if item.key == picked:
                return item
        print("Invalid option, try again.")


def choose_formats() -> list[FormatName]:
    print("\nOutput format:")
    print("  1. PNG")
    print("  2. SVG")
    print("  3. PNG + SVG")
    print("  4. Base64 (both)")

    picked = ask("Format", "3")
    mapping: dict[str, list[FormatName]] = {
        "1": ["png"],
        "2": ["svg"],
        "3": ["png", "svg"],
        "4": ["base64"],
    }
    return mapping.get(picked, ["png", "svg"])


def build_chart(template: Template, width: int, height: int) -> tuple[Any, str]:
    theme = ChartTheme(
        font_family="Inter, Segoe UI, sans-serif",
        paper_bgcolor="#FFFFFF",
        plot_background="#F7FAFC",
        colors=["#2563EB", "#F59E0B", "#10B981", "#EF4444", "#8B5CF6"],
    )

    chart: Any
    data: list[Any]

    if template.chart_type == "line":
        chart = LineChart(
            title=template.payload["title"],
            x_label=template.payload["x_label"],
            y_label=template.payload["y_label"],
            theme=theme,
            width=width,
            height=height,
        )
        data = [DataSeries(**item) for item in template.payload["data"]]
        return chart.build(data), "line_chart"

    if template.chart_type == "bar":
        chart = BarChart(
            title=template.payload["title"],
            x_label=template.payload["x_label"],
            y_label=template.payload["y_label"],
            theme=theme,
            width=width,
            height=height,
            barmode="group",
        )
        data = [DataSeries(**item) for item in template.payload["data"]]
        return chart.build(data), "bar_chart"

    if template.chart_type == "pie":
        chart = PieChart(
            title=template.payload["title"],
            theme=theme,
            width=width,
            height=height,
            hole=template.payload.get("hole", 0.0),
        )
        data = [PieDataSeries(**item) for item in template.payload["data"]]
        return chart.build(data), "pie_chart"

    if template.chart_type == "scatter":
        chart = ScatterChart(
            title=template.payload["title"],
            x_label=template.payload["x_label"],
            y_label=template.payload["y_label"],
            theme=theme,
            width=width,
            height=height,
            show_line=template.payload.get("show_line", False),
        )
        data = [DataSeries(**item) for item in template.payload["data"]]
        return chart.build(data), "scatter_chart"

    chart = AreaChart(
        title=template.payload["title"],
        x_label=template.payload["x_label"],
        y_label=template.payload["y_label"],
        theme=theme,
        width=width,
        height=height,
        stack=template.payload.get("stack", True),
        opacity=template.payload.get("opacity", 0.7),
    )
    data = [DataSeries(**item) for item in template.payload["data"]]
    return chart.build(data), "area_chart"


def run_interactive() -> int:
    print("VVK Charts CLI - interactive visual test client")
    print("Use this to quickly verify all chart functions.\n")

    output_mode = ask("Output mode: image or terminal", "image").strip().lower()
    if output_mode in {"terminal", "term", "t"}:
        return run_terminal_demo()

    template = choose_template()
    output_dir = Path(ask("Output folder", "./output")).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = ask("File name (without extension)", template.chart_type)
    formats = choose_formats()

    width = int(ask("Image width", "1280"))
    height = int(ask("Image height", "720"))

    figure, default_name = build_chart(template, width=width, height=height)
    base_name = filename or default_name
    result = export_chart(
        figure,
        format=formats,
        output_dir=None if formats == ["base64"] else output_dir,
        filename=base_name,
        width=width,
        height=height,
    )

    print("\nDone.")
    if "base64_png" in result:
        print("- Base64 PNG generated")
    if "base64_svg" in result:
        print("- Base64 SVG generated")
    if "png" in result:
        png_value = result["png"]
        print(f"- PNG: {png_value if isinstance(png_value, str) else '<bytes>'}")
    if "svg" in result:
        svg_value = result["svg"]
        print(f"- SVG: {svg_value if isinstance(svg_value, str) else '<content>'}")
    return 0


def run_terminal_demo() -> int:
    print("\nTerminal dashboard mode")
    print("  1. Dark corporate")
    print("  2. Pastel startup")
    picked = ask("Theme", "1")
    theme = "pastel_startup_cli" if picked == "2" else "dark_corporate_cli"

    panels = [
        {
            "type": "line",
            "title": "Revenue Trend",
            "x_label": "Month",
            "y_label": "k USD",
            "data": [
                {
                    "name": "Revenue",
                    "x": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
                    "y": [120, 132, 148, 160, 178, 190],
                }
            ],
        },
        {
            "type": "bar",
            "title": "Channel ROI",
            "x_label": "Channel",
            "y_label": "%",
            "data": [
                {
                    "name": "ROI",
                    "x": ["Search", "Social", "Email", "Aff"],
                    "y": [135, 110, 92, 77],
                }
            ],
        },
        {
            "type": "scatter",
            "title": "Spend vs Revenue",
            "x_label": "Spend",
            "y_label": "Revenue",
            "data": [
                {
                    "name": "Campaigns",
                    "x": [20, 30, 40, 55, 70, 90],
                    "y": [60, 83, 110, 149, 196, 248],
                }
            ],
        },
    ]

    result = render_terminal_dashboard(
        panels=panels,
        title="Terminal Marketing Dashboard",
        theme=theme,
        width=100,
        height=36,
        use_color=True,
        force_mono=False,
    )
    print("\n" + str(result["dashboard"]))
    print(
        f"\nrender_mode={result['render_mode']} engine={result['engine']} theme={result['theme']}"
    )
    return 0


def main() -> None:
    raise SystemExit(run_interactive())


if __name__ == "__main__":
    main()
