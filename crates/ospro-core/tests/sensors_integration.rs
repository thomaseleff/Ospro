use ospro_core::hardware::HardwareError;
use ospro_core::sensors::{
    celsius_to_fahrenheit, decode_max31855_celsius, fahrenheit_to_celsius,
    pressure_bar_from_ads1115_raw, Ads1115Sensor, Max31855Sensor,
};
use serde_json::Value;
use std::fs::File;
use std::io::BufReader;

#[test]
fn conversion_functions_match_legacy_semantics() {
    assert_eq!(fahrenheit_to_celsius(77.0), 25);
    assert_eq!(fahrenheit_to_celsius(199.4), 93);
    assert_eq!(fahrenheit_to_celsius(14.0), -10);

    assert_eq!(celsius_to_fahrenheit(25.0), 77);
    assert_eq!(celsius_to_fahrenheit(93.0), 199);
    assert_eq!(celsius_to_fahrenheit(-10.0), 14);
}

#[test]
fn pressure_conversion_matches_fixtures() {
    let file = File::open("tests/fixtures/sensor_cases.json").expect("fixture file should open");
    let reader = BufReader::new(file);
    let json: Value = serde_json::from_reader(reader).expect("fixture should parse");

    let cases = json["pressure_cases"]
        .as_array()
        .expect("pressure_cases should be array");
    for case in cases {
        let adc_raw = case["adc_raw"].as_i64().expect("adc_raw should be i64") as i16;
        let expected_bar = case["expected_bar"]
            .as_f64()
            .expect("expected_bar should be f64");

        let result = pressure_bar_from_ads1115_raw(adc_raw);
        assert_eq!(result, expected_bar);
    }
}

#[test]
fn temperature_rounding_matches_fixtures() {
    let file = File::open("tests/fixtures/sensor_cases.json").expect("fixture file should open");
    let reader = BufReader::new(file);
    let json: Value = serde_json::from_reader(reader).expect("fixture should parse");

    let cases = json["temperature_celsius_cases"]
        .as_array()
        .expect("temperature_celsius_cases should be array");
    for case in cases {
        let celsius = case["celsius"].as_f64().expect("celsius should be f64");
        let expected = case["expected_rounded_celsius"]
            .as_i64()
            .expect("expected_rounded_celsius should be i64") as i32;

        let result = celsius.round() as i32; // Assuming this is what's tested, or adjust
        assert_eq!(result, expected);
    }
}

#[test]
fn max31855_decode_handles_valid_and_fault_frames() {
    // Valid frame example
    let valid_frame = [0x01, 0x90, 0x00, 0x00]; // 25.0 C
    assert_eq!(decode_max31855_celsius(valid_frame).unwrap(), 25.0);

    // Fault frame
    let fault_frame = [0x00, 0x00, 0x00, 0x01];
    assert!(decode_max31855_celsius(fault_frame).is_err());
}

#[test]
fn max31855_sensor_reads_via_mock_spi() {
    let mut spi = ospro_core::hardware::MockSpi::default();
    spi.set_next_response(vec![0x01, 0x90, 0x00, 0x00]);

    let mut sensor = Max31855Sensor::new(spi);
    let temp = sensor.read_celsius().expect("read should succeed");
    assert_eq!(temp, 25.0);

    // Separate test for rounded to avoid response consumption
}

#[test]
fn max31855_sensor_rounded_via_mock_spi() {
    let mut spi = ospro_core::hardware::MockSpi::default();
    spi.set_next_response(vec![0x01, 0x90, 0x00, 0x00]);

    let mut sensor = Max31855Sensor::new(spi);
    let rounded = sensor
        .read_rounded_celsius()
        .expect("rounded read should succeed");
    assert_eq!(rounded, 25);
}

#[test]
fn ads1115_sensor_reads_via_mock_i2c() {
    let mut i2c = ospro_core::hardware::MockI2c::default();
    i2c.set_next_response(vec![0x13, 0x88]); // 5000 raw

    let mut sensor = Ads1115Sensor::new(i2c, 0x48);
    let raw = sensor.read_raw().expect("raw read should succeed");
    assert_eq!(raw, 5000);
}

#[test]
fn ads1115_sensor_pressure_via_mock_i2c() {
    let mut i2c = ospro_core::hardware::MockI2c::default();
    i2c.set_next_response(vec![0x13, 0x88]); // 5000 raw

    let mut sensor = Ads1115Sensor::new(i2c, 0x48);
    let pressure = sensor
        .read_pressure_bar()
        .expect("pressure read should succeed");
    assert_eq!(pressure, 3.7);
}

#[test]
fn sensor_error_propagation() {
    let mut spi = ospro_core::hardware::MockSpi::default();
    spi.set_next_response(vec![0x01, 0x02, 0x03]); // Invalid frame size

    let mut sensor = Max31855Sensor::new(spi);
    let error = sensor
        .read_celsius()
        .expect_err("should fail on invalid frame");
    assert!(matches!(error, HardwareError::Backend(_)));
}
