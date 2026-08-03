"""Tests for lovelace_dashboard service helpers."""
import json
import pytest

from app.services.lovelace_dashboard import (
    _extract_lovelace_config,
    _set_lovelace_config,
    _storage_key_from_id,
    _url_path_from_storage_key,
)


def test_url_path_from_storage_key():
    assert _url_path_from_storage_key("lovelace.dashboard_primary") == "primary"
    assert _url_path_from_storage_key("lovelace.lovelace") == "lovelace"
    assert _url_path_from_storage_key("lovelace") == "lovelace"


def test_storage_key_from_id():
    assert _storage_key_from_id("primary") == "lovelace.dashboard_primary"
    assert _storage_key_from_id("lovelace") == "lovelace.lovelace"
    assert _storage_key_from_id("overview") == "lovelace.lovelace"


def test_extract_lovelace_config_wrapper():
    raw = {
        "version": 1,
        "key": "lovelace.dashboard_primary",
        "data": {"config": {"views": [{"title": "Home"}]}},
    }
    config = _extract_lovelace_config(raw)
    assert config["views"][0]["title"] == "Home"


def test_set_lovelace_config_preserves_wrapper():
    raw = {
        "version": 1,
        "minor_version": 2,
        "key": "lovelace.dashboard_primary",
        "data": {"config": {"views": []}},
    }
    new_config = {"views": [{"title": "Updated"}]}
    updated = _set_lovelace_config(raw, new_config)
    assert updated["version"] == 1
    assert updated["data"]["config"]["views"][0]["title"] == "Updated"
