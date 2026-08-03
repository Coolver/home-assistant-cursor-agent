# 🎨 LOVELACE DASHBOARD GENERATION (AI-DRIVEN)

**Defaults:** Native Home Assistant cards only — no Mushroom, no manual HACS steps for the user.

**Optional:** After user approves in chat, install Mushroom via `ha_install_dashboard_enhancements`.

---

## Workflow

### 1. Discover

```
ha_list_dashboards
ha_read_dashboard {id}
ha_analyze_entities_for_dashboard (summary_only=true)
```

Do **not** rely on `ha_preview_dashboard` for storage dashboards.

### 2. Optional UI enhancements (ask first!)

```
ha_dashboard_enhancements_status
```

If `mushroom_hacs_installed` is false and user cares about looks:

> "Дашборд можно улучшить карточками Mushroom — установлю через HACS автоматически. Нужно ваше подтверждение. Без этого всё работает на стандартных карточках HA."

Only after **yes**:

```
ha_install_dashboard_enhancements
```

### 3. Optional Cursor skill (ask first!)

```
ha_list_bundled_skills
```

If user wants persistent dashboard guidance in Cursor:

> "Могу установить skill `home-assistant-dashboards` в ваш проект через агента (необязательно)."

After **yes**: `ha_install_bundled_skill` or `ha_get_bundled_skill` + write to `.cursor/skills/`.

### 4. Generate YAML (in Cursor)

- **Default:** `entities`, `thermostat`, `vacuum`, `weather-forecast`, `conditional`
- **After Mushroom:** `custom:mushroom-*` + resources only if enhancements status says installed

Filename must contain a hyphen: `home-main.yaml`, `climate-control.yaml`.

### 5. Apply safely

```
ha_create_checkpoint
ha_apply_dashboard_by_id OR ha_apply_dashboard
ha_check_config
ha_reload_config
```

---

## Card types (native default)

| Domain | Card |
|--------|------|
| climate | thermostat |
| vacuum | vacuum |
| light | light |
| sensor | entities |
| weather | weather-forecast |

---

## Never

- Require Mushroom or manual `/local/mushroom.js` setup
- Use `custom:*` without checking enhancements status
- Skip checkpoint before writes
- Force skill install — always optional

For conditional cards see **06_conditional_cards.md**.
