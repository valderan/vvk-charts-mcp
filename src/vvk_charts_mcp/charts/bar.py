"""Столбчатая диаграмма."""

from typing import Any, Literal

import plotly.graph_objects as go

from vvk_charts_mcp.charts.base import BaseChart, DataSeries


class BarChart(BaseChart):
    """Столбчатая диаграмма с поддержкой группировки и стекинга."""

    def __init__(
        self,
        title: str | None = None,
        x_label: str | None = None,
        y_label: str | None = None,
        theme: Any = None,
        width: int | None = None,
        height: int | None = None,
        orientation: Literal["v", "h"] = "v",
        barmode: Literal["group", "stack", "relative", "overlay"] = "group",
        bargap: float = 0.2,
        bargroupgap: float = 0.1,
    ):
        """
        Инициализация столбчатой диаграммы.

        Args:
            title: Заголовок графика
            x_label: Подпись оси X
            y_label: Подпись оси Y
            theme: Тема оформления
            width: Ширина графика
            height: Высота графика
            orientation: Ориентация (v - вертикальная, h - горизонтальная)
            barmode: Режим отображения (group, stack, relative, overlay)
            bargap: Промежуток между столбцами (0-1)
            bargroupgap: Промежуток между группами столбцов (0-1)
        """
        super().__init__(title, x_label, y_label, theme, width, height)
        self.orientation = orientation
        self.barmode = barmode
        self.bargap = bargap
        self.bargroupgap = bargroupgap

    def create_figure(self, data: list[DataSeries], **kwargs: Any) -> go.Figure:
        """Создаёт фигуру столбчатой диаграммы."""
        fig = go.Figure()
        orientation = kwargs.get("orientation", self.orientation)

        for idx, series in enumerate(data):
            marker_config = {
                "color": self.get_color(idx, series.color),
                "opacity": self.theme.opacity,
            }
            if series.marker:
                marker_config.update(series.marker)

            if orientation == "v":
                fig.add_trace(
                    go.Bar(
                        x=series.x,
                        y=series.y,
                        name=series.name or f"Серия {idx + 1}",
                        marker=marker_config,
                        text=series.text,
                        customdata=series.custom_data,
                        orientation="v",
                    )
                )
            else:
                fig.add_trace(
                    go.Bar(
                        x=series.y,
                        y=series.x,
                        name=series.name or f"Серия {idx + 1}",
                        marker=marker_config,
                        text=series.text,
                        customdata=series.custom_data,
                        orientation="h",
                    )
                )

        fig.update_layout(
            barmode=kwargs.get("barmode", self.barmode),
            bargap=kwargs.get("bargap", self.bargap),
            bargroupgap=kwargs.get("bargroupgap", self.bargroupgap),
        )

        return fig

    def apply_theme(self, figure: go.Figure) -> go.Figure:
        """Применяет тему к фигуре с учётом ориентации."""
        figure = super().apply_theme(figure)

        if self.orientation == "h":
            current_xaxis = figure.layout.xaxis.to_plotly_json() if figure.layout.xaxis else {}
            current_yaxis = figure.layout.yaxis.to_plotly_json() if figure.layout.yaxis else {}
            figure.update_layout(
                xaxis={**current_xaxis, "title_text": self.y_label},
                yaxis={**current_yaxis, "title_text": self.x_label},
            )

        return figure
