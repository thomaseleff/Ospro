use plotters::prelude::*;
use std::io::Write;
use std::path::Path;

/// Telemetry runtime facade for extraction/session reporting.
pub struct TelemetryRuntime;

#[derive(Debug, Clone, Copy, PartialEq)]
pub struct ExtractionSample {
    pub duration_s: f64,
    pub temperature: f64,
    pub pressure: f64,
}

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

    pub fn write_extraction_csv(
        &self,
        samples: &[ExtractionSample],
        path: &Path,
    ) -> Result<(), Box<dyn std::error::Error>> {
        let mut file = std::fs::File::create(path)?;
        writeln!(file, "Duration,Temperature,Pressure")?;
        for sample in samples {
            writeln!(
                file,
                "{:.1},{:.2},{:.2}",
                sample.duration_s, sample.temperature, sample.pressure
            )?;
        }
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

    #[test]
    fn write_extraction_csv_handles_empty_and_short_series() {
        let telemetry = TelemetryRuntime::new();

        let empty_path = temp_chart_path("empty-csv").with_extension("csv");
        telemetry
            .write_extraction_csv(&[], &empty_path)
            .expect("empty csv write should succeed");
        let empty_contents =
            std::fs::read_to_string(&empty_path).expect("empty csv should be readable");
        assert!(empty_contents.starts_with("Duration,Temperature,Pressure"));
        let _ = std::fs::remove_file(empty_path);

        let short_path = temp_chart_path("short-csv").with_extension("csv");
        let samples = [
            ExtractionSample {
                duration_s: 0.0,
                temperature: 92.0,
                pressure: 2.0,
            },
            ExtractionSample {
                duration_s: 0.1,
                temperature: 93.0,
                pressure: 7.0,
            },
            ExtractionSample {
                duration_s: 0.2,
                temperature: 94.0,
                pressure: 9.0,
            },
        ];
        telemetry
            .write_extraction_csv(&samples, &short_path)
            .expect("short csv write should succeed");
        let short_contents =
            std::fs::read_to_string(&short_path).expect("short csv should be readable");
        assert!(short_contents.lines().count() >= 4);
        let _ = std::fs::remove_file(short_path);
    }
}
