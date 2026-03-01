//! Actuator wrappers ported from Python v0.1.0.
//!
//! ## Assumptions and Limits
//! - ExtractionActuator: Assumes active-high GPIO for on state. Pin must support output mode.
//! - PwmActuator: Duty cycle 0.0 to 100.0%. Frequency must be positive and finite.
//!   Used for control loops; assumes underlying PWM hardware supports the frequency range.

use crate::hardware::{Gpio, HardwareError, Level, PinMode, Pull, Pwm};

/// Controls extraction on/off via a GPIO output pin.
pub struct ExtractionActuator<G: Gpio> {
    gpio: G,
    pin: u8,
}

impl<G: Gpio> ExtractionActuator<G> {
    /// Configures an output pin and defaults it to low (off).
    pub fn new(mut gpio: G, pin: u8) -> Result<Self, HardwareError> {
        gpio.setup(pin, PinMode::Output, Pull::Off)?;
        gpio.write(pin, Level::Low)?;
        Ok(Self { gpio, pin })
    }

    /// Sets extraction output high.
    pub fn start(&mut self) -> Result<(), HardwareError> {
        self.gpio.write(self.pin, Level::High)
    }

    /// Sets extraction output low.
    pub fn stop(&mut self) -> Result<(), HardwareError> {
        self.gpio.write(self.pin, Level::Low)
    }

    /// Reads current output level for this actuator pin.
    pub fn level(&self) -> Result<Level, HardwareError> {
        self.gpio.read(self.pin)
    }

    /// Cleans up the configured pin.
    pub fn cleanup(&mut self) -> Result<(), HardwareError> {
        self.gpio.cleanup(Some(self.pin))
    }
}

/// Controls PWM output for heating/pressure control loops.
pub struct PwmActuator<P: Pwm> {
    pwm: P,
    pin: u8,
    frequency_hz: f64,
}

impl<P: Pwm> PwmActuator<P> {
    pub fn new(pwm: P, pin: u8, frequency_hz: f64) -> Result<Self, HardwareError> {
        if !frequency_hz.is_finite() || frequency_hz <= 0.0 {
            return Err(HardwareError::InvalidValue("pwm.frequency_hz"));
        }

        Ok(Self {
            pwm,
            pin,
            frequency_hz,
        })
    }

    /// Starts PWM output with initial duty cycle.
    pub fn start(&mut self, duty_cycle_percent: f64) -> Result<(), HardwareError> {
        self.pwm
            .start(self.pin, self.frequency_hz, duty_cycle_percent)
    }

    /// Updates duty cycle.
    pub fn set_duty_cycle(&mut self, duty_cycle_percent: f64) -> Result<(), HardwareError> {
        self.pwm.set_duty_cycle(self.pin, duty_cycle_percent)
    }

    /// Returns current duty cycle.
    pub fn duty_cycle(&self) -> Result<f64, HardwareError> {
        self.pwm.duty_cycle(self.pin)
    }

    /// Stops PWM output.
    pub fn stop(&mut self) -> Result<(), HardwareError> {
        self.pwm.stop(self.pin)
    }
}
