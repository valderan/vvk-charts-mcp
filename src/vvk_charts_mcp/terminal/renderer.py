"""Terminal chart rendering with ANSI and monochrome fallback."""

from __future__ import annotations

import io
import math
import os
import re
from contextlib import redirect_stdout
from typing import Any, Literal

from vvk_charts_mcp.terminal.themes import resolve_cli_theme


def should_use_color(use_color: bool = True, force_mono: bool = False) -> bool:
    """Decide if ANSI color should be used."""
    if force_mono:
        return False
    if not use_color:
        return False
    if os.getenv("NO_COLOR"):
        return False
    term = os.getenv("TERM", "")
    if term.lower() == "dumb":
        return False
    return True


ANSI_RE = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")


def strip_ansi(text: str) -> str:
    """Strip ANSI escape sequences from text output."""
    return ANSI_RE.sub("", text)


def _safe_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _x_for_plotext(values: list[Any], length: int) -> list[float | int]:
    if not values:
        return list(range(1, length + 1))
    try:
        return [float(v) for v in values]
    except (TypeError, ValueError):
        return list(range(1, length + 1))


def _sparkline(values: list[float]) -> str:
    if not values:
        return ""
    ticks = "▁▂▃▄▅▆▇█"
    lo, hi = min(values), max(values)
    if math.isclose(lo, hi):
        return ticks[0] * len(values)
    return "".join(ticks[int((v - lo) / (hi - lo) * (len(ticks) - 1))] for v in values)


def _render_mono_chart(
    chart_type: str,
    data: list[dict[str, Any]],
    title: str | None,
    x_label: str | None,
    y_label: str | None,
    width: int,
    height: int,
    mono_symbol: str,
) -> str:
    lines: list[str] = []
    if title:
        lines.append(f"{title}")
        lines.append("-" * min(len(title), width))

    if chart_type in {"line", "scatter", "area"}:
        for idx, series in enumerate(data, start=1):
            name = str(series.get("name", f"Series {idx}"))
            y_values = [_safe_float(v) for v in series.get("y", [])]
            spark = _sparkline(y_values)
            if len(spark) > width - 20:
                spark = spark[: max(8, width - 23)] + "..."
            if y_values:
                lines.append(f"{name:<18} {spark}  min={min(y_values):.2f} max={max(y_values):.2f}")
            else:
                lines.append(f"{name:<18} (no data)")

    elif chart_type == "bar":
        max_val = 0.0
        rows: list[tuple[str, float]] = []
        for series in data:
            x_vals = series.get("x", [])
            y_vals = [_safe_float(v) for v in series.get("y", [])]
            for x, y in zip(x_vals, y_vals, strict=False):
                label = str(x)
                rows.append((label, y))
                max_val = max(max_val, y)

        bar_width = max(10, width - 28)
        for label, value in rows[: max(5, height * 2)]:
            size = int((value / max_val) * bar_width) if max_val > 0 else 0
            bar = mono_symbol * max(1, size)
            lines.append(f"{label[:14]:<14} | {bar:<{bar_width}} {value:.2f}")

    else:
        lines.append(f"Unsupported terminal chart type: {chart_type}")

    if x_label or y_label:
        lines.append("")
    if x_label:
        lines.append(f"X: {x_label}")
    if y_label:
        lines.append(f"Y: {y_label}")

    return "\n".join(lines)


def _render_plotext_chart(
    chart_type: str,
    data: list[dict[str, Any]],
    title: str | None,
    x_label: str | None,
    y_label: str | None,
    width: int,
    height: int,
    colors: list[str],
) -> str:
    import plotext as plt

    plt.clf()
    plt.plotsize(max(40, width), max(12, height))

    for idx, series in enumerate(data):
        y_vals = [_safe_float(v) for v in series.get("y", [])]
        x_vals = _x_for_plotext(series.get("x", []), len(y_vals))
        label = str(series.get("name", f"Series {idx + 1}"))
        color = colors[idx % len(colors)]

        if chart_type == "line":
            plt.plot(x_vals, y_vals, color=color, label=label)
        elif chart_type == "bar":
            plt.bar(x_vals, y_vals, color=color, label=label)
        elif chart_type == "scatter":
            plt.scatter(x_vals, y_vals, color=color, label=label)
        elif chart_type == "area":
            plt.plot(x_vals, y_vals, color=color, label=label)
        else:
            raise ValueError(f"Unsupported terminal chart type: {chart_type}")

    if title:
        plt.title(title)
    if x_label:
        plt.xlabel(x_label)
    if y_label:
        plt.ylabel(y_label)

    plt.grid(True)
    plt.canvas_color("default")
    plt.axes_color("default")

    out = io.StringIO()
    with redirect_stdout(out):
        plt.show()
    return out.getvalue().rstrip()


