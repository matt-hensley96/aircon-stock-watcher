"""Shared types and helpers used by every retailer's stock checker."""

import re
from collections.abc import Callable
from dataclasses import dataclass
from urllib.parse import quote_plus

from bs4 import BeautifulSoup

from .. import config

REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}

REQUEST_TIMEOUT_SECONDS = 20


@dataclass(frozen=True)
class ProductStatus:
    retailer: str
    title: str
    url: str
    in_stock: bool


class Retailer:
    """Base class for a retailer's stock checker.

    Subclasses implement check() to return every candidate product they found,
    already filtered down to ones matching config.matches_target_product().
    """

    name: str = "unknown"

    def check(self) -> list[ProductStatus]:
        raise NotImplementedError


_OUT_OF_STOCK_PHRASES = [
    "out of stock",
    "sold out",
    "currently unavailable",
    "notify me",
    "email me when available",
    "coming soon",
]
_IN_STOCK_PHRASES = ["add to basket", "add to cart", "add to trolley", "in stock", "available for"]


def search_all_brands(check_brand: Callable[[str], list["ProductStatus"]]) -> list["ProductStatus"]:
    """Run check_brand once per brand in config.ACCEPTED_BRANDS and return the
    union, deduped by product URL (some brand variants like "black+decker" and
    "black & decker" can otherwise return the same product twice).
    """

    products_by_url: dict[str, ProductStatus] = {}

    for brand in config.ACCEPTED_BRANDS:
        for product in check_brand(brand):
            products_by_url[product.url] = product

    return list(products_by_url.values())


def url_encode_brand(brand: str) -> str:
    """URL-encode a brand name for use in a search query string, e.g. turning
    "black & decker" into "black+%26+decker".
    """

    return quote_plus(brand)


def url_slug_brand(brand: str) -> str:
    """Turn a brand name into a hyphenated URL path segment, e.g. turning
    "black & decker" into "black-decker", for retailers whose search URL is a
    path slug rather than a query string.
    """

    return re.sub(r"[^a-z0-9]+", "-", brand.lower()).strip("-")


def fetch_rendered_html(url: str) -> str:
    """Render a JS-heavy page with a real headless browser and return its HTML.

    Used for retailers whose search results only appear after client-side JS runs
    (and/or that block plain HTTP requests outright). A real browser engine clears
    basic bot checks more often than a bare request, but isn't guaranteed to beat
    stronger bot protection (e.g. Amazon) - that's expected to surface as a
    per-retailer failure, not crash the whole run.
    """

    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(user_agent=REQUEST_HEADERS["User-Agent"])
        page.goto(url, timeout=REQUEST_TIMEOUT_SECONDS * 1000, wait_until="networkidle")
        html = page.content()
        browser.close()

    return html


def parse_matching_products(
    html: str, retailer_name: str, base_url: str, link_href_contains: str
) -> list["ProductStatus"]:
    """Find product links in a search results page, keeping only ones whose title
    matches config.matches_target_product(), and read each one's stock status from
    its product card's visible text.
    """

    soup = BeautifulSoup(html, "html.parser")
    products = []

    for link in soup.select(f"a[href*='{link_href_contains}']"):
        title = _extract_title(link)

        if not title or not config.matches_target_product(title):
            continue

        card = link.find_parent()
        card_text = card.get_text(" ", strip=True) if card else title
        products.append(
            ProductStatus(
                retailer=retailer_name,
                title=title,
                url=_absolute_url(base_url, link.get("href", "")),
                in_stock=looks_in_stock(card_text),
            )
        )

    return products


def _extract_title(link) -> str:
    """Product cards often wrap price/rating/delivery text in the same <a> as the
    title, so prefer a dedicated title element (heading, or a "name"/"title"
    data-testid) over the link's full text, which would otherwise pull all of
    that surrounding text into what's meant to be just the product title.
    """

    title_element = link.select_one("h1, h2, h3, h4, [data-testid*='name'], [data-testid*='title']")

    if title_element:
        return title_element.get_text(strip=True)

    return link.get_text(strip=True)


def _absolute_url(base_url: str, href: str) -> str:
    if href.startswith("http"):
        return href

    return f"{base_url}{href}"


def looks_in_stock(card_text: str) -> bool:
    """Best-effort stock read from a product card's visible text.

    Retailer HTML/class names change often and aren't worth hard-coding, so this
    matches on the wording shoppers actually see. Defaults to "not in stock" when
    neither phrase is found, since a missed restock alert (caught on the next poll)
    is a far smaller problem than a false "it's in stock" email.
    """

    lowered = card_text.lower()

    if any(phrase in lowered for phrase in _OUT_OF_STOCK_PHRASES):
        return False

    return any(phrase in lowered for phrase in _IN_STOCK_PHRASES)
