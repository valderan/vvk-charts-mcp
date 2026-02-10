"""MCP сервер для создания графиков и диаграмм."""

import json
from typing import Any, Literal

import mcp.server.stdio
import mcp.types as types
from mcp.server import Server

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
                                "x": {"type": "array", "description": "Значения оси X"},
                                "y": {"type": "array", "description": "Значения оси Y"},
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
                                "x": {"type": "array", "description": "Категории"},
                                "y": {"type": "array", "description": "Значения"},
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
                                "x": {"type": "array"},
                                "y": {"type": "array"},
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
                                "x": {"type": "array"},
                                "y": {"type": "array"},
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
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[types.TextContent]:
    """Обрабатывает вызов инструмента."""
    try:
        data = arguments.get("data", [])
        title = arguments.get("title")
        theme_dict = arguments.get("theme")
        fmt: Literal["png", "svg", "base64"] = arguments.get("format", "base64")
        output_path = arguments.get("output_path")
        filename = arguments.get("filename", f"{name.replace('create_', '')}")
        width = arguments.get("width")
        height = arguments.get("height")

        theme = parse_theme(theme_dict)

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
