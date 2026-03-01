use std::collections::HashMap;

/// General hardware/runtime errors surfaced by HAL implementations.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum HardwareError {
    InvalidPin(u8),
    NotConfigured(u8),
    InvalidValue(&'static str),
    UnsupportedPlatform(&'static str),
    Backend(String),
}

impl std::fmt::Display for HardwareError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            HardwareError::InvalidPin(pin) => write!(f, "invalid pin {pin}"),
            HardwareError::NotConfigured(pin) => write!(f, "pin {pin} is not configured"),
            HardwareError::InvalidValue(field) => write!(f, "invalid value for {field}"),
            HardwareError::UnsupportedPlatform(reason) => {
                write!(f, "unsupported platform: {reason}")
            }
            HardwareError::Backend(message) => write!(f, "hardware backend error: {message}"),
        }
    }
}

impl std::error::Error for HardwareError {}

/// Logical level for digital outputs and digital reads.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Level {
    Low,
    High,
}

/// GPIO mode for configured pins.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum PinMode {
    Input,
    Output,
}

/// Pull resistor setting for input pins.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Pull {
    Off,
    Down,
    Up,
}

/// Supported backend selection for HAL components.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum BackendKind {
    Mock,
    RaspberryPi,
}

/// SPI bus abstraction for sensors/interfaces.
pub trait SpiBus {
    fn transfer(&mut self, tx: &[u8]) -> Result<Vec<u8>, HardwareError>;
}

/// I2C bus abstraction for sensors/interfaces.
pub trait I2cBus {
    fn write_read(
        &mut self,
        address: u8,
        write: &[u8],
        read_len: usize,
    ) -> Result<Vec<u8>, HardwareError>;
}

/// GPIO abstraction for digital IO.
pub trait Gpio {
    fn setup(&mut self, pin: u8, mode: PinMode, pull: Pull) -> Result<(), HardwareError>;
    fn write(&mut self, pin: u8, level: Level) -> Result<(), HardwareError>;
    fn read(&self, pin: u8) -> Result<Level, HardwareError>;
    fn cleanup(&mut self, pin: Option<u8>) -> Result<(), HardwareError>;
}

impl<T: Gpio + ?Sized> Gpio for Box<T> {
    fn setup(&mut self, pin: u8, mode: PinMode, pull: Pull) -> Result<(), HardwareError> {
        (**self).setup(pin, mode, pull)
    }

    fn write(&mut self, pin: u8, level: Level) -> Result<(), HardwareError> {
        (**self).write(pin, level)
    }

    fn read(&self, pin: u8) -> Result<Level, HardwareError> {
        (**self).read(pin)
    }

    fn cleanup(&mut self, pin: Option<u8>) -> Result<(), HardwareError> {
        (**self).cleanup(pin)
    }
}

/// PWM abstraction used by control loops.
pub trait Pwm {
    fn start(
        &mut self,
        pin: u8,
        frequency_hz: f64,
        duty_cycle_percent: f64,
    ) -> Result<(), HardwareError>;
    fn set_duty_cycle(&mut self, pin: u8, duty_cycle_percent: f64) -> Result<(), HardwareError>;
    fn duty_cycle(&self, pin: u8) -> Result<f64, HardwareError>;
    fn stop(&mut self, pin: u8) -> Result<(), HardwareError>;
}

impl<T: Pwm + ?Sized> Pwm for Box<T> {
    fn start(
        &mut self,
        pin: u8,
        frequency_hz: f64,
        duty_cycle_percent: f64,
    ) -> Result<(), HardwareError> {
        (**self).start(pin, frequency_hz, duty_cycle_percent)
    }

    fn set_duty_cycle(&mut self, pin: u8, duty_cycle_percent: f64) -> Result<(), HardwareError> {
        (**self).set_duty_cycle(pin, duty_cycle_percent)
    }

    fn duty_cycle(&self, pin: u8) -> Result<f64, HardwareError> {
        (**self).duty_cycle(pin)
    }

    fn stop(&mut self, pin: u8) -> Result<(), HardwareError> {
        (**self).stop(pin)
    }
}

/// Backend identity and factory for HAL instances.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct HardwareBackend {
    kind: BackendKind,
}

impl HardwareBackend {
    /// Constructs the mock backend used for local development and tests.
    pub fn mock() -> Self {
        Self {
            kind: BackendKind::Mock,
        }
    }

    /// Constructs the Raspberry Pi backend selector.
    pub fn raspberry_pi() -> Self {
        Self {
            kind: BackendKind::RaspberryPi,
        }
    }

