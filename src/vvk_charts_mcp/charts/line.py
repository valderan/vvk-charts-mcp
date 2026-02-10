"""Линейный график."""

from typing import Any

import plotly.graph_objects as go

from vvk_charts_mcp.charts.base import BaseChart, DataSeries


class LineChart(BaseChart):
    """Линейный график с поддержкой множественных серий."""

    def __init__(
        self,
        title: str | None = None,
        x_label: str | None = None,
        y_label: str | None = None,
        theme: Any = None,
        width: int | None = None,
        height: int | None = None,
        line_mode: str = "lines+markers",
        line_shape: str = "linear",
        fill: str | None = None,
    ):
        """
        Инициализация линейного графика.

        Args:
            title: Заголовок графика
            x_label: Подпись оси X
            y_label: Подпись оси Y
            theme: Тема оформления
            width: Ширина графика
            height: Высота графика
            line_mode: Режим линии (lines, markers, lines+markers)
            line_shape: Форма линии (linear, spline, hv, vh, hvh, vhv)
            fill: Тип заливки (None, tozeroy, tozerox, tonexty, tonextx)
        """
        super().__init__(title, x_label, y_label, theme, width, height)
        self.line_mode = line_mode
        self.line_shape = line_shape
        self.fill = fill

    def create_figure(self, data: list[DataSeries], **kwargs: Any) -> go.Figure:
        """Создаёт фигуру линейного графика."""
        fig = go.Figure()
        line_mode = kwargs.get("line_mode", self.line_mode)
        line_shape = kwargs.get("line_shape", self.line_shape)
        fill = kwargs.get("fill", self.fill)

        for idx, series in enumerate(data):
            line_config = {"width": self.theme.line_width}
            if series.line:
                line_config.update(series.line)

            marker_config = {"size": self.theme.marker_size}
            if series.marker:
                marker_config.update(series.marker)

            fig.add_trace(
                go.Scatter(
                    x=series.x,
                    y=series.y,
                    name=series.name or f"Серия {idx + 1}",
                    mode=line_mode,
                    line=line_config
                    | {"shape": line_shape, "color": self.get_color(idx, series.color)},
                    marker=marker_config | {"color": self.get_color(idx, series.color)},
                    fill=fill,
                    text=series.text,
                    customdata=series.custom_data,
                    opacity=self.theme.opacity,
                )
            )

        return fig
