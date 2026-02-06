"""Market search utilities: use DuckDuckGo to find product pages and extract basic attributes.

This is a lightweight helper that prefers `duckduckgo_search` + `requests`.
"""
from typing import List, Dict, Optional
import logging
import re
from duckduckgo_search import DDGS
import requests

logger = logging.getLogger(__name__)

MATERIAL_KEYWORDS = ["PLA", "ABS", "PETG", "Nylon", "Aluminum", "Steel", "Titanium", "Carbon Fiber"]

def _extract_price(text: str) -> Optional[float]:
    # Look for $XX.XX
    m = re.search(r"\$\s*([0-9]+(?:\.[0-9]+)?)", text)
    if m:
        try:
            return float(m.group(1))
        except Exception:
            return None
    return None

def _extract_mpn(text: str) -> Optional[str]:
    # Look for common MPN patterns
    m = re.search(r"MPN[:\s]*([A-Za-z0-9\-_.]+)", text, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    # fallback: look for known parts
    m2 = re.search(r"(MG996R|SG90|NEMA17|28BYJ-48|608ZZ|17HS4401)", text, re.IGNORECASE)
    if m2:
        return m2.group(1).upper()
    return None

def _extract_material(text: str) -> Optional[str]:
    for kw in MATERIAL_KEYWORDS:
        if re.search(r"\b" + re.escape(kw) + r"\b", text, re.IGNORECASE):
            return kw
    return None

def _extract_availability(text: str) -> str:
    if any(kw in text.lower() for kw in ["in stock", "available", "ready to ship"]):
        return "In Stock"
    if any(kw in text.lower() for kw in ["out of stock", "backorder"]):
        return "Out of Stock"
    return "Unknown"

def _extract_lead_time(text: str) -> Optional[int]:
    m = re.search(r"(?:ships in|lead time|delivery in)\s*(\d+)\s*(?:days|business days)", text, re.IGNORECASE)
    if m:
        return int(m.group(1))
    return None

def _extract_manufacturer(text: str, title: str) -> Optional[str]:
    # Very simple heuristic
    known_mfgs = ["Creality", "Prusa", "E3D", "Noctua", "Mean Well", "StepperOnline", "Pololu", "Adafruit", "SparkFun"]
    for mfg in known_mfgs:
        if mfg.lower() in text.lower() or mfg.lower() in title.lower():
            return mfg
    return None

def search_part(query: str, max_results: int = 5) -> List[Dict]:
    """Search the web for the part/query and return a list of candidate pages with extracted info."""
    candidates = []

    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
    except Exception as e:
        logger.error(f"DuckDuckGo search failed: {e}")
        return []

    for r in results:
        url = r.get("href")
        title = r.get("title") or ""
        snippet = r.get("body") or ""

        entry = {
            "url": url,
            "title": title,
            "snippet": snippet,
            "availability": "Unknown",
            "lead_time_days": None,
            "manufacturer": None
        }

        if not url:
            continue

        try:
            resp = requests.get(url, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code == 200:
                text = resp.text
                full_text = text + "\n" + snippet

                price = _extract_price(full_text)
                mpn = _extract_mpn(full_text)
                material = _extract_material(full_text)
                availability = _extract_availability(full_text)
                lead_time = _extract_lead_time(full_text)
                mfg = _extract_manufacturer(full_text, title)

                entry.update({
                    "price_usd": price,
                    "mpn": mpn,
                    "material": material,
                    "availability": availability,
                    "lead_time_days": lead_time,
                    "manufacturer": mfg
                })
        except Exception as e:
            logger.warning(f"Failed to fetch {url}: {e}")
            # Fallback to snippet extraction if fetch fails
            entry.update({
                "price_usd": _extract_price(snippet),
                "mpn": _extract_mpn(snippet),
                "material": _extract_material(snippet)
            })

        candidates.append(entry)

    return candidates

def find_best_offer(candidates: List[Dict]) -> Optional[Dict]:
    """Return the candidate with lowest price and best availability."""
    # Filter only those with price and preferably In Stock
    valid_candidates = [c for c in candidates if c.get("price_usd") is not None]
    if not valid_candidates:
        return None

    # Sort by availability (In Stock first) then price
    valid_candidates.sort(key=lambda x: (x.get("availability") != "In Stock", x.get("price_usd")))

    return valid_candidates[0]
