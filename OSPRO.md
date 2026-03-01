# OSPRO v0.2.0 Project Plan

## Project Description

Ospro is a Raspberry Pi-based espresso control application with a local touch UI used to execute and monitor espresso extractions.

`v0.2.0` is a full runtime migration from the Python `v0.1.0` baseline to Rust to improve reliability, maintainability, performance predictability, and architecture clarity while preserving core brewing behavior.

## Progress

- Date: 2026-03-01
- Active branch: `v0.2.0-rust`
- Completed:
  - WS1 committed (`125590b`): governance docs, Rust tooling standards, CI quality gates, simplified workspace scaffold.
  - WS2 committed (`bff47a0`): Rust-style typed config model, legacy Python schema compatibility loader, validation rules, integration tests + fixtures.
- In progress:
  - WS3 Hardware Abstraction Layer (HAL traits, mock backend behavior, Raspberry Pi backend skeleton, hardware error taxonomy).

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

### WS1: Foundation and Governance

Estimated size: ~700 changed lines.

Scope:
- Create migration branch from `main`.
- Add governance docs (`adr/0001`, repo `AGENTS.md`, `adr/AGENTS.md`).
- Add this plan (`OSPRO.md`).
- Scaffold Rust workspace with baseline crate/module layout.
- Add CI quality gates (`fmt`, `clippy -D warnings`, `test`).

Code changes:
- Root `Cargo.toml` workspace.
- Initial crate manifests and placeholder modules.
- CI workflow and toolchain config.

Documentation:
- Update root docs for Rust toolchain bootstrap (minimal).
- Contribution/dev quick-start for workspace commands.

Tests:
- Workspace smoke tests and CI command verification.

Exit criteria:
- Workspace compiles.
- CI gates pass on empty scaffolding.

### WS2: Config and Domain Models

Estimated size: ~800 changed lines.

Scope:
- Implement typed config/profile models.
- Build Python `v0.1.0` schema-compatible loader/migrator.
- Add validation rules and explicit error reporting.

Code changes:
- `ospro-core::config` model definitions and parser.
- Migration/normalization from legacy field names.
- Config write/read contract for Rust runtime.

Documentation:
- Config schema reference and migration notes.

Tests:
- Fixture-based parse/migrate tests.
- Validation failure-path tests.
- Round-trip serialization tests.

Exit criteria:
- All baseline configs load and validate predictably.

### WS3: Hardware Abstraction Layer

Estimated size: ~850 changed lines.

Scope:
- Define HAL traits for GPIO/PWM/SPI/I2C.
- Implement mock backend and Raspberry Pi backend skeleton.
- Standardize hardware error taxonomy.

Code changes:
- `ospro-core::hardware` interfaces and backend modules.
- Backend selection wiring.

Documentation:
- HAL contracts and backend behavior notes.

Tests:
- Mock backend behavior tests.
- Trait-level contract tests.

Exit criteria:
- Mock backend fully testable.
- Pi backend compiles and exposes expected interfaces.

### WS4: Sensor and Actuator Ports

Estimated size: ~900 changed lines.

Scope:
- Port MAX31855 and ADS1115 sensor access.
- Port actuator wrappers (extraction output + PWM driver abstraction).
- Preserve conversion/calibration semantics.

Code changes:
- Sensor adapters in `ospro-core::hardware` (or a dedicated sensor module if justified).
- Units conversion and normalization functions.

Documentation:
- Sensor assumptions/calibration limits.

Tests:
- Conversion parity tests against reference fixtures.
- Sensor read error/fallback behavior tests.

Exit criteria:
- Sensor/actuator interactions are stable under mock + Pi-target build.

### WS5: Control Core and Safety State Machine

Estimated size: ~900 changed lines.

Scope:
- Implement runtime states and transitions.
- Implement control tick loop and safety fallback behavior.
- Isolate pure control logic from IO side effects.

Code changes:
- `ospro-core::control` state machine and control engine.
- Event/command model between control and orchestrator.

Documentation:
- Safety model and transition table.

Tests:
- Transition matrix tests.
- Deterministic loop behavior tests.
- Fault injection tests.

Exit criteria:
- Control runtime meets invariant safety rules under tested scenarios.

### WS6: Slint Touch UI MVP

Estimated size: ~950 changed lines.

Scope:
- Implement core touchscreen workflow for brewing operations.
- Display live metrics and operational state.
- Wire user intents to orchestration layer.

Code changes:
- `ospro-core::ui` Slint views/components.
- View-model bindings and command dispatch.

Documentation:
- UI flow map and operator interaction notes.

Tests:
- Presenter/view-model tests.
- Basic UI interaction tests where feasible.

Exit criteria:
- Touch-first MVP flow is complete and connected to runtime actions.

### WS7: Static Plotting and Extraction Review

Estimated size: ~700 changed lines.

Scope:
- Implement static chart rendering pipeline.
- Display extraction charts in Slint via image buffers.

Code changes:
- `ospro-core::telemetry` chart renderer (`plotters`).
- UI integration for chart display.

Documentation:
- Plotting data contract and rendering pipeline.

Tests:
- Snapshot/regression tests for deterministic renders.
- Data boundary tests for empty/short sessions.

Exit criteria:
- Static chart generation and display are stable and predictable.

### WS8: Integration, Parity, and Release Prep

Estimated size: ~850 changed lines.

Scope:
- End-to-end integration across crates.
- Parity validation against Python `v0.1.0` references.
- On-device Raspberry Pi validation and release documentation.

Code changes:
- Final orchestration wiring and startup/runtime polish.
- Error/reporting surfaces for operators.

Documentation:
- README runtime instructions for Rust.
- Operator deployment notes and troubleshooting.
- `v0.2.0` release notes and rollback checklist.

Tests:
- Integration tests spanning config/control/hardware mock/UI events.
- Hardware-in-loop validation checklist artifacts.

Exit criteria:
- Defined parity checks pass.
- On-device validation complete.
- Release package/docs ready.

## Execution and Review Rules

1. One active workstream at a time.
2. Workstream PRs must include explicit estimated and actual line-change counts.
3. If a workstream estimate exceeds 1,000 lines, split before implementation.
4. Any scope change to invariants/bounds requires ADR update.
5. No release without completed WS8 parity and on-device sign-off.

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
