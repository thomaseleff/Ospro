# GUI Visual Parity Baseline Contract

Purpose: define the manual visual parity contract for Rust GUI implementation at `1024x600`.

References:
- `GUI.md` (layout + control IDs)
- `THEME.md` (Nord token semantics)
- `dashboard.py` (behavioral baseline)

## 1) Capture Requirements

Viewport:
- `1024x600` only.

Required screen captures:
- `S1` Home
- `S2` Dashboard Idle
- `S3` Dashboard Extracting (Manual)
- `S3` Dashboard Extracting (Non-manual)
- `S4` Dashboard Stopped/Ready
- `S5` Plot (Manual profile)
- `S5` Plot (Non-manual profile)
- `S6` Settings
- `S7` Profile Editor
- `M1` Input Profile Name
- `M2` Error
- `M3` Overwrite Warning
- `M4` Delete Confirmation

## 2) Scenario Setup

Use deterministic scenario labels:
- `idle_manual`
- `extracting_manual`
- `extracting_auto_profile`
- `stopped_ready`
- `plot_manual`
- `plot_auto_profile`
- `settings_default`
- `profile_editor_default`

For each capture include metadata:
- Screen ID
- Scenario label
- Timestamp
- Branch/commit
- Runtime mode (`mock` or `raspberry-pi`)

## 3) Artifact Naming Convention

Store screenshots under:
- `agents/artifacts/`

Filename format:
- `<screen-id>__<scenario>__1024x600.png`

Examples:
- `S2__idle_manual__1024x600.png`
- `M3__profile_overwrite__1024x600.png`

## 4) Pass/Fail Checklist

A capture is PASS only if all checks pass:

Layout parity (`GUI.md`):
- Header/content/action/footer order matches.
- Controls required by screen ID exist.
- Control ordering matches wireframe intent.
- Disabled controls are visually distinct and semantically disabled.

Behavior parity (`dashboard.py`):
- Dashboard button enable/disable state matches current runtime state.
- Non-manual extraction disables manual stop.
- Modal blocks underlying interaction.

Theme parity (`THEME.md`):
- Core semantic colors applied correctly (temp/pressure/action/warn/error).
- Contrast and readability meet touch kiosk expectations.
- Primary/secondary/danger button styling is distinguishable.

## 5) Allowed Deviations

Allowed without escalation:
- Runtime-derived numeric values differ from sample values in wireframes.
- Small text wrapping differences where content length varies.

Requires explicit note in PR "Expected vs Actual":
- Missing or moved controls.
- Changed control order.
- New visual tokens not in `THEME.md`.
- Any behavior change from `dashboard.py` baseline.

## 6) Review Log Template

Use this table in PR descriptions:

| Screen | Scenario | Result | Notes |
| --- | --- | --- | --- |
| S2 | idle_manual | Pass/Fail | |
| S3 | extracting_auto_profile | Pass/Fail | |
| M3 | profile_overwrite | Pass/Fail | |

## 7) Completion Criteria

Visual baseline is complete when:
- All required captures exist with required naming.
- Checklist table has no unresolved FAIL items.
- Any approved deviation is documented and linked to corresponding `GUI.md`/`THEME.md` update.
