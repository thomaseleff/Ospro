//! Sensor adapters and conversion functions ported from Python v0.1.0.
//!
//! ## Assumptions and Calibration Limits
//! - MAX31855: Assumes K-type thermocouple. Absolute accuracy ±3°C (defined in TEMPERATURE_ACCURACY_C).
//!   Operating range: -200°C to +1350°C. Fault detection via lower 3 bits.
//! - ADS1115: Assumes integrated pressure transducer with calibration matching legacy logic.
//!   Absolute accuracy 0.344738 bar (defined in PRESSURE_ACCURACY_BAR). Readings rounded to 1 decimal place.
//! - Conversions preserve truncation and rounding semantics from Python baseline for parity.

use crate::hardware::{HardwareError, I2cBus, SpiBus};

/// Temperature sensor absolute accuracy in celsius for MAX31855 integrations.
pub const TEMPERATURE_ACCURACY_C: i32 = 3;
/// Pressure sensor absolute accuracy in bars for ADS1115/transducer integration.
pub const PRESSURE_ACCURACY_BAR: f64 = 0.344_738;

/// Converts Fahrenheit to Celsius, matching Python v0.1.0 truncation semantics.
pub fn fahrenheit_to_celsius(temperature_f: f64) -> i32 {
    ((temperature_f - 32.0) * 5.0 / 9.0) as i32
}

/// Converts Celsius to Fahrenheit, matching Python v0.1.0 truncation semantics.
pub fn celsius_to_fahrenheit(temperature_c: f64) -> i32 {
    ((temperature_c * 9.0 / 5.0) + 32.0) as i32
}

/// Decodes a MAX31855 32-bit frame into Celsius.
pub fn decode_max31855_celsius(frame: [u8; 4]) -> Result<f64, HardwareError> {
    let raw = u32::from_be_bytes(frame);

    // Lower 3 bits indicate fault conditions.
    if (raw & 0b111) != 0 {
        return Err(HardwareError::Backend(
            "max31855 fault flag present in frame".to_string(),
        ));
    }

    let mut value = ((raw >> 18) & 0x3FFF) as i16;
    if (value & 0x2000) != 0 {
        value -= 0x4000;
    }

    Ok((value as f64) * 0.25)
}

/// Converts ADS1115 raw ADC reading into pressure (bars), matching Python v0.1.0 logic.
pub fn pressure_bar_from_ads1115_raw(adc_raw: i16) -> f64 {
    let pressure = ((3.0 / 1750.0) * (adc_raw as f64)) - (34.0 / 7.0);
    round_to_1_decimal(pressure.abs())
}

/// MAX31855 sensor adapter over SPI.
pub struct Max31855Sensor<B: SpiBus> {
    bus: B,
}

impl<B: SpiBus> Max31855Sensor<B> {
    pub fn new(bus: B) -> Self {
        Self { bus }
    }

    /// Reads temperature in Celsius from the sensor.
    pub fn read_celsius(&mut self) -> Result<f64, HardwareError> {
        let bytes = self.bus.transfer(&[0, 0, 0, 0])?;
        let frame: [u8; 4] = bytes.as_slice().try_into().map_err(|_| {
            HardwareError::Backend("max31855 returned non-4-byte frame".to_string())
        })?;
        decode_max31855_celsius(frame)
    }

    /// Reads temperature in rounded Celsius, matching previous Python runtime behavior.
    pub fn read_rounded_celsius(&mut self) -> Result<i32, HardwareError> {
        Ok(self.read_celsius()?.round() as i32)
    }
}

/// ADS1115 pressure sensor adapter over I2C.
pub struct Ads1115Sensor<B: I2cBus> {
    bus: B,
    address: u8,
}

impl<B: I2cBus> Ads1115Sensor<B> {
    pub fn new(bus: B, address: u8) -> Self {
        Self { bus, address }
    }

    /// Reads signed ADC value from conversion register.
    pub fn read_raw(&mut self) -> Result<i16, HardwareError> {
        let bytes = self.bus.write_read(self.address, &[0x00], 2)?;
        let frame: [u8; 2] = bytes
            .as_slice()
            .try_into()
            .map_err(|_| HardwareError::Backend("ads1115 returned non-2-byte frame".to_string()))?;
        Ok(i16::from_be_bytes(frame))
    }

    /// Reads pressure value in bars.
    pub fn read_pressure_bar(&mut self) -> Result<f64, HardwareError> {
        Ok(pressure_bar_from_ads1115_raw(self.read_raw()?))
    }
}

fn round_to_1_decimal(value: f64) -> f64 {
    (value * 10.0).round() / 10.0
}
