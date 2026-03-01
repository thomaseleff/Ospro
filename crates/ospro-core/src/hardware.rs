/// Hardware backend selector and identity.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct HardwareBackend {
    backend: &'static str,
}

impl HardwareBackend {
    /// Constructs the mock backend used for development and tests.
    pub fn mock() -> Self {
        Self { backend: "mock" }
    }

    /// Returns backend identifier used by diagnostics/logging.
    pub fn backend_name(&self) -> &'static str {
        self.backend
    }
}
