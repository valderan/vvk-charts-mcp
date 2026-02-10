"""Базовый класс для графиков и тема оформления."""

from abc import ABC, abstractmethod
from typing import Any

import plotly.graph_objects as go
from pydantic import BaseModel, Field


class ChartTheme(BaseModel):
    """Тема оформления графика с полной кастомизацией."""

    colors: list[str] = Field(
        default=[
            "#6366F1",
            "#8B5CF6",
            "#EC4899",
            "#F43F5E",
            "#F97316",
            "#EAB308",
            "#22C55E",
            "#14B8A6",
            "#06B6D4",
            "#3B82F6",
            "#6366F1",
            "#8B5CF6",
        ],
        description="Список цветов для серий данных",
    )
    background: str = Field(
        default="#FFFFFF",
        description="Цвет фона графика",
    )
    plot_background: str = Field(
        default="#FAFAFA",
        description="Цвет фонa области построения",
    )
    font_family: str = Field(
        default="Inter, -apple-system, BlinkMacSystemFont, sans-serif",
        description="Семейство шрифтов",
    )
    font_color: str = Field(
        default="#1F2937",
        description="Цвет текста",
    )
    title_font_size: int = Field(
        default=22,
        description="Размер шрифта заголовка",
    )
    label_font_size: int = Field(
        default=14,
        description="Размер шрифта подписей",
    )
    tick_font_size: int = Field(
        default=12,
        description="Размер шрифта делений",
    )
    grid_color: str = Field(
        default="#E5E7EB",
        description="Цвет сетки",
    )
    grid_width: int = Field(
        default=1,
        description="Толщина линий сетки",
    )
    show_grid: bool = Field(
        default=True,
        description="Показывать сетку",
    )
    show_legend: bool = Field(
        default=True,
        description="Показывать легенду",
    )
    legend_position: str = Field(
        default="top",
        description="Позиция легенды: top, bottom, left, right",
    )
    legend_bgcolor: str = Field(
        default="rgba(255, 255, 255, 0.8)",
        description="Цвет фона легенды",
    )
    legend_border_color: str = Field(
        default="#E5E7EB",
        description="Цвет границы легенды",
    )
    margin: dict[str, int] = Field(
        default={"l": 60, "r": 30, "t": 60, "b": 60},
        description="Отступы графика",
    )
    paper_bgcolor: str = Field(
        default="#FFFFFF",
        description="Цвет фона всей фигуры",
    )
    line_width: int = Field(
        default=2,
        description="Толщина линий по умолчанию",
    )
    marker_size: int = Field(
        default=8,
        description="Размер маркеров по умолчанию",
    )
    opacity: float = Field(
        default=1.0,
        description="Прозрачность элементов",
    )

    def get_legend_settings(self) -> dict[str, Any]:
        """Возвращает настройки легенды для Plotly."""
        position_map = {
            "top": {"x": 0.5, "y": 1.0, "xanchor": "center", "yanchor": "bottom"},
            "bottom": {"x": 0.5, "y": 0.0, "xanchor": "center", "yanchor": "top"},
            "left": {"x": 0.0, "y": 0.5, "xanchor": "left", "yanchor": "middle"},
            "right": {"x": 1.0, "y": 0.5, "xanchor": "right", "yanchor": "middle"},
        }
        orientation = "h" if self.legend_position in ["top", "bottom"] else "v"
        return {
            "orientation": orientation,
            "bgcolor": self.legend_bgcolor,
            "bordercolor": self.legend_border_color,
            "borderwidth": 1,
            "font": {"family": self.font_family, "size": self.tick_font_size},
            **position_map.get(self.legend_position, position_map["top"]),
        }

    def get_grid_settings(self, axis: str = "both") -> dict[str, Any]:
        """Возвращает настройки сетки для осей."""
        settings = {
            "showgrid": self.show_grid,
            "gridcolor": self.grid_color,
            "gridwidth": self.grid_width,
            "linecolor": self.grid_color,
            "linewidth": 1,
        }
        return settings


class DataSeries(BaseModel):
    """Серия данных для графика."""

    x: list[Any] = Field(..., description="Значения по оси X")
    y: list[Any] = Field(..., description="Значения по оси Y")
    name: str | None = Field(default=None, description="Название серии")
    color: str | None = Field(default=None, description="Цвет серии")
    marker: dict[str, Any] | None = Field(default=None, description="Настройки маркера")
    line: dict[str, Any] | None = Field(default=None, description="Настройки линии")
    text: list[str] | None = Field(default=None, description="Текстовые метки")
    custom_data: list[Any] | None = Field(default=None, description="Дополнительные данные")


class BaseChart(ABC):
    """Базовый класс для всех типов графиков."""

    def __init__(
        self,
        title: str | None = None,
        x_label: str | None = None,
        y_label: str | None = None,
        theme: ChartTheme | None = None,
        width: int | None = None,
        height: int | None = None,
    ):
        self.title = title
        self.x_label = x_label
        self.y_label = y_label
        self.theme = theme or ChartTheme()
        self.width = width
        self.height = height
        self._figure: go.Figure | None = None

    @abstractmethod
    def create_figure(self, data: list[Any], **kwargs: Any) -> go.Figure:
        """Создаёт фигуру Plotly. Должен быть реализован в наследниках."""
        pass

    def apply_theme(self, figure: go.Figure) -> go.Figure:
        """Применяет тему к фигуре."""
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
            "plot_bgcolor": self.theme.plot_background,
            "margin": self.theme.margin,
            "showlegend": self.theme.show_legend,
            "legend": self.theme.get_legend_settings() if self.theme.show_legend else {},
        }

        if self.width:
            layout_updates["width"] = self.width
        if self.height:
            layout_updates["height"] = self.height

        axis_settings = {
            "title": {
                "font": {
                    "family": self.theme.font_family,
                    "size": self.theme.label_font_size,
                    "color": self.theme.font_color,
                },
            },
            "tickfont": {
                "family": self.theme.font_family,
                "size": self.theme.tick_font_size,
                "color": self.theme.font_color,
            },
            **self.theme.get_grid_settings(),
        }

        layout_updates["xaxis"] = {
            **axis_settings,
            "title_text": self.x_label,
        }
        layout_updates["yaxis"] = {
            **axis_settings,
            "title_text": self.y_label,
        }

        figure.update_layout(**layout_updates)
        return figure

    def get_color(self, index: int, custom_color: str | None = None) -> str:
        """Возвращает цвет для серии по индексу или кастомный."""
        if custom_color:
            return custom_color
        colors = self.theme.colors
        return colors[index % len(colors)]

    def build(self, data: list[Any], **kwargs: Any) -> go.Figure:
        """Строит график с применением темы."""
        self._figure = self.create_figure(data, **kwargs)
        self._figure = self.apply_theme(self._figure)
        return self._figure

    def get_figure(self) -> go.Figure | None:
        """Возвращает текущую фигуру."""
        return self._figure


class PieDataSeries(BaseModel):
    """Данные для круговой диаграммы."""

    values: list[float] = Field(..., description="Значения для секторов")
    labels: list[str] = Field(..., description="Метки для секторов")
    name: str | None = Field(default=None, description="Название серии")
    colors: list[str] | None = Field(default=None, description="Цвета секторов")
    textinfo: str | None = Field(default="label+percent", description="Информация на секторе")
    hovertemplate: str | None = Field(default=None, description="Шаблон всплывающей подсказки")
