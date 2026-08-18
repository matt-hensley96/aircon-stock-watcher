"""Currys blocks plain HTTP requests outright, so this renders the search page
with a real headless browser instead.
"""

from .. import config
from .base import (
    ProductStatus,
    Retailer,
    fetch_rendered_html,
    parse_matching_products,
    search_all_brands,
    url_encode_brand,
)

SEARCH_URL = "https://www.currys.co.uk/search?q={brand}+{btu}+btu+air+conditioner"
BASE_URL = "https://www.currys.co.uk"


class CurrysRetailer(Retailer):
    name = "Currys"

    def check(self) -> list[ProductStatus]:
        return search_all_brands(self._check_brand)

    def _check_brand(self, brand: str) -> list[ProductStatus]:
        url = SEARCH_URL.format(brand=url_encode_brand(brand), btu=config.TARGET_BTU)
        html = fetch_rendered_html(url)

        return parse_matching_products(html, self.name, BASE_URL, link_href_contains="/products/")
