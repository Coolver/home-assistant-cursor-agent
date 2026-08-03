# Dashboard migration (YAML + storage)

## On Home Assistant

- `dashboards/home-main.yaml` — migrated from `.storage/lovelace` (native cards by default)
- `dashboards/views/vacuum.yaml` — native `type: vacuum` (update `entity` when device exists)
- `packages/lovelace-dashboards.yaml` — registers `home-main` and `heating-now`
- `configuration.yaml` — `lovelace: !include packages/lovelace-dashboards.yaml`

## Defaults (no user manual steps)

- Native Lovelace cards only in generated YAML
- Mushroom: optional, installed by agent via HACS after user confirms in chat
- Cursor skill: optional via `ha_install_bundled_skill` from `bundled_skills/`

## Agent API

| Endpoint | Description |
|----------|-------------|
| `GET /api/lovelace/dashboards/list` | List YAML + storage dashboards |
| `GET /api/lovelace/dashboards/{id}` | Read normalized config |
| `POST /api/lovelace/dashboards/{id}/apply` | Apply to YAML or storage |
| `GET /api/lovelace/dashboards/enhancements/status` | Mushroom/HACS optional status |
| `POST /api/lovelace/dashboards/enhancements/install` | Install Mushroom (user-approved) |
| `GET /api/skills/bundled` | List bundled Cursor skills |
| `POST /api/skills/bundled/{name}/install` | Copy skill to `.cursor/skills/` |

## MCP tools

`ha_list_dashboards`, `ha_read_dashboard`, `ha_dashboard_enhancements_status`, `ha_install_dashboard_enhancements`, `ha_list_bundled_skills`, `ha_install_bundled_skill`
