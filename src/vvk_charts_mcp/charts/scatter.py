"""Точечный график."""

from typing import Any

import plotly.graph_objects as go

from vvk_charts_mcp.charts.base import BaseChart, DataSeries


class ScatterChart(BaseChart):
    """Точечный график с поддержкой пузырьковых диаграмм."""

    def __init__(
        self,
        title: str | None = None,
        x_label: str | None = None,
        y_label: str | None = None,
        theme: Any = None,
        width: int | None = None,
        height: int | None = None,
        marker_mode: bool = True,
        show_line: bool = False,
    ):
        """
        Инициализация точечного графика.

        Args:
            title: Заголовок графика
            x_label: Подпись оси X
            y_label: Подпись оси Y
            theme: Тема оформления
            width: Ширина графика
            height: Высота графика
            marker_mode: Показывать только маркеры
            show_line: Показывать линии между точками
        """
        super().__init__(title, x_label, y_label, theme, width, height)
        self.marker_mode = marker_mode
        self.show_line = show_line

    def create_figure(self, data: list[DataSeries], **kwargs: Any) -> go.Figure:
        """Создаёт фигуру точечного графика."""
        fig = go.Figure()
        show_line = kwargs.get("show_line", self.show_line)
        mode = "markers+lines" if show_line else "markers"

        for idx, series in enumerate(data):
            marker_config = {
                "size": self.theme.marker_size,
                "color": self.get_color(idx, series.color),
                "opacity": self.theme.opacity,
            }

            if series.marker:
                if "size" in series.marker and isinstance(series.marker["size"], list):
                    marker_config["sizemode"] = "diameter"
                    marker_config["sizeref"] = (
                        max(series.marker["size"]) / 50 if series.marker["size"] else 1
                    )
                marker_config.update(series.marker)

            line_config = None
            if show_line:
                line_config = {
                    "width": self.theme.line_width,
                    "color": self.get_color(idx, series.color),
                }
                if series.line:
                    line_config.update(series.line)

            fig.add_trace(
                go.Scatter(
                    x=series.x,
                    y=series.y,
                    name=series.name or f"Серия {idx + 1}",
                    mode=mode,
                    marker=marker_config,
                    line=line_config,
                    text=series.text,
                    customdata=series.custom_data,
                )
            )

        return fig
