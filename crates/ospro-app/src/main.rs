//! ospro-app: composition root for the Ospro Rust runtime.

use chrono::Local;
use crossbeam_channel::{Receiver, Sender};
use ospro_core::actuators::{ExtractionActuator, PwmActuator};
use ospro_core::config::{PressurePoint, RuntimeConfig};
use ospro_core::control::{Action, BrewState, ControlEngine, Event, Readings};
use ospro_core::hardware::{Gpio, HardwareBackend, HardwareError, Pwm};
use ospro_core::telemetry::{ExtractionMetadata, ExtractionSample, TelemetryRuntime};
use ospro_core::ui::{StateUpdate, UiEvent, UiRuntime};
use std::fs;
use std::path::PathBuf;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use std::thread;
use std::time::{Duration, Instant};

fn main() {
    let config = load_legacy_profile_curve(RuntimeConfig::default());
    let hardware = HardwareBackend::mock();
    let _telemetry = TelemetryRuntime::new();
    let (ui, update_tx, event_rx) = UiRuntime::new();
    let running = Arc::new(AtomicBool::new(true));
    let _supervisor_thread =
        spawn_runtime_supervisor(config, hardware, event_rx, update_tx, Arc::clone(&running));
    ui.run();
    running.store(false, Ordering::Relaxed);
}

fn summarize_actions(actions: &[Action]) -> usize {
    actions.len()
}

fn load_legacy_profile_curve(mut config: RuntimeConfig) -> RuntimeConfig {
    if !config.settings.pressure_curve.is_empty()
        || config.settings.profile.eq_ignore_ascii_case("manual")
    {
        return config;
    }

    let profile_path = PathBuf::from(&config.session.config_path)
        .join("profiles")
        .join(format!("{}.json", config.settings.profile));
    let raw = match fs::read_to_string(profile_path) {
        Ok(raw) => raw,
        Err(_) => return config,
    };
    let json = match serde_json::from_str::<serde_json::Value>(&raw) {
        Ok(json) => json,
        Err(_) => return config,
    };
    let settings = match json.get("settings") {
        Some(settings) => settings,
        None => return config,
    };
    let time_list = match settings.get("timeLst").and_then(|v| v.as_array()) {
        Some(list) => list,
        None => return config,
    };
    let pressure_list = match settings
        .get("pressureProfileLst")
        .and_then(|v| v.as_array())
    {
        Some(list) => list,
        None => return config,
    };

    let mut curve = Vec::<PressurePoint>::new();
    let mut last_time: Option<u32> = None;
    for (time, pressure) in time_list.iter().zip(pressure_list.iter()) {
        let time_s = match time.as_f64() {
            Some(time_s) if time_s.is_finite() && time_s >= 0.0 => time_s,
            _ => continue,
        };
        let pressure_bar = match pressure.as_f64() {
            Some(pressure_bar) if pressure_bar.is_finite() && pressure_bar >= 0.0 => pressure_bar,
            _ => continue,
        };
        let point_time = time_s.round() as u32;
        if last_time == Some(point_time) {
            if let Some(last) = curve.last_mut() {
                last.pressure = pressure_bar;
            }
            continue;
        }
        curve.push(PressurePoint {
            time: point_time,
            pressure: pressure_bar,
        });
        last_time = Some(point_time);
    }

    if !curve.is_empty() {
        config.settings.pressure_curve = curve;
    }
    config
}

type DynGpio = Box<dyn Gpio>;
type DynPwm = Box<dyn Pwm>;

