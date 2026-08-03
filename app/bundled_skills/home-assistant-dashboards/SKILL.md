---
name: home-assistant-dashboards
description: Design and edit Home Assistant Lovelace dashboards using MCP tools. Defaults to native HA cards; optionally installs Mushroom via HACS after user approval. Use for dashboards, lovelace, cards, layout, vacuum, climate views.
---

# Home Assistant Dashboards

## Defaults (no extra installs)

- Use **native** Lovelace cards only (`entities`, `thermostat`, `vacuum`, `weather-forecast`, etc.)
- Do **not** add `resources:` or `custom:*` unless enhancements are installed
- YAML dashboards in `dashboards/`; use `ha_list_dashboards` → `ha_read_dashboard`

## Optional: prettier cards (user must approve)

When the user is working on dashboards and wants a better look:

1. `ha_dashboard_enhancements_status` — check HACS + Mushroom
2. If not installed, **ask in chat**: "Могу поставить Mushroom через HACS автоматически — карточки будут аккуратнее. Продолжить?"
3. Only after **yes**: `ha_install_dashboard_enhancements` (HACS download + Lovelace resource)
4. Then use `custom:mushroom-*` and add resource only if status says `mushroom_resource_registered`

Never require Mushroom. Never ask the user to manually download JS or edit HACS UI.

## Optional: Cursor skill delivery

Bundled with the agent — **not mandatory**.

1. `ha_list_bundled_skills` — see what's available
2. If user wants dashboard help in Cursor: offer `ha_get_bundled_skill` or `ha_install_bundled_skill`
3. `ha_install_bundled_skill` copies to `/config/.cursor/skills/` (when config is the workspace)
4. If workspace is not `/config`: use `ha_get_bundled_skill` and write files to `.cursor/skills/` locally

Fallback (optional, not required): user may copy skill from [agent repo bundled_skills](https://github.com/Coolver/home-assistant-cursor-agent/tree/main/bundled_skills).

## Tool order

1. `ha_list_dashboards`
2. `ha_read_dashboard`
3. `ha_analyze_entities_for_dashboard` (`summary_only=true`)
4. `ha_dashboard_enhancements_status` (when improving UI)
5. `ha_create_checkpoint`
6. `ha_apply_dashboard_by_id` or `ha_write_file`

## Card snippets

**Native (default):**

```yaml
type: vacuum
entity: vacuum.ENTITY_ID
```

```yaml
type: thermostat
entity: climate.ENTITY_ID
```

**Mushroom (only after enhancements installed):**

```yaml
type: custom:mushroom-vacuum-card
entity: vacuum.ENTITY_ID
```

## Anti-patterns

- Requiring Mushroom or manual HACS clicks
- `custom:*` cards without `ha_dashboard_enhancements_status` showing installed
- Long-term `.storage` edits without migration to YAML
- Installing >3 frontend cards at once

See [reference.md](reference.md).
