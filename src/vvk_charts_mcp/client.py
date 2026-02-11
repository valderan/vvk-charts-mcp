"""Interactive CLI client for manual MCP tool checks."""

from __future__ import annotations

import asyncio
import json
import os
from copy import deepcopy
from typing import Any

import mcp.types as types

from vvk_charts_mcp.server import call_tool

IMAGE_TOOLS = [
    "create_line_chart",
    "create_bar_chart",
    "create_pie_chart",
    "create_scatter_chart",
    "create_area_chart",
    "create_combined_dashboard",
]

TERMINAL_TOOLS = ["create_terminal_chart", "create_terminal_dashboard"]
UTILITY_TOOLS = ["list_theme_presets"]

ALL_TOOL_PAYLOADS: dict[str, dict[str, Any]] = {
    "create_line_chart": {
        "title": "Monthly Revenue",
        "x_label": "Month",
        "y_label": "k USD",
        "format": "png",
        "filename": "line_revenue",
        "data": [
            {"name": "Online", "x": ["Jan", "Feb", "Mar", "Apr"], "y": [120, 140, 155, 170]},
            {"name": "Retail", "x": ["Jan", "Feb", "Mar", "Apr"], "y": [95, 102, 118, 130]},
        ],
    },
    "create_bar_chart": {
        "title": "ROI by Channel",
        "x_label": "Channel",
        "y_label": "%",
        "format": "png",
        "filename": "bar_roi",
        "barmode": "group",
        "data": [
            {"name": "Q1", "x": ["Search", "Social", "Email"], "y": [132, 108, 95]},
            {"name": "Q2", "x": ["Search", "Social", "Email"], "y": [140, 115, 102]},
        ],
    },
    "create_pie_chart": {
        "title": "Budget Mix",
        "format": "png",
        "filename": "pie_budget",
        "hole": 0.45,
        "data": [
            {
                "name": "Channels",
                "labels": ["Search", "Social", "Email", "Affiliate"],
                "values": [42, 28, 20, 10],
            }
        ],
    },
    "create_scatter_chart": {
        "title": "Spend vs Revenue",
        "x_label": "Spend",
        "y_label": "Revenue",
        "format": "png",
        "filename": "scatter_spend_revenue",
        "show_line": True,
        "data": [
            {
                "name": "Campaigns",
                "x": [20, 30, 40, 55, 70, 90],
                "y": [62, 84, 109, 150, 201, 248],
                "marker": {"size": [9, 11, 12, 14, 16, 18]},
            }
        ],
    },
    "create_area_chart": {
        "title": "Traffic by Source",
        "x_label": "Week",
        "y_label": "Visits",
        "format": "png",
        "filename": "area_traffic",
        "stack": True,
        "opacity": 0.65,
        "data": [
            {"name": "Organic", "x": ["W1", "W2", "W3", "W4"], "y": [3200, 3600, 3900, 4200]},
            {"name": "Paid", "x": ["W1", "W2", "W3", "W4"], "y": [1400, 1700, 2100, 2300]},
            {"name": "Social", "x": ["W1", "W2", "W3", "W4"], "y": [900, 1100, 1300, 1500]},
        ],
    },
    "create_combined_dashboard": {
        "title": "Executive Dashboard",
        "rows": 1,
        "cols": 2,
        "format": "png",
        "filename": "combined_exec",
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
                        "x": ["Jan", "Feb", "Mar", "Apr", "May"],
                        "y": [120, 132, 148, 160, 178],
                    }
                ],
                "options": {"line_shape": "spline"},
            },
            {
                "type": "pie",
                "row": 1,
                "col": 2,
                "title": "Budget Split",
                "data": [
                    {"labels": ["Search", "Social", "Email"], "values": [45, 35, 20], "name": "Mix"}
                ],
                "options": {"hole": 0.4},
            },
        ],
    },
    "create_terminal_chart": {
        "type": "line",
        "title": "Terminal Revenue Trend",
        "x_label": "Month",
        "y_label": "k USD",
        "theme": "dark_corporate_cli",
        "raw_output": False,
        "use_color": False,
        "force_mono": False,
        "data": [{"name": "Revenue", "x": ["Jan", "Feb", "Mar", "Apr"], "y": [120, 132, 148, 160]}],
    },
    "create_terminal_dashboard": {
        "title": "Terminal Marketing Dashboard",
        "theme": "dark_corporate_cli",
        "raw_output": False,
        "use_color": False,
        "force_mono": False,
        "panels": [
            {
                "type": "line",
                "title": "Revenue",
                "x_label": "Month",
                "y_label": "k USD",
                "data": [
                    {
                        "name": "Revenue",
                        "x": ["Jan", "Feb", "Mar", "Apr"],
                        "y": [120, 132, 148, 160],
                    }
                ],
            },
            {
                "type": "bar",
                "title": "ROI",
                "x_label": "Channel",
                "y_label": "%",
                "data": [{"name": "ROI", "x": ["Search", "Social", "Email"], "y": [136, 112, 96]}],
            },
        ],
    },
    "list_theme_presets": {},
}


