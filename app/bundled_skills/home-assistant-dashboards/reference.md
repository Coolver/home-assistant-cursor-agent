# Dashboard reference

## Product rules

1. **Native cards by default** — works out of the box after addon + MCP update
2. **Mushroom optional** — offer in dialog; install via `ha_install_dashboard_enhancements` only after user says yes
3. **Skills optional** — offer `ha_install_bundled_skill`; never require manual copy from GitHub

## MCP tools

| Tool | When |
|------|------|
| `ha_dashboard_enhancements_status` | Before suggesting Mushroom |
| `ha_install_dashboard_enhancements` | After user approves |
| `ha_list_bundled_skills` | When user wants Cursor skill |
| `ha_install_bundled_skill` | After user approves skill install |

## Links

- [Mushroom](https://github.com/piitaya/lovelace-mushroom) — installed via HACS by agent, not manually
- [HA Lovelace dashboards](https://www.home-assistant.io/dashboards/dashboards/)
