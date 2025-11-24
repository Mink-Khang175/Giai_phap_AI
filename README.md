# SaveSmart – AI Price Forecast Dashboard

SaveSmart is an end-to-end price analytics workspace that ingests marketplace time-series data, trains an LSTM-based forecaster, and serves an interactive dashboard for commercial teams. The Flask backend exposes REST APIs that power a single-page UI written in vanilla JavaScript, while optional integrations (LLM summaries, Unsplash imagery, live Tiki snapshots) enrich every product card with real-world context.

## Highlights
- Consolidates historical prices per `product_id`/platform pair and keeps derived stats (avg/max/min, sample size, ratings, stock).
- Provides an AI Forecast service that trains a lightweight PyTorch LSTM on demand and returns future price curves plus a natural-language briefing.
- Ships with an ergonomic dashboard (`Final/index.html`) that lets users pick a marketplace and SKU, inspect charts, compare platforms, and trigger predictions with a single click.
- Supports automatic product imagery via Unsplash and optional live data enrichment pulled from the public Tiki API.
- Clearly separated service layer (`services/forecast_service.py`, `services/integrations.py`) so you can reuse analytics logic outside the web application.

## Tech Stack
- **Backend:** Python 3.10+, Flask, pandas, NumPy.
- **Modeling:** PyTorch LSTM (`models/LSTM.py`), MinMaxScaler, configurable training loop.
- **Frontend:** Vanilla JS + CSS (no build step), SVG-based sparkline renderers.
- **Integrations:** Optional OpenAI (or any OpenAI-compatible) endpoint, Unsplash, Tiki API.

## Repository Layout
```
Giai_phap_AI/
├── Final/
│   ├── app.py                # Flask entry point + routing
│   ├── index.html            # Single-page dashboard
│   ├── static/               # mainstyle.css, mainjs.js
│   ├── services/             # Forecast service + integrations
│   ├── models/               # LSTM model/training utilities
│   ├── dataset/              # dataset.csv + metadata CSVs
│   └── .env.                 # Sample environment variables
└── requirements.txt          # Python dependencies
```

## Getting Started
1. **Create a virtual environment**
   ```bash
   cd Giai_phap_AI
   python3 -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   ```
2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure environment variables** – copy `Final/.env.` to `Final/.env` and fill in any required secrets (see next section).
4. **Prepare data** – place your cleaned CSV in `Final/dataset/dataset.csv` (see “Data format”).
5. **Run the server**
   ```bash
   cd Final
   python app.py  # serves http://localhost:5001
   ```
6. Open `http://localhost:5001` in a browser and start exploring.

## Environment Variables
Create `Final/.env` (or export them before running Flask).

| Variable | Required | Description |
| --- | --- | --- |
| `GEN_AI_API_KEY` | Optional (needed for AI copy) | Token for OpenAI or any OpenAI-compatible endpoint. |
| `GEN_AI_MODEL` | Optional | Defaults to `gpt-4o-mini`. Override if you prefer another chat/completions model. |
| `GEN_AI_API_URL` | Optional | Override base URL when pointing to self-hosted/OpenAI-compatible APIs. |
| `UNSPLASH_ACCESS_KEY` | Optional | Enables first-class Unsplash imagery. Without it, a generic placeholder/Source endpoint is used. |
| `ENABLE_TIKI_API` | Optional | Set to `0`/`false` to disable live Tiki enrichment. Enabled by default. |
| `TIKI_API_BASE` | Optional | Custom base URL for the Tiki API proxy. |
| `TIKI_PREFETCH_LIMIT` | Optional | Integer (default 8) controlling how many catalog images/prices to prefetch on startup. |
| `TIKI_API_USER_AGENT` | Optional | Override the default UA string for Tiki requests. |

> Tip: When `GEN_AI_API_KEY` is not set the system gracefully falls back to a rule-based summary so the dashboard remains functional offline.

## Data Format
- `Final/dataset/dataset.csv` is the master time-series table. Minimum required columns: `date`, `product_id`, `platform`, `price`. Optional but recommended columns include `original_price`, `is_promo`, `stock`, `brand`, `category`, `rating`.
- `Final/dataset/products.csv` provides metadata (`product_id`, `name`, `brand`, `category`, optional `image`). If absent, fallback metadata is used.
- `Final/dataset/platforms.csv` can list supported marketplaces via a `platform` column. Otherwise the service infers platforms directly from the dataset.

All CSVs are auto-loaded with encoding UTF-8, and the service auto-detects delimiters (`,` or `;`) and header offsets, so exporting from Excel/Numbers “just works”.

## Running the API
The Flask server exposes three routes:

| Endpoint | Method | Description |
| --- | --- | --- |
| `/api/catalog` | GET | Returns `{ platforms: [...], products: [...] }` for populating selectors. |
| `/api/metrics` | POST | Body: `{"product_id": "...", "platform": "...", "history_days": 30}`. Responds with latest price, stats, rating, historical series, and per-platform comparison. |
| `/api/predict` | POST | Body: `{"product_id": "...", "platform": "...", "future_days": 7}`. Triggers LSTM training/inference and returns `{predictions: [...], ai_summary, recommendation, expected_change_pct}`. |

All responses are JSON. Validation errors yield `400` with a message, and unexpected failures are wrapped in a friendly `500` payload.

## Frontend Workflow
1. Dashboard loads `/api/catalog` to hydrate the marketplace and product dropdowns.
2. “Phân tích ngay” posts to `/api/metrics`, which updates the product card, stats, history chart, and platform comparison grid.
3. “Xem Dự báo AI” triggers `/api/predict`; predictions render as an SVG chart and the AI summary/recommendation cards update automatically.
4. If live data is available (Tiki or AI imagery), the UI surfaces it via the “Live” badge and external link.

The frontend is dependency-free, making it easy to embed in other systems or migrate to a different UI toolkit.

## Customizing the Model
`services/forecast_service.py` instantiates `ProductAnalyticsService` with sensible defaults:

- `seq_len` (default 120): length of the sliding training window.
- `history_days` (default 30): number of days to display in the metrics card.
- `epochs`, `batch_size`, `lr`: forwarded straight to the LSTM trainer.

Tweak these parameters in `Final/app.py` or pass alternate implementations of `AIContentGenerator`, `ProductImageProvider`, or `TikiAPI` if you need different providers.

## Troubleshooting
- **“Không đủ dữ liệu …”** – reduce `seq_len` or feed longer histories per product per platform.
- **LLM errors** – ensure `GEN_AI_API_KEY` is valid; otherwise, the fallback summary is still shown.
- **Dataset parsing issues** – confirm the CSV has a `date` column and uses UTF-8 encoding; the service auto-detects delimiter but malformed headers can still fail.

## Next Steps
- Containerize the app (Flask + model runtime) for easier deployment.
- Wire up a scheduler that periodically refreshes `dataset.csv` via marketplace APIs.
- Replace the vanilla charts with Chart.js or ECharts if you need richer interactions, without changing the backend contract.

Happy forecasting! 🚀
