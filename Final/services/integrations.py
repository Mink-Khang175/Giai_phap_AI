from __future__ import annotations

import os
import json
from typing import Dict, Iterable, List, Optional

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

        # thử parse json trước
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
