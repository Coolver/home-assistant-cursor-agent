"""Lovelace dashboard discovery, read, write, and export (YAML + storage)."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

from app.services.file_manager import file_manager

logger = logging.getLogger("ha_cursor_agent")

STORAGE_PREFIX = "lovelace"
STORAGE_DIR = ".storage"


def _storage_path(storage_key: str) -> str:
    return f"{STORAGE_DIR}/{storage_key}"


def _url_path_from_storage_key(storage_key: str) -> str:
    """lovelace.dashboard_primary -> primary; lovelace.lovelace -> lovelace."""
    if storage_key == "lovelace":
        return "lovelace"
    if storage_key.startswith("lovelace.dashboard_"):
        return storage_key[len("lovelace.dashboard_") :]
    if storage_key == "lovelace.lovelace":
        return "lovelace"
    return storage_key.replace("lovelace.", "", 1)


def _storage_key_from_id(dashboard_id: str) -> str:
    """Resolve dashboard id to .storage file key (without path)."""
    normalized = dashboard_id.strip().lower()
    if normalized in ("lovelace", "overview", "default"):
        return "lovelace.lovelace"
    if normalized == "lovelace-legacy":
        return "lovelace"
    return f"lovelace.dashboard_{normalized}"


async def _read_storage_raw(storage_key: str) -> Tuple[Dict[str, Any], str]:
    path = _storage_path(storage_key)
    content = await file_manager.read_file(path, suppress_not_found_logging=True)
    return json.loads(content), path


async def _write_storage_raw(storage_key: str, data: Dict[str, Any]) -> str:
    path = _storage_path(storage_key)
    content = json.dumps(data, indent=2, ensure_ascii=False)
    await file_manager.write_file(path, content)
    return path


def _extract_lovelace_config(storage_data: Dict[str, Any]) -> Dict[str, Any]:
    """Return inner Lovelace config from HA Store wrapper."""
    if "data" in storage_data and isinstance(storage_data["data"], dict):
        inner = storage_data["data"]
        if "config" in inner and isinstance(inner["config"], dict):
            return inner["config"]
        # Some stores keep views at data level
        if "views" in inner:
            return inner
    if "views" in storage_data:
        return storage_data
    return storage_data


def _set_lovelace_config(storage_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """Merge Lovelace config back into HA Store wrapper."""
    if "data" in storage_data and isinstance(storage_data["data"], dict):
        if "config" in storage_data["data"]:
            storage_data["data"]["config"] = config
        else:
            storage_data["data"] = {**storage_data["data"], **config}
    else:
        storage_data = {
            "version": storage_data.get("version", 1),
            "minor_version": storage_data.get("minor_version", 1),
            "key": storage_data.get("key", STORAGE_PREFIX),
            "data": {"config": config},
        }
    return storage_data


async def _parse_yaml_dashboards() -> List[Dict[str, Any]]:
    """YAML dashboards registered in configuration.yaml."""
    results: List[Dict[str, Any]] = []
    try:
        content = await file_manager.read_file("configuration.yaml")
    except FileNotFoundError:
        return results

    try:
        config = yaml.safe_load(content) or {}
    except yaml.YAMLError:
        logger.warning("Could not parse configuration.yaml for lovelace dashboards")
        return results

    lovelace = config.get("lovelace") or {}
    dashboards = lovelace.get("dashboards") or {}
    if not isinstance(dashboards, dict):
        return results

    global_mode = lovelace.get("mode", "storage")

    for dashboard_id, entry in dashboards.items():
        if not isinstance(entry, dict):
            continue
        mode = entry.get("mode", "yaml")
        filename = entry.get("filename", f"{dashboard_id}.yaml")
        results.append(
            {
                "id": dashboard_id,
                "mode": mode,
                "title": entry.get("title", dashboard_id),
                "icon": entry.get("icon"),
                "filename": filename,
                "show_in_sidebar": entry.get("show_in_sidebar", True),
                "storage_key": None,
                "storage_path": None,
                "global_lovelace_mode": global_mode,
            }
        )
    return results


async def _list_storage_dashboards() -> List[Dict[str, Any]]:
    """Discover dashboards in .storage/lovelace*."""
    results: List[Dict[str, Any]] = []
    storage_dir = file_manager.config_path / STORAGE_DIR
    if not storage_dir.exists():
        return results

    for item in sorted(storage_dir.iterdir()):
        if not item.is_file():
            continue
        name = item.name
        if name == "lovelace" or name.startswith("lovelace."):
            storage_key = name
            url_path = _url_path_from_storage_key(storage_key)
            title = url_path.replace("-", " ").title()
            if url_path == "lovelace":
                title = "Overview"
            results.append(
                {
                    "id": url_path,
                    "mode": "storage",
                    "title": title,
                    "icon": None,
                    "filename": None,
                    "show_in_sidebar": None,
                    "storage_key": storage_key,
                    "storage_path": _storage_path(storage_key),
                    "global_lovelace_mode": None,
                }
            )
    return results


async def list_dashboards() -> List[Dict[str, Any]]:
    """All dashboards: YAML-registered first, then storage (dedupe by id)."""
    yaml_boards = await _parse_yaml_dashboards()
    storage_boards = await _list_storage_dashboards()
    by_id: Dict[str, Dict[str, Any]] = {}
    for board in yaml_boards:
        by_id[board["id"]] = board
    for board in storage_boards:
        if board["id"] not in by_id:
            by_id[board["id"]] = board
    return list(by_id.values())


async def resolve_dashboard(dashboard_id: str) -> Dict[str, Any]:
    """Resolve dashboard metadata by id."""
    boards = await list_dashboards()
    normalized = dashboard_id.strip().lower()
    for board in boards:
        if board["id"].lower() == normalized:
            return board

    # Allow direct storage key patterns
    if normalized.startswith("lovelace"):
        storage_key = normalized
    else:
        storage_key = _storage_key_from_id(normalized)

    path = file_manager.config_path / _storage_path(storage_key)
    if path.exists():
        return {
            "id": _url_path_from_storage_key(storage_key),
            "mode": "storage",
            "title": dashboard_id,
            "storage_key": storage_key,
            "storage_path": _storage_path(storage_key),
            "filename": None,
        }

    raise FileNotFoundError(f"Dashboard not found: {dashboard_id}")


async def read_dashboard(dashboard_id: str) -> Dict[str, Any]:
    """Read normalized Lovelace config and metadata."""
    meta = await resolve_dashboard(dashboard_id)

    if meta["mode"] == "yaml":
        filename = meta.get("filename") or f"{meta['id']}.yaml"
        content = await file_manager.read_file(filename)
        config = yaml.safe_load(content) or {}
        return {
            **meta,
            "config": config,
            "yaml": content,
            "format": "yaml",
        }

    storage_key = meta.get("storage_key") or _storage_key_from_id(meta["id"])
    storage_data, storage_path = await _read_storage_raw(storage_key)
    config = _extract_lovelace_config(storage_data)
    return {
        **meta,
        "config": config,
        "storage_key": storage_key,
        "storage_path": storage_path,
        "format": "storage",
    }


async def apply_dashboard_by_id(
    dashboard_id: str,
    dashboard_config: Dict[str, Any],
    create_backup: bool = True,
    commit_message: Optional[str] = None,
) -> Dict[str, Any]:
    """Apply config to YAML file or storage JSON."""
    meta = await resolve_dashboard(dashboard_id)

    if meta["mode"] == "yaml":
        filename = meta.get("filename") or f"{meta['id']}.yaml"
        dashboard_yaml = yaml.dump(
            dashboard_config,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )
        msg = commit_message or f"Apply dashboard {dashboard_id}: {filename}"
        await file_manager.write_file(filename, dashboard_yaml, commit_message=msg)
        return {
            "id": meta["id"],
            "mode": "yaml",
            "path": filename,
            "views": len(dashboard_config.get("views", [])),
        }

    storage_key = meta.get("storage_key") or _storage_key_from_id(meta["id"])
    storage_data, storage_path = await _read_storage_raw(storage_key)
    storage_data = _set_lovelace_config(storage_data, dashboard_config)
    msg = commit_message or f"Apply storage dashboard: {dashboard_id}"
    await file_manager.write_file(storage_path, json.dumps(storage_data, indent=2, ensure_ascii=False), commit_message=msg)
    return {
        "id": meta["id"],
        "mode": "storage",
        "path": storage_path,
        "views": len(dashboard_config.get("views", [])),
    }


async def export_dashboard_to_yaml(
    dashboard_id: str,
    filename: Optional[str] = None,
) -> Dict[str, Any]:
    """Export storage dashboard config as YAML text and suggested filename."""
    meta = await resolve_dashboard(dashboard_id)
    if meta["mode"] != "storage":
        raise ValueError(f"Dashboard '{dashboard_id}' is not storage mode (mode={meta['mode']})")

    payload = await read_dashboard(dashboard_id)
    config = payload["config"]
    suggested = filename or f"dashboards/{meta['id']}.yaml"
    if "-" not in Path(suggested).stem:
        suggested = f"dashboards/{meta['id']}-dashboard.yaml"

    yaml_content = yaml.dump(
        config,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
    )
    return {
        "id": meta["id"],
        "suggested_filename": suggested,
        "yaml": yaml_content,
        "config": config,
        "register_example": {
            "lovelace": {
                "mode": "storage",
                "dashboards": {
                    meta["id"]: {
                        "mode": "yaml",
                        "title": meta.get("title", meta["id"]),
                        "icon": "mdi:view-dashboard",
                        "show_in_sidebar": True,
                        "filename": suggested,
                    }
                },
            }
        },
    }
