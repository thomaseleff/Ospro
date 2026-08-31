# UI State Machine Contract

Purpose: define canonical UI state transitions, guards, and side effects for Rust parity implementation.

References:
- `GUI.md`
- `dashboard.py`
- `crates/ospro-core/src/ui.rs`
- `crates/ospro-app/src/main.rs`

## 1) State Model

Top-level screen states:
- `Home`
- `Dashboard`
- `Plot`
- `Settings`
- `ProfileEditor`

Dashboard substates:
- `Idle`
- `ExtractingManual`
- `ExtractingAuto`
- `Stopped`
- `Fault`

Modal states:
- `None`
- `InputProfileName` (`M1`)
- `Error` (`M2`)
- `OverwriteWarning` (`M3`)
- `DeleteConfirm` (`M4`)

Invariant:
- Exactly one top-level screen is active.
- At most one modal is active.
- Active modal blocks events to base screen except modal actions.

## 2) Screen Transition Table

| From | Event | Guard | To | Side Effects |
| --- | --- | --- | --- | --- |
| Home | OpenDashboard | none | Dashboard.Idle | none |
| Home | OpenSettings | none | Settings | load current settings values |
| Dashboard.* | OpenPlot | state == Stopped | Plot | show latest chart/review |
| Dashboard.* | OpenSettings | settings_enabled | Settings | none |
| Dashboard.* | Back | back_enabled | Home | none |
| Settings | BackSave | valid config | Home or caller | persist settings |
| Settings | OpenProfileEditor | profile != Manual or creating new | ProfileEditor | load/create draft |
| ProfileEditor | Back | none | Settings | discard unsaved draft |
| Plot | Back | none | Dashboard.Stopped | none |

## 3) Dashboard Control Availability Matrix

IDs from `GUI.md`:
- `D04 Start`, `D05 Stop`, `D06 Plot`, `D07 Settings`, `D08 Save`, `D09 Reset`, `D01 Back`

| Dashboard State | D04 | D05 | D06 | D07 | D08 | D09 | D01 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Idle | enabled | disabled | disabled | enabled | disabled | disabled | enabled |
| ExtractingManual | disabled | enabled | disabled | disabled | disabled | enabled | disabled |
| ExtractingAuto | disabled | disabled | disabled | disabled | disabled | enabled | disabled |
| Stopped | enabled | disabled | enabled | disabled | enabled | enabled | disabled |
| Fault | disabled | disabled | disabled | disabled | disabled | enabled | disabled |

## 4) Modal Transition Table

| From Modal | Event | Guard | To Modal | Side Effects |
| --- | --- | --- | --- | --- |
| None | RaiseError(msg) | none | Error | show message |
| None | RequestOverwrite(name) | profile exists | OverwriteWarning | stage pending save |
| None | RequestDelete(name) | profile != Manual | DeleteConfirm | stage pending delete |
| None | RequestProfileName | from plot/profile flow | InputProfileName | initialize default name |
| Error | ConfirmNo/ConfirmYes/Okay | none | None | return focus to invoker |
| OverwriteWarning | ConfirmYes | none | None | commit profile save |
| OverwriteWarning | ConfirmNo | none | None | cancel staged save |
| DeleteConfirm | ConfirmYes | none | None | commit delete + refresh list |
| DeleteConfirm | ConfirmNo | none | None | cancel delete |
| InputProfileName | SaveName(name) | valid name | None | commit profile save |
| InputProfileName | Back | none | None | cancel |

## 5) Runtime State Mapping

Map control-engine states into UI dashboard substates:
- `BrewState::Idle` -> `Dashboard.Idle`
- `BrewState::Preinfusion|Extraction` + manual profile -> `Dashboard.ExtractingManual`
- `BrewState::Preinfusion|Extraction` + non-manual profile -> `Dashboard.ExtractingAuto`
- `BrewState::Done` -> `Dashboard.Stopped`
- `BrewState::Fault` -> `Dashboard.Fault`

## 6) Event Ownership

UI-owned events:
- navigation (`Open*`, `Back`)
- form mutation (`SetScale`, `SetSetPoint`, `SetFlush`, `SetProfile`)
- profile editor draft changes

Runtime-owned events:
- extraction state transitions
- sensor value updates
- fault events
- persistence result notifications

## 7) Validation Rules

- Reject transitions that violate guards; no-op with optional warning log.
- Every transition updates availability flags deterministically.
- Modal closure must restore focus to invoking control ID.

## 8) Minimal Test Matrix

Required tests:
- state->availability mapping for all dashboard substates
- modal blocking behavior
- guarded transitions (`OpenPlot` only when stopped, manual edit restriction)
- fault transition disables unsafe actions
