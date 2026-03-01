//! ospro-app: composition root for the Ospro Rust runtime.

use ospro_core::config::RuntimeConfig;
use ospro_core::control::{Action, BrewState, ControlEngine, Event, Readings};
use ospro_core::hardware::HardwareBackend;
use ospro_core::telemetry::TelemetryRuntime;
use ospro_core::ui::{StateUpdate, UiEvent, UiRuntime};
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use std::time::{Duration, Instant};

fn main() {
    let config = RuntimeConfig::default();
    let _hardware = HardwareBackend::mock();
    let _telemetry = TelemetryRuntime::new();
    let (ui, update_tx, event_rx) = UiRuntime::new();
    let running = Arc::new(AtomicBool::new(true));
    let running_loop = Arc::clone(&running);

    let _runtime_thread = std::thread::spawn(move || {
        let mut control = ControlEngine::new(config);
        let mut shot_start: Option<Instant> = None;
        let mut last_update = Instant::now();
        let readings = Readings {
            temperature_c: 93.0,
            pressure_bar: 9.0,
        };

        while running_loop.load(Ordering::Relaxed) {
            let mut actions = Vec::new();

            match event_rx.recv_timeout(Duration::from_millis(100)) {
                Ok(UiEvent::StartBrew) => {
                    shot_start = Some(Instant::now());
                    actions.extend(control.handle_event(Event::StartExtraction));
                }
                Ok(UiEvent::StopBrew) => {
                    actions.extend(control.handle_event(Event::StopExtraction))
                }
                Ok(UiEvent::Reset) => {
                    shot_start = None;
                    actions.extend(control.handle_event(Event::Reset));
                }
                Err(crossbeam_channel::RecvTimeoutError::Timeout) => {}
                Err(crossbeam_channel::RecvTimeoutError::Disconnected) => break,
            }

            actions.extend(control.tick(readings.clone(), Instant::now()));

            if matches!(control.state(), BrewState::Done | BrewState::Fault) {
                shot_start = None;
            }

            let _ = summarize_actions(&actions);

            if last_update.elapsed() >= Duration::from_millis(100) {
                let timer_ms = shot_start
                    .map(|start| start.elapsed().as_millis() as u64)
                    .unwrap_or(0);
                let update = StateUpdate {
                    brew_state: format!("{:?}", control.state()),
                    temperature: readings.temperature_c,
                    pressure: readings.pressure_bar,
                    timer_ms,
                    chart_path: None,
                };
                let _ = update_tx.send(update);
                last_update = Instant::now();
            }
        }
    });
    ui.run();
    running.store(false, Ordering::Relaxed);
}

fn summarize_actions(actions: &[Action]) -> usize {
    actions.len()
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
