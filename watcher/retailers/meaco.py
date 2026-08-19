"""Meaco's own site (meaco.com) is Shopify and exposes a public search JSON
endpoint with a real 'available' boolean per product, so no HTML parsing is
needed here.
"""

from urllib.parse import urlsplit, urlunsplit

import requests

from .. import config
from .base import REQUEST_HEADERS, REQUEST_TIMEOUT_SECONDS, ProductStatus, Retailer

SEARCH_URL = "https://meaco.com/search/suggest.json"


class MeacoRetailer(Retailer):
    name = "Meaco"

    def check(self) -> list[ProductStatus]:
        return [_to_product_status(item) for item in _fetch_search_results() if _matches(item)]


def _matches(item: dict) -> bool:
    # Titles on Meaco's own site don't repeat the brand name (e.g. "Cirro+ 14000
    # BTU..."), so prepend it before running the shared brand+BTU matcher.
    return config.matches_target_product(f"Meaco {item['title']}")


def _fetch_search_results() -> list[dict]:
    params = {
        "q": config.TARGET_BTU,
        "resources[type]": "product",
        "resources[limit]": 10,
        "resources[options][unavailable_products]": "show",
    }
    response = requests.get(
        SEARCH_URL, params=params, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT_SECONDS
    )
    response.raise_for_status()

    return response.json()["resources"]["results"]["products"]


def _to_product_status(item: dict) -> ProductStatus:
    return ProductStatus(
        retailer=MeacoRetailer.name,
        title=item["title"],
        url=_strip_query_string(f"https://meaco.com{item['url']}"),
        in_stock=bool(item.get("available")),
    )


def _strip_query_string(url: str) -> str:
    """Meaco's search results include Shopify predictive-search tracking params
    (e.g. _pos, _psq, _psid, _ss) that change on every request, so keeping them
    in the URL would make each search look like a different product to state.py.
    """

    parts = urlsplit(url)

    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))
