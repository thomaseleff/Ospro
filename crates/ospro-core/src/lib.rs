//! ospro-core: domain modules for configuration, control, hardware, telemetry, and UI.

pub mod config {
    #[derive(Debug, Clone, PartialEq, Eq)]
    pub struct RuntimeConfig {
        pub mode: String,
    }

    impl Default for RuntimeConfig {
        fn default() -> Self {
            Self {
                mode: String::from("dev"),
            }
        }
    }
}

pub mod control {
    #[derive(Debug, Clone, Copy, PartialEq, Eq)]
    pub enum BrewState {
        Idle,
    }

    #[derive(Debug, Clone)]
    pub struct ControlRuntime {
        state: BrewState,
    }

    impl ControlRuntime {
        pub fn new() -> Self {
            Self {
                state: BrewState::Idle,
            }
        }

        pub fn state(&self) -> &'static str {
            match self.state {
                BrewState::Idle => "idle",
            }
        }
    }

    impl Default for ControlRuntime {
        fn default() -> Self {
            Self::new()
        }
    }
}

pub mod hardware {
    #[derive(Debug, Clone, PartialEq, Eq)]
    pub struct HardwareBackend {
        backend: &'static str,
    }

    impl HardwareBackend {
        pub fn mock() -> Self {
            Self { backend: "mock" }
        }

        pub fn backend_name(&self) -> &'static str {
            self.backend
        }
    }
}

pub mod telemetry {
    #[derive(Debug, Clone)]
    pub struct TelemetryRuntime {
        status: &'static str,
    }

    impl TelemetryRuntime {
        pub fn new() -> Self {
            Self { status: "ready" }
        }

        pub fn status(&self) -> &'static str {
            self.status
        }
    }

    impl Default for TelemetryRuntime {
        fn default() -> Self {
            Self::new()
        }
    }
}

pub mod ui {
    #[derive(Debug, Clone)]
    pub struct UiRuntime {
        status: &'static str,
    }

    impl UiRuntime {
        pub fn new() -> Self {
            Self { status: "ready" }
        }

        pub fn status(&self) -> &'static str {
            self.status
        }
    }

    impl Default for UiRuntime {
        fn default() -> Self {
            Self::new()
        }
    }
}

#[cfg(test)]
mod tests {
    use super::config::RuntimeConfig;
    use super::control::ControlRuntime;
    use super::hardware::HardwareBackend;
    use super::telemetry::TelemetryRuntime;
    use super::ui::UiRuntime;

    #[test]
    fn core_modules_construct_defaults() {
        let config = RuntimeConfig::default();
        let control = ControlRuntime::new();
        let hardware = HardwareBackend::mock();
        let telemetry = TelemetryRuntime::new();
        let ui = UiRuntime::new();

        assert_eq!(config.mode, "dev");
        assert_eq!(control.state(), "idle");
        assert_eq!(hardware.backend_name(), "mock");
        assert_eq!(telemetry.status(), "ready");
        assert_eq!(ui.status(), "ready");
    }
}
