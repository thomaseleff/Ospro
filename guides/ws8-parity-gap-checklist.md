# WS8 Parity Gap Checklist and Execution Plan

## Objective

Track and close Python `v0.1.0` to Rust `v0.2.0` runtime parity gaps before release sign-off.

## Usage Rules

- One gap owner per item.
- Do not mark complete without code, tests, and docs updates.
- Attach evidence (test name, screenshot, artifact path, or commit) for each completed checkbox.
- Keep scope parity-focused; no net-new product features.

## Exit Criteria

- All `P1` gaps closed.
- All `P2` gaps either closed or explicitly deferred by ADR/release note.
- `cargo fmt --all`, `cargo clippy --workspace --all-targets --all-features -- -D warnings`, and `cargo test --workspace --all-targets` passing in CI.
- on-device HIL checklist complete.

## Gap Tracker

### P1-01 Raspberry Pi HAL parity (GPIO/PWM/SPI/I2C)

Status: `Open`  
Owner: `TBD`

Python baseline:
- Real platform IO exists in [raspberry_pi.py](/t/Documents/Projects/Ospro/ospro/platform/raspberry_pi.py:7).
- Sensors use real hardware libs in [temp.py](/t/Documents/Projects/Ospro/ospro/sensors/temp.py:53) and [pressure.py](/t/Documents/Projects/Ospro/ospro/sensors/pressure.py:55).

Rust gap:
- Raspberry Pi HAL returns unsupported errors in [hardware.rs](/t/Documents/Projects/Ospro/crates/ospro-core/src/hardware.rs:381).

Checklist:
- [ ] Implement `RaspberryPiGpio` contract (`setup`, `write`, `read`, `cleanup`).
- [ ] Implement `RaspberryPiPwm` contract (`start`, `set_duty_cycle`, `duty_cycle`, `stop`).
- [ ] Implement `RaspberryPiSpi::transfer`.
- [ ] Implement `RaspberryPiI2c::write_read`.
- [ ] Add integration tests for all Raspberry Pi HAL paths (or gated HIL tests).
- [ ] Update docs in [rust-runtime-operations.md](/t/Documents/Projects/Ospro/guides/rust-runtime-operations.md:48).

Acceptance:
- Runtime can actuate extraction/pump/heater on target Pi without unsupported errors.

Evidence:
- Pending.

---

### P1-02 Live sensor integration in runtime loop

Status: `Open`  
Owner: `TBD`

Python baseline:
- Continuous live sensor reads in [dashboard.py](/t/Documents/Projects/Ospro/dashboard.py:934), [dashboard.py](/t/Documents/Projects/Ospro/dashboard.py:1087), and [temp_pid.py](/t/Documents/Projects/Ospro/temp_pid.py:87).

Rust gap:
- Runtime uses fixed readings (`93C`, `9 bar`) in [main.rs](/t/Documents/Projects/Ospro/crates/ospro-app/src/main.rs:348).

Checklist:
- [ ] Wire `Max31855Sensor` and `Ads1115Sensor` into `run_runtime_loop`.
- [ ] Respect backend selection (`mock` vs `raspberry-pi`) for sensor creation.
- [ ] Handle read failures with fault transition parity.
- [ ] Add integration tests for mock live-read flow.
- [ ] Add HIL verification step for real sensor readings.

Acceptance:
- UI metrics and control actions respond to actual sensor changes.

Evidence:
- Pending.

---

### P1-03 Brew timing semantics parity (manual vs profile-driven stop)

Status: `Open`  
Owner: `TBD`

Python baseline:
- Manual profile runs until user stop in [dashboard.py](/t/Documents/Projects/Ospro/dashboard.py:1009).
- Non-manual stop tied to profile duration in [dashboard.py](/t/Documents/Projects/Ospro/dashboard.py:1132).

Rust gap:
- Always preinfusion/extraction timers from config in [control.rs](/t/Documents/Projects/Ospro/crates/ospro-core/src/control.rs:271).

Checklist:
- [ ] Define parity spec for manual/profile stop behavior.
- [ ] Update control state machine/runtime orchestration to match spec.
- [ ] Add tests for manual stop-only flow.
- [ ] Add tests for profile-driven automatic stop.
- [ ] Validate artifact timing (`Duration`, `ProfileValues`) remains consistent.

Acceptance:
- Manual and profile modes behave like Python baseline unless explicitly superseded.

Evidence:
- Pending.

---

