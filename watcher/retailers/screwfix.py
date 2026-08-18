"""Screwfix's site search returns loosely-matched results (e.g. unrelated
radiators sharing a "BTU" figure), so the shared brand+BTU title matcher is
what actually narrows results down, not the search query itself.
"""

import requests

from .. import config
from .base import (
    REQUEST_HEADERS,
    REQUEST_TIMEOUT_SECONDS,
    ProductStatus,
    Retailer,
    parse_matching_products,
    search_all_brands,
)

SEARCH_URL = "https://www.screwfix.com/search"
BASE_URL = "https://www.screwfix.com"


class ScrewfixRetailer(Retailer):
    name = "Screwfix"

    def check(self) -> list[ProductStatus]:
        return search_all_brands(self._check_brand)

    def _check_brand(self, brand: str) -> list[ProductStatus]:
        html = _fetch_search_html(brand)

        return parse_matching_products(html, self.name, BASE_URL, link_href_contains="/p/")


def _fetch_search_html(brand: str) -> str:
    params = {"search": f"{brand} {config.TARGET_BTU}"}
    response = requests.get(
        SEARCH_URL, params=params, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT_SECONDS
    )
    response.raise_for_status()

    return response.text
