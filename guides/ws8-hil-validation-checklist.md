# WS8 Hardware-in-Loop Validation Checklist

Date: ____________________  
Operator: ____________________  
Hardware target: ____________________

## Build and Gate Checks

- [ ] `cargo fmt --all`
- [ ] `cargo check --workspace --all-targets`
- [ ] `cargo clippy --workspace --all-targets --all-features -- -D warnings`
- [ ] `cargo test --workspace --all-targets`

## Device Configuration

- [ ] `config/config.json` present on target
- [ ] `config/profiles/*.json` present on target
- [ ] Diagnostics directory writable
- [ ] GPIO/SPI/I2C interfaces enabled on Raspberry Pi

## Runtime Flow Validation

- [ ] Runtime starts without panic
- [ ] UI renders and responds to touch inputs
- [ ] `Start` transitions to preinfusion behavior
- [ ] `Stop` transitions to `Done` and saves artifacts
- [ ] `Reset` returns to `Idle`

## Artifact Validation

- [ ] CSV created in diagnostics directory
- [ ] PNG chart created in diagnostics directory
- [ ] CSV includes expected metadata fields:
  - `User`, `UniqueID`, `Date`, `Time`, `Profile`, `ProfileValues`
- [ ] Extraction review panel displays last-shot summary

## Fault and Safety Validation

- [ ] Injected fault transitions to `Fault` state
- [ ] Fault path issues shutdown action
- [ ] Actuator cleanup path executes on runtime exit/fault

## Sign-Off

- [ ] WS8 parity checks passed
- [ ] On-device validation passed
- [ ] Release candidate approved

Notes:

```
____________________________________________________________________
____________________________________________________________________
____________________________________________________________________
```