def render_terminal_chart(
    chart_type: str,
    data: list[dict[str, Any]],
    title: str | None = None,
    x_label: str | None = None,
    y_label: str | None = None,
    width: int = 100,
    height: int = 28,
    theme: str | dict[str, Any] | None = None,
    use_color: bool = True,
    force_mono: bool = False,
    text_mode: Literal["auto", "plotext_stripped", "fallback"] = "auto",
) -> dict[str, Any]:
    """Render a terminal chart and return text plus metadata."""
    if chart_type not in {"line", "bar", "scatter", "area"}:
        raise ValueError("terminal chart type must be one of: line, bar, scatter, area")

    if not data:
        raise ValueError("'data' must be a non-empty array")

    if text_mode not in {"auto", "plotext_stripped", "fallback"}:
        raise ValueError("'text_mode' must be one of: auto, plotext_stripped, fallback")

    resolved_theme = resolve_cli_theme(theme)
    ansi_enabled = should_use_color(use_color=use_color, force_mono=force_mono)
    plotext_error: str | None = None

    if text_mode != "fallback":
        try:
            text = _render_plotext_chart(
                chart_type=chart_type,
                data=data,
                title=title,
                x_label=x_label,
                y_label=y_label,
                width=width,
                height=height,
                colors=resolved_theme["colors"],
            )
            if text_mode == "plotext_stripped":
                return {
                    "success": True,
                    "render_mode": "mono",
                    "engine": "plotext-stripped",
                    "theme": resolved_theme["name"],
                    "chart": strip_ansi(text),
                }

            if ansi_enabled:
                return {
                    "success": True,
                    "render_mode": "ansi",
                    "engine": "plotext",
                    "theme": resolved_theme["name"],
                    "chart": text,
                }

            return {
                "success": True,
                "render_mode": "mono",
                "engine": "plotext-stripped",
                "theme": resolved_theme["name"],
                "chart": strip_ansi(text),
            }
        except Exception as exc:
            plotext_error = str(exc)

    text = _render_mono_chart(
        chart_type=chart_type,
        data=data,
        title=title,
        x_label=x_label,
        y_label=y_label,
        width=width,
        height=height,
        mono_symbol=resolved_theme["mono_symbol"],
    )
    result = {
        "success": True,
        "render_mode": "mono",
        "engine": "fallback",
        "theme": resolved_theme["name"],
        "chart": text,
    }
    if plotext_error:
        result["fallback_reason"] = plotext_error
    return result


def render_terminal_dashboard(
    panels: list[dict[str, Any]],
    title: str | None = None,
    width: int = 120,
    height: int = 32,
    theme: str | dict[str, Any] | None = None,
    use_color: bool = True,
    force_mono: bool = False,
    text_mode: Literal["auto", "plotext_stripped", "fallback"] = "auto",
) -> dict[str, Any]:
    """Render several terminal charts as a text dashboard."""
    if not panels:
        raise ValueError("'panels' must be a non-empty array")

    rendered: list[str] = []
    mode = "ansi"
    engine_rank = 0
    panel_fallback_reasons: list[str] = []
    for idx, panel in enumerate(panels, start=1):
        result = render_terminal_chart(
            chart_type=str(panel.get("type", "line")),
            data=panel.get("data", []),
            title=panel.get("title") or f"Panel {idx}",
            x_label=panel.get("x_label"),
            y_label=panel.get("y_label"),
            width=max(40, width),
            height=max(10, height // max(1, len(panels))),
            theme=theme,
            use_color=use_color,
            force_mono=force_mono,
            text_mode=text_mode,
        )
        if result["engine"] == "fallback":
            engine_rank = max(engine_rank, 2)
            mode = "mono"
        elif result["engine"] == "plotext-stripped":
            engine_rank = max(engine_rank, 1)
            mode = "mono"
        if "fallback_reason" in result:
            panel_fallback_reasons.append(str(result["fallback_reason"]))
        rendered.append(str(result["chart"]))

    blocks: list[str] = []
    if title:
        blocks.append(title)
        blocks.append("=" * min(max(len(title), 12), width))
    blocks.append("\n\n".join(rendered))

    engine = "plotext"
    if engine_rank == 2:
        engine = "fallback"
    elif engine_rank == 1:
        engine = "plotext-stripped"

    result = {
        "success": True,
        "render_mode": mode,
        "engine": engine,
        "theme": resolve_cli_theme(theme)["name"],
        "dashboard": "\n".join(blocks),
    }
    if panel_fallback_reasons:
        result["fallback_reason"] = "; ".join(panel_fallback_reasons)
    return result
