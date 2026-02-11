"""Terminal theme presets and color helpers."""

from __future__ import annotations

from typing import Any

CLI_THEMES: dict[str, dict[str, Any]] = {
    "dark_corporate_cli": {
        "name": "dark_corporate_cli",
        "colors": ["blue", "green", "yellow", "magenta", "cyan", "white"],
        "mono_symbol": "#",
    },
    "pastel_startup_cli": {
        "name": "pastel_startup_cli",
        "colors": ["cyan", "magenta", "yellow", "green", "blue", "white"],
        "mono_symbol": "*",
    },
}

DEFAULT_CLI_THEME = "dark_corporate_cli"


def resolve_cli_theme(theme: str | dict[str, Any] | None) -> dict[str, Any]:
    """Resolve CLI theme name or custom dict to final theme."""
    if theme is None:
        return CLI_THEMES[DEFAULT_CLI_THEME]

    if isinstance(theme, str):
        return CLI_THEMES.get(theme, CLI_THEMES[DEFAULT_CLI_THEME])

    colors = theme.get("colors")
    if not isinstance(colors, list) or not colors:
        colors = CLI_THEMES[DEFAULT_CLI_THEME]["colors"]

    mono_symbol = str(theme.get("mono_symbol", "#"))[:1] or "#"
    return {
        "name": str(theme.get("name", "custom_cli_theme")),
        "colors": [str(c) for c in colors],
        "mono_symbol": mono_symbol,
    }