fn apply_actions(
    actions: &[Action],
    extraction: &mut Option<ExtractionActuator<DynGpio>>,
    heater: &mut Option<PwmActuator<DynPwm>>,
    pump: &mut Option<PwmActuator<DynPwm>>,
    heater_started: &mut bool,
    pump_started: &mut bool,
) -> Option<HardwareError> {
    for action in actions {
        let result = match action {
            Action::StartExtractionOutput => extraction.as_mut().map(|a| a.start()).transpose(),
            Action::SetHeaterDuty(duty) => match heater.as_mut() {
                Some(actuator) => if *heater_started {
                    actuator.set_duty_cycle(*duty)
                } else {
                    *heater_started = true;
                    actuator.start(*duty)
                }
                .map(Some),
                None => Ok(None),
            },
            Action::SetPumpDuty(duty) => match pump.as_mut() {
                Some(actuator) => if *pump_started {
                    actuator.set_duty_cycle(*duty)
                } else {
                    *pump_started = true;
                    actuator.start(*duty)
                }
                .map(Some),
                None => Ok(None),
            },
            Action::Shutdown => {
                if let Some(actuator) = extraction.as_mut() {
                    if let Err(error) = actuator.stop() {
                        return Some(error);
                    }
                }
                if let Some(actuator) = heater.as_mut() {
                    if *heater_started {
                        if let Err(error) = actuator.stop() {
                            return Some(error);
                        }
                    }
                    *heater_started = false;
                }
                if let Some(actuator) = pump.as_mut() {
                    if *pump_started {
                        if let Err(error) = actuator.stop() {
                            return Some(error);
                        }
                    }
                    *pump_started = false;
                }
                Ok(Some(()))
            }
            Action::StartTimer(_) | Action::SaveData | Action::ResetData => Ok(None),
        };
        if let Err(error) = result {
            return Some(error);
        }
    }
    None
}

fn force_cleanup_actuators(
    extraction: &mut Option<ExtractionActuator<DynGpio>>,
    heater: &mut Option<PwmActuator<DynPwm>>,
    pump: &mut Option<PwmActuator<DynPwm>>,
    heater_started: &mut bool,
    pump_started: &mut bool,
) -> Option<HardwareError> {
    if let Some(actuator) = heater.as_mut() {
        if *heater_started {
            if let Err(error) = actuator.stop() {
                return Some(error);
            }
        }
        *heater_started = false;
    }
    if let Some(actuator) = pump.as_mut() {
        if *pump_started {
            if let Err(error) = actuator.stop() {
                return Some(error);
            }
        }
        *pump_started = false;
    }
    if let Some(actuator) = extraction.as_mut() {
        if let Err(error) = actuator.stop() {
            return Some(error);
        }
        if let Err(error) = actuator.cleanup() {
            return Some(error);
        }
    }
    None
}