def ask(prompt: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default else ""
    value = input(f"{prompt}{suffix}: ").strip()
    return value or (default or "")


def _apply_runtime_options(
    tool_name: str,
    payload: dict[str, Any],
    save_to_disk: bool,
    fmt: str,
    theme_preset: str,
) -> None:
    if tool_name in IMAGE_TOOLS:
        payload["save_to_disk"] = save_to_disk
        payload["format"] = fmt
        payload["theme_preset"] = theme_preset


def _print_text_payload(text: str) -> None:
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        print(text)
        return

    print(json.dumps(parsed, ensure_ascii=False, indent=2))


def _print_result_blocks(result: list[types.ContentBlock]) -> None:
    has_image = False
    for block in result:
        if isinstance(block, types.ImageContent):
            has_image = True
            print(f"- image content: mime={block.mimeType}, base64_length={len(block.data)}")
        elif isinstance(block, types.TextContent):
            print("- text content:")
            _print_text_payload(block.text)
        else:
            print(f"- other content block: {type(block).__name__}")

    if not has_image:
        print("- image preview: not returned")


async def _invoke_tool(tool_name: str, payload: dict[str, Any]) -> None:
    print(f"\n=== {tool_name} ===")
    result = await call_tool(tool_name, payload)
    _print_result_blocks(result)


def choose_tool() -> str:
    tools = UTILITY_TOOLS + IMAGE_TOOLS + TERMINAL_TOOLS
    print("\nChoose MCP method:")
    for idx, tool_name in enumerate(tools, start=1):
        print(f"  {idx}. {tool_name}")

    while True:
        picked = ask("Method number", "1")
        if picked.isdigit():
            index = int(picked) - 1
            if 0 <= index < len(tools):
                return tools[index]
        print("Invalid option, try again.")


def choose_mode() -> tuple[bool, str, str]:
    print("\nImage behavior:")
    print("  1. Preview only (default)")
    print("  2. Save to disk if OUTPUT_DIR is set")
    mode = ask("Mode", "1")
    save_to_disk = mode == "2"

    print("\nFormat for image methods:")
    print("  1. png")
    print("  2. svg")
    print("  3. base64")
    fmt_pick = ask("Format", "1")
    fmt = {"1": "png", "2": "svg", "3": "base64"}.get(fmt_pick, "png")
    print("\nImage theme preset:")
    print("  1. clean_light")
    print("  2. dark_corporate")
    print("  3. pastel_startup")
    print("  4. medical_monitor")
    theme_pick = ask("Theme preset", "1")
    theme_preset = {
        "1": "clean_light",
        "2": "dark_corporate",
        "3": "pastel_startup",
        "4": "medical_monitor",
    }.get(theme_pick, "clean_light")
    return save_to_disk, fmt, theme_preset


async def run_single(save_to_disk: bool, fmt: str, theme_preset: str) -> int:
    tool_name = choose_tool()
    payload = deepcopy(ALL_TOOL_PAYLOADS[tool_name])
    _apply_runtime_options(
        tool_name,
        payload,
        save_to_disk=save_to_disk,
        fmt=fmt,
        theme_preset=theme_preset,
    )
    await _invoke_tool(tool_name, payload)
    return 0


async def run_all(save_to_disk: bool, fmt: str, theme_preset: str) -> int:
    for tool_name in UTILITY_TOOLS + IMAGE_TOOLS + TERMINAL_TOOLS:
        payload = deepcopy(ALL_TOOL_PAYLOADS[tool_name])
        _apply_runtime_options(
            tool_name,
            payload,
            save_to_disk=save_to_disk,
            fmt=fmt,
            theme_preset=theme_preset,
        )
        await _invoke_tool(tool_name, payload)
    return 0


def run_interactive() -> int:
    print("VVK Charts CLI - MCP tools smoke checker")
    print("This client calls all server methods with example payloads.")
    print(f"OUTPUT_DIR={os.getenv('OUTPUT_DIR', '<not set>')}")

    save_to_disk, fmt, theme_preset = choose_mode()

    print("\nAction:")
    print("  1. Run one method")
    print("  2. Run all methods")
    action = ask("Action", "2")

    if action == "1":
        return asyncio.run(
            run_single(save_to_disk=save_to_disk, fmt=fmt, theme_preset=theme_preset)
        )

    return asyncio.run(run_all(save_to_disk=save_to_disk, fmt=fmt, theme_preset=theme_preset))


def main() -> None:
    raise SystemExit(run_interactive())


if __name__ == "__main__":
    main()
