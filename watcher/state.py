"""Persisted state: last-known stock per product, and per-retailer failure
streaks, so alerts only fire on real transitions and repeated errors.
"""

import json
from pathlib import Path

from .config import FAILURE_ALERT_THRESHOLD, FAILURE_REMINDER_INTERVAL
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


_NO_ALERT_SENT_YET = None


def record_success(state: dict, retailer_name: str) -> None:
    state["retailer_failures"][retailer_name] = {
        "consecutive_failures": 0,
        "failures_at_last_alert": _NO_ALERT_SENT_YET,
    }


def record_failure(state: dict, retailer_name: str) -> bool:
    """Record a failed check for a retailer. Returns True the first time its
    consecutive failure count reaches the alert threshold, and again every
    FAILURE_REMINDER_INTERVAL failures after that - so a retailer that's broken
    for a long stretch gets an occasional reminder rather than either silence
    or an email every run.
    """

    failures = state["retailer_failures"].setdefault(
        retailer_name, {"consecutive_failures": 0, "failures_at_last_alert": _NO_ALERT_SENT_YET}
    )
    failures["consecutive_failures"] += 1
    failure_count = failures["consecutive_failures"]
    failures_at_last_alert = failures["failures_at_last_alert"]

    if failure_count < FAILURE_ALERT_THRESHOLD:
        return False

    first_alert = failures_at_last_alert is _NO_ALERT_SENT_YET
    reminder_due = not first_alert and failure_count - failures_at_last_alert >= FAILURE_REMINDER_INTERVAL
    should_alert = first_alert or reminder_due

    if should_alert:
        failures["failures_at_last_alert"] = failure_count

    return should_alert