fn spawn_runtime_supervisor(
    config: RuntimeConfig,
    hardware: HardwareBackend,
    event_rx: Receiver<UiEvent>,
    update_tx: Sender<StateUpdate>,
    running: Arc<AtomicBool>,
) -> thread::JoinHandle<()> {
    thread::spawn(move || {
        while running.load(Ordering::Relaxed) {
            let worker_running = Arc::clone(&running);
            let worker_config = config.clone();
            let worker_hardware = hardware.clone();
            let worker_event_rx = event_rx.clone();
            let worker_update_tx = update_tx.clone();

            let worker = thread::spawn(move || {
                run_runtime_loop(
                    worker_config,
                    worker_hardware,
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
    hardware: HardwareBackend,
    event_rx: Receiver<UiEvent>,
    update_tx: Sender<StateUpdate>,
    running: Arc<AtomicBool>,
) {
    let mut control = ControlEngine::new(config.clone());
    let mut extraction =
        ExtractionActuator::new(hardware.create_gpio(), config.extraction.pin).ok();
    let mut heater = PwmActuator::new(hardware.create_pwm(), config.tpid.pin, 1.0).ok();
    let mut pump = PwmActuator::new(hardware.create_pwm(), config.ppid.pin, 1.0).ok();
    let mut heater_started = false;
    let mut pump_started = false;
    let mut shot_start: Option<Instant> = None;
    let mut last_update = Instant::now();
    let mut temperatures = Vec::<f64>::new();
    let mut pressures = Vec::<f64>::new();
    let mut latest_chart_path: Option<String> = None;
    let mut latest_review: Option<ExtractionReview> = None;
    let readings = Readings {
        temperature_c: 93.0,
        pressure_bar: 9.0,
    };

    while running.load(Ordering::Relaxed) {
        let mut actions = Vec::new();

        match event_rx.recv_timeout(Duration::from_millis(100)) {
            Ok(UiEvent::StartBrew) => {
                shot_start = Some(Instant::now());
                temperatures.clear();
                pressures.clear();
                actions.extend(control.handle_event(Event::StartExtraction));
            }
            Ok(UiEvent::StopBrew) => actions.extend(control.handle_event(Event::StopExtraction)),
            Ok(UiEvent::Reset) => {
                shot_start = None;
                temperatures.clear();
                pressures.clear();
                latest_chart_path = None;
                latest_review = None;
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
        }

        for action in &actions {
            if matches!(action, Action::SaveData) {
                if let Some(review) =
                    persist_extraction_artifacts(&config, &temperatures, &pressures)
                {
                    latest_chart_path = Some(review.chart_path.clone());
                    latest_review = Some(review);
                }
            }
        }
        if let Some(error) = apply_actions(
            &actions,
            &mut extraction,
            &mut heater,
            &mut pump,
            &mut heater_started,
            &mut pump_started,
        ) {
            let fault_actions = control.handle_event(Event::FaultDetected(error));
            let _ = apply_actions(
                &fault_actions,
                &mut extraction,
                &mut heater,
                &mut pump,
                &mut heater_started,
                &mut pump_started,
            );
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
                review_visible: latest_review.is_some(),
                review_profile: latest_review
                    .as_ref()
                    .map(|review| review.profile.clone())
                    .unwrap_or_default(),
                review_duration: latest_review
                    .as_ref()
                    .map(|review| review.duration.clone())
                    .unwrap_or_default(),
                review_temp_range: latest_review
                    .as_ref()
                    .map(|review| review.temp_range.clone())
                    .unwrap_or_default(),
                review_pressure_range: latest_review
                    .as_ref()
                    .map(|review| review.pressure_range.clone())
                    .unwrap_or_default(),
            };
            let _ = update_tx.send(update);
            last_update = Instant::now();
        }
    }

    let _ = force_cleanup_actuators(
        &mut extraction,
        &mut heater,
        &mut pump,
        &mut heater_started,
        &mut pump_started,
    );
}

fn persist_extraction_artifacts(
    config: &RuntimeConfig,
    temperatures: &[f64],
    pressures: &[f64],
) -> Option<ExtractionReview> {
    let telemetry = TelemetryRuntime::new();
    let diagnostics_dir = PathBuf::from(&config.session.diagnostics_path);
    if fs::create_dir_all(&diagnostics_dir).is_err() {
        return None;
    }

    let extraction_id = next_extraction_id(&diagnostics_dir)?;
    let stamp = diagnostic_stamp();
    let stem = format!("Diagnostics_{}_{}", extraction_id, stamp.file_date);
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
            profile_value: profile_target_value(config, idx as f64 / 10.0),
        })
        .collect();

    let metadata = ExtractionMetadata {
        user: format!("{}, {}", config.user.last, config.user.first),
        unique_id: extraction_id.to_string(),
        date: stamp.date_display,
        time: stamp.time_display,
        temperature_unit: config.settings.scale.clone(),
        pressure_unit: "Bars".to_string(),
        temp_set_point: format!("{:.1}", config.tpid.set_point),
        profile: config.settings.profile.clone(),
    };

    if telemetry
        .write_extraction_csv_with_metadata(&samples, &metadata, &csv_path)
        .is_err()
    {
        return None;
    }
    if telemetry
        .generate_chart(temperatures, pressures, &png_path)
        .is_err()
    {
        return None;
    }

    let duration = samples
        .last()
        .map(|sample| sample.duration_s)
        .unwrap_or(0.0);
    let min_temp = samples
        .iter()
        .map(|sample| sample.temperature)
        .reduce(f64::min)
        .unwrap_or(0.0);
    let max_temp = samples
        .iter()
        .map(|sample| sample.temperature)
        .reduce(f64::max)
        .unwrap_or(0.0);
    let min_pressure = samples
        .iter()
        .map(|sample| sample.pressure)
        .reduce(f64::min)
        .unwrap_or(0.0);
    let max_pressure = samples
        .iter()
        .map(|sample| sample.pressure)
        .reduce(f64::max)
        .unwrap_or(0.0);

    Some(ExtractionReview {
        chart_path: png_path.to_string_lossy().to_string(),
        profile: config.settings.profile.clone(),
        duration: format!("{duration:.1}s"),
        temp_range: format!("{min_temp:.1}..{max_temp:.1} {}", config.settings.scale),
        pressure_range: format!("{min_pressure:.1}..{max_pressure:.1} bar"),
    })
}

#[derive(Debug, Clone, PartialEq, Eq)]
struct ExtractionReview {
    chart_path: String,
    profile: String,
    duration: String,
    temp_range: String,
    pressure_range: String,
}

fn profile_target_value(config: &RuntimeConfig, duration_s: f64) -> f64 {
    if config.settings.profile.eq_ignore_ascii_case("manual") {
        return 0.0;
    }

    let elapsed = duration_s.max(0.0);
    let curve = &config.settings.pressure_curve;
    if curve.is_empty() {
        return config.settings.extraction_pressure;
    }

    let mut prev = &curve[0];
    if elapsed < prev.time as f64 {
        return prev.pressure;
    }
    for point in &curve[1..] {
        if elapsed < point.time as f64 {
            let dt = (point.time - prev.time) as f64;
            if dt <= 0.0 {
                return prev.pressure;
            }
            let t = (elapsed - prev.time as f64) / dt;
            return prev.pressure + t * (point.pressure - prev.pressure);
        }
        prev = point;
    }
    prev.pressure
}

#[derive(Debug, Clone, PartialEq, Eq)]
struct DiagnosticStamp {
    date_display: String,
    time_display: String,
    file_date: String,
}

fn diagnostic_stamp() -> DiagnosticStamp {
    let now = Local::now();
    let date_display = now.format("%d/%b/%Y").to_string().to_uppercase();
    let time_display = now.format("%H:%M:%S").to_string();
    let file_date = date_display.replace('/', "");
    DiagnosticStamp {
        date_display,
        time_display,
        file_date,
    }
}

fn parse_diagnostics_id(stem: &str) -> Option<u64> {
    let mut parts = stem.split('_');
    let prefix = parts.next()?;
    if prefix != "Diagnostics" {
        return None;
    }
    let id = parts.next()?.parse::<u64>().ok()?;
    Some(id)
}

fn next_extraction_id(diagnostics_dir: &PathBuf) -> Option<u64> {
    let mut max_id = 0_u64;
    let entries = fs::read_dir(diagnostics_dir).ok()?;
    for entry in entries.flatten() {
        let path = entry.path();
        if path.extension().and_then(|ext| ext.to_str()) != Some("csv") {
            continue;
        }
        let stem = path.file_stem().and_then(|name| name.to_str())?;
        if let Some(id) = parse_diagnostics_id(stem) {
            max_id = max_id.max(id);
        }
    }
    Some(max_id.saturating_add(1))
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs::File;
    use std::io::Write;

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

    #[test]
    fn parse_diagnostics_id_extracts_numeric_id() {
        assert_eq!(parse_diagnostics_id("Diagnostics_12_01MAR2026"), Some(12));
        assert_eq!(parse_diagnostics_id("Diagnostics_x_01MAR2026"), None);
        assert_eq!(parse_diagnostics_id("Other_12_01MAR2026"), None);
    }

    #[test]
    fn next_extraction_id_scans_existing_files() {
        let stamp = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .expect("system time should be after unix epoch")
            .as_nanos();
        let test_dir = std::env::temp_dir().join(format!("ospro-diagnostics-{stamp}"));
        fs::create_dir_all(&test_dir).expect("temp diagnostics dir should be created");

        let mut one = File::create(test_dir.join("Diagnostics_1_01MAR2026.csv"))
            .expect("first diagnostics fixture should be created");
        writeln!(one, "header").expect("fixture should be writable");
        let mut nine = File::create(test_dir.join("Diagnostics_9_02MAR2026.csv"))
            .expect("second diagnostics fixture should be created");
        writeln!(nine, "header").expect("fixture should be writable");

        assert_eq!(next_extraction_id(&test_dir), Some(10));

        let _ = fs::remove_file(test_dir.join("Diagnostics_1_01MAR2026.csv"));
        let _ = fs::remove_file(test_dir.join("Diagnostics_9_02MAR2026.csv"));
        let _ = fs::remove_dir(test_dir);
    }

    #[test]
    fn profile_target_value_returns_zero_for_manual_profile() {
        let config = RuntimeConfig::default();
        assert_eq!(profile_target_value(&config, 5.0), 0.0);
    }

    #[test]
    fn profile_target_value_interpolates_curve() {
        let mut config = RuntimeConfig::default();
        config.settings.profile = "Custom".to_string();
        config.settings.pressure_curve = vec![
            ospro_core::config::PressurePoint {
                time: 0,
                pressure: 3.0,
            },
            ospro_core::config::PressurePoint {
                time: 10,
                pressure: 9.0,
            },
        ];

        assert_eq!(profile_target_value(&config, 0.0), 3.0);
        assert_eq!(profile_target_value(&config, 5.0), 6.0);
        assert_eq!(profile_target_value(&config, 10.0), 9.0);
    }

    #[test]
    fn apply_actions_controls_mock_actuators() {
        let backend = HardwareBackend::mock();
        let mut extraction = ExtractionActuator::new(backend.create_gpio(), 23).ok();
        let mut heater = PwmActuator::new(backend.create_pwm(), 25, 1.0).ok();
        let mut pump = PwmActuator::new(backend.create_pwm(), 24, 1.0).ok();
        let mut heater_started = false;
        let mut pump_started = false;
        let actions = vec![
            Action::StartExtractionOutput,
            Action::SetHeaterDuty(25.0),
            Action::SetPumpDuty(40.0),
            Action::Shutdown,
        ];

        let error = apply_actions(
            &actions,
            &mut extraction,
            &mut heater,
            &mut pump,
            &mut heater_started,
            &mut pump_started,
        );
        assert!(error.is_none());
    }

    #[test]
    fn force_cleanup_actuators_stops_and_cleans_up() {
        let backend = HardwareBackend::mock();
        let mut extraction = ExtractionActuator::new(backend.create_gpio(), 23).ok();
        let mut heater = PwmActuator::new(backend.create_pwm(), 25, 1.0).ok();
        let mut pump = PwmActuator::new(backend.create_pwm(), 24, 1.0).ok();
        let mut heater_started = false;
        let mut pump_started = false;
        let _ = apply_actions(
            &[
                Action::StartExtractionOutput,
                Action::SetHeaterDuty(20.0),
                Action::SetPumpDuty(30.0),
            ],
            &mut extraction,
            &mut heater,
            &mut pump,
            &mut heater_started,
            &mut pump_started,
        );

        let error = force_cleanup_actuators(
            &mut extraction,
            &mut heater,
            &mut pump,
            &mut heater_started,
            &mut pump_started,
        );
        assert!(error.is_none());
    }

    #[test]
    fn load_legacy_profile_curve_reads_profile_file_when_curve_empty() {
        let stamp = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .expect("system time should be after unix epoch")
            .as_nanos();
        let root = std::env::temp_dir().join(format!("ospro-profile-load-{stamp}"));
        let profiles = root.join("profiles");
        fs::create_dir_all(&profiles).expect("profiles dir should be created");
        fs::write(
            profiles.join("Pre-Infusion.json"),
            r#"{
                "settings": {
                    "timeLst": [0.0, 0.4, 1.2, 2.0],
                    "pressureProfileLst": [3.0, 4.0, 8.0, 9.0]
                }
            }"#,
        )
        .expect("profile fixture should be written");

        let mut config = RuntimeConfig::default();
        config.session.config_path = root.to_string_lossy().to_string();
        config.settings.profile = "Pre-Infusion".to_string();
        config.settings.pressure_curve.clear();

        let loaded = load_legacy_profile_curve(config);
        assert!(!loaded.settings.pressure_curve.is_empty());
        assert_eq!(loaded.settings.pressure_curve[0].pressure, 4.0);

        let _ = fs::remove_file(profiles.join("Pre-Infusion.json"));
        let _ = fs::remove_dir(profiles);
        let _ = fs::remove_dir(root);
    }

    #[test]
    fn load_legacy_profile_curve_keeps_existing_curve_or_manual_profile() {
        let mut with_curve = RuntimeConfig::default();
        with_curve.settings.profile = "Pre-Infusion".to_string();
        with_curve.settings.pressure_curve = vec![PressurePoint {
            time: 1,
            pressure: 5.0,
        }];
        let unchanged = load_legacy_profile_curve(with_curve.clone());
        assert_eq!(
            unchanged.settings.pressure_curve,
            with_curve.settings.pressure_curve
        );

        let manual = RuntimeConfig::default();
        let loaded_manual = load_legacy_profile_curve(manual.clone());
        assert_eq!(
            loaded_manual.settings.pressure_curve,
            manual.settings.pressure_curve
        );
    }
}
