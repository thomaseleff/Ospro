# OSPRO v0.2.0 Project Plan

## Project Description

Ospro is a Raspberry Pi-based espresso control application with a local touch UI used to execute and monitor espresso extractions.

`v0.2.0` is a full runtime migration from the Python `v0.1.0` baseline to Rust to improve reliability, maintainability, performance predictability, and architecture clarity while preserving core brewing behavior.

## Invariants

1. Local-first operation: brewing must not depend on network access.
2. Touch-first usability: core brewing workflow is fully operable by touch.
3. Safety-first runtime: faults default to fail-safe hardware behavior.
4. Deterministic control: control loops run on bounded cadence with explicit timing assumptions.
5. Behavioral parity baseline: Python `v0.1.0` defines expected baseline behavior unless superseded by ADR.
6. Quality gates: each merged increment must pass fmt, clippy, and tests.
7. Workstream completeness: each workstream must include code, documentation, and tests.

## Bounds

In scope for `v0.2.0`:
- Rust runtime replacement for core application behavior.
- Hardware integration for current Raspberry Pi IO and attached sensors.
- Touch UI for core extraction operations.
- Static extraction chart generation/viewing.
- Operator/developer docs required to run and maintain system.

Out of scope for `v0.2.0`:
- Net-new web platform architecture.
- Cloud-dependent functionality.
- Non-essential feature expansion beyond parity and operational robustness.

## Target Architecture

Workspace layout (simplicity/YAGNI baseline):

1. `ospro-app` crate
- Composition root and runtime orchestration.
- Application startup, lifecycle, and dependency wiring.

2. `ospro-core` crate
- Internal modules for `config`, `control`, `hardware`, `ui`, and `telemetry`.
- Keep these as modules until concrete pressure justifies additional crates.

Runtime model:
- UI emits intent events to orchestrator.
- Orchestrator coordinates control/hardware/config services.
- Control and hardware tasks run off UI thread and publish state updates.

## Implementation Workstreams

Workstream policy:
- Each workstream is comprehensive: code + tests + docs.
- Target roughly 600 changed lines per workstream.
- No workstream may exceed 1,000 estimated changed lines.

| Workstream | Status | Commits | Note |
| --- | --- | --- | --- |
| WS1: Foundation and Governance | Completed | `125590b` | Workspace, governance docs, and CI quality gates established. |
| WS2: Config and Domain Models | Completed | `bff47a0` | Typed config model + legacy Python schema compatibility + validation/tests. |
| WS3: Hardware Abstraction Layer | Completed | `54965e2` | HAL traits, mock backend, and Raspberry Pi backend skeleton landed. |
| WS4: Sensor and Actuator Ports | Completed | `7ec2271` | Sensor/actuator ports and parity-oriented conversion behavior landed. |
| WS5: Control Core and Safety State Machine | Completed | `aefebfd` | Deterministic control state machine + PID behavior and safety tests landed. |
| WS6: Slint Touch UI MVP | Completed | `4ae8f5c` | Touch UI MVP integrated with runtime and quality gates passing. |
| WS7: Static Plotting and Extraction Review | Completed | `89f8714`, `42b2e8a`, `b3cce14` | Chart rendering, persisted artifacts, and extraction review UX parity complete. |
| WS7.1: Gap Closure and Parity Hardening | Completed | `219357d`..`b3cce14` | Correctness/parity hardening checklist completed with commit evidence. |
| WS8: Integration, Parity, and Release Prep | Completed | `e5d5781`, `c2ae45d`, `d584ae2`, `ef76967` | Integration/parity tests, startup hardening, and release artifacts completed. |
| WS9: GUI Parity Closure (Python -> Rust) | Not started | N/A | Close the UI/UX gap between `dashboard.py` and Rust Slint UI using `GUI.md` + `THEME.md` as implementation contract. |
| WS10: GUI Theme Infrastructure Hardening (Post-Parity) | Not started | N/A | Optional post-parity refactor for reusable theme architecture once WS9 proves concrete needs. |
| WS11: GUI QA Automation Hardening (Post-Parity) | Not started | N/A | Optional post-parity visual QA automation (goldens/diff tooling) after manual parity is stable. |
| WS12: On-Device Validation and Release Sign-Off | Not started | N/A | Final Raspberry Pi HIL validation and release sign-off pending after GUI parity closure. |

### WS9: GUI Parity Closure (Python -> Rust)

Estimated size: ~900 changed lines total, executed as bounded slices (`<= 600` lines each, no slice `> 1,000`).

Objective:
- Replace current Slint MVP presentation with a production GUI matching Python `v0.1.0` behavior and layout intent for `1024x600`.
- Implement screen/state structure from `GUI.md`.
- Implement visual language from `THEME.md` (Nord-based semantic tokens).

#### WS9 Gap Analysis (Current State vs Target)

