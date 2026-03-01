use crossbeam_channel::{bounded, Receiver, Sender};
use slint::{ComponentHandle, Duration};
slint::include_modules!();

#[derive(Clone, Debug)]
pub enum UiEvent {
    StartExtraction,
    StopExtraction,
    Reset,
}

#[derive(Clone, Debug)]
pub struct StateUpdate {
    pub brew_state: String,
    pub temperature: f64,
    pub pressure: f64,
    pub timer_ms: u64,
}

#[derive(Debug)]
pub struct UiRuntime {
    _app: ComponentHandle<App>,
    event_tx: Sender<UiEvent>,
    update_rx: Receiver<StateUpdate>,
}

impl UiRuntime {
    pub fn new() -> (Self, Sender<StateUpdate>, Receiver<UiEvent>) {
        let (update_tx, update_rx) = bounded::<StateUpdate>(100);
        let (event_tx, event_rx) = bounded::<UiEvent>(100);
        let app = App::new().unwrap();

        let ui = Self {
            _app: app.clone(),
            event_tx,
            update_rx,
        };

        // Spawn update loop
        std::thread::spawn(move || {
            while let Ok(update) = update_rx.recv() {
                app.set_brew_state(update.brew_state.into());
                app.set_temperature(update.temperature.into());
                app.set_pressure(update.pressure.into());
                app.set_timer(Duration::from_millis(update.timer_ms));
            }
        });

        // Event handler thread if needed
        std::thread::spawn(move || {
            while let Ok(event) = event_rx.recv() {
                match event {
                    UiEvent::StartExtraction => println!("UI: Start brew"),
                    UiEvent::StopExtraction => println!("UI: Stop brew"),
                    UiEvent::Reset => println!("UI: Reset"),
                }
            }
        });

        (ui, update_tx, ui.event_tx.clone())
    }

    pub fn run(self) {
        self._app.run().unwrap();
    }

    pub fn status(&self) -> &'static str {
        "slint-wired"
    }
}

impl Default for UiRuntime {
    fn default() -> Self {
        Self::new().0
    }
}
