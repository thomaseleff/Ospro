//! ospro-app: composition root for the Ospro Rust runtime.

use ospro_core::config::RuntimeConfig;
use ospro_core::control::{ControlEngine, Readings};
use ospro_core::hardware::HardwareBackend;
use ospro_core::telemetry::TelemetryRuntime;
use ospro_core::ui::{StateUpdate, UiRuntime};
use std::time::Instant;

fn main() {
    let config = RuntimeConfig::default();
    let _hardware = HardwareBackend::mock();
    let mut control = ControlEngine::new(config.clone());
    let _telemetry = TelemetryRuntime::new();
    let (ui, update_tx, event_rx) = UiRuntime::new();

    let _control_thread = std::thread::spawn(move || {
        let now = Instant::now();
        let readings = Readings {
            temperature_c: 93.0,
            pressure_bar: 9.0,
        }; // Mock readings
        control.tick(readings, now);
    });

    std::thread::spawn(move || {
        while let Ok(_event) = event_rx.recv() {
            // Handle events and update control
        }
    });

    // Update UI
    update_tx
        .send(StateUpdate {
            brew_state: "Idle".to_string(),
            temperature: 93.0,
            pressure: 9.0,
            timer_ms: 0,
            chart_path: None,
        })
        .unwrap();

    ui.run();
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