Observed current Rust UI implementation:
- Current Slint UI is a single MVP window with basic text + three buttons:
  - `crates/ospro-core/src/ui.rs:7`..`69`
  - Title still `Ospro WS6` at `crates/ospro-core/src/ui.rs:10`
  - `1024x768` viewport at `crates/ospro-core/src/ui.rs:8`..`9` (target is `1024x600`)
  - No screen routing (`Home/Dashboard/Plot/Settings/Profile Editor`)
- Current UI event model only includes:
  - `StartBrew`, `StopBrew`, `Reset` at `crates/ospro-core/src/ui.rs:72`..`76`
- `UiRuntime::status()` still reports `"slint-mvp"`:
  - `crates/ospro-core/src/ui.rs:150`..`152`
  - Asserted in app tests at `crates/ospro-app/src/main.rs:651`
- Runtime loop currently pushes fixed synthetic readings (`93C`, `9 bar`) and does not expose full settings/profile editing intents:
  - `crates/ospro-app/src/main.rs:348`..`351`

Python baseline breadth (already implemented in `dashboard.py`):
- Dashboard controls + stateful enable/disable behavior:
  - `dashboard.py:2172`..`2575`
- Plot screen with correl statistic and add-profile flow:
  - `dashboard.py:2578`..`2966`
- Settings screen with scale/setpoint/profile/flush controls:
  - `dashboard.py:2969`..`3305`
- Pressure profile editor with sliders + live profile plotting:
  - `dashboard.py:3308`..`4072`
- Root shell / home screen and navigation:
  - `dashboard.py:4075`..`4550`

Target spec references:
- Layout contract and screen/control IDs in `GUI.md:7`..`271`
- Nord token semantics and component style constraints in `THEME.md:25`..`260`

#### Target UI Architecture for WS9

```text
+-----------------------------+        +----------------------------------+
|  Slint View Layer           |        |  Runtime Orchestrator            |
|  (ospro-core::ui)           |        |  (ospro-app main loop)           |
|                             |        |                                  |
|  Screen Router              |<------>|  UiEvent receiver                |
|  - Home                     | events |  - start/stop/reset              |
|  - Dashboard                |        |  - settings/profile mutations    |
|  - Plot                     |        |  - modal decisions               |
|  - Settings                 |        |                                  |
|  - Profile Editor           |        |  StateUpdate sender              |
|  - Modals                   | update |  - state + metrics + availability|
+-----------------------------+        +----------------------------------+
         |
         v
+-----------------------------+
| Theme Tokens (THEME.md)     |
| + Layout Contract (GUI.md)  |
+-----------------------------+
```

#### Data / Event Model Delta Required

Current events are insufficient for parity. Expand `UiEvent` and `StateUpdate` in `crates/ospro-core/src/ui.rs`.

Proposed `UiEvent` additions (minimum):
- `OpenDashboard`, `OpenSettings`, `OpenPlot`, `Back`
- `SaveExtraction`, `Flush`
- `SetScale(String)`, `SetSetPoint(f64)`, `SetFlush(u8)`, `SetProfile(String)`
- `OpenProfileEditor { edit_existing: bool }`
- `ProfileEditorChanged(ProfileDraftPatch)`
- `SaveProfile`, `DeleteProfile(String)`, `RefreshProfiles`
- Modal intents: `ConfirmYes(ModalKind)`, `ConfirmNo(ModalKind)`

Proposed `StateUpdate` additions (minimum):
- `active_screen`, `modal_state`
- `button_enabled` flags mirroring `GUI.md` IDs (`D04`..`D09`, etc.)
- Settings form values + selectable profile list
- Profile editor draft values + derived params summary
- Theme mode/token references (or derived style enum)

Mock contract sketch:

```rust
pub enum Screen {
    Home,
    Dashboard(DashboardState),
    Plot,
    Settings,
    ProfileEditor,
}

pub enum DashboardState {
    Idle,
    Extracting { manual_stop_allowed: bool },
    Stopped,
    Fault,
}

pub struct UiAvailability {
    pub start: bool,
    pub stop: bool,
    pub plot: bool,
    pub save: bool,
    pub reset: bool,
    pub settings: bool,
    pub back: bool,
}
```

#### Layout Delivery Plan (Bounded Slices)

WS9.1 (`~450` lines) - Shell, routing, and Dashboard parity
- Replace MVP single-layout Slint tree with screen router and `1024x600` root window.
- Implement `S1`, `S2`, `S3`, `S4` from `GUI.md`.
- Implement state-dependent button availability parity for dashboard flow.
- Files:
  - `crates/ospro-core/src/ui.rs` (primary)
  - `crates/ospro-app/src/main.rs` (event handling + update mapping)
