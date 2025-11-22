from __future__ import annotations

import os
import json
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional

import requests



class AIContentGenerator:
    """
    Gọi LLM để viết phân tích + khuyến nghị.
    Trả về dict {"analysis": str, "recommendation": str} hoặc None nếu lỗi.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 60,
    ) -> None:
        self.api_key = api_key or os.getenv("GEN_AI_API_KEY")
        self.api_url = api_url or os.getenv("GEN_AI_API_URL", "https://api.openai.com/v1/chat/completions")
        self.model = model or os.getenv("GEN_AI_MODEL", "gpt-4o-mini")
        self.timeout = timeout

    def is_enabled(self) -> bool:
        return bool(self.api_key)

    def _strip_code_fence(self, content: str) -> str:
        content = content.strip()
        if content.startswith("```"):
            lines = content.splitlines()
            lines = lines[1:]
            if lines and lines[-1].strip().startswith("```"):
                lines = lines[:-1]
            content = "\n".join(lines).strip()
        return content

    def generate_summary(
        self,
        product_name: str,
        platform: str,
        history: Iterable[float],
        predictions: Iterable[float],
    ) -> Optional[Dict[str, str]]:
        if not self.is_enabled():
            return None

        history_list = list(history)
        prediction_list = list(predictions)

        prompt = (
            "Bạn là chuyên gia thương mại điện tử. Hãy phân tích lịch sử giá và dự báo để viết mô tả ngắn "
            "và đưa ra khuyến nghị mua hàng rõ ràng.\n"
            f"- Sản phẩm: {product_name}\n"
            f"- Sàn: {platform}\n"
            f"- Giá 30 ngày gần nhất: {history_list[-30:]}\n"
            f"- Dự báo {len(prediction_list)} ngày tới: {prediction_list}\n"
            "Trả lời bằng JSON với hai khóa: analysis (tối đa 3 câu), recommendation (1 câu rõ ràng)."
        )

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "Bạn là trợ lý thương mại điện tử, trả lời gọn và hữu ích."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.4,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            resp = requests.post(self.api_url, headers=headers, json=payload, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException:
            return None

        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            return None

        content = self._strip_code_fence(content)

        analysis = ""
        recommendation = ""
        try:
            parsed = json.loads(content)
            analysis = str(parsed.get("analysis", "")).strip()
            recommendation = str(parsed.get("recommendation", "")).strip()
        except Exception:
            
            analysis = content.strip()
            recommendation = ""

        if not analysis:
            return None

        return {
            "analysis": analysis,
            "recommendation": recommendation or "Hãy cân nhắc tùy ngân sách của bạn.",
        }


class ProductImageProvider:
    def __init__(self, placeholder_url: str, unsplash_key: Optional[str] = None) -> None:
        self.placeholder_url = placeholder_url
        self.unsplash_key = unsplash_key or os.getenv("UNSPLASH_ACCESS_KEY")
        self.cache: Dict[str, str] = {}

    def get_image(self, *keywords: str) -> str:
        query = " ".join(filter(None, keywords)).strip()
        if not query:
            return self.placeholder_url
        if query in self.cache:
            return self.cache[query]

        url = None
        if self.unsplash_key:
            url = self._query_unsplash(query)

        if not url:
            url = f"https://source.unsplash.com/400x400/?{query.replace(' ', '+')}"

        self.cache[query] = url
        return url

    def _query_unsplash(self, query: str) -> Optional[str]:
        endpoint = "https://api.unsplash.com/search/photos"
        params = {"query": query, "per_page": 1, "orientation": "squarish"}
        headers = {"Authorization": f"Client-ID {self.unsplash_key}"}
        try:
            r = requests.get(endpoint, headers=headers, params=params, timeout=10)
            r.raise_for_status()
            data = r.json()
            results: List[dict] = data.get("results", [])
            if not results:
                return None
            return results[0]["urls"].get("regular")
        except requests.RequestException:
            return None


class TikiAPI:
    """Simple wrapper để kéo dữ liệu sản phẩm trực tiếp từ Tiki."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: int = 10,
        enabled: Optional[bool] = None,
        prefetch_limit: Optional[int] = None,
    ) -> None:
        env_flag = os.getenv("ENABLE_TIKI_API")
        if enabled is None:
            enabled = env_flag is None or env_flag.lower() not in {"0", "false", "off"}

        self.enabled = enabled
        self.base_url = base_url or os.getenv("TIKI_API_BASE", "https://tiki.vn/api/v2")
        self.timeout = timeout
        if prefetch_limit is None:
            prefetch_limit = int(os.getenv("TIKI_PREFETCH_LIMIT", "8"))
        self.prefetch_limit = max(0, prefetch_limit)
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": os.getenv(
                    "TIKI_API_USER_AGENT",
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
                ),
                "Accept": "application/json",
            }
        )
        self.search_cache: Dict[str, List[Dict[str, Any]]] = {}
        self.snapshot_cache: Dict[str, Optional[Dict[str, Any]]] = {}

    def is_enabled(self) -> bool:
        return self.enabled

    def _request(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        try:
            resp = self.session.get(url, params=params, timeout=self.timeout)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException:
            return {}

    def _normalize_product(self, item: Dict[str, Any]) -> Dict[str, Any]:
        url_path = (item.get("url_path") or "").lstrip("/")
        product_url = f"https://tiki.vn/{url_path}" if url_path else None
        thumbnail = item.get("thumbnail_url") or item.get("image_url")
        brand = None
        brand_data = item.get("brand")
        if isinstance(brand_data, dict):
            brand = brand_data.get("name")
        seller = None
        seller_data = item.get("seller")
        if isinstance(seller_data, dict):
            seller = seller_data.get("name")
        return {
            "id": item.get("id"),
            "name": item.get("name"),
            "price": item.get("price") or item.get("min_price"),
            "original_price": item.get("original_price") or item.get("list_price"),
            "thumbnail_url": thumbnail,
            "url": product_url,
            "rating": item.get("rating_average"),
            "review_count": item.get("review_count"),
            "discount_rate": item.get("discount_rate"),
            "brand": brand,
            "seller": seller,
            "checked_at": datetime.utcnow().isoformat(),
        }

    def search_products(self, keyword: str, limit: int = 5) -> List[Dict[str, Any]]:
        if not self.enabled:
            return []
        query = (keyword or "").strip()
        if not query:
            return []
        cache_key = f"{query.lower()}::{limit}"
        if cache_key in self.search_cache:
            return self.search_cache[cache_key]

        params = {"limit": limit, "page": 1, "q": query}
        payload = self._request("/products", params=params)
        items = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(items, list):
            self.search_cache[cache_key] = []
            return []

        normalized = [self._normalize_product(item) for item in items if isinstance(item, dict)]
        self.search_cache[cache_key] = normalized
        return normalized

    def get_product_snapshot(self, keyword: str) -> Optional[Dict[str, Any]]:
        query = (keyword or "").strip()
        if not query:
            return None
        cache_key = query.lower()
        if cache_key in self.snapshot_cache:
            return self.snapshot_cache[cache_key]

        results = self.search_products(query, limit=1)
        snapshot = results[0] if results else None
        self.snapshot_cache[cache_key] = snapshot
        return snapshot

    def enrich_product_meta(self, meta: Dict[str, Any]) -> Dict[str, Any]:
        if not self.enabled:
            return meta
        query = (meta.get("name") or meta.get("id") or "").strip()
        if not query:
            return meta

        snapshot = self.get_product_snapshot(query)
        if not snapshot:
            return meta

        enriched = dict(meta)
        image = snapshot.get("thumbnail_url")
        if image:
            enriched["image"] = image
        enriched["live_price"] = snapshot.get("price")
        enriched["live_original_price"] = snapshot.get("original_price")
        enriched["live_source"] = "Tiki"
        enriched["live_url"] = snapshot.get("url")
        enriched["live_rating"] = snapshot.get("rating")
        enriched["live_review_count"] = snapshot.get("review_count")
        enriched["live_checked_at"] = snapshot.get("checked_at")
        if snapshot.get("seller"):
            enriched["live_seller"] = snapshot.get("seller")
        if snapshot.get("brand") and not enriched.get("brand"):
            enriched["brand"] = snapshot.get("brand")
        return enriched
