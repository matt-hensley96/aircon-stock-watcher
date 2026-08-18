from watcher.config import matches_target_product


def test_given_meaco_brand_and_matching_btu_when_checking_match_then_true():
    assert matches_target_product("MeacoCool MC Series Pro 14000 BTU Portable Air Conditioner")


def test_given_black_and_decker_brand_and_matching_btu_when_checking_match_then_true():
    assert matches_target_product("Black+Decker 14000 BTU Portable Air Conditioner")


def test_given_delonghi_brand_and_matching_btu_when_checking_match_then_true():
    assert matches_target_product("Delonghi 14,000 BTU Air Conditioner PAC EX140")


def test_given_matching_brand_and_higher_btu_when_checking_match_then_false():
    assert not matches_target_product("Meaco 18000 BTU Portable Air Conditioner")


def test_given_matching_brand_and_lower_btu_when_checking_match_then_false():
    assert not matches_target_product("MeacoCool MC Series Pro 12000 BTU Portable Air Conditioner")


def test_given_matching_btu_and_unaccepted_brand_when_checking_match_then_false():
    assert not matches_target_product("Stelrad 14000 BTU Convector Radiator")


def test_given_accessory_with_no_btu_in_title_when_checking_match_then_false():
    assert not matches_target_product("MeacoCool MC Series Castors")