- Tests:
  - UI state mapping unit tests (`Idle/Extracting/Stopped` -> enabled controls)
  - Runtime tests asserting dashboard transitions populate matching availability flags.

WS9.2 (`~300` lines) - Plot + Settings parity
- Implement `S5` and `S6` layout + events.
- Wire settings interactions into runtime/config mutation path.
- Keep plot image integration, but place in `S5` structure and include profile/duration/correl fields.
- Files:
  - `crates/ospro-core/src/ui.rs`
  - `crates/ospro-app/src/main.rs`
  - optionally `crates/ospro-core/src/config.rs` (if additional typed update helpers required)
- Tests:
  - Settings mutation event tests (scale, set-point, flush, profile)
  - Plot visibility and review metadata mapping tests.

WS9.3 (`~550` lines) - Profile editor + modal system + minimal theming application
- Implement `S7`, `M1`, `M2`, `M3`, `M4` from `GUI.md`.
- Add profile-draft state and update callbacks.
- Apply `THEME.md` semantic tokens with the smallest practical implementation (constants/simple mapping). Avoid broad theming framework in WS9.
- Files:
  - `crates/ospro-core/src/ui.rs`
  - optional small theme constants module only if needed (`crates/ospro-core/src/ui_theme.rs`)
  - `crates/ospro-app/src/main.rs`
- Tests:
  - Modal blocking/focus behavior tests (logic-level)
  - Basic theme token mapping unit tests
  - Profile editor validation path tests (`Manual` restrictions, overwrite flow).

Note: If any slice estimate trends above `1,000` lines, split before implementation.

#### Screen/Feature Parity Matrix

| Capability | Python baseline reference | Rust current | WS9 target |
| --- | --- | --- | --- |
| Home screen | `dashboard.py:4262`..`4350` | Missing | Implement `S1` |
| Dashboard stateful controls | `dashboard.py:2172`..`2575`, `905`..`1331` | Partial (Start/Stop/Reset only) | Implement `S2/S3/S4` parity |
| Plot screen + add profile | `dashboard.py:2578`..`2966` | Partial image only | Implement `S5` + add-profile modal flow |
| Settings screen | `dashboard.py:2969`..`3305` | Missing | Implement `S6` with config events |
| Profile editor | `dashboard.py:3308`..`4072` | Missing | Implement `S7` |
| Error/warn/confirm modals | `dashboard.py:95`..`1885` | Missing | Implement `M1..M4` |
| Theme fidelity | `THEME.md:25`..`260` | Missing | Apply semantic tokens |
| Layout contract compliance | `GUI.md:7`..`271` | Missing | Full compliance checks |

#### Acceptance Criteria

- `cargo run` displays `1024x600` GUI with screen set `S1`..`S7` and modal set `M1`..`M4`.
- Dashboard controls follow behavioral contract from `GUI.md` section `5`.
- Theme token mapping reflects `THEME.md` (at minimum colors + typography scale + button states).
- No regression to safety constraints:
  - Extracting state still prevents unsafe control combinations.
  - Fault state remains fail-safe.
- Tests and quality gates pass:
  - `cargo fmt --all`
  - `cargo check --workspace --all-targets`
  - `cargo clippy --workspace --all-targets --all-features -- -D warnings`
  - `cargo test --workspace --all-targets`

#### WS9 Blocking Prerequisites (Must Be Added Before Coding)

1. Minimal visual parity Definition of Done (manual)
- Add `agents/contracts/visual-parity-baseline.md` with:
  - required manual captures for `S1..S7`, `M1..M4` at `1024x600`
  - capture scenarios per state (`idle`, `extracting`, `stopped`, modal-open)
  - simple pass/fail rule: layout/control behavior matches `GUI.md`; color/type intent matches `THEME.md`.

2. Formal UI state-machine contract
- Add `agents/contracts/ui-state-machine.md` containing:
  - screen-level transitions (`Home`, `Dashboard`, `Plot`, `Settings`, `ProfileEditor`)
  - dashboard substate transitions (`Idle`, `Extracting`, `Stopped`, `Fault`)
  - modal transitions (`None`, `Error`, `Warning`, `Confirm`, `InputProfileName`)
  - per-transition definition:
    - trigger event
    - guard condition
    - side effects
    - resulting availability flags

3. Settings/Profile persistence contract
- Add `agents/contracts/persistence-contract.md` with explicit rules for:
  - write timing (immediate vs deferred) per control
  - profile CRUD semantics (create/edit/delete/overwrite)
  - I/O error handling UX (modal text, retry/cancel behavior)
  - rollback behavior for failed writes
  - mapping to existing config/profile files under `config/` and `config/profiles/`

#### WS9 Required QA Loop (Per PR)

