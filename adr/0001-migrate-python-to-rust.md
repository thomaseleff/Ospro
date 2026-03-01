# ADR 0001: Migrate Application Architecture from Python to Rust

- Status: Accepted
- Date: 2026-03-01
- Version Target: v0.2.0

## Context

Ospro is a Raspberry Pi-based espresso control application with a local touchscreen UI.

The Python runtime established in `v0.1.0` is functional but difficult to evolve safely:
- Large monolithic UI surface with global mutable state.
- In-progress refactor branches with partial architectural changes.
- Configuration/schema drift across files and naming conventions.

For `v0.2.0`, the project needs a clean architectural reset with stronger correctness guarantees and clearer module boundaries.

## Decision

For `v0.2.0`, Ospro will migrate the runtime application from Python to Rust.

This is a replacement migration (not a long-lived hybrid runtime):
- Python `v0.1.0` remains the behavioral baseline/reference.
- Rust becomes the primary implementation language for runtime UI/control/hardware logic.
- Existing Python code is used for parity validation during migration, then replaced as active runtime.

## Scope

In scope:
- Touch-first local UI runtime.
- Raspberry Pi hardware IO integration (GPIO/PWM/SPI/I2C).
- Temperature and pressure control loop runtime.
- Configuration/profile loading, validation, and migration compatibility.
- Static extraction chart rendering.

Out of scope:
- New web platform architecture.
- Net-new product features beyond parity, safety, and maintainability goals.

## Rationale

- Strong compile-time guarantees for safety-sensitive control and IO boundaries.
- Better long-term maintainability through strict typing and modular crates.
- Predictable performance/resource usage on constrained Raspberry Pi hardware.
- Opportunity to avoid further churn in incomplete Python refactors.

## Consequences

Positive:
- Clear architecture and language direction for `v0.2.0+`.
- Improved testability and reliability foundations.
- Better separation of UI, control logic, and hardware interfaces.

Costs:
- Significant one-time migration effort.
- New toolchain and deployment pipeline setup.
- Temporary productivity cost while establishing Rust-first patterns.

## Alternatives Considered

1. Continue Python + Tkinter refactor
- Rejected: limited long-term architectural payoff and continued churn risk.

2. Python + TUI framework
- Rejected: misaligned with touch-first appliance UX.

3. Python + local web UI
- Deferred: plausible future direction, not required for current minimal product scope.

## Implementation Notes

- Start migration branch from `main` as approved.
- Govern project process with repository `AGENTS.md` and ADR guidance.
- Execute migration in bounded workstreams with parity gates against Python `v0.1.0`.
- Require code + tests + documentation in each workstream before merge.