### P1-04 Temperature PID behavior parity

Status: `Open`  
Owner: `TBD`

Python baseline:
- Unstable-reading pass, dead-zone under/over handling, extraction override, sample-rate pacing in [temp_pid.py](/t/Documents/Projects/Ospro/temp_pid.py:95), [temp_pid.py](/t/Documents/Projects/Ospro/temp_pid.py:124), [temp_pid.py](/t/Documents/Projects/Ospro/temp_pid.py:159), [temp_pid.py](/t/Documents/Projects/Ospro/temp_pid.py:239), [temp_pid.py](/t/Documents/Projects/Ospro/temp_pid.py:253).

Rust gap:
- Current PID semantics differ in [control.rs](/t/Documents/Projects/Ospro/crates/ospro-core/src/control.rs:107).

Checklist:
- [ ] Document exact parity rules for temperature control.
- [ ] Implement unstable reading guard and dead-zone branch parity.
- [ ] Implement extraction override behavior parity.
- [ ] Align loop cadence with configured sampling assumptions.
- [ ] Add regression tests against Python fixture cases.

Acceptance:
- PID outputs and branch behavior match parity fixtures across representative scenarios.

Evidence:
- Pending.

---

### P2-01 UI feature parity (settings/profile management/plot workflows)

Status: `Open`  
Owner: `TBD`

Python baseline:
- Rich flows in [dashboard.py](/t/Documents/Projects/Ospro/dashboard.py:2578), [dashboard.py](/t/Documents/Projects/Ospro/dashboard.py:2969), [dashboard.py](/t/Documents/Projects/Ospro/dashboard.py:3308).

Rust current:
- MVP controls and review panel in [ui.rs](/t/Documents/Projects/Ospro/crates/ospro-core/src/ui.rs:23).

Checklist:
- [ ] Decide required parity subset for `v0.2.0` release.
- [ ] Implement settings updates (scale, setpoint, flush, profile selection).
- [ ] Implement profile CRUD/editor parity subset.
- [ ] Implement extraction plot review details parity subset.
- [ ] Add UI integration tests and operator validation steps.

Acceptance:
- Touch workflow covers agreed Python-equivalent operational tasks.

Evidence:
- Pending.

---

### P2-02 Entrypoint orchestration parity (process supervision semantics)

Status: `Open`  
Owner: `TBD`

Python baseline:
- Module probing and subprocess poll/restart logic in [main.py](/t/Documents/Projects/Ospro/main.py:56) and [main.py](/t/Documents/Projects/Ospro/main.py:205).

Rust current:
- Single integrated runtime in [main.rs](/t/Documents/Projects/Ospro/crates/ospro-app/src/main.rs:18).

Checklist:
- [ ] Confirm intended parity policy: preserve integrated model or reintroduce equivalent supervision guarantees.
- [ ] If integrated model is intentional, document behavioral differences and risk mitigation.
- [ ] Add startup/runtime failure recovery tests matching chosen policy.
- [ ] Update release notes with explicit divergence if retained.

Acceptance:
- Supervision behavior is explicit, tested, and documented.

Evidence:
- Pending.

---

### P2-03 EPFA and pressure-profile simulation tooling parity decision

Status: `Open`  
Owner: `TBD`

Python baseline:
- EPFA solver and simulation scripts in [espresso_profile_fitting_algorithm.py](/t/Documents/Projects/Ospro/ospro/algorithms/espresso_profile_fitting_algorithm.py:22) and [simulate_pressure_profiles.py](/t/Documents/Projects/Ospro/simulate_pressure_profiles.py:13).

Rust current:
- No equivalent module.

Checklist:
- [ ] Decide if EPFA is in runtime parity scope or explicitly out-of-scope tooling.
- [ ] If in scope, implement Rust equivalent with fixture parity tests.
- [ ] If out-of-scope, document explicit exclusion in release notes and `OSPRO.md`.

Acceptance:
- No ambiguity on EPFA parity scope at release sign-off.

Evidence:
- Pending.

## Suggested Execution Order

1. P1-01 HAL parity.
2. P1-02 live sensor integration.
3. P1-03 timing semantics parity.
4. P1-04 temperature PID parity.
5. P2-01 UI parity subset.
6. P2-02 orchestration semantics decision.
7. P2-03 EPFA scope decision.

## Weekly Review Cadence

- Review all open items.
- Reconfirm owners and blockers.
- Move completed evidence into release notes and sign-off artifacts.
