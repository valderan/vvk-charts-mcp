"""Круговая диаграмма."""

from typing import Any

import plotly.graph_objects as go

from vvk_charts_mcp.charts.base import BaseChart, PieDataSeries


class PieChart(BaseChart):
    """Круговая диаграмма с поддержкой doughnut и вырезанных секторов."""

    def __init__(
        self,
        title: str | None = None,
        theme: Any = None,
        width: int | None = None,
        height: int | None = None,
        hole: float = 0.0,
        textinfo: str = "label+percent",
        textposition: str = "auto",
        showlegend: bool = True,
        sort: bool = False,
    ):
        """
        Инициализация круговой диаграммы.

        Args:
            title: Заголовок графика
            theme: Тема оформления
            width: Ширина графика
            height: Высота графика
            hole: Размер отверстия в центре (0-1, 0 = обычный pie, >0 = doughnut)
            textinfo: Информация на секторах (label, text, value, percent)
            textposition: Позиция текста (inside, outside, auto, none)
            showlegend: Показывать легенду
            sort: Сортировать сектора по значению
        """
        super().__init__(title, None, None, theme, width, height)
        self.hole = hole
        self.textinfo = textinfo
        self.textposition = textposition
        self._showlegend = showlegend
        self.sort = sort

    def create_figure(self, data: list[PieDataSeries], **kwargs: Any) -> go.Figure:
        """Создаёт фигуру круговой диаграммы."""
        fig = go.Figure()

        if len(data) == 1:
            series = data[0]
            colors = series.colors if series.colors else self.theme.colors[: len(series.values)]

            fig.add_trace(
                go.Pie(
                    values=series.values,
                    labels=series.labels,
                    name=series.name,
                    hole=kwargs.get("hole", self.hole),
                    textinfo=series.textinfo or kwargs.get("textinfo", self.textinfo),
                    textposition=kwargs.get("textposition", self.textposition),
                    textfont={
                        "family": self.theme.font_family,
                        "size": self.theme.tick_font_size,
                        "color": self.theme.font_color,
                    },
                    marker={
                        "colors": colors,
                        "line": {"color": self.theme.background, "width": 2},
                    },
                    sort=kwargs.get("sort", self.sort),
                    hovertemplate=series.hovertemplate
                    or "%{label}: %{value} (%{percent})<extra></extra>",
                )
            )
        else:
            cols = min(len(data), 2)
            rows = (len(data) + 1) // 2

            from plotly.subplots import make_subplots

            fig = make_subplots(
                rows=rows,
                cols=cols,
                specs=[[{"type": "domain"}] * cols for _ in range(rows)],
                subplot_titles=[s.name or f"Диаграмма {i + 1}" for i, s in enumerate(data)],
            )

            for idx, series in enumerate(data):
                row = idx // cols + 1
                col = idx % cols + 1
                colors = series.colors if series.colors else self.theme.colors[: len(series.values)]

                fig.add_trace(
                    go.Pie(
                        values=series.values,
                        labels=series.labels,
                        name=series.name or f"Диаграмма {idx + 1}",
                        hole=kwargs.get("hole", self.hole),
                        textinfo=series.textinfo or kwargs.get("textinfo", self.textinfo),
                        textposition=kwargs.get("textposition", self.textposition),
                        textfont={
                            "family": self.theme.font_family,
                            "size": self.theme.tick_font_size,
                            "color": self.theme.font_color,
                        },
                        marker={
                            "colors": colors,
                            "line": {"color": self.theme.background, "width": 2},
                        },
                        sort=kwargs.get("sort", self.sort),
                        hovertemplate=series.hovertemplate
                        or "%{label}: %{value} (%{percent})<extra></extra>",
                    ),
                    row=row,
                    col=col,
                )

        return fig

    def apply_theme(self, figure: go.Figure) -> go.Figure:
        """Применяет тему к фигуре круговой диаграммы."""
        layout_updates: dict[str, Any] = {
            "title": {
                "text": self.title,
                "font": {
                    "family": self.theme.font_family,
                    "size": self.theme.title_font_size,
                    "color": self.theme.font_color,
                },
                "x": 0.5,
                "xanchor": "center",
            }
            if self.title
            else None,
            "font": {
                "family": self.theme.font_family,
                "color": self.theme.font_color,
            },
            "paper_bgcolor": self.theme.paper_bgcolor,
            "showlegend": self._showlegend,
            "legend": self.theme.get_legend_settings() if self._showlegend else {},
        }

        if self.width:
            layout_updates["width"] = self.width
        if self.height:
            layout_updates["height"] = self.height

        figure.update_layout(**layout_updates)
        return figure
