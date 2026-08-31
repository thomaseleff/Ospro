# Persistence Contract

Purpose: define when and how GUI actions persist data, including failures and rollback behavior.

References:
- `dashboard.py` persistence behavior
- `config/config.json`
- `config/profiles/*.json`
- Rust runtime config and telemetry paths in `crates/ospro-app/src/main.rs`

## 1) Persistence Surfaces

Configuration:
- `config/config.json`

Profile definitions:
- `config/profiles/<ProfileName>.json`

Extraction artifacts:
- Diagnostics CSV and plot PNG in configured diagnostics path

## 2) Save Timing Rules

Settings screen (`S6`):
- Form changes are staged in UI/runtime memory.
- Persist only on `S01 Back/Save`.
- `Close` exits without committing staged changes.

Dashboard extraction:
- `D08 Save` persists extraction artifacts (CSV + PNG).
- `D09 Reset` clears in-memory extraction buffers only.

Profile editor (`S7`):
- Slider/field updates are draft-only until `E12 Save`.
- `Back` cancels draft changes.

## 3) Profile CRUD Semantics

Create:
- New profile defaults to incremented `Custom_N`/`User_N` style name.
- If name is unique, write directly.

Overwrite:
- If target name exists, show `M3 Overwrite Warning`.
- Persist only when user confirms `Yes`.

Delete:
- Deleting `Manual` is forbidden; show `M2 Error`.
- For non-manual profile, show `M4 Delete Confirmation`.
- Delete only on `Yes`.

Edit:
- Editing `Manual` is forbidden; show `M2 Error`.
- Editing non-manual loads profile file into draft.

## 4) Validation and Error Handling

Validation failures (name empty, invalid value ranges, malformed profile) must:
- prevent write
- show `M2 Error` with concrete field-specific message
- preserve current draft for correction

I/O failures (permission/path/disk errors) must:
- prevent partial commit perception in UI
- show `M2 Error` with operation context (`save settings`, `save profile`, `delete profile`)
- keep user on originating screen/modal for retry or cancel

## 5) Atomicity and Rollback

Config/profile writes:
- write to temp file in same directory then rename into place (atomic replace where supported).
- on failure, original file remains unchanged.

Delete operations:
- if delete fails, keep profile visible and selected; show error.

Multi-step operations:
- if operation includes write + UI refresh, only refresh after successful write.

## 6) Runtime/UI Synchronization Rules

After successful writes:
- refresh in-memory model from persisted source-of-truth values.
- publish `StateUpdate` with updated lists/values.

After failed writes:
- do not mutate source-of-truth state in runtime.
- keep staged values visible where correction is possible.

## 7) File Compatibility Rules

- Runtime-internal model uses snake_case.
- Compatibility with legacy Python schema via serde aliasing/renames at boundaries.
- Do not propagate legacy camelCase names inside domain logic.

Profiles:
- preserve required settings structure and pressure curve fields needed for parity.

## 8) Required Tests

- Settings deferred save: change values then close without save -> no file mutation.
- Settings save: file mutation occurs and reload reflects changes.
- Profile overwrite path: warning modal + yes/no branching.
- Manual edit/delete blocked with error.
- Failed write leaves source files unchanged.
- Extraction save writes both CSV and PNG or reports failure clearly.
