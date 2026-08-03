"""Optional Lovelace UI enhancements (Mushroom via HACS) — never required."""
from __future__ import annotations

import json
import logging
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.services.file_manager import file_manager
from app.services.ha_websocket import get_ws_client

logger = logging.getLogger("ha_cursor_agent")

HACS_INSTALL_PATH = Path("/config/custom_components/hacs")
MUSHROOM_REPOSITORY = "piitaya/lovelace-mushroom"
MUSHROOM_HACS_CATEGORY = "plugin"
MUSHROOM_RESOURCE_URL = "/hacsfiles/lovelace-mushroom/mushroom.js"
LOVELACE_RESOURCES_STORAGE = ".storage/lovelace_resources"


def _hacs_installed() -> bool:
    return HACS_INSTALL_PATH.exists()


async def _read_lovelace_resources() -> Dict[str, Any]:
    try:
        raw = await file_manager.read_file(LOVELACE_RESOURCES_STORAGE)
        return json.loads(raw)
    except FileNotFoundError:
        return {
            "version": 1,
            "minor_version": 1,
            "key": "lovelace_resources",
            "data": {"items": []},
        }


def _mushroom_resource_registered(resources_data: Dict[str, Any]) -> bool:
    items = resources_data.get("data", {}).get("items", [])
    if not isinstance(items, list):
        return False
    for item in items:
        url = (item or {}).get("url", "")
        if "mushroom" in url.lower():
            return True
    return False


async def get_enhancements_status() -> Dict[str, Any]:
    """Report whether optional Mushroom stack is available (never blocks dashboards)."""
    hacs_ok = _hacs_installed()
    resources_data = await _read_lovelace_resources()
    resource_ok = _mushroom_resource_registered(resources_data)

    mushroom_in_www = False
    www_candidates = [
        Path(file_manager.config_path) / "www" / "community" / "lovelace-mushroom",
        Path(file_manager.config_path) / "www" / "mushroom.js",
    ]
    for candidate in www_candidates:
        if candidate.exists():
            mushroom_in_www = True
            break

    installed = resource_ok or mushroom_in_www
    return {
        "hacs_installed": hacs_ok,
        "mushroom_hacs_installed": installed,
        "mushroom_resource_registered": resource_ok,
        "mushroom_files_on_disk": mushroom_in_www,
        "recommended_resource_url": MUSHROOM_RESOURCE_URL,
        "can_auto_install": hacs_ok,
        "default_card_mode": "native",
        "enhanced_card_mode": "mushroom",
        "user_action_required": None
        if installed
        else (
            "Optional: ask user to approve ha_install_dashboard_enhancements for prettier cards. "
            "Native HA cards work without this."
        ),
    }


async def _install_mushroom_via_hacs() -> Dict[str, Any]:
    if not _hacs_installed():
        return {
            "success": False,
            "error": "hacs_not_installed",
            "message": "HACS is not installed. Dashboards work with native cards. "
            "Optional: install HACS via ha_install_hacs, then retry.",
        }

    ws_client = await get_ws_client()
    await ws_client.call_service(
        domain="hacs",
        service="download",
        service_data={"repository": MUSHROOM_REPOSITORY},
    )

    return {"success": True, "repository": MUSHROOM_REPOSITORY, "category": MUSHROOM_HACS_CATEGORY}


async def _register_mushroom_lovelace_resource() -> Dict[str, Any]:
    resources_data = await _read_lovelace_resources()
    if _mushroom_resource_registered(resources_data):
        return {"registered": False, "message": "Mushroom resource already registered"}

    items: List[Dict[str, Any]] = list(resources_data.get("data", {}).get("items", []))
    items.append(
        {
            "id": uuid.uuid4().hex,
            "url": MUSHROOM_RESOURCE_URL,
            "type": "module",
        }
    )
    resources_data.setdefault("data", {})["items"] = items
    await file_manager.write_file(
        LOVELACE_RESOURCES_STORAGE,
        json.dumps(resources_data, indent=2, ensure_ascii=False),
        commit_message="Register Mushroom Lovelace resource (dashboard enhancements)",
    )
    return {"registered": True, "url": MUSHROOM_RESOURCE_URL}


async def install_dashboard_enhancements() -> Dict[str, Any]:
    """
    Install optional Mushroom cards via HACS and register Lovelace resource.
    Safe to skip — native cards remain the default.
    """
    steps: List[Dict[str, Any]] = []

    hacs_step = await _install_mushroom_via_hacs()
    steps.append({"step": "hacs_download_mushroom", **hacs_step})
    if not hacs_step.get("success"):
        return {
            "success": False,
            "steps": steps,
            "message": hacs_step.get("message", "Failed to install Mushroom via HACS"),
        }

    import asyncio

    await asyncio.sleep(2)

    resource_step = await _register_mushroom_lovelace_resource()
    steps.append({"step": "lovelace_resource", **resource_step})

    status = await get_enhancements_status()
    return {
        "success": True,
        "steps": steps,
        "status": status,
        "message": "Mushroom installed. Hard-refresh the HA UI (Cmd+Shift+R). "
        "You can now use custom:mushroom-* cards in dashboards.",
    }
