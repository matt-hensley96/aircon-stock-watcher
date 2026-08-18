from pathlib import Path

from watcher.config import FAILURE_ALERT_THRESHOLD
from watcher.retailers.base import ProductStatus
from watcher.state import load_state, record_failure, record_success, update_products_and_get_restocks

_NONEXISTENT_STATE_PATH = Path("does-not-exist") / "state.json"


def _product(in_stock: bool) -> ProductStatus:
    return ProductStatus(retailer="Meaco", title="Cirro+ 14000 BTU", url="https://meaco.com/x", in_stock=in_stock)


def test_given_new_in_stock_product_when_updating_state_then_reported_as_restock():
    state = load_state_for_test()

    restocks = update_products_and_get_restocks(state, [_product(in_stock=True)])

    assert restocks == [_product(in_stock=True)]


def test_given_new_out_of_stock_product_when_updating_state_then_no_restock_reported():
    state = load_state_for_test()

    restocks = update_products_and_get_restocks(state, [_product(in_stock=False)])

    assert restocks == []


def test_given_product_already_in_stock_when_checked_again_still_in_stock_then_no_duplicate_restock():
    state = load_state_for_test()
    update_products_and_get_restocks(state, [_product(in_stock=True)])

    restocks = update_products_and_get_restocks(state, [_product(in_stock=True)])

    assert restocks == []


def test_given_product_goes_out_of_stock_then_back_in_stock_when_updating_state_then_restock_reported_again():
    state = load_state_for_test()
    update_products_and_get_restocks(state, [_product(in_stock=True)])
    update_products_and_get_restocks(state, [_product(in_stock=False)])

    restocks = update_products_and_get_restocks(state, [_product(in_stock=True)])

    assert restocks == [_product(in_stock=True)]


def test_given_failures_below_threshold_when_recording_failure_then_no_alert_triggered():
    state = load_state_for_test()

    for _ in range(FAILURE_ALERT_THRESHOLD - 1):
        should_alert = record_failure(state, "Amazon UK")

    assert should_alert is False


def test_given_failures_reach_threshold_when_recording_failure_then_alert_triggered_once():
    state = load_state_for_test()

    alerts = [record_failure(state, "Amazon UK") for _ in range(FAILURE_ALERT_THRESHOLD + 2)]

    assert alerts.count(True) == 1


def test_given_retailer_had_failures_when_recording_success_then_failure_count_resets():
    state = load_state_for_test()
    record_failure(state, "Amazon UK")

    record_success(state, "Amazon UK")

    assert state["retailer_failures"]["Amazon UK"]["consecutive_failures"] == 0


def load_state_for_test() -> dict:
    return load_state(_NONEXISTENT_STATE_PATH)
