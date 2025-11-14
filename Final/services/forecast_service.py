from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("KMP_INIT_AT_FORK", "FALSE")

import numpy as np
import pandas as pd

from models.LSTM import ForecastConfig, train_and_predict
from services.integrations import AIContentGenerator, ProductImageProvider

"""
Service xử lý dữ liệu + AI cho hệ thống dự báo giá.

Biến môi trường liên quan:
- GEN_AI_API_KEY: bật mô tả/khuyến nghị từ model ngoài (ví dụ OpenAI).
- GEN_AI_MODEL, GEN_AI_API_URL: tùy chọn override model hoặc endpoint.
- UNSPLASH_ACCESS_KEY: nếu có sẽ dùng API Unsplash chính thức để lấy ảnh sản phẩm.
"""

DEFAULT_IMAGE = "https://dummyimage.com/300x300/1f2937/ffffff&text=AI"

PRODUCT_METADATA: Dict[str, Dict[str, str]] = {
    "iphone14": {
        "name": "iPhone 14 128GB",
        "image": "https://images.unsplash.com/photo-1661961110671-77b529b5a091?auto=format&fit=crop&w=400&q=60",
    },
    "iphone15": {
        "name": "iPhone 15 128GB",
        "image": "https://images.unsplash.com/photo-1695048133142-919945489c86?auto=format&fit=crop&w=400&q=60",
    },
    "iphone15promax": {
        "name": "iPhone 15 Pro Max 256GB",
        "image": "https://images.unsplash.com/photo-1695048133975-9ec21f84f5a3?auto=format&fit=crop&w=400&q=60",
    },
    "ipadpro11": {
        "name": "iPad Pro 11\"",
        "image": "https://images.unsplash.com/photo-1510552776732-05b39eca7f00?auto=format&fit=crop&w=400&q=60",
    },
    "airpodspro2": {
        "name": "AirPods Pro 2",
        "image": "https://images.unsplash.com/photo-1585386959984-a4155224a1ad?auto=format&fit=crop&w=400&q=60",
    },
    "macbookairm2": {
        "name": "MacBook Air M2",
        "image": "https://images.unsplash.com/photo-1502877338535-766e1452684a?auto=format&fit=crop&w=400&q=60",
    },
    "macbookpro14": {
        "name": "MacBook Pro 14\"",
        "image": "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?auto=format&fit=crop&w=400&q=60",
    },
    "dellxps13": {
        "name": "Dell XPS 13",
        "image": "https://images.unsplash.com/photo-1517436073-3b1d8f2e0d19?auto=format&fit=crop&w=400&q=60",
    },
    "sonyWH1000XM5": {
        "name": "Sony WH-1000XM5",
        "image": "https://images.unsplash.com/photo-1484704849700-f032a568e944?auto=format&fit=crop&w=400&q=60",
    },
    "gopro12": {
        "name": "GoPro Hero 12",
        "image": "https://images.unsplash.com/photo-1508896694512-1eade5586790?auto=format&fit=crop&w=400&q=60",
    },
}


def _format_currency(value: float) -> str:
    return f"{int(round(value)):,} đ".replace(",", ".")


@dataclass
class PredictionSummary:
    analysis: str
    recommendation: str
    change_pct: float


