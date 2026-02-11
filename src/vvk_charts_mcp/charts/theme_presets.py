"""Image chart theme presets and helpers."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from vvk_charts_mcp.charts.base import ChartTheme

IMAGE_THEME_PRESETS: dict[str, dict[str, Any]] = {
    "clean_light": {
        "colors": ["#2563EB", "#0EA5E9", "#14B8A6", "#22C55E", "#F59E0B", "#EF4444"],
        "paper_bgcolor": "#FFFFFF",
        "plot_background": "#F8FAFC",
        "font_family": "Inter, -apple-system, BlinkMacSystemFont, sans-serif",
        "font_color": "#0F172A",
        "grid_color": "#CBD5E1",
        "legend_bgcolor": "rgba(255, 255, 255, 0.85)",
        "legend_border_color": "#CBD5E1",
        "title_font_size": 24,
        "label_font_size": 14,
        "tick_font_size": 12,
    },
    "dark_corporate": {
        "colors": ["#60A5FA", "#34D399", "#F472B6", "#FBBF24", "#A78BFA", "#22D3EE"],
        "paper_bgcolor": "#050F2A",
        "plot_background": "#0F1A33",
        "font_family": "Inter, -apple-system, BlinkMacSystemFont, sans-serif",
        "font_color": "#E5E7EB",
        "grid_color": "#334155",
        "legend_bgcolor": "rgba(15, 26, 51, 0.65)",
        "legend_border_color": "#334155",
        "title_font_size": 24,
        "label_font_size": 14,
        "tick_font_size": 12,
    },
    "pastel_startup": {
        "colors": ["#7DD3FC", "#86EFAC", "#F9A8D4", "#FDE68A", "#C4B5FD", "#67E8F9"],
        "paper_bgcolor": "#FFFDF8",
        "plot_background": "#FFFBEB",
        "font_family": "Inter, -apple-system, BlinkMacSystemFont, sans-serif",
        "font_color": "#1F2937",
        "grid_color": "#E5E7EB",
        "legend_bgcolor": "rgba(255, 255, 255, 0.9)",
        "legend_border_color": "#E5E7EB",
        "title_font_size": 24,
        "label_font_size": 14,
        "tick_font_size": 12,
    },
    "medical_monitor": {
        "colors": ["#22C55E", "#EF4444", "#FACC15", "#3B82F6", "#14B8A6", "#A78BFA"],
        "paper_bgcolor": "#F8FAFC",
        "plot_background": "#FFFFFF",
        "font_family": "Inter, -apple-system, BlinkMacSystemFont, sans-serif",
        "font_color": "#111827",
        "grid_color": "#D1D5DB",
        "legend_bgcolor": "rgba(255, 255, 255, 0.9)",
        "legend_border_color": "#D1D5DB",
        "title_font_size": 24,
        "label_font_size": 14,
        "tick_font_size": 12,
    },
}

IMAGE_THEME_DESCRIPTIONS: dict[str, str] = {
    "clean_light": "Светлая универсальная тема с нейтральной сеткой.",
    "dark_corporate": "Тёмная корпоративная тема для дашбордов и презентаций.",
    "pastel_startup": "Мягкая пастельная тема для продуктовых отчетов.",
    "medical_monitor": "Контрастная медицинская тема для глюкозы и метрик здоровья.",
}

DEFAULT_IMAGE_THEME = "clean_light"


def resolve_image_theme(
    theme_preset: str | None,
    theme_override: dict[str, Any] | None,
) -> tuple[ChartTheme, str]:
    """Resolve image theme from preset plus optional override dict."""
    preset_name = theme_preset or DEFAULT_IMAGE_THEME
    preset = IMAGE_THEME_PRESETS.get(preset_name)
    if preset is None:
        available = ", ".join(IMAGE_THEME_PRESETS.keys())
        raise ValueError(
            f"Unknown image theme preset '{preset_name}'. Available presets: {available}"
        )

    merged_theme: dict[str, Any] = deepcopy(preset)
    if theme_override:
        merged_theme.update(theme_override)

    return ChartTheme(**merged_theme), preset_name
