"""Market search utilities: use DuckDuckGo to find product pages and extract basic attributes.

This is a lightweight helper that prefers `duckduckgo_search` + `requests`. If `firecrawl`
is available it can be integrated for cleaner Markdown extraction.
"""
from typing import List, Dict, Optional
import logging
import re

logger = logging.getLogger(__name__)

try:
    from duckduckgo_search import ddg
except Exception:
    ddg = None

import requests

MATERIAL_KEYWORDS = ["PLA", "ABS", "PETG", "Nylon", "Aluminum", "Steel", "Titanium"]


def _extract_price(text: str) -> Optional[float]:
    m = re.search(r"\$\s*([0-9]+(?:\.[0-9]+)?)", text)
    if m:
        try:
            return float(m.group(1))
        except Exception:
            return None
    return None


def _extract_mpn(text: str) -> Optional[str]:
    # Look for common MPN patterns (alphanumeric, dashes, dots)
    m = re.search(r"MPN[:\s]*([A-Za-z0-9\-_.]+)", text, re.IGNORECASE)
    if m:
        return m.group(1)
    # fallback: look for known parts
    m2 = re.search(r"(MG996R|SG90|NEMA17|28BYJ-48|608ZZ|17HS4401)", text, re.IGNORECASE)
    if m2:
        return m2.group(1)
    return None


def _extract_material(text: str) -> Optional[str]:
    for kw in MATERIAL_KEYWORDS:
        if re.search(r"\b" + re.escape(kw) + r"\b", text, re.IGNORECASE):
            return kw
    return None


def search_part(query: str, max_results: int = 5) -> List[Dict]:
    """Search the web for the part/query and return a list of candidate pages with extracted info."""
    if ddg is None:
        raise RuntimeError("duckduckgo_search package not available — add to requirements and install")

    results = ddg(query, max_results=max_results)
    candidates = []

    for r in results:
        url = r.get("href") or r.get("url") or r.get("link")
        title = r.get("title") or ""
        snippet = r.get("body") or r.get("snippet") or ""

        entry = {"url": url, "title": title, "snippet": snippet}

        if not url:
            continue

        try:
            resp = requests.get(url, timeout=6, headers={"User-Agent": "robot-cem/1.0"})
            text = resp.text

            # Extract simple attributes
            price = _extract_price(text + "\n" + snippet)
            mpn = _extract_mpn(text + "\n" + snippet)
            material = _extract_material(text + "\n" + snippet)

            entry.update({"price_usd": price, "mpn": mpn, "material": material})

        except Exception as e:
            logger.warning(f"Failed to fetch {url}: {e}")

        candidates.append(entry)

    return candidates


def find_best_offer(candidates: List[Dict]) -> Optional[Dict]:
    """Return the candidate with lowest price if available."""
    best = None
    for c in candidates:
        p = c.get("price_usd")
        if p is None:
            continue
        if best is None or p < best.get("price_usd", float('inf')):
            best = c
    return best
