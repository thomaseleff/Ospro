# OSPRO GUI Theme Specification (Nord)

## Purpose

This document defines the visual design language for the GUI.

Scope:
- Keep the current screen information architecture from `GUI.md`.
- Adopt the Textual `nord` theme palette and semantics.
- Provide implementation-ready tokens and component behavior.

## Source References

- Textual design guide: https://textual.textualize.io/guide/design/
- Textual built-in `nord` theme token source: https://raw.githubusercontent.com/Textualize/textual/main/src/textual/theme.py
- Nord palette reference: https://www.nordtheme.com/docs/colors-and-palettes

## Theme Principles

- Calm, low-glare dark surfaces for kiosk readability.
- High information contrast for temperature, pressure, and safety state.
- Consistent semantic colors across all screens.
- Minimal visual noise; focus on actionable controls.

## Core Palette (From Textual `nord`)

Primary Nord/Textual tokens:

- `background`: `#2E3440`
- `panel`: `#3B4252`
- `surface`: `#434C5E`
- `foreground`: `#D8DEE9`
- `foreground-muted`: `#A3AEBE`
- `foreground-disabled`: `#4C566A`
- `border`: `#88C0D0`
- `border-blurred`: `#4C566A`
- `accent`: `#88C0D0`
- `primary`: `#88C0D0`
- `secondary`: `#81A1C1`
- `success`: `#A3BE8C`
- `warning`: `#EBCB8B`
- `error`: `#BF616A`
- `text`: `#D8DEE9`

Supporting ramp (Textual nord):

- `lighten-1`: `#363d4b`
- `lighten-2`: `#434d60`
- `lighten-3`: `#526077`
- `darken-1`: `#2c313d`
- `darken-2`: `#2b303b`
- `darken-3`: `#272c38`

## OSPRO Semantic Tokens

Use these names in Rust GUI code, independent of UI framework.

- `color.bg.app = #2E3440`
- `color.bg.panel = #3B4252`
- `color.bg.card = #434C5E`
- `color.bg.overlay = #2E3440CC`
- `color.text.primary = #D8DEE9`
- `color.text.muted = #A3AEBE`
- `color.text.disabled = #4C566A`
- `color.border.default = #4C566A`
- `color.border.focus = #88C0D0`
- `color.action.primary = #88C0D0`
- `color.action.secondary = #81A1C1`
- `color.state.success = #A3BE8C`
- `color.state.warning = #EBCB8B`
- `color.state.error = #BF616A`

Domain-specific semantic tokens:

- `color.metric.temperature = #88C0D0`
- `color.metric.pressure = #BF616A`
- `color.metric.setpoint = #81A1C1`
- `color.state.extracting = #A3BE8C`
- `color.state.stopped = #EBCB8B`
- `color.state.fault = #BF616A`

## Typography

- Font family: clean sans-serif with good kiosk legibility.
- Default size: `16px` equivalent.
- Scale:
- `type.title = 30`
- `type.section = 22`
- `type.body = 16`
- `type.label = 14`
- `type.metric = 36`
- `type.timer = 72`
- Weight:
- `regular` for labels/body.
- `semibold` for section headers.
- `bold` for primary metrics and timer.

## Spacing and Shape

- Grid unit: `8px`.
- Spacing scale:
- `space.1 = 4`
- `space.2 = 8`
- `space.3 = 12`
- `space.4 = 16`
- `space.5 = 24`
- `space.6 = 32`
- Corner radius:
- `radius.sm = 6`
- `radius.md = 10`
- `radius.lg = 16`
- Border width:
- `border.thin = 1`
- `border.strong = 2`

## Elevation

- Keep elevation subtle.
- Prefer border + slight value shift instead of strong shadows.
- Optional shadow for modal/card only:
- `shadow.modal = 0 8 24 rgba(0,0,0,0.35)`

## Component Styling Rules

### App Shell

- Window background uses `color.bg.app`.
- Main content areas use `color.bg.panel`.
- Grouped regions/cards use `color.bg.card`.

### Top Bar / Header Controls

- Header text: `color.text.primary`.
- Secondary info: `color.text.muted`.
- Header buttons (`Back`, `Close`) use secondary button style unless action is destructive.

