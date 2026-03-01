use ospro_core::telemetry::{ExtractionMetadata, ExtractionSample, TelemetryRuntime};
use serde::Deserialize;
use std::collections::HashMap;
use std::fs;
use std::path::PathBuf;
use std::time::{SystemTime, UNIX_EPOCH};

#[derive(Debug, Deserialize)]
struct ParityCase {
    metadata: ExtractionMetadata,
    samples: Vec<ExtractionSample>,
    expected_first_row: HashMap<String, String>,
    expected_last_row: Option<HashMap<String, String>>,
}

fn fixture_path(name: &str) -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("tests")
        .join("fixtures")
        .join(name)
}

fn temp_csv_path() -> PathBuf {
    let stamp = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .expect("system time should be after unix epoch")
        .as_nanos();
    std::env::temp_dir().join(format!("ospro-parity-{stamp}.csv"))
}

fn parse_csv_record(line: &str) -> Vec<String> {
    let mut fields = Vec::new();
    let mut current = String::new();
    let mut in_quotes = false;
    let chars: Vec<char> = line.chars().collect();
    let mut i = 0;
    while i < chars.len() {
        let ch = chars[i];
        if ch == '"' {
            if in_quotes && i + 1 < chars.len() && chars[i + 1] == '"' {
                current.push('"');
                i += 1;
            } else {
                in_quotes = !in_quotes;
            }
        } else if ch == ',' && !in_quotes {
            fields.push(current);
            current = String::new();
        } else {
            current.push(ch);
        }
        i += 1;
    }
    fields.push(current);
    fields
}

fn parse_csv_rows(csv: &str) -> Vec<HashMap<String, String>> {
    let mut lines = csv.lines();
    let header = lines.next().expect("csv should include header");
    let columns = parse_csv_record(header);
    let mut rows = Vec::new();
    for line in lines {
        let values = parse_csv_record(line);
        assert_eq!(columns.len(), values.len());
        let mut row = HashMap::<String, String>::new();
        for (column, value) in columns.iter().cloned().zip(values.into_iter()) {
            row.insert(column, value);
        }
        rows.push(row);
    }
    rows
}

#[test]
fn diagnostics_csv_matches_python_style_fixture_row() {
    let fixture = fixture_path("python_diagnostics_parity_case.json");
    let raw = fs::read_to_string(fixture).expect("parity fixture should be readable");
    let case: ParityCase = serde_json::from_str(&raw).expect("parity fixture should parse");

    let telemetry = TelemetryRuntime::new();
    let out = temp_csv_path();
    telemetry
        .write_extraction_csv_with_metadata(&case.samples, &case.metadata, &out)
        .expect("csv should be generated");

    let csv = fs::read_to_string(&out).expect("generated csv should be readable");
    let rows = parse_csv_rows(&csv);
    let row = rows.first().expect("csv should include first data row");

    for (column, expected) in &case.expected_first_row {
        let actual = row.get(column).expect("expected column should exist");
        assert_eq!(actual, expected, "column {column} mismatch");
    }

    if let Some(expected_last_row) = case.expected_last_row {
        let row = rows.last().expect("csv should include last data row");
        for (column, expected) in expected_last_row {
            let actual = row.get(&column).expect("expected column should exist");
            assert_eq!(actual, &expected, "column {column} mismatch");
        }
    }

    let _ = fs::remove_file(out);
}

#[test]
fn diagnostics_csv_maintains_profile_series_and_metadata_across_rows() {
    let fixture = fixture_path("python_diagnostics_profile_series_case.json");
    let raw = fs::read_to_string(fixture).expect("parity fixture should be readable");
    let case: ParityCase = serde_json::from_str(&raw).expect("parity fixture should parse");

    let telemetry = TelemetryRuntime::new();
    let out = temp_csv_path();
    telemetry
        .write_extraction_csv_with_metadata(&case.samples, &case.metadata, &out)
        .expect("csv should be generated");

    let csv = fs::read_to_string(&out).expect("generated csv should be readable");
    let rows = parse_csv_rows(&csv);
    assert_eq!(rows.len(), case.samples.len());

    for (idx, row) in rows.iter().enumerate() {
        assert_eq!(
            row.get("ProfileValues"),
            Some(&format!("{:.2}", case.samples[idx].profile_value))
        );
        assert_eq!(row.get("User"), Some(&case.metadata.user));
    }

    let _ = fs::remove_file(out);
}
