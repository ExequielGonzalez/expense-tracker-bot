# Agent Instructions (expense-tracker-bot)

This repo is a small Python Telegram bot that extracts expense data from receipt images.
It supports:
- **V3**: Ollama vision LLM (default `qwen3-vl:4b-instruct`)

There are currently **no Cursor/Copilot rule files** found in this repo (no `.cursor/rules/`, `.cursorrules`, or `.github/copilot-instructions.md`).

## Quick Commands

### Environment setup (local)
- Create venv: `python -m venv venv && source venv/bin/activate`
- Install deps:
  - `pip install -r requirements.txt`
- Env vars: `cp .env.example .env` then set `TELEGRAM_BOT_TOKEN=...`

### Run the bot
- Local: `python bot.py`
- Docker:
  - Build: `docker compose build`
  - Up: `docker compose up -d`
  - Logs: `docker logs -f expense-tracker-bot`
  - Down: `docker compose down`

### Tests
This repo does not use `pytest`/`unittest` test runners; tests are **executable scripts**.

- V3 Ollama integration tests (local):
  - Full: `python test_receipts_v3.py`
  - Quick (first 2 images): `python test_receipts_v3.py --quick`
  - Verbose (store raw model text): `python test_receipts_v3.py --verbose`

- In Docker:
  - `docker exec expense-tracker-bot python test_receipts_v3.py --quick`

### Run a “single test”
There is no per-test selection framework; use one of these patterns:
- Prefer “quick mode” for V3: `python test_receipts_v3.py --quick`
- Run analysis on a single image via helper script:
  - `python -c "from receipt_analyzer_v3 import ReceiptAnalyzerV3; print(ReceiptAnalyzerV3().analyze_receipt('data/receipts/<image>.jpg'))"`

## Linting / Formatting

No lint/format configuration is currently checked in (no `pyproject.toml`, `ruff`, `black`, `flake8`, `isort`, `pre-commit`).

Agents should:
- Keep changes minimal and consistent with existing style.
- If you want to run a formatter locally, prefer:
  - `python -m pip install ruff` then `ruff check .` / `ruff format .`
  - BUT do not add new tooling/config unless requested.

## Code Style Guidelines

### Python version / typing
- Target **Python 3.10+** style (repo uses modern type hints in V3).
- Add type hints when touching code that already uses them (notably `receipt_analyzer_v3.py`).
- Avoid introducing heavy abstractions; this repo is mostly single-file modules.

### Imports
- Follow this order (consistent with current files):
  1. Standard library
  2. Third-party
  3. Local imports
- Use one import per line when it improves readability.
- Avoid cyclic imports; analyzers should not import bot UI.

### Formatting
- Use 4 spaces, no tabs.
- Keep lines reasonably short (~100 chars); wrap long f-strings if needed.
- Prefer f-strings.

### Naming conventions
- Functions/variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Classes: `PascalCase`
- Receipt fields:
  - Use existing keys (`amount`, `date`, `title`, `category`, `*_confidence`, `overall_confidence`, `ocr_engine`).
  - Preserve the V2 output schema since `bot.py` expects it.

### Data contracts (important)
- `bot.py` expects analyzers to return dicts with keys used in the reply message.
- V3 normalizes its output to be **V2-compatible**; keep that compatibility.
- Valid categories are a fixed set and must stay in sync across:
  - `app/config.py`
  - `receipt_analyzer_v3.py` (`VALID_CATEGORIES`)

### Error handling and robustness
- Bot runtime should not crash on a single bad receipt.
- Prefer:
  - catching broad exceptions at module boundaries (Telegram handlers)
  - raising specific exceptions inside analyzers where useful
- Include helpful error messages with enough context to debug (engine/model, file path).

### Logging
- Repo currently uses `print()` with tags like `[INFO]`, `[WARN]`, `[DEBUG]`.
- Keep using that convention unless asked to refactor to `logging`.
- Don’t print secrets (Telegram token, etc.).

### IO and paths
- Receipt images are stored under `data/receipts/`.
- CSV is `data/expenses.csv`.
- Ensure directories exist before writing (`os.makedirs(..., exist_ok=True)`).

## How the app is organized
- `app/`: modular bot logic (handlers, storage, config).
- `bot.py`: entrypoint for the Telegram bot.
- `receipt_analyzer_v3.py`: Ollama vision LLM analyzer; calls local Ollama HTTP API.
- `test_receipts_v3.py`: integration tests using images in `data/receipts/`.

## V3 (Ollama) notes
- Docker compose sets:
  - `OLLAMA_BASE_URL=http://localhost:11434`
  - `OLLAMA_MODEL=qwen3-vl:4b-instruct`
  - `ANALYZER_VERSION=v3`
- V3 tests will **fail hard** if Ollama is unreachable or model missing.

## Safe changes for agents
- Keep changes scoped; don’t rename receipt keys or categories without updating all call sites.
- Avoid adding new dependencies unless explicitly requested.
- When touching tests, prefer extending existing scripts instead of introducing new frameworks.
