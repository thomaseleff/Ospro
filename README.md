# Ospro

Ospro `v0.2.0` is a Rust runtime migration of the Python `v0.1.0` espresso controller behavior.

## Status

- Active runtime target: Rust (`crates/ospro-app` + `crates/ospro-core`)
- Parity baseline: Python `v0.1.0` behavior, validated through fixtures and integration tests
- Scope and workstreams: [`OSPRO.md`](OSPRO.md)

## Repository Layout

- `crates/ospro-app`: composition root and runtime orchestration
- `crates/ospro-core`: config, control, hardware, telemetry, and UI modules
- `config/`: runtime config and pressure profile files
- `diagnostics/`: extraction CSV and static chart artifacts
- `guides/`: operator/deployment docs
- `adr/`: architecture decision records

## Rust Runtime Quickstart

### Prerequisites

- Rust stable toolchain (see `rust-toolchain.toml`)
- Platform dependencies required by Slint and `plotters`

### Build and Run

```bash
cargo run -p ospro-app
```

Optional config override:

```bash
OSPRO_CONFIG_PATH=/absolute/path/to/config.json cargo run -p ospro-app
```

If `OSPRO_CONFIG_PATH` fails to load, runtime falls back to repository `config/config.json`, then finally to internal defaults.

## Quality Gates

Run before merge:

```bash
cargo fmt --all
cargo check --workspace --all-targets
cargo clippy --workspace --all-targets --all-features -- -D warnings
cargo test --workspace --all-targets
```

Equivalent aliases are available in `.cargo/config.toml`:

- `cargo fmt-all`
- `cargo check-all`
- `cargo lint`
- `cargo test-all`

## Operator and Release Docs

- Deployment + troubleshooting: [`guides/rust-runtime-operations.md`](guides/rust-runtime-operations.md)
- Hardware-in-loop validation artifact: [`guides/ws8-hil-validation-checklist.md`](guides/ws8-hil-validation-checklist.md)
- `v0.2.0` release notes + rollback: [`guides/v0.2.0-release-notes.md`](guides/v0.2.0-release-notes.md)

## Safety Notes

- Control behavior is safety-sensitive; faults must default to fail-safe action paths.
- Hardware interfaces are trait-bounded and mock-testable.
- Keep blocking IO off the UI thread and preserve deterministic control timing assumptions.
