# Repository Agent Guidance

## Mission

Ospro `v0.2.0` is a Rust replacement migration from Python `v0.1.0` behavior.
Treat Python runtime code as reference for parity, not as target architecture.

## Engineering Principles

- Prioritize simplicity as a design goal.
- Follow YAGNI: do not add structure, abstractions, or dependencies before a concrete need exists.
- Prefer the smallest implementation that satisfies current requirements and tests.

## Architectural Direction

- Primary runtime language: Rust.
- UI direction: touch-first native UI suitable for Raspberry Pi kiosk operation.
- Keep runtime local-first and lightweight.
- Avoid introducing remote/web architecture unless explicitly accepted by ADR.

## Rust Standards

- Rust edition: 2021 or newer.
- Toolchain pin: `rust-toolchain.toml` (`stable` + `rustfmt` + `clippy`).
- Formatting gate: `cargo fmt --all`.
- Lint gate: `cargo clippy --workspace --all-targets --all-features -- -D warnings`.
- Test gate: `cargo test --workspace --all-targets`.
- Prefer explicit typed API boundaries and cohesive modules.
- Use `Result`-based error propagation; avoid `unwrap`/`expect` in non-test code.

## Standard Dev Commands

Use cargo aliases from `.cargo/config.toml`:

- `cargo fmt-all`
- `cargo check-all`
- `cargo lint`
- `cargo test-all`

## Safety and Control Expectations

- Treat brew control behavior as safety-sensitive.
- Keep hardware access behind narrow traits/interfaces.
- Keep control logic deterministic and independently testable.
- Keep blocking IO off the UI thread.
- Document timing assumptions, sample rates, and fail-safe conditions.

## Dependency Policy

- Prefer minimal, maintained crates with active support.
- Add crates only when they materially reduce risk or complexity.
- Record significant dependency decisions in ADRs.

## Crate Boundary Policy

- Default to fewer crates and more internal modules during early implementation.
- Split into additional crates only when there is a clear boundary (independent lifecycle, strict API contract, or compile-time isolation benefit).
- If adding a new crate, document the reason in the change description; if strategic, capture it in an ADR.

## Workstream Policy

- Implement in bounded workstreams, each including code + tests + docs.
- Target each workstream at roughly 600 lines changed.
- Do not exceed 1,000 estimated lines changed per workstream.
- Maintain passing quality gates at every workstream boundary.

## Migration Policy

- Replace runtime implementation in Rust; avoid long-lived Python/Rust production hybrid.
- Validate parity against Python `v0.1.0` behavior via fixtures/logs/checklists.
- Keep changes small, reviewable, and reversible.

## Documentation Policy

- Significant architectural/process decisions require ADRs in `adr/`.
- Keep `README.md` and operator documentation consistent with active runtime behavior.