    /// Returns backend identifier used by diagnostics/logging.
    pub fn backend_name(&self) -> &'static str {
        match self.kind {
            BackendKind::Mock => "mock",
            BackendKind::RaspberryPi => "raspberry-pi",
        }
    }

    /// Creates a GPIO interface for the selected backend.
    pub fn create_gpio(&self) -> Box<dyn Gpio> {
        match self.kind {
            BackendKind::Mock => Box::<MockGpio>::default(),
            BackendKind::RaspberryPi => Box::<RaspberryPiGpio>::default(),
        }
    }

    /// Creates a PWM interface for the selected backend.
    pub fn create_pwm(&self) -> Box<dyn Pwm> {
        match self.kind {
            BackendKind::Mock => Box::<MockPwm>::default(),
            BackendKind::RaspberryPi => Box::<RaspberryPiPwm>::default(),
        }
    }

    /// Creates an SPI interface for the selected backend.
    pub fn create_spi(&self) -> Box<dyn SpiBus> {
        match self.kind {
            BackendKind::Mock => Box::<MockSpi>::default(),
            BackendKind::RaspberryPi => Box::<RaspberryPiSpi>::default(),
        }
    }

    /// Creates an I2C interface for the selected backend.
    pub fn create_i2c(&self) -> Box<dyn I2cBus> {
        match self.kind {
            BackendKind::Mock => Box::<MockI2c>::default(),
            BackendKind::RaspberryPi => Box::<RaspberryPiI2c>::default(),
        }
    }
}

#[derive(Debug, Clone, Copy)]
struct MockPin {
    mode: PinMode,
    level: Level,
}

/// In-memory mock GPIO implementation for tests/dev.
#[derive(Default)]
pub struct MockGpio {
    pins: HashMap<u8, MockPin>,
}

impl Gpio for MockGpio {
    fn setup(&mut self, pin: u8, mode: PinMode, _pull: Pull) -> Result<(), HardwareError> {
        if pin == 0 {
            return Err(HardwareError::InvalidPin(pin));
        }

        self.pins.insert(
            pin,
            MockPin {
                mode,
                level: Level::Low,
            },
        );
        Ok(())
    }

    fn write(&mut self, pin: u8, level: Level) -> Result<(), HardwareError> {
        let pin_state = self
            .pins
            .get_mut(&pin)
            .ok_or(HardwareError::NotConfigured(pin))?;

        if pin_state.mode != PinMode::Output {
            return Err(HardwareError::InvalidValue("gpio.mode"));
        }

        pin_state.level = level;
        Ok(())
    }

    fn read(&self, pin: u8) -> Result<Level, HardwareError> {
        let pin_state = self
            .pins
            .get(&pin)
            .ok_or(HardwareError::NotConfigured(pin))?;
        Ok(pin_state.level)
    }

    fn cleanup(&mut self, pin: Option<u8>) -> Result<(), HardwareError> {
        match pin {
            Some(pin_number) => {
                self.pins.remove(&pin_number);
            }
            None => {
                self.pins.clear();
            }
        }
        Ok(())
    }
}

/// In-memory mock PWM implementation for tests/dev.
#[derive(Default)]
pub struct MockPwm {
    channels: HashMap<u8, f64>,
}

impl Pwm for MockPwm {
    fn start(
        &mut self,
        pin: u8,
        frequency_hz: f64,
        duty_cycle_percent: f64,
    ) -> Result<(), HardwareError> {
        if pin == 0 {
            return Err(HardwareError::InvalidPin(pin));
        }

        if !frequency_hz.is_finite() || frequency_hz <= 0.0 {
            return Err(HardwareError::InvalidValue("pwm.frequency_hz"));
        }

        validate_duty_cycle(duty_cycle_percent)?;
        self.channels.insert(pin, duty_cycle_percent);
        Ok(())
    }

    fn set_duty_cycle(&mut self, pin: u8, duty_cycle_percent: f64) -> Result<(), HardwareError> {
        validate_duty_cycle(duty_cycle_percent)?;

        let channel = self
            .channels
            .get_mut(&pin)
            .ok_or(HardwareError::NotConfigured(pin))?;
        *channel = duty_cycle_percent;
        Ok(())
    }

    fn duty_cycle(&self, pin: u8) -> Result<f64, HardwareError> {
        self.channels
            .get(&pin)
            .copied()
            .ok_or(HardwareError::NotConfigured(pin))
    }

    fn stop(&mut self, pin: u8) -> Result<(), HardwareError> {
        let channel = self
            .channels
            .get_mut(&pin)
            .ok_or(HardwareError::NotConfigured(pin))?;
        *channel = 0.0;
        Ok(())
    }
}

/// In-memory mock SPI implementation for tests/dev.
#[derive(Default)]
pub struct MockSpi {
    next_response: Vec<u8>,
}

