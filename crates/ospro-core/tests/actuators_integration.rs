use ospro_core::actuators::{ExtractionActuator, PwmActuator};
use ospro_core::hardware::{HardwareError, Level, MockGpio, MockPwm};

#[test]
fn extraction_actuator_controls_gpio() {
    let gpio = MockGpio::default();
    let mut actuator = ExtractionActuator::new(gpio, 23).expect("new should succeed");

    actuator.start().expect("start should succeed");
    assert_eq!(
        actuator.level().expect("level should be readable"),
        Level::High
    );

    actuator.stop().expect("stop should succeed");
    assert_eq!(
        actuator.level().expect("level should be readable"),
        Level::Low
    );

    actuator.cleanup().expect("cleanup should succeed");
    let error = actuator.level().expect_err("should fail after cleanup");
    assert!(matches!(error, HardwareError::NotConfigured(_)));
}

#[test]
fn pwm_actuator_controls_duty_cycle() {
    let pwm = MockPwm::default();
    let mut actuator = PwmActuator::new(pwm, 25, 1.0).expect("new should succeed");

    actuator.start(50.0).expect("start should succeed");
    assert_eq!(
        actuator.duty_cycle().expect("duty should be readable"),
        50.0
    );

    actuator.set_duty_cycle(12.5).expect("set should succeed");
    assert_eq!(
        actuator.duty_cycle().expect("duty should be readable"),
        12.5
    );

    actuator.stop().expect("stop should succeed");
    assert_eq!(actuator.duty_cycle().expect("duty should be readable"), 0.0);
}

#[test]
fn pwm_actuator_validates_inputs() {
    let pwm = MockPwm::default();
    if let Err(error) = PwmActuator::new(pwm, 25, 0.0) {
        assert!(matches!(error, HardwareError::InvalidValue(_)));
    } else {
        panic!("Expected error for invalid frequency");
    }
}
