//! Control engine and state machine for brewing operations.
//!
//! Implements the core control logic for espresso extraction, including state management,
//! PID calculations, and safety fallbacks. Migrated from Python v0.1.0 behavior in `temp_pid.py`
//! and `dashboard.py`, with implicit states made explicit for clarity and testability.
//!
//! ## Safety Model
//! - Faults (e.g., sensor errors, timeouts) transition to `Fault` state and issue `Shutdown` action.
//! - All actuators default to off/low in fault states.
//! - Control tick is deterministic and bounded; assumes external scheduling at config.sample_rate.
//! - Invariants: No unwraps, explicit error propagation, fail-safe defaults.

//! ## Transition Table
//! | Current State    | Event              | New State     | Actions                          |
//! |------------------|--------------------|---------------|----------------------------------|
//! | Idle            | StartExtraction   | Preinfusion  | StartTimer, SetPumpDuty(preinfuse), SetHeaterDuty(100) |
//! | Preinfusion     | TimerExpired      | Extraction   | StartTimer, SetPumpDuty(50.0) |
//! | Preinfusion     | StopExtraction    | Done         | Shutdown, SaveData               |
//! | Preinfusion     | FaultDetected     | Fault        | Shutdown                         |
//! | Extraction      | TimerExpired      | Done         | Shutdown, SaveData               |
//! | Extraction      | StopExtraction    | Done         | Shutdown, SaveData               |
//! | Extraction      | FaultDetected     | Fault        | Shutdown                         |
//! | Done            | Reset             | Idle         | ResetData                        |
//! | Fault           | Reset             | Idle         | ResetData                        |
//! | *               | *                 | Fault        | Shutdown (on unhandled)          |

use crate::config::{PidConfig, RuntimeConfig};
use crate::hardware::HardwareError;
use std::time::{Duration, Instant};

/// High-level brewing states, explicit version of Python's implicit flags (idling, extracting).
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum BrewState {
    /// Ready for user input, no active operations.
    Idle,
    /// Pre-infusion phase with lower pressure.
    Preinfusion,
    /// Main extraction phase.
    Extraction,
    /// Extraction complete, ready for review/reset.
    Done,
    /// Fault detected, operations halted.
    Fault,
}

/// Events that trigger state transitions.
#[derive(Debug, Clone, PartialEq)]
pub enum Event {
    /// User-initiated start of extraction.
    StartExtraction,
    /// User-initiated stop.
    StopExtraction,
    /// Reset after done/fault.
    Reset,
    /// Preinfusion or extraction timer expired.
    TimerExpired,
    /// Sensor/hardware fault detected.
    FaultDetected(HardwareError),
}

/// Actions issued by the state machine for the orchestrator to apply.
#[derive(Debug, Clone, PartialEq)]
pub enum Action {
    /// Set pump PWM duty cycle (for pressure control).
    SetPumpDuty(f64),
    /// Set heater PWM duty cycle (for temperature control).
    SetHeaterDuty(f64),
    /// Start extraction GPIO high.
    StartExtractionOutput,
    /// Stop extraction GPIO low and all PWMs to 0.
    Shutdown,
    /// Start a timer for the given duration.
    StartTimer(Duration),
    /// Save current extraction data.
    SaveData,
    /// Reset accumulated data (temps, pressures, etc.).
    ResetData,
}

/// Readings provided to the control tick (from sensors).
#[derive(Debug, Clone, PartialEq)]
pub struct Readings {
    pub temperature_c: f64,
    pub pressure_bar: f64,
}

/// PID controller for temperature or pressure.
#[derive(Debug, Clone)]
pub struct Pid {
    config: PidConfig,
    integral: f64,
    last_error: f64,
    last_time: Instant,
}

impl Pid {
    pub fn new(config: PidConfig) -> Self {
        Self {
            config,
            integral: 0.0,
            last_error: 0.0,
            last_time: Instant::now(),
        }
    }

    /// Computes PID output (duty cycle 0-100).
    pub fn compute(&mut self, current: f64, now: Instant) -> f64 {
        let error = self.config.set_point - current;
        if error.abs() < self.config.dead_zone_range / 2.0 {
            return 0.0;
        }
        let dt = now.duration_since(self.last_time).as_secs_f64();
        if dt == 0.0 {
            return 0.0; // Avoid div by zero
        }

        self.integral += error * dt;
        let windup_limit = 100.0 / self.config.i.max(1e-6);
        self.integral = self.integral.clamp(-windup_limit, windup_limit);
        let derivative = (error - self.last_error) / dt;
        let p_out = self.config.p * error;
        let i_out = self.config.i * self.integral;
        let d_out = self.config.d * derivative;

        let output = p_out + i_out + d_out;
        self.last_error = error;
        self.last_time = now;

        output.clamp(0.0, 100.0)
    }

    pub fn reset(&mut self) {
        self.integral = 0.0;
        self.last_error = 0.0;
        self.last_time = Instant::now();
    }

    pub fn set_set_point(&mut self, sp: f64) {
        self.config.set_point = sp;
    }
}