impl MockSpi {
    pub fn set_next_response(&mut self, bytes: Vec<u8>) {
        self.next_response = bytes;
    }
}

impl SpiBus for MockSpi {
    fn transfer(&mut self, tx: &[u8]) -> Result<Vec<u8>, HardwareError> {
        if !self.next_response.is_empty() {
            let response = std::mem::take(&mut self.next_response);
            return Ok(response);
        }
        Ok(tx.to_vec())
    }
}

/// In-memory mock I2C implementation for tests/dev.
#[derive(Default)]
pub struct MockI2c {
    next_response: Vec<u8>,
}

impl MockI2c {
    pub fn set_next_response(&mut self, bytes: Vec<u8>) {
        self.next_response = bytes;
    }
}

impl I2cBus for MockI2c {
    fn write_read(
        &mut self,
        address: u8,
        _write: &[u8],
        read_len: usize,
    ) -> Result<Vec<u8>, HardwareError> {
        if address == 0 {
            return Err(HardwareError::InvalidValue("i2c.address"));
        }

        if read_len == 0 {
            return Ok(Vec::new());
        }

        if !self.next_response.is_empty() {
            let mut response = std::mem::take(&mut self.next_response);
            response.truncate(read_len);
            while response.len() < read_len {
                response.push(0);
            }
            return Ok(response);
        }

        Ok(vec![0; read_len])
    }
}

/// Raspberry Pi GPIO skeleton.
#[derive(Default)]
pub struct RaspberryPiGpio;

impl Gpio for RaspberryPiGpio {
    fn setup(&mut self, _pin: u8, _mode: PinMode, _pull: Pull) -> Result<(), HardwareError> {
        Err(HardwareError::UnsupportedPlatform(
            "raspberry-pi gpio not implemented yet",
        ))
    }

    fn write(&mut self, _pin: u8, _level: Level) -> Result<(), HardwareError> {
        Err(HardwareError::UnsupportedPlatform(
            "raspberry-pi gpio not implemented yet",
        ))
    }

    fn read(&self, _pin: u8) -> Result<Level, HardwareError> {
        Err(HardwareError::UnsupportedPlatform(
            "raspberry-pi gpio not implemented yet",
        ))
    }

    fn cleanup(&mut self, _pin: Option<u8>) -> Result<(), HardwareError> {
        Err(HardwareError::UnsupportedPlatform(
            "raspberry-pi gpio not implemented yet",
        ))
    }
}

/// Raspberry Pi PWM skeleton.
#[derive(Default)]
pub struct RaspberryPiPwm;

impl Pwm for RaspberryPiPwm {
    fn start(
        &mut self,
        _pin: u8,
        _frequency_hz: f64,
        _duty_cycle_percent: f64,
    ) -> Result<(), HardwareError> {
        Err(HardwareError::UnsupportedPlatform(
            "raspberry-pi pwm not implemented yet",
        ))
    }

    fn set_duty_cycle(&mut self, _pin: u8, _duty_cycle_percent: f64) -> Result<(), HardwareError> {
        Err(HardwareError::UnsupportedPlatform(
            "raspberry-pi pwm not implemented yet",
        ))
    }

    fn duty_cycle(&self, _pin: u8) -> Result<f64, HardwareError> {
        Err(HardwareError::UnsupportedPlatform(
            "raspberry-pi pwm not implemented yet",
        ))
    }

    fn stop(&mut self, _pin: u8) -> Result<(), HardwareError> {
        Err(HardwareError::UnsupportedPlatform(
            "raspberry-pi pwm not implemented yet",
        ))
    }
}

/// Raspberry Pi SPI skeleton.
#[derive(Default)]
pub struct RaspberryPiSpi;

impl SpiBus for RaspberryPiSpi {
    fn transfer(&mut self, _tx: &[u8]) -> Result<Vec<u8>, HardwareError> {
        Err(HardwareError::UnsupportedPlatform(
            "raspberry-pi spi not implemented yet",
        ))
    }
}

/// Raspberry Pi I2C skeleton.
#[derive(Default)]
pub struct RaspberryPiI2c;

impl I2cBus for RaspberryPiI2c {
    fn write_read(
        &mut self,
        _address: u8,
        _write: &[u8],
        _read_len: usize,
    ) -> Result<Vec<u8>, HardwareError> {
        Err(HardwareError::UnsupportedPlatform(
            "raspberry-pi i2c not implemented yet",
        ))
    }
}

fn validate_duty_cycle(value: f64) -> Result<(), HardwareError> {
    if !value.is_finite() || !(0.0..=100.0).contains(&value) {
        return Err(HardwareError::InvalidValue("pwm.duty_cycle_percent"));
    }
    Ok(())
}
