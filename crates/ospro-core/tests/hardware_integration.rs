use ospro_core::hardware::{HardwareBackend, Level, PinMode, Pull};

#[test]
fn mock_gpio_supports_setup_write_read_cleanup_contract() {
    let backend = HardwareBackend::mock();
    let mut gpio = backend.create_gpio();

    gpio.setup(23, PinMode::Output, Pull::Off)
        .expect("pin setup should succeed");
    gpio.write(23, Level::High).expect("write should succeed");

    let level = gpio.read(23).expect("read should succeed");
    assert_eq!(level, Level::High);

    gpio.cleanup(Some(23)).expect("cleanup should succeed");
    let error = gpio.read(23).expect_err("read should fail after cleanup");
    assert!(error.to_string().contains("not configured"));
}

#[test]
fn mock_pwm_supports_start_update_stop_contract() {
    let backend = HardwareBackend::mock();
    let mut pwm = backend.create_pwm();

    pwm.start(25, 1.0, 50.0).expect("pwm start should succeed");
    assert_eq!(pwm.duty_cycle(25).expect("duty should be readable"), 50.0);

    pwm.set_duty_cycle(25, 12.5)
        .expect("duty update should succeed");
    assert_eq!(pwm.duty_cycle(25).expect("duty should be readable"), 12.5);

    pwm.stop(25).expect("stop should succeed");
    assert_eq!(pwm.duty_cycle(25).expect("duty should be readable"), 0.0);
}

#[test]
fn mock_spi_and_i2c_return_deterministic_results() {
    let backend = HardwareBackend::mock();

    let mut spi = backend.create_spi();
    let spi_rx = spi.transfer(&[0xAA, 0x55]).expect("spi should succeed");
    assert_eq!(spi_rx, vec![0xAA, 0x55]);

    let mut i2c = backend.create_i2c();
    let i2c_rx = i2c
        .write_read(0x48, &[0x00], 2)
        .expect("i2c should succeed");
    assert_eq!(i2c_rx, vec![0, 0]);
}

#[test]
fn backend_selection_wires_mock_and_raspberry_pi() {
    let mock = HardwareBackend::mock();
    assert_eq!(mock.backend_name(), "mock");

    let rpi = HardwareBackend::raspberry_pi();
    assert_eq!(rpi.backend_name(), "raspberry-pi");
}

#[test]
fn raspberry_pi_skeleton_returns_unsupported_errors() {
    let backend = HardwareBackend::raspberry_pi();
    let mut gpio = backend.create_gpio();

    let error = gpio
        .setup(23, PinMode::Output, Pull::Off)
        .expect_err("rpi skeleton should return unsupported error");

    assert!(error.to_string().contains("not implemented yet"));
}