class ProductAnalyticsService:
    def __init__(
        self,
        csv_path: str | Path,
        seq_len: int = 120,
        history_days: int = 30,
        epochs: int = 20,
        batch_size: int = 32,
        lr: float = 1e-3,
        ai_generator: Optional[AIContentGenerator] = None,
        image_provider: Optional[ProductImageProvider] = None,
        products_path: Optional[str | Path] = None,
        platforms_path: Optional[str | Path] = None,
    ) -> None:
        self.csv_path = Path(csv_path)
        self.seq_len = seq_len
        self.history_days = history_days
        self.epochs = epochs
        self.batch_size = batch_size
        self.lr = lr
        self.ai_generator = ai_generator or AIContentGenerator()
        self.image_provider = image_provider or ProductImageProvider(DEFAULT_IMAGE)
        self.products_path = Path(products_path) if products_path else (self.csv_path.parent / "products.csv")
        if self.products_path and not self.products_path.exists():
            self.products_path = None
        self.platforms_path = Path(platforms_path) if platforms_path else (self.csv_path.parent / "platforms.csv")
        if self.platforms_path and not self.platforms_path.exists():
            self.platforms_path = None

        self.products_df = self._load_products_meta()
        self.products_lookup = (
            self.products_df.set_index("product_id").to_dict(orient="index") if self.products_df is not None else {}
        )
        self.df = self._load_dataframe()
        self.df["date"] = pd.to_datetime(self.df["date"])
        self.df = self.df.sort_values("date")
        self.platforms = self._load_platforms_list()
        self.catalog = self._build_catalog()
        self.catalog_index = {item["id"]: item for item in self.catalog}

    def _load_dataframe(self) -> pd.DataFrame:
        """
        Đọc file CSV, tự động nhận biết delimiter (',' hoặc ';').
        Một số file xuất từ Numbers/Excel sẽ dùng ';', nếu đọc bằng default (',') sẽ lỗi.
        """
        sample_lines: List[str] = []
        with self.csv_path.open("r", encoding="utf-8") as f:
            for _ in range(5):
                line = f.readline()
                if not line:
                    break
                sample_lines.append(line)

        sample_text = "".join(sample_lines)
        delimiter = "," if sample_text.count(",") >= sample_text.count(";") else ";"

        skip_rows = 0
        header_candidate = sample_lines[0].strip().lower() if sample_lines else ""
        if "date" not in header_candidate and len(sample_lines) > 1:
            second_line = sample_lines[1].strip().lower()
            if "date" in second_line:
                skip_rows = 1

        df = pd.read_csv(self.csv_path, sep=delimiter, skiprows=skip_rows)

        if "date" not in df.columns:
            raise ValueError("Không tìm thấy cột 'date' trong file CSV. Vui lòng kiểm tra lại tiêu đề cột.")
        if self.products_df is not None:
            df = df.merge(self.products_df, on="product_id", how="left")
        return df

    def _load_products_meta(self) -> Optional[pd.DataFrame]:
        if not self.products_path:
            return None
        try:
            df = pd.read_csv(self.products_path)
            expected_cols = {"product_id", "name", "brand", "category"}
            if not expected_cols.issubset(df.columns):
                return None
            return df
        except Exception:
            return None

    def _load_platforms_list(self) -> List[str]:
        if self.platforms_path:
            try:
                platform_df = pd.read_csv(self.platforms_path)
                if "platform" in platform_df.columns:
                    platforms = sorted(platform_df["platform"].dropna().unique().tolist())
                    if platforms:
                        return platforms
            except Exception:
                pass
        return sorted(self.df["platform"].dropna().unique())

    def _build_catalog(self) -> List[Dict[str, Any]]:
        catalog: List[Dict[str, Any]] = []
        if self.products_df is not None:
            merged = self.products_df.copy()
            platform_map = (
                self.df.groupby("product_id")["platform"]
                .apply(lambda ser: sorted(ser.dropna().unique().tolist()))
                .to_dict()
            )
            for record in merged.to_dict(orient="records"):
                product_id = record["product_id"]
                name = record.get("name") or product_id
                brand = record.get("brand")
                category = record.get("category")
                image = record.get("image") or self.image_provider.get_image(name, brand or "", category or "")
                catalog.append(
                    {
                        "id": product_id,
                        "name": name,
                        "brand": brand,
                        "category": category,
                        "image": image or DEFAULT_IMAGE,
                        "platforms": platform_map.get(product_id, self.platforms),
                    }
                )
        else:
            for product_id, group in self.df.groupby("product_id"):
                meta = PRODUCT_METADATA.get(product_id, {})
                name = meta.get("name") or product_id
                brand = group["brand"].iloc[0] if "brand" in group.columns else meta.get("brand")
                category = group["category"].iloc[0] if "category" in group.columns else meta.get("category")
                image = meta.get("image") or self.image_provider.get_image(name, brand or "", category or "")
                catalog.append(
                    {
                        "id": product_id,
                        "name": name,
                        "brand": brand,
                        "category": category,
                        "image": image or DEFAULT_IMAGE,
                        "platforms": sorted(group["platform"].unique().tolist()),
                    }
                )
        catalog.sort(key=lambda item: item["name"])
        return catalog

    def get_catalog(self) -> Dict[str, Any]:
        return {"platforms": self.platforms, "products": self.catalog}

    def _filter_series(self, product_id: str, platform: str) -> pd.DataFrame:
        subset = self.df[(self.df["product_id"] == product_id) & (self.df["platform"] == platform)].copy()
        subset = subset.sort_values("date")
        if subset.empty:
            raise ValueError("Không tìm thấy dữ liệu cho lựa chọn này.")
        return subset

    def _get_product_meta(self, product_id: str) -> Dict[str, Any]:
        meta = self.catalog_index.get(product_id)
        if meta:
            return meta
        fallback = self.products_lookup.get(product_id, {})
        if not fallback:
            fallback = PRODUCT_METADATA.get(product_id, {})
        return {
            "id": product_id,
            "name": fallback.get("name", product_id),
            "brand": fallback.get("brand", ""),
            "category": fallback.get("category", ""),
            "image": fallback.get("image") or self.image_provider.get_image(fallback.get("name", product_id)),
            "platforms": self.platforms,
        }

    def _build_comparison(self, product_id: str) -> Dict[str, Any]:
        prices: Dict[str, float] = {}
        for platform in self.platforms:
            subset = self.df[(self.df["product_id"] == product_id) & (self.df["platform"] == platform)]
            if subset.empty:
                continue
            latest = subset.iloc[-1]
            price_value = latest.get("price")
            if pd.isna(price_value):
                continue
            prices[platform] = float(price_value)

        best_platform = None
        if prices:
            best_platform = min(prices.items(), key=lambda item: item[1])[0]
        return {"prices": prices, "best_platform": best_platform}

    def get_metrics(self, product_id: str, platform: str, history_days: Optional[int] = None) -> Dict[str, Any]:
        subset = self._filter_series(product_id, platform)
        days = history_days or self.history_days
        recent = subset.tail(max(1, days))
        latest = subset.iloc[-1]

        history_payload = [
            {"date": row["date"].strftime("%Y-%m-%d"), "price": float(row["price"])}
            for _, row in recent.iterrows()
        ]

        stats = {
            "avg_price": float(recent["price"].mean()),
            "max_price": float(recent["price"].max()),
            "min_price": float(recent["price"].min()),
        }

        rating = latest.get("rating")
        stock = latest.get("stock")

        product_meta = self._get_product_meta(product_id)
        comparison = self._build_comparison(product_id)

        return {
            "product": product_meta,
            "platform": platform,
            "latest_price": float(latest["price"]),
            "last_updated": latest["date"].strftime("%Y-%m-%d"),
            "history": history_payload,
            "stats": stats,
            "comparison": comparison,
            "rating": None if pd.isna(rating) else float(rating),
            "stock": None if pd.isna(stock) else int(stock),
            "sample_size": int(len(subset)),
        }

    def _generate_summary(self, history_prices: List[float], predictions: np.ndarray) -> PredictionSummary:
        if not history_prices:
            history_prices = [predictions[0]]
        last_observed = history_prices[-1]
        last_prediction = float(predictions[-1])
        change = last_prediction - last_observed
        change_pct = 0.0 if last_observed == 0 else (change / last_observed) * 100

        direction = "tăng" if change > 0 else "giảm"
        magnitude = abs(change_pct)

        if magnitude < 0.5:
            recommendation = "Giá khá ổn định, bạn có thể mua bất cứ lúc nào."
        elif change > 0:
            recommendation = "AI khuyến nghị nên mua sớm trước khi giá tăng thêm."
        else:
            recommendation = "Nên chờ thêm vài ngày để tận dụng xu hướng giảm giá."

        avg_price = np.mean(history_prices)
        analysis = (
            f"Giá trung bình {len(history_prices)} ngày qua là {_format_currency(avg_price)}. "
            f"Mô hình dự báo giá sẽ {direction} khoảng {magnitude:.2f}% trong {len(predictions)} ngày tới."
        )

        return PredictionSummary(analysis=analysis, recommendation=recommendation, change_pct=change_pct)

    def get_prediction(self, product_id: str, platform: str, future_days: int = 7) -> Dict[str, Any]:
        config = ForecastConfig(
            csv_path=str(self.csv_path),
            product_id=product_id,
            platform=platform,
            seq_len=self.seq_len,
            batch_size=self.batch_size,
            epochs=self.epochs,
            lr=self.lr,
        )
        forecast_result = train_and_predict(config, future_days=future_days, df=self.df)
        predictions = [float(value) for value in forecast_result.predictions]
        subset = self._filter_series(product_id, platform)
        last_date = subset["date"].max()
        product_meta = self._get_product_meta(product_id)

        prediction_payload = []
        for idx, price in enumerate(predictions, start=1):
            prediction_payload.append(
                {
                    "date": (last_date + timedelta(days=idx)).strftime("%Y-%m-%d"),
                    "price": round(price, 2),
                }
            )

        recent_prices = subset.tail(self.history_days)["price"].tolist()
        summary_payload = None
        try:
            summary_payload = self.ai_generator.generate_summary(
                product_meta["name"],
                platform,
                recent_prices,
                forecast_result.predictions,
            )
        except Exception as e:
            print("⚠️ AI summary failed:", e)
            summary_payload = None

        fallback_summary = self._generate_summary(recent_prices, forecast_result.predictions)
        analysis_text = summary_payload["analysis"] if summary_payload else "Không thể kết nối tới dịch vụ AI. Vui lòng thử lại."
        summary = PredictionSummary(
            analysis=analysis_text,
            recommendation=fallback_summary.recommendation,
            change_pct=fallback_summary.change_pct,
        )

        return {
            "product": product_meta,
            "platform": platform,
            "predictions": prediction_payload,
            "ai_summary": summary.analysis,
            "recommendation": summary.recommendation,
            "expected_change_pct": float(summary.change_pct),
        }