### Buttons

Primary button (`Start`, `Save`, `Add Profile`):
- Background: `color.action.primary`
- Text: `#2E3440`
- Border: none or `color.action.primary`

Secondary button (`Settings`, `Refresh`, `Back`):
- Background: `color.action.secondary`
- Text: `#2E3440`

Danger button (`Stop`, destructive confirms):
- Background: `color.state.error`
- Text: `#ECEFF4`

Disabled button:
- Background: `#434C5E`
- Text: `color.text.disabled`
- Border: `color.border.default`

Interactive states:
- Hover: lighten background by one ramp step.
- Pressed: darken background by one ramp step.
- Focus: `2px` outline with `color.border.focus`.

### Inputs and Selectors

- Background: `color.bg.card`
- Text: `color.text.primary`
- Placeholder/text hint: `color.text.muted`
- Border default: `color.border.default`
- Border focus: `color.border.focus`
- Invalid: border `color.state.error`, helper text `color.state.error`

### Sliders

- Track: `#4C566A`
- Fill: `color.action.primary`
- Thumb: `#88C0D0` with dark outline `#2E3440`
- Disabled fill/thumb: `#434C5E` / `#4C566A`

### Cards and Panels

- Background: `color.bg.card`
- Border: `1px solid color.border.default`
- Title text: `color.text.primary`

### Modals

- Scrim: `color.bg.overlay`
- Modal panel background: `color.bg.panel`
- Modal border: `color.border.focus`
- Error modal title/accent: `color.state.error`
- Warning modal title/accent: `color.state.warning`
- Confirmation destructive action button: `color.state.error`

### Charts (Dashboard Plot + Profile Plot)

- Plot background: `color.bg.card`
- Axis/labels: `color.text.muted`
- Temperature line: `color.metric.temperature`
- Temperature set-point line: `color.metric.setpoint` (dashed)
- Pressure line: `color.metric.pressure`
- Target profile line: `#D08770` (Nord orange) dashed
- Grid lines: `#4C566A` at low alpha

## Screen-Specific Mapping

### Home Screen

- Brand/title uses `color.text.primary`.
- Live metric values:
- Temperature value in `color.metric.temperature`.
- Pressure value in `color.metric.pressure`.
- Profile value in `color.text.primary`.

### Dashboard

- Timer value:
- Idle: `color.text.primary`
- Extracting: `color.state.success`
- Stopped/flashing: alternate `color.state.warning` and `color.text.primary`
- Action row must preserve enabled/disabled contrast.

### Settings

- Section headers use `type.section` and `color.text.primary`.
- Inline action buttons (`Delete`, `Edit`, `New`) align to semantic colors.

### Pressure Profiler

- Parameter summary line uses `color.text.muted`.
- Active slider focus ring must always be visible on dark surfaces.

## State and Safety Semantics

Safety-sensitive visual meanings must remain stable:

- Green (`success`) means active/healthy runtime.
- Yellow (`warning`) means caution/manual confirmation needed.
- Red (`error`) means stop/fault/destructive action.
- Disabled controls must look non-interactive and never resemble enabled controls.

## Accessibility and Readability

- Target minimum contrast ratio:
- Body text: `>= 4.5:1`
- Large text/metrics: `>= 3:1`
- Ensure focus indicator is visible on every interactive element.
- Do not communicate state by color alone; pair with label/icon/text.
- Keep tap targets and clickable controls at least `44x44px` equivalent for touch.

## Implementation Notes for Rust GUI

- Implement theme as strongly typed tokens, not ad-hoc inline hex strings.
- Keep one authoritative theme module (for example `crates/ospro-ui/src/theme.rs`).
- Expose semantic APIs, e.g. `Theme::button(ButtonKind::Primary, WidgetState::Hovered)`.
- Keep chart palette in the same theme module to avoid drift.
- Add snapshot tests or visual regression checks for:
- Home
- Dashboard (idle/extracting/stopped)
- Settings
- Profile editor
- Modals (error/warning/confirm)

## Versioning

- Theme spec version: `1.0.0`
- Baseline: Textual `nord` (as published in Textual theme source at time of writing).
- Any palette or semantic remap changes should update this document and note reason in changelog/ADR when significant.
