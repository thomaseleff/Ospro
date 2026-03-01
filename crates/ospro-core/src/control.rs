/// High-level brew lifecycle state.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum BrewState {
    Idle,
}

/// Control runtime facade for state-machine and control-loop ownership.
#[derive(Debug, Clone)]
pub struct ControlRuntime {
    state: BrewState,
}

impl ControlRuntime {
    /// Constructs control runtime in the safe idle state.
    pub fn new() -> Self {
        Self {
            state: BrewState::Idle,
        }
    }

    /// Returns a stable state identifier suitable for logs and UI badges.
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
