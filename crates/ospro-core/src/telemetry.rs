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
        let root = BitMapBackend::new(path, (800, 600)).into_drawing_area();
        root.fill(&WHITE)?;

        let mut chart = ChartBuilder::on(&root)
            .caption("Extraction Chart", ("sans-serif", 50).into_font())
            .margin(5)
            .x_label_area_size(30)
            .y_label_area_size(30)
            .build_cartesian_2d(0f32..temperatures.len() as f32, 0f32..100f32)?;

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
