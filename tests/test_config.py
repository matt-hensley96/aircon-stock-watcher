from pathlib import Path

import pytest

from watcher import config


def test_given_actual_workflow_file_when_loading_check_interval_then_matches_configured_cron():
    assert config._load_check_interval_minutes() == 15


def test_given_minute_step_cron_when_loading_check_interval_then_returns_step_value(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "WORKFLOW_PATH", _write_workflow(tmp_path, cron="*/30 * * * *"))

    assert config._load_check_interval_minutes() == 30


def test_given_unsupported_cron_when_loading_check_interval_then_raises(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "WORKFLOW_PATH", _write_workflow(tmp_path, cron="0 * * * *"))

    with pytest.raises(ValueError, match="Can't derive a check interval"):
        config._load_check_interval_minutes()


def _write_workflow(tmp_path: Path, cron: str) -> Path:
    workflow_path = tmp_path / "check_stock.yml"
    workflow_path.write_text(f'on:\n  schedule:\n    - cron: "{cron}"\n')

    return workflow_path