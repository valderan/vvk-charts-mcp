"""Утилиты для экспорта графиков в различные форматы."""

import base64
from pathlib import Path
from typing import Literal, cast

import plotly.graph_objects as go

ExportFormat = Literal["png", "svg", "base64"]


def export_to_png(
    figure: go.Figure,
    output_path: str | Path | None = None,
    width: int | None = None,
    height: int | None = None,
    scale: float = 2.0,
) -> bytes | None:
    """
    Экспортирует график в PNG.

    Args:
        figure: Фигура Plotly
        output_path: Путь для сохранения файла (опционально)
        width: Ширина изображения в пикселях
        height: Высота изображения в пикселях
        scale: Масштаб для увеличения разрешения

    Returns:
        Байты изображения если output_path не указан, иначе None
    """
    figure_width = cast(int | None, getattr(figure.layout, "width", None))
    figure_height = cast(int | None, getattr(figure.layout, "height", None))

    img_bytes = cast(
        bytes,
        figure.to_image(
            format="png",
            width=width or figure_width or 1200,
            height=height or figure_height or 800,
            scale=scale,
            engine="kaleido",
        ),
    )

    if output_path:
        Path(output_path).write_bytes(img_bytes)
        return None

    return img_bytes


def export_to_svg(
    figure: go.Figure,
    output_path: str | Path | None = None,
    width: int | None = None,
    height: int | None = None,
) -> str | None:
    """
    Экспортирует график в SVG.

    Args:
        figure: Фигура Plotly
        output_path: Путь для сохранения файла (опционально)
        width: Ширина изображения в пикселях
        height: Высота изображения в пикселях

    Returns:
        SVG строка если output_path не указан, иначе None
    """
    figure_width = cast(int | None, getattr(figure.layout, "width", None))
    figure_height = cast(int | None, getattr(figure.layout, "height", None))

    svg_str = cast(
        bytes,
        figure.to_image(
            format="svg",
            width=width or figure_width or 1200,
            height=height or figure_height or 800,
            engine="kaleido",
        ),
    ).decode("utf-8")

    if output_path:
        Path(output_path).write_text(svg_str, encoding="utf-8")
        return None

    return svg_str


def export_to_base64(
    figure: go.Figure,
    format: Literal["png", "svg"] = "png",
    width: int | None = None,
    height: int | None = None,
    scale: float = 2.0,
) -> str:
    """
    Экспортирует график в base64 строку.

    Args:
        figure: Фигура Plotly
        format: Формат изображения (png или svg)
        width: Ширина изображения в пикселях
        height: Высота изображения в пикселях
        scale: Масштаб для увеличения разрешения (только для PNG)

    Returns:
        Base64 закодированная строка с data URI префиксом
    """
    if format == "png":
        img_bytes = export_to_png(figure, width=width, height=height, scale=scale)
        if img_bytes is None:
            raise ValueError("Failed to export PNG")
        b64_str = base64.b64encode(img_bytes).decode("utf-8")
        return f"data:image/png;base64,{b64_str}"
    else:
        svg_str = export_to_svg(figure, width=width, height=height)
        if svg_str is None:
            raise ValueError("Failed to export SVG")
        b64_str = base64.b64encode(svg_str.encode("utf-8")).decode("utf-8")
        return f"data:image/svg+xml;base64,{b64_str}"


def export_chart(
    figure: go.Figure,
    format: ExportFormat | list[ExportFormat],
    output_dir: str | Path | None = None,
    filename: str = "chart",
    width: int | None = None,
    height: int | None = None,
    scale: float = 2.0,
) -> dict[str, str | bytes | None]:
    """
    Экспортирует график в указанные форматы.

    Args:
        figure: Фигура Plotly
        format: Формат или список форматов для экспорта
        output_dir: Директория для сохранения файлов
        filename: Имя файла без расширения
        width: Ширина изображения
        height: Высота изображения
        scale: Масштаб для PNG

    Returns:
        Словарь с результатами экспорта:
        - "png": путь к файлу или байты
        - "svg": путь к файлу или строка SVG
        - "base64_png": base64 строка PNG
        - "base64_svg": base64 строка SVG
    """
    formats = [format] if isinstance(format, str) else format
    results: dict[str, str | bytes | None] = {}

    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

    for fmt in formats:
        if fmt == "png":
            if output_dir:
                path = output_dir / f"{filename}.png"
                export_to_png(figure, path, width, height, scale)
                results["png"] = str(path)
            else:
                results["png"] = export_to_png(figure, None, width, height, scale)

        elif fmt == "svg":
            if output_dir:
                path = output_dir / f"{filename}.svg"
                export_to_svg(figure, path, width, height)
                results["svg"] = str(path)
            else:
                results["svg"] = export_to_svg(figure, None, width, height)

        elif fmt == "base64":
            results["base64_png"] = export_to_base64(figure, "png", width, height, scale)
            results["base64_svg"] = export_to_base64(figure, "svg", width, height)

    return results
