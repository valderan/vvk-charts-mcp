"""Area chart (диаграмма с областями)."""

from typing import Any

import plotly.graph_objects as go

from vvk_charts_mcp.charts.base import BaseChart, DataSeries


class AreaChart(BaseChart):
    """Диаграмма с областями с поддержкой стекинга."""

    def __init__(
        self,
        title: str | None = None,
        x_label: str | None = None,
        y_label: str | None = None,
        theme: Any = None,
        width: int | None = None,
        height: int | None = None,
        stack: bool = True,
        normalize: bool = False,
        show_markers: bool = False,
        opacity: float = 0.6,
    ):
        """
        Инициализация area chart.

        Args:
            title: Заголовок графика
            x_label: Подпись оси X
            y_label: Подпись оси Y
            theme: Тема оформления
            width: Ширина графика
            height: Высота графика
            stack: Складывать области друг на друга
            normalize: Нормализовать к 100% (только при stack=True)
            show_markers: Показывать маркеры точек
            opacity: Прозрачность заливки (0-1)
        """
        super().__init__(title, x_label, y_label, theme, width, height)
        self.stack = stack
        self.normalize = normalize
        self.show_markers = show_markers
        self.area_opacity = opacity

    def create_figure(self, data: list[DataSeries], **kwargs: Any) -> go.Figure:
        """Создаёт фигуру area chart."""
        fig = go.Figure()
        stack = kwargs.get("stack", self.stack)
        normalize = kwargs.get("normalize", self.normalize)
        show_markers = kwargs.get("show_markers", self.show_markers)
        opacity = kwargs.get("opacity", self.area_opacity)

        mode = "lines+markers" if show_markers else "lines"

        for idx, series in enumerate(data):
            color = self.get_color(idx, series.color)

            if idx == 0:
                fill = "tozeroy"
            elif stack:
                fill = "tonexty"
            else:
                fill = "tozeroy"

            line_config = {"width": self.theme.line_width, "color": color, "shape": "linear"}
            if series.line:
                line_config.update(series.line)

            marker_config = {"size": self.theme.marker_size, "color": color}
            if series.marker:
                marker_config.update(series.marker)

            fig.add_trace(
                go.Scatter(
                    x=series.x,
                    y=series.y,
                    name=series.name or f"Серия {idx + 1}",
                    mode=mode,
                    fill=fill,
                    line=line_config,
                    marker=marker_config,
                    text=series.text,
                    customdata=series.custom_data,
                    opacity=opacity,
                    fillcolor=color,
                )
            )

        if normalize and stack:
            fig.update_layout(yaxis_tickformat=".0%")

        return fig
