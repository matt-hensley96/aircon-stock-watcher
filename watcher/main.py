"""Orchestrator: check every retailer, alert on restocks, and alert once if a
retailer's checker looks persistently broken. Designed to be run on a schedule
(see .github/workflows/check_stock.yml) via `python -m watcher.main`.
"""

import sys
from pathlib import Path

from . import config, notifier, state
from .retailers.amazon import AmazonRetailer
from .retailers.argos import ArgosRetailer
from .retailers.base import Retailer
from .retailers.bq import BqRetailer
from .retailers.currys import CurrysRetailer
from .retailers.john_lewis import JohnLewisRetailer
from .retailers.meaco import MeacoRetailer
from .retailers.screwfix import ScrewfixRetailer
from .retailers.toolstation import ToolstationRetailer

STATE_PATH = Path(__file__).resolve().parent.parent / "state.json"

# Keys must match the retailer names used in config.json's "ignored_retailers" list.
# Every retailer here runs by default; a name only needs adding to that list to skip it.
RETAILER_CLASSES_BY_NAME: dict[str, type[Retailer]] = {
    "meaco": MeacoRetailer,
    "amazon": AmazonRetailer,
    "argos": ArgosRetailer,
    "currys": CurrysRetailer,
    "screwfix": ScrewfixRetailer,
    "bq": BqRetailer,
    "toolstation": ToolstationRetailer,
    "john_lewis": JohnLewisRetailer,
}


def build_enabled_retailers() -> list[Retailer]:
    unknown_names = set(config.IGNORED_RETAILERS) - RETAILER_CLASSES_BY_NAME.keys()

    if unknown_names:
        raise ValueError(
            f"Unknown retailer(s) in config.json's ignored_retailers: {sorted(unknown_names)}. "
            f"Valid names: {sorted(RETAILER_CLASSES_BY_NAME)}"
        )

    return [
        retailer_class()
        for name, retailer_class in RETAILER_CLASSES_BY_NAME.items()
        if name not in config.IGNORED_RETAILERS
    ]


def main() -> None:
    watcher_state = state.load_state(STATE_PATH)

    for retailer in build_enabled_retailers():
        check_retailer(retailer, watcher_state)

    state.save_state(STATE_PATH, watcher_state)


def check_retailer(retailer: Retailer, watcher_state: dict) -> None:
    try:
        products = retailer.check()
    except Exception as error:  # noqa: BLE001 - one retailer's failure must not stop the rest
        handle_check_failure(retailer, watcher_state, error)
        return

    state.record_success(watcher_state, retailer.name)
    alert_on_restocks(watcher_state, products)


def handle_check_failure(retailer: Retailer, watcher_state: dict, error: Exception) -> None:
    print(f"[{retailer.name}] check failed: {error}", file=sys.stderr)
    crossed_threshold = state.record_failure(watcher_state, retailer.name)

    if crossed_threshold:
        failures = watcher_state["retailer_failures"][retailer.name]["consecutive_failures"]
        notifier.send_broken_retailer_alert(retailer.name, failures)


def alert_on_restocks(watcher_state: dict, products) -> None:
    restocks = state.update_products_and_get_restocks(watcher_state, products)

    for product in restocks:
        notifier.send_restock_alert(product)


if __name__ == "__main__":
    main()
