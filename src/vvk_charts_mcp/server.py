"""MCP сервер для создания графиков и диаграмм."""

import json
import os
import re
from pathlib import Path
from typing import Any, Literal

import mcp.server.stdio
import mcp.types as types
import plotly.graph_objects as go
from mcp.server import Server
from plotly.subplots import make_subplots

from vvk_charts_mcp.charts import (
    DEFAULT_IMAGE_THEME,
    IMAGE_THEME_DESCRIPTIONS,
    IMAGE_THEME_PRESETS,
    AreaChart,
    BarChart,
    ChartTheme,
    DataSeries,
    LineChart,
    PieChart,
    PieDataSeries,
    ScatterChart,
    resolve_image_theme,
)
from vvk_charts_mcp.terminal import render_terminal_chart, render_terminal_dashboard
from vvk_charts_mcp.terminal.themes import CLI_THEMES, DEFAULT_CLI_THEME
from vvk_charts_mcp.utils.export import export_chart, export_to_base64

server = Server("vvk-charts-mcp")

IMAGE_TOOL_NAMES = {
    "create_line_chart",
    "create_bar_chart",
    "create_pie_chart",
    "create_scatter_chart",
    "create_area_chart",
    "create_combined_dashboard",
}
FILENAME_SAFE_RE = re.compile(r"[^A-Za-z0-9._-]+")
IMAGE_THEME_PRESET_NAMES = list(IMAGE_THEME_PRESETS.keys())


def parse_data_series(data: list[dict[str, Any]]) -> list[DataSeries]:
    """Парсит список словарей в список DataSeries."""
    return [DataSeries(**item) for item in data]


def parse_pie_data_series(data: list[dict[str, Any]]) -> list[PieDataSeries]:
    """Парсит список словарей в список PieDataSeries."""
    return [PieDataSeries(**item) for item in data]


def _resolve_output_dir() -> Path | None:
    output_dir = os.getenv("OUTPUT_DIR", "").strip()
    if not output_dir:
        return None
    return Path(output_dir).expanduser().resolve()


def _strip_data_uri_prefix(value: str) -> str:
    if value.startswith("data:image") and "," in value:
        return value.split(",", 1)[1]
    return value


def _sanitize_filename(name: str | None, fallback: str) -> str:
    base_name = Path((name or fallback).strip() or fallback).name
    stem = Path(base_name).stem or fallback
    safe_name = FILENAME_SAFE_RE.sub("_", stem).strip("._")
    return safe_name or fallback


