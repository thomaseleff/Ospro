//! ospro-app: composition root for the Ospro Rust runtime.

use ospro_core::config::RuntimeConfig;
use ospro_core::control::ControlEngine;
use ospro_core::hardware::HardwareBackend;
use ospro_core::telemetry::TelemetryRuntime;
use ospro_core::ui::UiRuntime;

fn main() {
    let config = RuntimeConfig::default();
    let hardware = HardwareBackend::mock();
    let control = ControlEngine::new(RuntimeConfig::default());
    let telemetry = TelemetryRuntime::new();
    let (ui, _update_tx, _event_rx) = UiRuntime::new();

    println!(
        "ospro-app bootstrapped: mode={}, backend={}, state={:?}, telemetry={}, ui={}",
        config.mode(),
        hardware.backend_name(),
        control.state(),
        telemetry.status(),
        ui.status()
    );
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn bootstrap_components_are_constructible() {
        let config = RuntimeConfig::default();
        let hardware = HardwareBackend::mock();
        let control = ControlEngine::new(RuntimeConfig::default());
        let telemetry = TelemetryRuntime::new();
        let (ui, _update_tx, _event_rx) = UiRuntime::new();

        assert_eq!(config.mode(), "dev");
        assert_eq!(hardware.backend_name(), "mock");
        assert_eq!(control.state(), ospro_core::control::BrewState::Idle);
        assert_eq!(telemetry.status(), "ready");
        assert_eq!(ui.status(), "slint-mvp");
    }
}
