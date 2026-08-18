"""Amazon UK has the strongest bot protection of the retailers checked here.
A real headless browser clears some sites' checks but is not expected to
reliably beat Amazon's - this is the retailer most likely to need the
broken-checker alert (see state.py) and manual attention over time.
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

SEARCH_URL = "https://www.amazon.co.uk/s?k={brand}+{btu}+btu+air+conditioner"
BASE_URL = "https://www.amazon.co.uk"


class AmazonRetailer(Retailer):
    name = "Amazon UK"

    def check(self) -> list[ProductStatus]:
        return search_all_brands(self._check_brand)

    def _check_brand(self, brand: str) -> list[ProductStatus]:
        url = SEARCH_URL.format(brand=url_encode_brand(brand), btu=config.TARGET_BTU)
        html = fetch_rendered_html(url)

        return parse_matching_products(html, self.name, BASE_URL, link_href_contains="/dp/")