def _build_combined_figure(
    panels: list[dict[str, Any]],
    rows: int,
    cols: int,
    theme: ChartTheme,
    title: str | None,
    width: int | None,
    height: int | None,
    shared_xaxes: bool,
    vertical_spacing: float,
    horizontal_spacing: float,
) -> go.Figure:
    """Создаёт комбинированный дашборд из нескольких графиков."""
    specs: list[list[dict[str, str]]] = []
    subplot_titles: list[str] = []

    panel_map: dict[tuple[int, int], dict[str, Any]] = {
        (int(panel["row"]), int(panel["col"])): panel for panel in panels
    }

    for row in range(1, rows + 1):
        spec_row: list[dict[str, str]] = []
        for col in range(1, cols + 1):
            panel = panel_map.get((row, col))
            if panel and panel.get("type") == "pie":
                spec_row.append({"type": "domain"})
            else:
                spec_row.append({"type": "xy"})

            subplot_titles.append(panel.get("title", "") if panel else "")
        specs.append(spec_row)

    figure = make_subplots(
        rows=rows,
        cols=cols,
        specs=specs,
        subplot_titles=subplot_titles,
        shared_xaxes=shared_xaxes,
        vertical_spacing=vertical_spacing,
        horizontal_spacing=horizontal_spacing,
    )

    for panel in panels:
        panel_type = panel["type"]
        row = int(panel["row"])
        col = int(panel["col"])
        panel_data = panel.get("data", [])
        options = panel.get("options", {})

        if panel_type == "line":
            chart_figure = LineChart(theme=theme).create_figure(
                parse_data_series(panel_data),
                line_mode=options.get("line_mode", "lines+markers"),
                line_shape=options.get("line_shape", "linear"),
            )
        elif panel_type == "bar":
            chart_figure = BarChart(theme=theme).create_figure(
                parse_data_series(panel_data),
                orientation=options.get("orientation", "v"),
                barmode=options.get("barmode", "group"),
            )
        elif panel_type == "pie":
            chart_figure = PieChart(theme=theme, showlegend=False).create_figure(
                parse_pie_data_series(panel_data),
                hole=options.get("hole", 0.0),
                textinfo=options.get("textinfo", "label+percent"),
            )
        elif panel_type == "scatter":
            chart_figure = ScatterChart(theme=theme).create_figure(
                parse_data_series(panel_data),
                show_line=options.get("show_line", False),
            )
        elif panel_type == "area":
            chart_figure = AreaChart(theme=theme).create_figure(
                parse_data_series(panel_data),
                stack=options.get("stack", True),
                normalize=options.get("normalize", False),
                opacity=options.get("opacity", 0.6),
            )
        else:
            raise ValueError(f"Unsupported panel type: {panel_type}")

        for trace in chart_figure.data:
            figure.add_trace(trace, row=row, col=col)

        if panel_type != "pie":
            if panel.get("x_label"):
                figure.update_xaxes(title_text=panel["x_label"], row=row, col=col)
            if panel.get("y_label"):
                figure.update_yaxes(title_text=panel["y_label"], row=row, col=col)

    figure.update_layout(
        title={
            "text": title,
            "font": {
                "family": theme.font_family,
                "size": theme.title_font_size,
                "color": theme.font_color,
            },
            "x": 0.5,
            "xanchor": "center",
        }
        if title
        else None,
        font={"family": theme.font_family, "color": theme.font_color},
        paper_bgcolor=theme.paper_bgcolor,
        plot_bgcolor=theme.plot_background,
        margin=theme.margin,
        showlegend=theme.show_legend,
        legend=theme.get_legend_settings() if theme.show_legend else {},
        width=width,
        height=height,
    )

    figure.update_xaxes(
        tickfont={
            "family": theme.font_family,
            "size": theme.tick_font_size,
            "color": theme.font_color,
        },
        **theme.get_grid_settings(),
    )
    figure.update_yaxes(
        tickfont={
            "family": theme.font_family,
            "size": theme.tick_font_size,
            "color": theme.font_color,
        },
        **theme.get_grid_settings(),
    )

    return figure


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    """Возвращает список доступных инструментов."""
    return [
        types.Tool(
            name="list_theme_presets",
            description=(
                "Возвращает список доступных тем для image и terminal графиков, "
                "чтобы выбрать тему без чтения документации."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="create_line_chart",
            description="Создаёт линейный график с поддержкой множественных серий данных. "
            "Возвращает base64 изображение или путь к файлу.",
            inputSchema={
                "type": "object",
                "properties": {
                    "data": {
                        "type": "array",
                        "description": "Массив серий данных",
                        "items": {
                            "type": "object",
                            "properties": {
                                "x": {
                                    "type": "array",
                                    "items": {"type": ["string", "number", "integer", "boolean"]},
                                    "description": "Значения оси X",
                                },
                                "y": {
                                    "type": "array",
                                    "items": {"type": "number"},
                                    "description": "Значения оси Y",
                                },
                                "name": {"type": "string", "description": "Название серии"},
                                "color": {"type": "string", "description": "Цвет серии"},
                            },
                            "required": ["x", "y"],
                        },
                    },
                    "title": {"type": "string", "description": "Заголовок графика"},
                    "x_label": {"type": "string", "description": "Подпись оси X"},
                    "y_label": {"type": "string", "description": "Подпись оси Y"},
                    "theme_preset": {
                        "type": "string",
                        "enum": IMAGE_THEME_PRESET_NAMES,
                        "default": DEFAULT_IMAGE_THEME,
                        "description": "Название базовой темы оформления",
                    },
                    "theme": {"type": "object", "description": "Тема оформления (кастомизация)"},
                    "format": {
                        "type": "string",
                        "enum": ["png", "svg", "base64"],
                        "default": "base64",
                        "description": "Формат вывода",
                    },
                    "save_to_disk": {
                        "type": "boolean",
                        "default": False,
                        "description": (
                            "Сохранять файл на диск в директорию из env OUTPUT_DIR. "
                            "По умолчанию false (только preview для чата)."
                        ),
                    },
                    "filename": {
                        "type": "string",
                        "default": "line_chart",
                        "description": "Имя файла",
                    },
                    "width": {"type": "integer", "description": "Ширина изображения"},
                    "height": {"type": "integer", "description": "Высота изображения"},
                    "line_mode": {
                        "type": "string",
                        "enum": ["lines", "markers", "lines+markers"],
                        "default": "lines+markers",
                    },
                    "line_shape": {
                        "type": "string",
                        "enum": ["linear", "spline", "hv", "vh", "hvh", "vhv"],
                        "default": "linear",
                    },
                },
                "required": ["data"],
            },
        ),
        types.Tool(
            name="create_bar_chart",
            description="Создаёт столбчатую диаграмму с поддержкой группировки и стекинга. "
            "Возвращает base64 изображение или путь к файлу.",
            inputSchema={
                "type": "object",
                "properties": {
                    "data": {
                        "type": "array",
                        "description": "Массив серий данных",
                        "items": {
                            "type": "object",
                            "properties": {
                                "x": {
                                    "type": "array",
                                    "items": {"type": ["string", "number", "integer", "boolean"]},
                                    "description": "Категории",
                                },
                                "y": {
                                    "type": "array",
                                    "items": {"type": "number"},
                                    "description": "Значения",
                                },
                                "name": {"type": "string", "description": "Название серии"},
                                "color": {"type": "string", "description": "Цвет серии"},
                            },
                            "required": ["x", "y"],
                        },
                    },
                    "title": {"type": "string", "description": "Заголовок графика"},
                    "x_label": {"type": "string", "description": "Подпись оси X"},
                    "y_label": {"type": "string", "description": "Подпись оси Y"},
                    "theme_preset": {
                        "type": "string",
                        "enum": IMAGE_THEME_PRESET_NAMES,
                        "default": DEFAULT_IMAGE_THEME,
                        "description": "Название базовой темы оформления",
                    },
                    "theme": {"type": "object", "description": "Тема оформления"},
                    "format": {
                        "type": "string",
                        "enum": ["png", "svg", "base64"],
                        "default": "base64",
                    },
                    "save_to_disk": {
                        "type": "boolean",
                        "default": False,
                        "description": "Сохранять файл на диск в директорию из env OUTPUT_DIR",
                    },
                    "filename": {"type": "string", "default": "bar_chart"},
                    "width": {"type": "integer"},
                    "height": {"type": "integer"},
                    "orientation": {
                        "type": "string",
                        "enum": ["v", "h"],
                        "default": "v",
                        "description": "v - вертикальная, h - горизонтальная",
                    },
                    "barmode": {
                        "type": "string",
                        "enum": ["group", "stack", "relative", "overlay"],
                        "default": "group",
                    },
                },
                "required": ["data"],
            },
        ),
        types.Tool(
            name="create_pie_chart",
            description="Создаёт круговую диаграмму с поддержкой doughnut. "
            "Возвращает base64 изображение или путь к файлу.",
            inputSchema={
                "type": "object",
                "properties": {
                    "data": {
                        "type": "array",
                        "description": "Данные для диаграммы",
                        "items": {
                            "type": "object",
                            "properties": {
                                "values": {"type": "array", "items": {"type": "number"}},
                                "labels": {"type": "array", "items": {"type": "string"}},
                                "name": {"type": "string"},
                                "colors": {"type": "array", "items": {"type": "string"}},
                            },
                            "required": ["values", "labels"],
                        },
                    },
                    "title": {"type": "string", "description": "Заголовок графика"},
                    "theme_preset": {
                        "type": "string",
                        "enum": IMAGE_THEME_PRESET_NAMES,
                        "default": DEFAULT_IMAGE_THEME,
                        "description": "Название базовой темы оформления",
                    },
                    "theme": {"type": "object", "description": "Тема оформления"},
                    "format": {
                        "type": "string",
                        "enum": ["png", "svg", "base64"],
                        "default": "base64",
                    },
                    "save_to_disk": {
                        "type": "boolean",
                        "default": False,
                        "description": "Сохранять файл на диск в директорию из env OUTPUT_DIR",
                    },
                    "filename": {"type": "string", "default": "pie_chart"},
                    "width": {"type": "integer"},
                    "height": {"type": "integer"},
                    "hole": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 1,
                        "default": 0,
                        "description": "Размер отверстия (0 = pie, >0 = doughnut)",
                    },
                    "textinfo": {
                        "type": "string",
                        "default": "label+percent",
                    },
                },
                "required": ["data"],
            },
        ),
        types.Tool(
            name="create_scatter_chart",
            description="Создаёт точечный график с поддержкой пузырьковых диаграмм. "
            "Возвращает base64 изображение или путь к файлу.",
            inputSchema={
                "type": "object",
                "properties": {
                    "data": {
                        "type": "array",
                        "description": "Массив серий данных",
                        "items": {
                            "type": "object",
                            "properties": {
                                "x": {
                                    "type": "array",
                                    "items": {"type": ["string", "number", "integer", "boolean"]},
                                },
                                "y": {
                                    "type": "array",
                                    "items": {"type": "number"},
                                },
                                "name": {"type": "string"},
                                "color": {"type": "string"},
                                "marker": {
                                    "type": "object",
                                    "properties": {
                                        "size": {
                                            "oneOf": [
                                                {"type": "integer"},
                                                {"type": "array", "items": {"type": "integer"}},
                                            ]
                                        }
                                    },
                                },
                            },
                            "required": ["x", "y"],
                        },
                    },
                    "title": {"type": "string"},
                    "x_label": {"type": "string"},
                    "y_label": {"type": "string"},
                    "theme_preset": {
                        "type": "string",
                        "enum": IMAGE_THEME_PRESET_NAMES,
                        "default": DEFAULT_IMAGE_THEME,
                        "description": "Название базовой темы оформления",
                    },
                    "theme": {"type": "object"},
                    "format": {
                        "type": "string",
                        "enum": ["png", "svg", "base64"],
                        "default": "base64",
                    },
                    "save_to_disk": {
                        "type": "boolean",
                        "default": False,
                        "description": "Сохранять файл на диск в директорию из env OUTPUT_DIR",
                    },
                    "filename": {"type": "string", "default": "scatter_chart"},
                    "width": {"type": "integer"},
                    "height": {"type": "integer"},
                    "show_line": {
                        "type": "boolean",
                        "default": False,
                        "description": "Показывать линии между точками",
                    },
                },
                "required": ["data"],
            },
        ),
        types.Tool(
            name="create_area_chart",
            description="Создаёт диаграмму с областями с поддержкой стекинга. "
            "Возвращает base64 изображение или путь к файлу.",
            inputSchema={
                "type": "object",
                "properties": {
                    "data": {
                        "type": "array",
                        "description": "Массив серий данных",
                        "items": {
                            "type": "object",
                            "properties": {
                                "x": {
                                    "type": "array",
                                    "items": {"type": ["string", "number", "integer", "boolean"]},
                                },
                                "y": {
                                    "type": "array",
                                    "items": {"type": "number"},
                                },
                                "name": {"type": "string"},
                                "color": {"type": "string"},
                            },
                            "required": ["x", "y"],
                        },
                    },
                    "title": {"type": "string"},
                    "x_label": {"type": "string"},
                    "y_label": {"type": "string"},
                    "theme_preset": {
                        "type": "string",
                        "enum": IMAGE_THEME_PRESET_NAMES,
                        "default": DEFAULT_IMAGE_THEME,
                        "description": "Название базовой темы оформления",
                    },
                    "theme": {"type": "object"},
                    "format": {
                        "type": "string",
                        "enum": ["png", "svg", "base64"],
                        "default": "base64",
                    },
                    "save_to_disk": {
                        "type": "boolean",
                        "default": False,
                        "description": "Сохранять файл на диск в директорию из env OUTPUT_DIR",
                    },
                    "filename": {"type": "string", "default": "area_chart"},
                    "width": {"type": "integer"},
                    "height": {"type": "integer"},
                    "stack": {
                        "type": "boolean",
                        "default": True,
                        "description": "Складывать области",
                    },
                    "normalize": {
                        "type": "boolean",
                        "default": False,
                        "description": "Нормализовать к 100%",
                    },
                    "opacity": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 1,
                        "default": 0.6,
                    },
                },
                "required": ["data"],
            },
        ),
        types.Tool(
            name="create_combined_dashboard",
            description="Создаёт комбинированный дашборд из нескольких графиков и диаграмм "
            "на одном изображении.",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Общий заголовок дашборда"},
                    "rows": {"type": "integer", "minimum": 1, "default": 1},
                    "cols": {"type": "integer", "minimum": 1, "default": 2},
                    "shared_xaxes": {"type": "boolean", "default": False},
                    "vertical_spacing": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 1,
                        "default": 0.12,
                    },
                    "horizontal_spacing": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 1,
                        "default": 0.08,
                    },
                    "theme_preset": {
                        "type": "string",
                        "enum": IMAGE_THEME_PRESET_NAMES,
                        "default": DEFAULT_IMAGE_THEME,
                        "description": "Название базовой темы оформления",
                    },
                    "theme": {"type": "object", "description": "Тема оформления"},
                    "format": {
                        "type": "string",
                        "enum": ["png", "svg", "base64"],
                        "default": "base64",
                    },
                    "save_to_disk": {
                        "type": "boolean",
                        "default": False,
                        "description": "Сохранять файл на диск в директорию из env OUTPUT_DIR",
                    },
                    "filename": {"type": "string", "default": "combined_dashboard"},
                    "width": {"type": "integer"},
                    "height": {"type": "integer"},
                    "panels": {
                        "type": "array",
                        "description": "Массив панелей дашборда",
                        "items": {
                            "type": "object",
                            "properties": {
                                "type": {
                                    "type": "string",
                                    "enum": ["line", "bar", "pie", "scatter", "area"],
                                },
                                "row": {"type": "integer", "minimum": 1},
                                "col": {"type": "integer", "minimum": 1},
                                "title": {"type": "string"},
                                "x_label": {"type": "string"},
                                "y_label": {"type": "string"},
                                "data": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "x": {
                                                "type": "array",
                                                "items": {
                                                    "type": [
                                                        "string",
                                                        "number",
                                                        "integer",
                                                        "boolean",
                                                    ]
                                                },
                                            },
                                            "y": {
                                                "type": "array",
                                                "items": {"type": "number"},
                                            },
                                            "values": {
                                                "type": "array",
                                                "items": {"type": "number"},
                                            },
                                            "labels": {
                                                "type": "array",
                                                "items": {"type": "string"},
                                            },
                                            "name": {"type": "string"},
                                            "color": {"type": "string"},
                                            "colors": {
                                                "type": "array",
                                                "items": {"type": "string"},
                                            },
                                        },
                                    },
                                },
                                "options": {
                                    "type": "object",
                                    "description": "Опции для конкретного типа панели",
                                },
                            },
                            "required": ["type", "row", "col", "data"],
                        },
                    },
                },
                "required": ["panels"],
            },
        ),
        types.Tool(
            name="create_terminal_chart",
            description="Рисует график для консоли (ANSI с авто-fallback в монохром).",
            inputSchema={
                "type": "object",
                "properties": {
                    "type": {
                        "type": "string",
                        "enum": ["line", "bar", "scatter", "area"],
                        "description": "Тип терминального графика",
                    },
                    "data": {
                        "type": "array",
                        "description": "Серии данных",
                        "items": {
                            "type": "object",
                            "properties": {
                                "x": {
                                    "type": "array",
                                    "items": {"type": ["string", "number", "integer", "boolean"]},
                                },
                                "y": {"type": "array", "items": {"type": "number"}},
                                "name": {"type": "string"},
                            },
                            "required": ["y"],
                        },
                    },
                    "title": {"type": "string"},
                    "x_label": {"type": "string"},
                    "y_label": {"type": "string"},
                    "width": {"type": "integer", "default": 100},
                    "height": {"type": "integer", "default": 28},
                    "theme": {
                        "oneOf": [
                            {
                                "type": "string",
                                "enum": ["dark_corporate_cli", "pastel_startup_cli"],
                            },
                            {"type": "object"},
                        ]
                    },
                    "use_color": {"type": "boolean", "default": False},
                    "force_mono": {"type": "boolean", "default": False},
                    "text_mode": {
                        "type": "string",
                        "enum": ["auto", "plotext_stripped", "fallback"],
                        "default": "auto",
                        "description": (
                            "Режим текстового рендера: авто, strip ANSI из plotext, или fallback"
                        ),
                    },
                    "raw_output": {
                        "type": "boolean",
                        "default": True,
                        "description": "Вернуть только сырой текст графика без JSON-обёртки",
                    },
                },
                "required": ["type", "data"],
            },
        ),
        types.Tool(
            name="create_terminal_dashboard",
            description="Рисует текстовый дашборд для консоли из нескольких панелей.",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "width": {"type": "integer", "default": 120},
                    "height": {"type": "integer", "default": 32},
                    "theme": {
                        "oneOf": [
                            {
                                "type": "string",
                                "enum": ["dark_corporate_cli", "pastel_startup_cli"],
                            },
                            {"type": "object"},
                        ]
                    },
                    "use_color": {"type": "boolean", "default": False},
                    "force_mono": {"type": "boolean", "default": False},
                    "text_mode": {
                        "type": "string",
                        "enum": ["auto", "plotext_stripped", "fallback"],
                        "default": "auto",
                        "description": (
                            "Режим текстового рендера: авто, strip ANSI из plotext, или fallback"
                        ),
                    },
                    "raw_output": {
                        "type": "boolean",
                        "default": True,
                        "description": "Вернуть только сырой текст дашборда без JSON-обёртки",
                    },
                    "panels": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "type": {
                                    "type": "string",
                                    "enum": ["line", "bar", "scatter", "area"],
                                },
                                "title": {"type": "string"},
                                "x_label": {"type": "string"},
                                "y_label": {"type": "string"},
                                "data": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "x": {
                                                "type": "array",
                                                "items": {
                                                    "type": [
                                                        "string",
                                                        "number",
                                                        "integer",
                                                        "boolean",
                                                    ]
                                                },
                                            },
                                            "y": {"type": "array", "items": {"type": "number"}},
                                            "name": {"type": "string"},
                                        },
                                        "required": ["y"],
                                    },
                                },
                            },
                            "required": ["type", "data"],
                        },
                    },
                },
                "required": ["panels"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[types.ContentBlock]:
    """Обрабатывает вызов инструмента."""
    try:
        data = arguments.get("data", [])
        title = arguments.get("title")
        theme_arg = arguments.get("theme")
        theme_preset_arg = arguments.get("theme_preset")
        fmt: Literal["png", "svg", "base64"] = arguments.get("format", "base64")
        save_to_disk = bool(arguments.get("save_to_disk", False))
        filename = _sanitize_filename(
            arguments.get("filename"),
            f"{name.replace('create_', '')}",
        )
        width = arguments.get("width")
        height = arguments.get("height")

        if name == "list_theme_presets":
            payload = {
                "success": True,
                "defaults": {
                    "image": DEFAULT_IMAGE_THEME,
                    "terminal": DEFAULT_CLI_THEME,
                },
                "image_themes": [
                    {
                        "name": preset_name,
                        "description": IMAGE_THEME_DESCRIPTIONS.get(preset_name, ""),
                        "sample_colors": preset_data.get("colors", []),
                    }
                    for preset_name, preset_data in IMAGE_THEME_PRESETS.items()
                ],
                "terminal_themes": [
                    {
                        "name": theme_name,
                        "description": (
                            "CLI тема для терминального рендера"
                            if theme_name == "dark_corporate_cli"
                            else "CLI пастельная тема для терминального рендера"
                        ),
                        "colors": theme_data.get("colors", []),
                        "mono_symbol": theme_data.get("mono_symbol", "#"),
                    }
                    for theme_name, theme_data in CLI_THEMES.items()
                ],
            }
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(payload, ensure_ascii=False, indent=2),
                )
            ]

        if name in IMAGE_TOOL_NAMES and "output_path" in arguments:
            raise ValueError(
                "'output_path' is not supported. Use env OUTPUT_DIR and 'save_to_disk'."
            )

        theme_preset_used = DEFAULT_IMAGE_THEME
        if name in IMAGE_TOOL_NAMES:
            theme_override = theme_arg if isinstance(theme_arg, dict) else None
            if theme_arg is not None and not isinstance(theme_arg, dict):
                raise ValueError("'theme' must be an object for image chart tools")
            if theme_preset_arg is not None and not isinstance(theme_preset_arg, str):
                raise ValueError("'theme_preset' must be a string")

            theme_preset = theme_preset_arg if isinstance(theme_preset_arg, str) else None
            theme, theme_preset_used = resolve_image_theme(theme_preset, theme_override)
        else:
            theme = ChartTheme()

        chart: Any
        series: list[Any]
        figure: Any

        if name == "create_line_chart":
            x_label = arguments.get("x_label")
            y_label = arguments.get("y_label")
            line_mode = arguments.get("line_mode", "lines+markers")
            line_shape = arguments.get("line_shape", "linear")

            chart = LineChart(
                title=title,
                x_label=x_label,
                y_label=y_label,
                theme=theme,
                width=width,
                height=height,
                line_mode=line_mode,
                line_shape=line_shape,
            )
            series = parse_data_series(data)
            figure = chart.build(series, line_mode=line_mode, line_shape=line_shape)

        elif name == "create_bar_chart":
            x_label = arguments.get("x_label")
            y_label = arguments.get("y_label")
            orientation = arguments.get("orientation", "v")
            barmode = arguments.get("barmode", "group")

            chart = BarChart(
                title=title,
                x_label=x_label,
                y_label=y_label,
                theme=theme,
                width=width,
                height=height,
                orientation=orientation,
                barmode=barmode,
            )
            series = parse_data_series(data)
            figure = chart.build(series, orientation=orientation, barmode=barmode)

        elif name == "create_pie_chart":
            hole = arguments.get("hole", 0.0)
            textinfo = arguments.get("textinfo", "label+percent")

            chart = PieChart(
                title=title,
                theme=theme,
                width=width,
                height=height,
                hole=hole,
                textinfo=textinfo,
            )
            series = parse_pie_data_series(data)
            figure = chart.build(series, hole=hole, textinfo=textinfo)

        elif name == "create_scatter_chart":
            x_label = arguments.get("x_label")
            y_label = arguments.get("y_label")
            show_line = arguments.get("show_line", False)

            chart = ScatterChart(
                title=title,
                x_label=x_label,
                y_label=y_label,
                theme=theme,
                width=width,
                height=height,
                show_line=show_line,
            )
            series = parse_data_series(data)
            figure = chart.build(series, show_line=show_line)

        elif name == "create_area_chart":
            x_label = arguments.get("x_label")
            y_label = arguments.get("y_label")
            stack = arguments.get("stack", True)
            normalize = arguments.get("normalize", False)
            opacity = arguments.get("opacity", 0.6)

            chart = AreaChart(
                title=title,
                x_label=x_label,
                y_label=y_label,
                theme=theme,
                width=width,
                height=height,
                stack=stack,
                normalize=normalize,
                opacity=opacity,
            )
            series = parse_data_series(data)
            figure = chart.build(series, stack=stack, normalize=normalize, opacity=opacity)

        elif name == "create_combined_dashboard":
            panels = arguments.get("panels", [])
            rows = arguments.get("rows", 1)
            cols = arguments.get("cols", 2)
            shared_xaxes = arguments.get("shared_xaxes", False)
            vertical_spacing = arguments.get("vertical_spacing", 0.12)
            horizontal_spacing = arguments.get("horizontal_spacing", 0.08)

            if not isinstance(panels, list) or len(panels) == 0:
                raise ValueError("'panels' must be a non-empty array")

            figure = _build_combined_figure(
                panels=panels,
                rows=rows,
                cols=cols,
                theme=theme,
                title=title,
                width=width,
                height=height,
                shared_xaxes=shared_xaxes,
                vertical_spacing=vertical_spacing,
                horizontal_spacing=horizontal_spacing,
            )

        elif name == "create_terminal_chart":
            result = render_terminal_chart(
                chart_type=arguments.get("type", "line"),
                data=arguments.get("data", []),
                title=title,
                x_label=arguments.get("x_label"),
                y_label=arguments.get("y_label"),
                width=arguments.get("width", 100),
                height=arguments.get("height", 28),
                theme=theme_arg,
                use_color=arguments.get("use_color", False),
                force_mono=arguments.get("force_mono", False),
                text_mode=arguments.get("text_mode", "auto"),
            )
            if arguments.get("raw_output", True):
                return [types.TextContent(type="text", text=str(result["chart"]))]
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(result, ensure_ascii=False, indent=2),
                )
            ]

        elif name == "create_terminal_dashboard":
            result = render_terminal_dashboard(
                panels=arguments.get("panels", []),
                title=title,
                width=arguments.get("width", 120),
                height=arguments.get("height", 32),
                theme=theme_arg,
                use_color=arguments.get("use_color", False),
                force_mono=arguments.get("force_mono", False),
                text_mode=arguments.get("text_mode", "auto"),
            )
            if arguments.get("raw_output", True):
                return [types.TextContent(type="text", text=str(result["dashboard"]))]
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(result, ensure_ascii=False, indent=2),
                )
            ]

        else:
            return [types.TextContent(type="text", text=f"Неизвестный инструмент: {name}")]

        if name in IMAGE_TOOL_NAMES:
            output_dir = _resolve_output_dir()
            saved_files: list[str] = []
            format_saved: Literal["png", "svg"] | None = None

            if save_to_disk and output_dir:
                format_saved = "svg" if fmt == "svg" else "png"
                export_result = export_chart(
                    figure,
                    format=[format_saved],
                    output_dir=output_dir,
                    filename=filename,
                    width=width,
                    height=height,
                )
                saved_value = export_result.get(format_saved)
                if isinstance(saved_value, str):
                    saved_files = [str(Path(saved_value).resolve())]

            preview_uri = export_to_base64(
                figure,
                format="png",
                width=width,
                height=height,
            )
            preview_data = _strip_data_uri_prefix(preview_uri)

            if save_to_disk and output_dir is None:
                message = (
                    "save_to_disk=true, но OUTPUT_DIR не задан. "
                    "Файл не сохранён, возвращён preview."
                )
            elif save_to_disk and saved_files:
                message = f"График сохранён: {saved_files[0]}"
            elif save_to_disk:
                message = "Сохранение запрошено, но файл не был сохранён."
            else:
                message = "Возвращён preview для чата без сохранения на диск."

            response_payload = {
                "success": True,
                "saved": bool(saved_files),
                "saved_files": saved_files,
                "format_requested": fmt,
                "format_saved": format_saved,
                "theme_preset_used": theme_preset_used,
                "preview_mime_type": "image/png",
                "preview_base64": preview_uri,
                "message": message,
            }

            return [
                types.ImageContent(type="image", mimeType="image/png", data=preview_data),
                types.TextContent(
                    type="text",
                    text=json.dumps(response_payload, ensure_ascii=False, indent=2),
                ),
            ]

        return [types.TextContent(type="text", text=f"Неизвестный инструмент: {name}")]

    except Exception as e:
        return [
            types.TextContent(
                type="text",
                text=json.dumps(
                    {"success": False, "error": str(e)},
                    ensure_ascii=False,
                    indent=2,
                ),
            )
        ]


def main():
    """Точка входа MCP сервера."""
    import asyncio

    asyncio.run(run_server())


async def run_server():
    """Запускает MCP сервер."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    main()
