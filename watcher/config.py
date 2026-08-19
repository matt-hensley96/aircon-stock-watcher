"""Shared configuration: which products count as a match, which retailers to
skip, and alert/email settings.

Brands, target BTU, ignored retailers, and the failure alert threshold are user-editable
via config.json at the repo root, rather than in this file, so changing them doesn't
require touching Python code.
"""

import json
import os
import re
from pathlib import Path

import yaml

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.json"
WORKFLOW_PATH = Path(__file__).resolve().parent.parent / ".github" / "workflows" / "check_stock.yml"
_MINUTE_STEP_CRON_PATTERN = re.compile(r"^\*/(\d+) \* \* \* \*$")

GMAIL_ADDRESS = os.environ.get("GMAIL_ADDRESS", "")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")

# ALERT_EMAIL_TO holds one or more comma-separated addresses, e.g. "a@x.com,b@y.com".
ALERT_EMAIL_RECIPIENTS: list[str] = [
    address.strip() for address in os.environ.get("ALERT_EMAIL_TO", "").split(",") if address.strip()
]

_BTU_MENTION_PATTERN = re.compile(r"(\d[\d,\s]*\d)\s*btu", re.IGNORECASE)


def _load_config() -> dict:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Missing {CONFIG_PATH} - see config.json.example or the README.")

    return json.loads(CONFIG_PATH.read_text())


def _load_check_interval_minutes() -> int:
    workflow = yaml.safe_load(WORKFLOW_PATH.read_text())
    triggers = workflow.get("on", workflow.get(True))
    cron_expression = triggers["schedule"][0]["cron"]
    match = _MINUTE_STEP_CRON_PATTERN.match(cron_expression)

    if not match:
        raise ValueError(
            f"Can't derive a check interval from cron '{cron_expression}' in {WORKFLOW_PATH} - "
            "only a simple '*/N * * * *' (every N minutes) schedule is supported."
        )

    return int(match.group(1))


_config = _load_config()

TARGET_BTU: int = _config["target_btu"]
ACCEPTED_BRANDS: list[str] = [brand.lower() for brand in _config["brands"]]

# Retailers not listed here run by default, so a newly-added retailer module is
# included automatically without needing a config.json change.
IGNORED_RETAILERS: list[str] = _config.get("ignored_retailers", [])

FAILURE_ALERT_THRESHOLD: int = _config.get("failure_alert_threshold", 5)

_FAILURE_REMINDER_DAYS: int = _config.get("failure_reminder_days", 7)
_MINUTES_PER_DAY = 24 * 60
FAILURE_REMINDER_INTERVAL: int = max(1, _FAILURE_REMINDER_DAYS * _MINUTES_PER_DAY // _load_check_interval_minutes())


def matches_target_product(title: str) -> bool:
    """A product counts as a match if its title names an accepted brand and the
    configured target BTU. Each retailer's search query is itself built from
    TARGET_BTU (see watcher/retailers/), so only products whose searchable text
    mentions that figure are ever candidates here in the first place - this is
    an exact match, not a minimum, to reflect that.
    """

    lowered = title.lower()
    has_brand = any(brand in lowered for brand in ACCEPTED_BRANDS)

    return has_brand and _mentions_target_btu(lowered)


def _mentions_target_btu(lowered_title: str) -> bool:
    for mention in _BTU_MENTION_PATTERN.finditer(lowered_title):
        digits = mention.group(1).replace(",", "").replace(" ", "")

        if digits.isdigit() and int(digits) == TARGET_BTU:
            return True

    return False