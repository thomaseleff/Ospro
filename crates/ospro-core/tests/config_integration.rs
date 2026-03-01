use std::path::PathBuf;

use ospro_core::config::RuntimeConfig;

fn fixture_path(name: &str) -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("tests")
        .join("fixtures")
        .join(name)
}

#[test]
fn loads_python_v0_1_0_legacy_schema() {
    let fixture = fixture_path("v0_1_0_config.json");
    let config = RuntimeConfig::load_from_path(fixture).expect("config should load");

    assert_eq!(config.mode(), "production");
    assert!(config.session.gui);
    assert!(config.session.temp_pid);
    assert!(!config.session.pressure_pid);
    assert_eq!(config.settings.scale, "F");
    assert_eq!(config.tpid.sample_rate, 1.0);
    assert_eq!(config.tpid.set_point, 93.0);
    assert_eq!(config.tpid.error, Some(15.0));
}

#[test]
fn loads_snake_case_schema_for_rust_runtime() {
    let fixture = fixture_path("snake_case_config.json");
    let config = RuntimeConfig::load_from_path(fixture).expect("config should load");

    assert_eq!(config.mode(), "dev");
    assert_eq!(config.settings.scale, "F");
    assert_eq!(config.format.label_size, 13);
    assert_eq!(config.ppid.sample_rate, 0.1);
    assert_eq!(config.ppid.error, None);
}

#[test]
fn rejects_invalid_scale_label_combinations() {
    let raw = r##"
    {
      "user": { "first": "Tom", "last": "Eleff" },
      "session": {
        "dev": true,
        "running": true,
        "gui": true,
        "temp_pid": true,
        "pressure_pid": false,
        "assets_path": "./assets",
        "config_path": "./config",
        "diagnostics_path": "./diagnostics",
        "modules_path": "./",
        "controllers_path": "./",
        "sensors_path": "./ospro/sensors",
        "utils_path": "./ospro/utils"
      },
      "formats": {
        "width": 1024,
        "height": 600,
        "font": "Roboto",
        "header_size": 14,
        "label_size": 13,
        "button_size": 13,
        "counter_size": 115,
        "metrics_size": 48,
        "button_height": 30,
        "button_width": 90,
        "pad_x": 5,
        "pad_y": 5,
        "white": "#FFFFFF",
        "black": "#000000",
        "red": "#FF3333",
        "orange": "#FFAA33",
        "yellow": "#FFCC33",
        "green": "#00D05E",
        "blue": "#3a7ebf",
        "color1": "#242424",
        "color2": "#808080",
        "color3": "#e5e5e5",
        "color4": "#f2f2f2"
      },
      "settings": {
        "scale_label": "Fahrenheit [F]",
        "scale": "C",
        "flush": 1,
        "profile": "Manual"
      },
      "extraction": { "pin": 23 },
      "tpid": {
        "pin": 25,
        "sample_rate": 1.0,
        "set_point": 93,
        "dead_zone_range": 30,
        "p": 1.025,
        "i": 0.001,
        "d": 0.0
      },
      "ppid": {
        "pin": 24,
        "sample_rate": 0.1,
        "set_point": 9.0,
        "dead_zone_range": 1.0,
        "p": 0.0,
        "i": 0.0,
        "d": 0.0
      }
    }
    "##;

    let error = RuntimeConfig::from_json_str(raw).expect_err("config should fail validation");
    let message = error.to_string();
    assert!(message.contains("scale_label"));
}

#[test]
fn rejects_invalid_flush_range() {
    let fixture = fixture_path("snake_case_config.json");
    let raw = std::fs::read_to_string(fixture).expect("fixture should be readable");
    let invalid = raw.replace("\"flush\": 1", "\"flush\": 7");

    let error = RuntimeConfig::from_json_str(&invalid).expect_err("config should fail validation");
    assert!(error
        .to_string()
        .contains("settings.flush must be between 1 and 5"));
}
