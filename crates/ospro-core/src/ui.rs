use crossbeam_channel::{bounded, Receiver, Sender};
use slint::slint;

slint! {
    import { Button } from "std-widgets.slint";

    export component App inherits Window {
        width: 1024px;
        height: 768px;
        title: "Ospro WS6";

        in property <string> brew-state: "Idle";
        in property <float> temperature: 93.0;
        in property <float> pressure: 9.0;
        in property <duration> timer: 0ms;
        in property <image> chart-image;

        callback start-brew();
        callback stop-brew();
        callback reset();

        VerticalLayout {
            padding: 20px;
            spacing: 20px;

            Text {
                text: "Ospro WS6 MVP";
                font-size: 32px;
                horizontal-alignment: center;
            }

            VerticalLayout {
                spacing: 10px;
                Text { text: "State: {brew-state}"; font-size: 24px; }
                Text { text: "Temp: {temperature} °C"; font-size: 24px; }
                Text { text: "Pressure: {pressure} bar"; font-size: 24px; }
                Text { text: "Timer: {timer}"; font-size: 24px; }
            }

            HorizontalLayout {
                spacing: 10px;
                Button { text: "Start"; clicked => { root.start-brew(); } }
                Button { text: "Stop"; clicked => { root.stop-brew(); } }
                Button { text: "Reset"; clicked => { root.reset(); } }
            }

            Image {
                source: chart-image;
                width: 640px;
                height: 240px;
            }
        }
    }
}

#[derive(Clone, Debug)]
pub enum UiEvent {
    StartBrew,
    StopBrew,
    Reset,
}

#[derive(Clone, Debug)]
pub struct StateUpdate {
    pub brew_state: String,
    pub temperature: f64,
    pub pressure: f64,
    pub timer_ms: u64,
    pub chart_path: Option<String>,
}

pub struct UiRuntime {
    _app: App,
}

impl UiRuntime {
    pub fn new() -> (Self, Sender<StateUpdate>, Receiver<UiEvent>) {
        let (update_tx, update_rx) = bounded::<StateUpdate>(100);
        let (event_tx, event_rx) = bounded::<UiEvent>(100);
        let app = App::new().expect("Failed to create App component");

        let weak_app = app.as_weak();

        let start_tx = event_tx.clone();
        app.on_start_brew(move || {
            let _ = start_tx.send(UiEvent::StartBrew);
        });
        let stop_tx = event_tx.clone();
        app.on_stop_brew(move || {
            let _ = stop_tx.send(UiEvent::StopBrew);
        });
        let reset_tx = event_tx.clone();
        app.on_reset(move || {
            let _ = reset_tx.send(UiEvent::Reset);
        });

        let ui = Self { _app: app };

        std::thread::spawn(move || {
            while let Ok(update) = update_rx.recv() {
                if let Some(app) = weak_app.upgrade() {
                    app.set_brew_state(update.brew_state.into());
                    app.set_temperature(update.temperature as f32);
                    app.set_pressure(update.pressure as f32);
                    app.set_timer(update.timer_ms as i64);
                    if let Some(path) = update.chart_path {
                        if let Ok(image) = slint::Image::load_from_path(std::path::Path::new(&path))
                        {
                            app.set_chart_image(image);
                        }
                    }
                } else {
                    break;
                }
            }
        });

        (ui, update_tx, event_rx)
    }

    pub fn run(self) {
        self._app.run().expect("Failed to run UI");
    }

    pub fn status(&self) -> &'static str {
        "slint-mvp"
    }
}

impl Default for UiRuntime {
    fn default() -> Self {
        Self::new().0
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn ui_new_returns_channels() {
        let (ui, update_tx, event_rx) = UiRuntime::new();
        assert_eq!(ui.status(), "slint-mvp");
        update_tx
            .send(StateUpdate {
                brew_state: "Test".to_string(),
                temperature: 93.0,
                pressure: 9.0,
                timer_ms: 1000,
                chart_path: None,
            })
            .unwrap();
        let event = event_rx.try_recv();
        assert!(event.is_err());
    }
}
