use ospro_core::config::{PidConfig, RuntimeConfig};
use ospro_core::control::{Action, BrewState, ControlEngine, Event, Readings};
use ospro_core::hardware::HardwareError;
use std::time::{Duration, Instant};

#[test]
fn transition_matrix_cases() {
    let config = RuntimeConfig::default();
    let cases = vec![
        // Idle -> Preinfusion on Start
        (
            BrewState::Idle,
            Event::StartExtraction,
            BrewState::Preinfusion,
            vec![
                Action::StartExtractionOutput,
                Action::StartTimer(Duration::from_secs(10)),
                Action::SetPumpDuty(50.0),
                Action::SetHeaterDuty(100.0),
            ],
        ),
        // Preinfusion -> Extraction on TimerExpired
        (
            BrewState::Preinfusion,
            Event::TimerExpired,
            BrewState::Extraction,
            vec![
                Action::StartTimer(Duration::from_secs(30)),
                Action::SetPumpDuty(50.0),
            ],
        ),
        // Preinfusion -> Done on Stop
        (
            BrewState::Preinfusion,
            Event::StopExtraction,
            BrewState::Done,
            vec![Action::Shutdown, Action::SaveData],
        ),
        // Preinfusion -> Fault on FaultDetected
        (
            BrewState::Preinfusion,
            Event::FaultDetected(HardwareError::InvalidPin(0)),
            BrewState::Fault,
            vec![Action::Shutdown, Action::ResetData],
        ),
        // Extraction -> Done on Stop
        (
            BrewState::Extraction,
            Event::StopExtraction,
            BrewState::Done,
            vec![Action::Shutdown, Action::SaveData],
        ),
        // Extraction -> Done on TimerExpired
        (
            BrewState::Extraction,
            Event::TimerExpired,
            BrewState::Done,
            vec![Action::Shutdown, Action::SaveData],
        ),
        // Extraction -> Fault on FaultDetected
        (
            BrewState::Extraction,
            Event::FaultDetected(HardwareError::InvalidPin(0)),
            BrewState::Fault,
            vec![Action::Shutdown, Action::ResetData],
        ),
        // Done -> Idle on Reset
        (
            BrewState::Done,
            Event::Reset,
            BrewState::Idle,
            vec![Action::ResetData],
        ),
        // Fault -> Idle on Reset
        (
            BrewState::Fault,
            Event::Reset,
            BrewState::Idle,
            vec![Action::ResetData],
        ),
        // Unhandled -> Fault with Shutdown
        (
            BrewState::Idle,
            Event::TimerExpired,
            BrewState::Fault,
            vec![Action::Shutdown, Action::ResetData],
        ),
    ];

    for (initial, event, expected_state, expected_actions) in cases {
        let mut engine = ControlEngine::new(config.clone());
        engine.state = initial;
        let actions = engine.handle_event(event);
        assert_eq!(engine.state, expected_state);
        assert_eq!(actions, expected_actions);
    }
}

#[test]
fn pid_compute_basics() {
    let pid_config = PidConfig {
        pin: 0,
        sample_rate: 1.0,
        set_point: 93.0,
        dead_zone_range: 30.0,
        p: 1.025,
        i: 0.001,
        d: 0.0,
        error: Some(0.0),
    };
    let mut pid = ospro_core::control::Pid::new(pid_config);

    let now = Instant::now();
    let duty = pid.compute(70.0, now + Duration::from_secs(1));
    assert!(duty > 0.0);

    pid.reset();
    let duty_zero = pid.compute(93.0, now + Duration::from_secs(2));
    assert_eq!(duty_zero, 0.0);
}

#[test]
fn tick_triggers_timer_event() {
    let mut engine = ControlEngine::new(RuntimeConfig::default());
    engine.handle_event(Event::StartExtraction); // To Preinfusion
    assert_eq!(engine.state, BrewState::Preinfusion);

    let now = Instant::now() + Duration::from_secs(11); // Past preinfusion time
    let actions = engine.tick(
        Readings {
            temperature_c: 90.0,
            pressure_bar: 2.0,
        },
        now,
    );
    assert_eq!(engine.state, BrewState::Extraction);
    assert!(!actions.is_empty());
}

#[test]
fn fault_injection_stops_operations() {
    let mut engine = ControlEngine::new(RuntimeConfig::default());
    engine.handle_event(Event::StartExtraction); // To Preinfusion

    let actions = engine.handle_event(Event::FaultDetected(
        ospro_core::hardware::HardwareError::Backend("test fault".to_string()),
    ));
    assert_eq!(engine.state, BrewState::Fault);
    assert_eq!(actions, vec![Action::Shutdown, Action::ResetData]);
}
