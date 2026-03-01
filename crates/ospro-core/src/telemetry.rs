use plotters::prelude::*;
use std::path::Path;

/// Telemetry runtime facade for extraction/session reporting.
pub struct TelemetryRuntime;

impl TelemetryRuntime {
    pub fn new() -> Self {
        Self
    }

    pub fn status(&self) -> &'static str {
        "ready"
    }

    pub fn generate_chart(
        &self,
        temperatures: &[f64],
        pressures: &[f64],
        path: &Path,
    ) -> Result<(), Box<dyn std::error::Error>> {
        let max_len = temperatures.len().max(pressures.len()).max(1) as f32;

        let root = BitMapBackend::new(path, (800, 600)).into_drawing_area();
        root.fill(&WHITE)?;

        let mut chart = ChartBuilder::on(&root)
            .caption("Extraction Chart", ("sans-serif", 50).into_font())
            .margin(5)
            .x_label_area_size(30)
            .y_label_area_size(30)
            .build_cartesian_2d(0f32..max_len, 0f32..100f32)?;

        chart.configure_mesh().draw()?;

        chart
            .draw_series(LineSeries::new(
                temperatures
                    .iter()
                    .enumerate()
                    .map(|(i, &t)| (i as f32, t as f32)),
                &RED,
            ))?
            .label("Temperature")
            .legend(|(x, y)| PathElement::new(vec![(x, y), (x + 20, y)], RED));

        chart
            .draw_series(LineSeries::new(
                pressures
                    .iter()
                    .enumerate()
                    .map(|(i, &p)| (i as f32, (p * 10.0) as f32)), // Scale pressure for visibility
                &BLUE,
            ))?
            .label("Pressure (scaled)")
            .legend(|(x, y)| PathElement::new(vec![(x, y), (x + 20, y)], BLUE));

        chart
            .configure_series_labels()
            .background_style(WHITE.mix(0.8))
            .border_style(BLACK)
            .draw()?;

        root.present()?;

        Ok(())
    }
}

impl Default for TelemetryRuntime {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::path::PathBuf;
    use std::time::{SystemTime, UNIX_EPOCH};

    fn temp_chart_path(name: &str) -> PathBuf {
        let stamp = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .expect("system time should be after unix epoch")
            .as_nanos();
        std::env::temp_dir().join(format!("ospro-{name}-{stamp}.png"))
    }

    #[test]
    fn generate_chart_handles_empty_series() {
        let telemetry = TelemetryRuntime::new();
        let path = temp_chart_path("empty");

        let result = telemetry.generate_chart(&[], &[], &path);
        assert!(result.is_ok());
        assert!(path.exists());

        let _ = std::fs::remove_file(path);
    }

    #[test]
    fn generate_chart_handles_short_series() {
        let telemetry = TelemetryRuntime::new();
        let path = temp_chart_path("short");

        let result = telemetry.generate_chart(&[92.0, 93.0, 94.0], &[2.0, 7.0, 9.0], &path);
        assert!(result.is_ok());
        assert!(path.exists());

        let _ = std::fs::remove_file(path);
    }
}
