//! ospro-app: composition root for the Ospro Rust runtime.

use crossbeam_channel::{Receiver, Sender};
use ospro_core::config::RuntimeConfig;
use ospro_core::control::{Action, BrewState, ControlEngine, Event, Readings};
use ospro_core::hardware::HardwareBackend;
use ospro_core::telemetry::{ExtractionSample, TelemetryRuntime};
use ospro_core::ui::{StateUpdate, UiEvent, UiRuntime};
use std::fs;
use std::path::PathBuf;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use std::thread;
use std::time::{Duration, Instant, SystemTime, UNIX_EPOCH};

fn main() {
    let config = RuntimeConfig::default();
    let _hardware = HardwareBackend::mock();
    let _telemetry = TelemetryRuntime::new();
    let (ui, update_tx, event_rx) = UiRuntime::new();
    let running = Arc::new(AtomicBool::new(true));
    let _supervisor_thread =
        spawn_runtime_supervisor(config, event_rx, update_tx, Arc::clone(&running));
    ui.run();
    running.store(false, Ordering::Relaxed);
}

fn summarize_actions(actions: &[Action]) -> usize {
    actions.len()
}

fn spawn_runtime_supervisor(
    config: RuntimeConfig,
    event_rx: Receiver<UiEvent>,
    update_tx: Sender<StateUpdate>,
    running: Arc<AtomicBool>,
) -> thread::JoinHandle<()> {
    thread::spawn(move || {
        while running.load(Ordering::Relaxed) {
            let worker_running = Arc::clone(&running);
            let worker_config = config.clone();
            let worker_event_rx = event_rx.clone();
            let worker_update_tx = update_tx.clone();

            let worker = thread::spawn(move || {
                run_runtime_loop(
                    worker_config,
                    worker_event_rx,
                    worker_update_tx,
                    worker_running,
                )
            });

            match worker.join() {
                Ok(()) => break,
                Err(_) => thread::sleep(Duration::from_millis(250)),
            }
        }
    })
}

fn run_runtime_loop(
    config: RuntimeConfig,
    event_rx: Receiver<UiEvent>,
    update_tx: Sender<StateUpdate>,
    running: Arc<AtomicBool>,
) {
    let mut control = ControlEngine::new(config.clone());
    let mut shot_start: Option<Instant> = None;
    let mut last_update = Instant::now();
    let mut sample_index: u64 = 0;
    let mut temperatures = Vec::<f64>::new();
    let mut pressures = Vec::<f64>::new();
    let mut latest_chart_path: Option<String> = None;
    let readings = Readings {
        temperature_c: 93.0,
        pressure_bar: 9.0,
    };

    while running.load(Ordering::Relaxed) {
        let mut actions = Vec::new();

        match event_rx.recv_timeout(Duration::from_millis(100)) {
            Ok(UiEvent::StartBrew) => {
                shot_start = Some(Instant::now());
                sample_index = 0;
                temperatures.clear();
                pressures.clear();
                actions.extend(control.handle_event(Event::StartExtraction));
            }
            Ok(UiEvent::StopBrew) => actions.extend(control.handle_event(Event::StopExtraction)),
            Ok(UiEvent::Reset) => {
                shot_start = None;
                sample_index = 0;
                temperatures.clear();
                pressures.clear();
                latest_chart_path = None;
                actions.extend(control.handle_event(Event::Reset));
            }
            Err(crossbeam_channel::RecvTimeoutError::Timeout) => {}
            Err(crossbeam_channel::RecvTimeoutError::Disconnected) => break,
        }

        actions.extend(control.tick(readings.clone(), Instant::now()));

        if matches!(
            control.state(),
            BrewState::Preinfusion | BrewState::Extraction
        ) {
            temperatures.push(readings.temperature_c);
            pressures.push(readings.pressure_bar);
            sample_index = sample_index.saturating_add(1);
        }

        for action in &actions {
            if matches!(action, Action::SaveData) {
                latest_chart_path =
                    persist_extraction_artifacts(&config, &temperatures, &pressures, sample_index);
            }
        }

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
                chart_path: latest_chart_path.take(),
            };
            let _ = update_tx.send(update);
            last_update = Instant::now();
        }
    }
}

fn persist_extraction_artifacts(
    config: &RuntimeConfig,
    temperatures: &[f64],
    pressures: &[f64],
    sample_index: u64,
) -> Option<String> {
    let telemetry = TelemetryRuntime::new();
    let diagnostics_dir = PathBuf::from(&config.session.diagnostics_path);
    if fs::create_dir_all(&diagnostics_dir).is_err() {
        return None;
    }

    let stamp = SystemTime::now().duration_since(UNIX_EPOCH).ok()?.as_secs();
    let stem = format!("Diagnostics_{}_{}", stamp, sample_index);
    let csv_path = diagnostics_dir.join(format!("{stem}.csv"));
    let png_path = diagnostics_dir.join(format!("{stem}.png"));

    let samples: Vec<ExtractionSample> = temperatures
        .iter()
        .zip(pressures.iter())
        .enumerate()
        .map(|(idx, (temperature, pressure))| ExtractionSample {
            duration_s: idx as f64 / 10.0,
            temperature: *temperature,
            pressure: *pressure,
        })
        .collect();

    if telemetry.write_extraction_csv(&samples, &csv_path).is_err() {
        return None;
    }
    if telemetry
        .generate_chart(temperatures, pressures, &png_path)
        .is_err()
    {
        return None;
    }

    Some(png_path.to_string_lossy().to_string())
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
