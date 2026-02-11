"""MCP сервер для создания графиков и диаграмм."""

import json
from typing import Any, Literal

import mcp.server.stdio
import mcp.types as types
import plotly.graph_objects as go
from mcp.server import Server
from plotly.subplots import make_subplots

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
from vvk_charts_mcp.terminal import render_terminal_chart, render_terminal_dashboard
from vvk_charts_mcp.utils.export import export_chart

server = Server("vvk-charts-mcp")


def parse_theme(theme_dict: dict[str, Any] | None) -> ChartTheme:
    """Парсит словарь темы в объект ChartTheme."""
    if theme_dict is None:
        return ChartTheme()
    return ChartTheme(**theme_dict)


def parse_data_series(data: list[dict[str, Any]]) -> list[DataSeries]:
    """Парсит список словарей в список DataSeries."""
    return [DataSeries(**item) for item in data]


def parse_pie_data_series(data: list[dict[str, Any]]) -> list[PieDataSeries]:
    """Парсит список словарей в список PieDataSeries."""
    return [PieDataSeries(**item) for item in data]


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
                    "theme": {"type": "object", "description": "Тема оформления (кастомизация)"},
                    "format": {
                        "type": "string",
                        "enum": ["png", "svg", "base64"],
                        "default": "base64",
                        "description": "Формат вывода",
                    },
                    "output_path": {"type": "string", "description": "Путь для сохранения файла"},
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
                    "theme": {"type": "object", "description": "Тема оформления"},
                    "format": {
                        "type": "string",
                        "enum": ["png", "svg", "base64"],
                        "default": "base64",
                    },
                    "output_path": {"type": "string", "description": "Путь для сохранения"},
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
                    "theme": {"type": "object", "description": "Тема оформления"},
                    "format": {
                        "type": "string",
                        "enum": ["png", "svg", "base64"],
                        "default": "base64",
                    },
                    "output_path": {"type": "string"},
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
                    "theme": {"type": "object"},
                    "format": {
                        "type": "string",
                        "enum": ["png", "svg", "base64"],
                        "default": "base64",
                    },
                    "output_path": {"type": "string"},
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
                    "theme": {"type": "object"},
                    "format": {
                        "type": "string",
                        "enum": ["png", "svg", "base64"],
                        "default": "base64",
                    },
                    "output_path": {"type": "string"},
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
                    "theme": {"type": "object", "description": "Тема оформления"},
                    "format": {
                        "type": "string",
                        "enum": ["png", "svg", "base64"],
                        "default": "base64",
                    },
                    "output_path": {"type": "string"},
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
                    "use_color": {"type": "boolean", "default": True},
                    "force_mono": {"type": "boolean", "default": False},
                    "raw_output": {
                        "type": "boolean",
                        "default": False,
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
                    "use_color": {"type": "boolean", "default": True},
                    "force_mono": {"type": "boolean", "default": False},
                    "raw_output": {
                        "type": "boolean",
                        "default": False,
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
async def call_tool(name: str, arguments: dict[str, Any]) -> list[types.TextContent]:
    """Обрабатывает вызов инструмента."""
    try:
        data = arguments.get("data", [])
        title = arguments.get("title")
        theme_arg = arguments.get("theme")
        fmt: Literal["png", "svg", "base64"] = arguments.get("format", "base64")
        output_path = arguments.get("output_path")
        filename = arguments.get("filename", f"{name.replace('create_', '')}")
        width = arguments.get("width")
        height = arguments.get("height")

        theme = (
            parse_theme(theme_arg)
            if isinstance(theme_arg, dict) or theme_arg is None
            else ChartTheme()
        )

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
                use_color=arguments.get("use_color", True),
                force_mono=arguments.get("force_mono", False),
            )
            if arguments.get("raw_output", False):
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
                use_color=arguments.get("use_color", True),
                force_mono=arguments.get("force_mono", False),
            )
            if arguments.get("raw_output", False):
                return [types.TextContent(type="text", text=str(result["dashboard"]))]
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(result, ensure_ascii=False, indent=2),
                )
            ]

        else:
            return [types.TextContent(type="text", text=f"Неизвестный инструмент: {name}")]

        formats: list[Literal["png", "svg", "base64"]] = [fmt] if fmt != "base64" else ["base64"]

        if output_path:
            results = export_chart(
                figure,
                format=formats,
                output_dir=output_path,
                filename=filename,
                width=width,
                height=height,
            )
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "success": True,
                            "message": f"График сохранён: {results}",
                            "files": results,
                        },
                        ensure_ascii=False,
                        indent=2,
                    ),
                )
            ]
        else:
            results = export_chart(
                figure,
                format=formats,
                filename=filename,
                width=width,
                height=height,
            )
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "success": True,
                            "data": {
                                k: v[:100] + "..." if isinstance(v, str) and len(v) > 100 else v
                                for k, v in results.items()
                            },
                            "format": fmt,
                        },
                        ensure_ascii=False,
                        indent=2,
                    ),
                )
            ]

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
