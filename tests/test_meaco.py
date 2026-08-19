from watcher.retailers.meaco import _to_product_status


def test_given_search_result_with_predictive_search_tracking_params_when_converting_then_url_has_no_query_string():
    item = {
        "title": "Cirro+® 14000 BTU Super Quiet Inverter Smart Portable Air Conditioner & Heater",
        "url": "/products/meaco-cirro-14000-btu-super-quiet-inverter-smart-portable-air-conditioner-heater"
        "?_pos=1&_psq=14000&_psid=0c3e6927c&_ss=e",
        "available": False,
    }

    product = _to_product_status(item)

    assert product.url == (
        "https://meaco.com/products/meaco-cirro-14000-btu-super-quiet-inverter-smart-portable"
        "-air-conditioner-heater"
    )
