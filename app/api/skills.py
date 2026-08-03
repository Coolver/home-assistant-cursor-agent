"""Bundled Cursor skills — deliver via agent, never require manual install."""
from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.auth import verify_token
from app.models.schemas import Response
from app.services.file_manager import file_manager

logger = logging.getLogger("ha_cursor_agent")
router = APIRouter()

# Shipped with the addon (next to app/)
_BUNDLED_SKILLS_ROOT = Path(__file__).resolve().parent.parent / "bundled_skills"


def _list_skill_dirs() -> list[Path]:
    if not _BUNDLED_SKILLS_ROOT.is_dir():
        return []
    return sorted(p for p in _BUNDLED_SKILLS_ROOT.iterdir() if p.is_dir() and (p / "SKILL.md").is_file())


@router.get("/bundled", response_model=Response, dependencies=[Depends(verify_token)])
async def list_bundled_skills():
    """List Cursor skills bundled with the agent (optional install)."""
    skills = []
    for skill_dir in _list_skill_dirs():
        skills.append(
            {
                "name": skill_dir.name,
                "description": _read_skill_description(skill_dir / "SKILL.md"),
                "files": [f.name for f in skill_dir.rglob("*") if f.is_file()],
            }
        )
    return Response(
        success=True,
        message=f"Found {len(skills)} bundled skill(s)",
        data={
            "skills": skills,
            "count": len(skills),
            "note": "Optional. Use install endpoint or copy files into your IDE workspace .cursor/skills/",
        },
    )


def _read_skill_description(skill_md: Path) -> str:
    try:
        text = skill_md.read_text(encoding="utf-8")
        for line in text.splitlines():
            if line.startswith("description:"):
                return line.split("description:", 1)[1].strip()
    except OSError:
        pass
    return ""


@router.get("/bundled/{skill_name}", response_model=Response, dependencies=[Depends(verify_token)])
async def get_bundled_skill(skill_name: str):
    """Return all files for a bundled skill (for IDE to write locally)."""
    skill_dir = _BUNDLED_SKILLS_ROOT / skill_name
    if not skill_dir.is_dir() or not (skill_dir / "SKILL.md").is_file():
        return Response(success=False, message=f"Bundled skill not found: {skill_name}", data=None)

    files = {}
    for path in skill_dir.rglob("*"):
        if path.is_file():
            rel = str(path.relative_to(skill_dir))
            files[rel] = path.read_text(encoding="utf-8")

    return Response(
        success=True,
        message=f"Bundled skill: {skill_name}",
        data={
            "name": skill_name,
            "files": files,
            "install_hint": "Write files to .cursor/skills/{name}/ in your Cursor workspace, "
            "or call POST .../install if /config is your workspace root.",
        },
    )


@router.post("/bundled/{skill_name}/install", response_model=Response, dependencies=[Depends(verify_token)])
async def install_bundled_skill(
    skill_name: str,
    target_subdir: str = Query(
        ".cursor/skills",
        description="Directory under /config to copy skill into (default .cursor/skills)",
    ),
):
    """
    Copy bundled skill into Home Assistant config (e.g. .cursor/skills/ when config is the IDE workspace).
    Not required — skills are optional helpers for the AI in Cursor.
    """
    skill_dir = _BUNDLED_SKILLS_ROOT / skill_name
    if not skill_dir.is_dir():
        return Response(success=False, message=f"Bundled skill not found: {skill_name}", data=None)

    dest_root = file_manager.config_path / target_subdir.strip("/") / skill_name
    dest_root.mkdir(parents=True, exist_ok=True)

    copied = []
    for path in skill_dir.rglob("*"):
        if path.is_file():
            rel = path.relative_to(skill_dir)
            dest = dest_root / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dest)
            copied.append(str(dest.relative_to(file_manager.config_path)))

    return Response(
        success=True,
        message=f"Installed bundled skill '{skill_name}' to {target_subdir}/{skill_name}",
        data={
            "skill": skill_name,
            "target": str(dest_root.relative_to(file_manager.config_path)),
            "files_copied": copied,
            "optional": True,
        },
    )
