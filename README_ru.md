# vvk-charts-mcp

Современный MCP сервер на Python для построения графиков и диаграмм (line, bar, pie, scatter, area) с подписями, кастомизацией темы и экспортом в PNG/SVG/base64.

## Возможности

- MCP-инструменты для `line`, `bar`, `pie`, `scatter`, `area`
- Современный дизайн на базе Plotly и полная настройка темы
- Поддержка больших наборов данных и нескольких серий
- Экспорт в `png`, `svg`, `base64` (PNG + SVG)
- Интерактивный CLI-клиент для проверки с готовыми шаблонами

## Установка из GitHub (uvx)

```bash
uvx install git+https://github.com/valderan/vvk-charts-mcp.git
```

## Запуск MCP сервера

```bash
uvx run vvk-charts-mcp
```

## Запуск интерактивного клиента

```bash
uvx run vvk-charts-cli
```

Клиент интерактивно спрашивает:

- какой шаблон графика построить
- куда сохранить файлы
- в каком формате экспортировать
- размер изображения и имя файла

## AI пресеты (skill и agent)

В репозитории добавлены два готовых пресета в `ai/`:

- `ai/vvk-charts-skill.md` - skill-инструкция для формирования payload'ов MCP
- `ai/vvk-charts-agent.md` - профиль агента, специализированный на графиках

Можно использовать любой вариант, который удобнее пользователю.

## Подключение в OpenCode (подробно)

### 1) Добавить MCP сервер в OpenCode

Создайте или отредактируйте `opencode.json` (глобально или в проекте):

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "vvkcharts": {
      "type": "local",
      "enabled": true,
      "command": [
        "uvx",
        "--from",
        "git+https://github.com/valderan/vvk-charts-mcp.git",
        "vvk-charts-mcp"
      ]
    }
  }
}
```

### 2) Установка как OpenCode skill

По спецификации OpenCode skill должен лежать в `.opencode/skills/<name>/SKILL.md`, а `name` должен совпадать с именем директории.

```bash
mkdir -p .opencode/skills/vvk-charts-mcp
cp ai/vvk-charts-skill.md .opencode/skills/vvk-charts-mcp/SKILL.md
```

Как использовать:
- ставьте задачи по визуализации и при необходимости указывайте использовать `vvkcharts` tools;
- модель сможет загрузить skill через встроенный инструмент `skill`.

### 3) Установка как OpenCode agent

```bash
mkdir -p .opencode/agents
cp ai/vvk-charts-agent.md .opencode/agents/vvk-charts.md
```

Как использовать:
- в чате вызывайте `@vvk-charts ...`;
- либо переключитесь на агента `vvk-charts` в интерфейсе OpenCode.

### 4) Проверка в OpenCode

- Запустите `opencode` в проекте.
- Убедитесь, что инструменты `vvkcharts_*` доступны.
- Тестовый запрос:
  - `Build a monthly revenue line chart and save as png in ./output using vvkcharts`.

## Подключение в Codex (подробно)

Окружения Codex могут отличаться в зависимости от клиента. Используйте эту схему в Codex-совместимых клиентах с поддержкой MCP.

### 1) Зарегистрировать MCP сервер

Команда запуска MCP:

```bash
uvx --from git+https://github.com/valderan/vvk-charts-mcp.git vvk-charts-mcp
```

Если клиент использует JSON-конфиг (частый формат), блок обычно выглядит так:

```json
{
  "mcpServers": {
    "vvkcharts": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/valderan/vvk-charts-mcp.git",
        "vvk-charts-mcp"
      ]
    }
  }
}
```

### 2) Использовать skill-файл в инструкциях Codex

В Codex обычно нет автозагрузки `SKILL.md` как в OpenCode, поэтому `ai/vvk-charts-skill.md` используйте как шаблон:
- вставьте содержимое в project/system instructions, или
- храните как отдельный промпт-пресет и подключайте при задачах по графикам.

### 3) Использовать agent-файл как профиль Codex

`ai/vvk-charts-agent.md` можно использовать как системный промпт отдельного профиля:
- создайте профиль/пресет в клиенте Codex,
- вставьте содержимое файла,
- выбирайте этот профиль для задач визуализации.

### 4) Проверка в Codex

- Отправьте запрос с явным использованием MCP, например:
  - `Use vvkcharts tools to generate a bar chart and save it to ./output/sales-q1.png`.
- Проверьте, что файл создан и соответствует формату.

## MCP tools

- `create_line_chart`
- `create_bar_chart`
- `create_pie_chart`
- `create_scatter_chart`
- `create_area_chart`
- `create_combined_dashboard` (несколько типов графиков на одном изображении)

Все инструменты поддерживают:

- кастомную `theme`
- `title`
- `width` / `height`
- формат `format`
- путь сохранения `output_path`

### Комбинированные дашборды

Используйте `create_combined_dashboard`, чтобы строить несколько панелей в одном изображении (например line + bar или line + pie).

Минимальный пример payload:

```json
{
  "title": "Marketing Dashboard",
  "rows": 1,
  "cols": 2,
  "format": "png",
  "output_path": "./demo",
  "filename": "combined_dashboard",
  "panels": [
    {
      "type": "line",
      "row": 1,
      "col": 1,
      "title": "Revenue Trend",
      "x_label": "Month",
      "y_label": "k USD",
      "data": [
        {
          "name": "Revenue",
          "x": ["Jan", "Feb", "Mar", "Apr"],
          "y": [120, 132, 148, 160]
        }
      ],
      "options": {
        "line_shape": "spline"
      }
    },
    {
      "type": "pie",
      "row": 1,
      "col": 2,
      "title": "Budget Split",
      "data": [
        {
          "labels": ["Search", "Social", "Email"],
          "values": [45, 35, 20]
        }
      ],
      "options": {
        "hole": 0.45
      }
    }
  ]
}
```

## Локальная разработка

```bash
uv sync
uv run ruff check .
```

## Репозиторий

- https://github.com/valderan/vvk-charts-mcp
