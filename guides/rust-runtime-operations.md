# Rust Runtime Operations (WS8)

## Deployment Target

- Raspberry Pi-based kiosk runtime
- Local-first execution (no network required for extraction)
- Touch-first operation through Slint UI

## Deployment Procedure

1. Install Rust stable toolchain on target host.
2. Clone repository branch intended for deployment.
3. Verify config files:
   - `config/config.json`
   - `config/profiles/*.json`
4. Build and smoke-test on device:
   - `cargo check --workspace --all-targets`
   - `cargo test --workspace --all-targets`
5. Run runtime:
   - `cargo run -p ospro-app`

## Runtime Inputs and Outputs

- Input config path:
  - `OSPRO_CONFIG_PATH` environment variable (optional override)
  - fallback path: repository `config/config.json`
- Output artifacts:
  - extraction CSV files in `diagnostics/`
  - extraction chart PNG files in `diagnostics/`

## Operator-Facing Fault Surface

- Startup config load failures are emitted to stderr and fall back to default path/internal defaults.
- UI initialization and runtime execution failures are emitted to stderr and stop runtime safely.
- Control faults transition to `Fault` state and issue `Shutdown` actions.

## Troubleshooting

1. Symptom: runtime starts with default user/profile unexpectedly.
   - Check `OSPRO_CONFIG_PATH` value and file readability.
   - Validate config JSON against runtime schema aliases.
2. Symptom: no new extraction artifacts in `diagnostics/`.
   - Ensure directory is writable.
   - Confirm extraction reached a `SaveData` path (`Stop` or timer completion).
3. Symptom: chart not visible in UI.
   - Confirm PNG file exists and is readable.
   - Verify UI process has path access to diagnostics directory.
4. Symptom: no hardware actuation on device.
   - Confirm backend selection and HAL implementation status.
   - Validate pin mappings in config (`extraction.pin`, `tpid.pin`, `ppid.pin`).
