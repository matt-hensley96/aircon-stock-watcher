"""Persisted state: last-known stock per product, and per-retailer failure
streaks, so alerts only fire on real transitions and repeated errors.
"""

import json
from pathlib import Path

from .config import FAILURE_ALERT_THRESHOLD
from .retailers.base import ProductStatus

_EMPTY_STATE = {"products": {}, "retailer_failures": {}}


def load_state(path: Path) -> dict:
    if not path.exists():
        return json.loads(json.dumps(_EMPTY_STATE))

    return json.loads(path.read_text())


def save_state(path: Path, state: dict) -> None:
    path.write_text(json.dumps(state, indent=2, sort_keys=True))


def update_products_and_get_restocks(state: dict, products: list[ProductStatus]) -> list[ProductStatus]:
    """Update known stock status for each product and return the ones that just
    transitioned from out-of-stock (or unseen) to in-stock.
    """

    restocks = []

    for product in products:
        key = f"{product.retailer}|{product.url}"
        previously_in_stock = state["products"].get(key, {}).get("in_stock", False)

        if product.in_stock and not previously_in_stock:
            restocks.append(product)

        state["products"][key] = {"title": product.title, "in_stock": product.in_stock}

    return restocks


def record_success(state: dict, retailer_name: str) -> None:
    state["retailer_failures"][retailer_name] = {"consecutive_failures": 0, "alerted": False}


def record_failure(state: dict, retailer_name: str) -> bool:
    """Record a failed check for a retailer. Returns True the first time its
    consecutive failure count reaches the alert threshold, so the caller sends
    exactly one "this retailer looks broken" email rather than one per run.
    """

    failures = state["retailer_failures"].setdefault(retailer_name, {"consecutive_failures": 0, "alerted": False})
    failures["consecutive_failures"] += 1

    should_alert = failures["consecutive_failures"] >= FAILURE_ALERT_THRESHOLD and not failures["alerted"]

    if should_alert:
        failures["alerted"] = True

    return should_alert