/// Core control engine owning state and PID controllers.
pub struct ControlEngine {
    pub state: BrewState,
    temp_pid: Pid,
    press_pid: Pid,
    start_time: Instant,
    timer_duration: Duration,
    temperatures: Vec<f64>,
    pressures: Vec<f64>,
    config: RuntimeConfig,
}

impl ControlEngine {
    /// Creates a new engine with given config.
    pub fn new(config: RuntimeConfig) -> Self {
        Self {
            state: BrewState::Idle,
            temp_pid: Pid::new(config.tpid.clone()),
            press_pid: Pid::new(config.ppid.clone()),
            start_time: Instant::now(),
            timer_duration: Duration::ZERO,
            temperatures: Vec::new(),
            pressures: Vec::new(),
            config,
        }
    }

    /// Current state.
    pub fn state(&self) -> BrewState {
        self.state
    }

    /// Processes an event and returns actions to apply.
    pub fn handle_event(&mut self, event: Event) -> Vec<Action> {
        let (new_state, actions) = transition(self.state, &event, &self.config);
        for action in actions.iter() {
            if let Action::StartTimer(d) = *action {
                self.timer_duration = d;
                self.start_time = Instant::now();
            }
        }

        let old_state = self.state;
        self.state = new_state;
        if old_state != new_state && matches!(new_state, BrewState::Idle | BrewState::Fault) {
            self.temp_pid.reset();
            self.press_pid.reset();
            self.temperatures.clear();
            self.pressures.clear();
        }
        // Set points now handled in tick

        actions
    }

    /// Control tick: computes based on readings and time, returns actions.
    /// Assumes called at config.sample_rate.
    pub fn tick(&mut self, readings: Readings, now: Instant) -> Vec<Action> {
        let mut actions = Vec::new();

        // Check timer
        if self.timer_duration > Duration::ZERO
            && now.duration_since(self.start_time) >= self.timer_duration
        {
            actions.extend(self.handle_event(Event::TimerExpired));
        }

        // Compute PID and collect readings only if active
        match self.state {
            BrewState::Preinfusion | BrewState::Extraction => {
                self.temperatures.push(readings.temperature_c);
                self.pressures.push(readings.pressure_bar);

                let set_point = self.get_current_pressure_setpoint(now);
                self.press_pid.set_set_point(set_point);
                let pump_duty = self.press_pid.compute(readings.pressure_bar, now);

                let heater_duty = if self.state == BrewState::Extraction {
                    10.0
                } else {
                    self.temp_pid.compute(readings.temperature_c, now)
                };

                actions.push(Action::SetHeaterDuty(heater_duty));
                actions.push(Action::SetPumpDuty(pump_duty));
            }
            _ => {}
        }

        actions
    }

    fn get_current_pressure_setpoint(&self, now: Instant) -> f64 {
        let elapsed = now.duration_since(self.start_time).as_secs() as u32;
        if self.state == BrewState::Preinfusion {
            self.config.settings.preinfusion_pressure
        } else {
            let curve = &self.config.settings.pressure_curve;
            if curve.is_empty() {
                return self.config.settings.extraction_pressure;
            }
            let mut prev = &curve[0];
            if elapsed < prev.time {
                return prev.pressure;
            }
            for point in &curve[1..] {
                if elapsed < point.time {
                    let t = (elapsed - prev.time) as f64 / (point.time - prev.time) as f64;
                    return prev.pressure + t * (point.pressure - prev.pressure);
                }
                prev = point;
            }
            prev.pressure
        }
    }
}

/// Pure transition function.
fn transition(
    current: BrewState,
    event: &Event,
    config: &RuntimeConfig,
) -> (BrewState, Vec<Action>) {
    match (current, event) {
        (BrewState::Idle, Event::StartExtraction) => (
            BrewState::Preinfusion,
            vec![
                Action::StartExtractionOutput,
                Action::StartTimer(Duration::from_secs(config.settings.preinfusion_time as u64)),
                Action::SetPumpDuty(50.0),
                Action::SetHeaterDuty(100.0), // Full heat during brew
            ],
        ),
        (BrewState::Preinfusion, Event::TimerExpired) => (
            BrewState::Extraction,
            vec![
                Action::StartTimer(Duration::from_secs(config.settings.extraction_time as u64)),
                Action::SetPumpDuty(50.0),
            ],
        ),
        (BrewState::Extraction, Event::TimerExpired) => {
            (BrewState::Done, vec![Action::Shutdown, Action::SaveData])
        }
        (BrewState::Preinfusion | BrewState::Extraction, Event::StopExtraction) => {
            (BrewState::Done, vec![Action::Shutdown, Action::SaveData])
        }
        (BrewState::Preinfusion | BrewState::Extraction, Event::FaultDetected(_)) => {
            (BrewState::Fault, vec![Action::Shutdown, Action::ResetData])
        }
        (BrewState::Done | BrewState::Fault, Event::Reset) => {
            (BrewState::Idle, vec![Action::ResetData])
        }
        _ => (BrewState::Fault, vec![Action::Shutdown, Action::ResetData]), // Safety fallback
    }
}
