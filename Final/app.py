from __future__ import annotations

import sys
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

if load_dotenv:
    load_dotenv(dotenv_path=BASE_DIR / ".env")

from services.forecast_service import ProductAnalyticsService 

app = Flask(__name__, static_folder=str(BASE_DIR / "static"), template_folder=str(BASE_DIR))


service = ProductAnalyticsService(
    BASE_DIR / "dataset" / "dataset.csv",
    products_path=BASE_DIR / "dataset" / "products.csv",
    platforms_path=BASE_DIR / "dataset" / "platforms.csv",
)


@app.route("/")
def index() -> object:
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/api/catalog", methods=["GET"])
def catalog() -> object:
    data = service.get_catalog()
    return jsonify(data)


@app.route("/api/metrics", methods=["POST"])
def metrics() -> object:
    payload = request.get_json(force=True) or {}
    product_id = payload.get("product_id")
    platform = payload.get("platform")
    history_days = payload.get("history_days")
    if not product_id or not platform:
        return jsonify({"message": "Thiếu product_id hoặc platform."}), 400

    data = service.get_metrics(
        product_id=product_id,
        platform=platform,
        history_days=int(history_days) if history_days else None,
    )
    return jsonify(data)


@app.route("/api/predict", methods=["POST"])
def predict() -> object:
    payload = request.get_json(force=True) or {}
    product_id = payload.get("product_id")
    platform = payload.get("platform")
    future_days = int(payload.get("future_days", 7))
    if not product_id or not platform:
        return jsonify({"message": "Thiếu product_id hoặc platform."}), 400

    data = service.get_prediction(product_id=product_id, platform=platform, future_days=future_days)
    return jsonify(data)


@app.errorhandler(ValueError)
def handle_value_error(error: ValueError) -> object:
    return jsonify({"message": str(error)}), 400


@app.errorhandler(Exception)
def handle_exception(error: Exception) -> object:
    return jsonify({"message": "Đã xảy ra lỗi ngoài ý muốn.", "detail": str(error)}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)