Each WS9 PR is incomplete without:
- Screenshot artifacts at `1024x600` for changed screens/states.
- A filled checklist section in `agents/contracts/gui-parity-checklist.md` referencing control IDs (example: `S6.S05`).
- A short “expected vs actual” table for any intentional divergence from `GUI.md`/`THEME.md`.
- Evidence that disabled/enabled behavior matches dashboard and modal contracts.

Explicitly out of scope for WS9:
- Automated screenshot diff tooling.
- Golden image pipelines.
- Large reusable design-system abstraction layers.

#### WS9 Early Realistic Data Validation (WS9.1 Gate)

Before WS9.1 is marked complete, replace synthetic static UI values with dynamic sampled updates in the UI test/demo path:
- Current static readings source: `crates/ospro-app/src/main.rs:348`..`351`.
- Gate requirement:
  - demonstrate varying temperature/pressure/timer updates across time
  - demonstrate non-manual profile path where manual stop becomes unavailable
  - verify dashboard control enablement under changing runtime state

This gate exists to prevent false confidence from static-value UI behavior.

#### Documentation Deliverables

- Update `GUI.md` only for intentional layout contract changes (not implementation drift).
- Update `THEME.md` only for intentional theme-token changes (with rationale).
- Add `agents/contracts/gui-parity-checklist.md` containing:
  - screen-by-screen acceptance checklist (`S1`..`S7`, `M1`..`M4`)
  - parity notes vs Python references
  - screenshots/artifacts from Rust GUI.

#### Recommended PR Strategy

1. PR-A: WS9.1 shell/router/dashboard state parity.
2. PR-B: WS9.2 plot/settings integration.
3. PR-C: WS9.3 profile editor/modals/theme.

Each PR should include:
- Estimated and actual line counts.
- Updated checklist evidence.
- Before/after screenshots at `1024x600`.

### WS10: GUI Theme Infrastructure Hardening (Post-Parity)

Estimated size: ~300 changed lines.

Scope:
- Refactor minimal WS9 theme constants into a reusable typed theme module only where duplication/pain has been proven.
- Keep behavior and visual output unchanged from WS9 unless explicitly approved.

Work items:
- [ ] Introduce typed theme tokens API for reuse (no speculative abstractions).
- [ ] Consolidate repeated component style mappings.
- [ ] Add focused tests for token-to-component mapping logic.

Exit criteria:
- Theme code simpler to maintain than WS9 baseline.
- No behavioral or visual regression versus WS9 parity captures.

### WS11: GUI QA Automation Hardening (Post-Parity)

Estimated size: ~350 changed lines.

Scope:
- Add lightweight visual QA automation after WS9 parity is stable.

Work items:
- [ ] Define repeatable screenshot capture script for `1024x600`.
- [ ] Add baseline artifact structure for key screens/states.
- [ ] Add CI-friendly comparison checks with practical tolerance and review workflow.

Exit criteria:
- Automated visual checks catch unintended GUI regressions.
- Manual parity checklist remains source of truth for intentional changes.

### WS12: On-Device Validation and Release Sign-Off

Estimated size: ~400 changed lines.

Scope:
- Execute Raspberry Pi hardware-in-loop validation using WS8-produced checklists/docs.
- Capture objective validation evidence and finalize release go/no-go decision.

Work items:
- [ ] Execute and record Raspberry Pi hardware-in-loop validation runs using checklist artifacts.
- [ ] Attach parity and device validation evidence to release candidate notes.
- [ ] Complete final release sign-off and rollback readiness confirmation.

Documentation:
- Completed HIL checklist with run metadata, outcomes, and issues.
- Finalized release sign-off record.

Tests:
- On-device scenario checks (manual + scripted where feasible), recorded as artifacts.

Exit criteria:
- On-device validation complete and recorded.
- Release sign-off approved with rollback readiness confirmed.

## Execution and Review Rules

1. One active workstream at a time.
2. Workstream PRs must include explicit estimated and actual line-change counts.
3. If a workstream estimate exceeds 1,000 lines, split before implementation.
4. Any scope change to invariants/bounds requires ADR update.
5. No release without completed WS8 parity, WS9 GUI parity closure, and WS12 on-device sign-off.

## Rust Tooling and Style Enforcement

Repository-level tooling baseline:
- `rust-toolchain.toml`: pins stable toolchain and required components (`rustfmt`, `clippy`).
- `.rustfmt.toml`: consistent formatting defaults (2021 edition, width/newline policy).
- `clippy.toml`: lint thresholds and project-wide lint preferences.
- `.cargo/config.toml`: standard command aliases for formatting, checking, linting, tests.
- `.github/workflows/rust-quality.yml`: CI enforcement for fmt, clippy (`-D warnings`), and tests.

Required local check sequence before merge:
1. `cargo fmt --all`
2. `cargo check --workspace --all-targets`
3. `cargo clippy --workspace --all-targets --all-features -- -D warnings`
4. `cargo test --workspace --all-targets`
