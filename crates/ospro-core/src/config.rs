use std::fmt;
use std::fs;
use std::path::Path;

use serde::{Deserialize, Serialize};

/// Temperature unit identifier for Fahrenheit.
pub const SCALE_FAHRENHEIT: &str = "F";
/// Temperature unit identifier for Celsius.
pub const SCALE_CELSIUS: &str = "C";
/// Display label used when [`SCALE_FAHRENHEIT`] is selected.
pub const SCALE_LABEL_FAHRENHEIT: &str = "Fahrenheit [F]";
/// Display label used when [`SCALE_CELSIUS`] is selected.
pub const SCALE_LABEL_CELSIUS: &str = "Celsius [C]";

/// Configuration loading and validation errors.
#[derive(Debug)]
pub enum ConfigError {
    /// Failed to read configuration bytes from disk.
    Io(std::io::Error),
    /// Failed to parse the configuration JSON payload.
    Parse(serde_json::Error),
    /// Parsed payload is syntactically valid JSON but violates domain rules.
    Validation(String),
}

impl fmt::Display for ConfigError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            ConfigError::Io(source) => write!(f, "failed to read configuration: {source}"),
            ConfigError::Parse(source) => write!(f, "failed to parse configuration json: {source}"),
            ConfigError::Validation(message) => write!(f, "invalid configuration: {message}"),
        }
    }
}

impl std::error::Error for ConfigError {}

impl From<std::io::Error> for ConfigError {
    fn from(source: std::io::Error) -> Self {
        ConfigError::Io(source)
    }
}

impl From<serde_json::Error> for ConfigError {
    fn from(source: serde_json::Error) -> Self {
        ConfigError::Parse(source)
    }
}

/// Full runtime configuration with compatibility aliases for legacy Python keys.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct RuntimeConfig {
    pub user: UserConfig,
    pub session: SessionConfig,
    #[serde(rename = "format", alias = "formats")]
    pub format: FormatConfig,
    pub settings: SettingsConfig,
    pub extraction: ExtractionConfig,
    #[serde(rename = "tPID", alias = "tpid")]
    pub tpid: PidConfig,
    #[serde(rename = "pPID", alias = "ppid")]
    pub ppid: PidConfig,
}

impl RuntimeConfig {
    /// Parses and validates runtime configuration from a JSON string.
    pub fn from_json_str(raw: &str) -> Result<Self, ConfigError> {
        let config: Self = serde_json::from_str(raw)?;
        config.validate()?;
        Ok(config)
    }

    /// Reads, parses, and validates runtime configuration from disk.
    pub fn load_from_path<P>(path: P) -> Result<Self, ConfigError>
    where
        P: AsRef<Path>,
    {
        let raw = fs::read_to_string(path)?;
        Self::from_json_str(&raw)
    }

    /// Returns runtime mode derived from the `session.dev` flag.
    pub fn mode(&self) -> &'static str {
        if self.session.dev {
            "dev"
        } else {
            "production"
        }
    }

    fn validate(&self) -> Result<(), ConfigError> {
        self.user.validate()?;
        self.session.validate()?;
        self.settings.validate()?;
        self.tpid.validate("tpid")?;
        self.ppid.validate("ppid")?;

        if self.settings.scale == SCALE_FAHRENHEIT
            && self.settings.scale_label != SCALE_LABEL_FAHRENHEIT
        {
            return Err(ConfigError::Validation(
                "settings.scale_label must be 'Fahrenheit [F]' when settings.scale is 'F'"
                    .to_string(),
            ));
        }

        if self.settings.scale == SCALE_CELSIUS && self.settings.scale_label != SCALE_LABEL_CELSIUS
        {
            return Err(ConfigError::Validation(
                "settings.scale_label must be 'Celsius [C]' when settings.scale is 'C'".to_string(),
            ));
        }

        Ok(())
    }
}

impl Default for RuntimeConfig {
    fn default() -> Self {
        Self {
            user: UserConfig {
                first: "Unknown".to_string(),
                last: "User".to_string(),
            },
            session: SessionConfig {
                dev: true,
                running: false,
                gui: true,
                temp_pid: true,
                pressure_pid: false,
                assets_path: ".".to_string(),
                config_path: ".".to_string(),
                diagnostics_path: ".".to_string(),
                modules_path: ".".to_string(),
                controllers_path: ".".to_string(),
                sensors_path: ".".to_string(),
                utils_path: ".".to_string(),
            },
            format: FormatConfig::default(),
            settings: SettingsConfig {
                scale: SCALE_FAHRENHEIT.to_string(),
                scale_label: SCALE_LABEL_FAHRENHEIT.to_string(),
                flush: 1,
                profile: "Manual".to_string(),
                preinfusion_time: default_preinfusion_time(),
                preinfusion_pressure: default_preinfusion_pressure(),
                extraction_time: default_extraction_time(),
                extraction_pressure: default_extraction_pressure(),
            },
            extraction: ExtractionConfig { pin: 23 },
            tpid: PidConfig::default_temperature(),
            ppid: PidConfig::default_pressure(),
        }
    }
}

/// User identity settings.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct UserConfig {
    pub first: String,
    pub last: String,
}

impl UserConfig {
    fn validate(&self) -> Result<(), ConfigError> {
        if self.first.trim().is_empty() {
            return Err(ConfigError::Validation(
                "user.first must not be empty".to_string(),
            ));
        }
        if self.last.trim().is_empty() {
            return Err(ConfigError::Validation(
                "user.last must not be empty".to_string(),
            ));
        }
        Ok(())
    }
}

/// Session/runtime wiring flags and paths.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SessionConfig {
    pub dev: bool,
    pub running: bool,
    #[serde(alias = "dashboard")]
    pub gui: bool,
    #[serde(alias = "tempPID")]
    pub temp_pid: bool,
    #[serde(alias = "pressurePID")]
    pub pressure_pid: bool,
    #[serde(alias = "assetsLoc")]
    pub assets_path: String,
    #[serde(alias = "configLoc")]
    pub config_path: String,
    #[serde(alias = "diagnosticsLoc")]
    pub diagnostics_path: String,
    #[serde(alias = "modulesLoc")]
    pub modules_path: String,
    #[serde(alias = "controllersLoc")]
    pub controllers_path: String,
    #[serde(alias = "sensorsLoc")]
    pub sensors_path: String,
    #[serde(alias = "utilsLoc")]
    pub utils_path: String,
}

impl SessionConfig {
    fn validate(&self) -> Result<(), ConfigError> {
        for (key, value) in [
            ("session.assets_path", self.assets_path.as_str()),
            ("session.config_path", self.config_path.as_str()),
            ("session.diagnostics_path", self.diagnostics_path.as_str()),
            ("session.modules_path", self.modules_path.as_str()),
            ("session.controllers_path", self.controllers_path.as_str()),
            ("session.sensors_path", self.sensors_path.as_str()),
            ("session.utils_path", self.utils_path.as_str()),
        ] {
            if value.trim().is_empty() {
                return Err(ConfigError::Validation(format!("{key} must not be empty")));
            }
        }
        Ok(())
    }
}

/// UI layout and color settings.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct FormatConfig {
    pub width: i32,
    pub height: i32,
    pub font: String,
    #[serde(alias = "headerSize")]
    pub header_size: i32,
    #[serde(alias = "labelSize")]
    pub label_size: i32,
    #[serde(alias = "buttonSize")]
    pub button_size: i32,
    #[serde(alias = "counterSize")]
    pub counter_size: i32,
    #[serde(alias = "metricsSize")]
    pub metrics_size: i32,
    #[serde(alias = "buttonHeight")]
    pub button_height: i32,
    #[serde(alias = "buttonWidth")]
    pub button_width: i32,
    #[serde(alias = "padX")]
    pub pad_x: i32,
    #[serde(alias = "padY")]
    pub pad_y: i32,
    pub white: String,
    pub black: String,
    pub red: String,
    pub orange: String,
    pub yellow: String,
    pub green: String,
    pub blue: String,
    pub color1: String,
    pub color2: String,
    pub color3: String,
    pub color4: String,
}

impl Default for FormatConfig {
    fn default() -> Self {
        Self {
            width: 1024,
            height: 600,
            font: "Roboto".to_string(),
            header_size: 14,
            label_size: 13,
            button_size: 13,
            counter_size: 115,
            metrics_size: 48,
            button_height: 30,
            button_width: 90,
            pad_x: 5,
            pad_y: 5,
            white: "#FFFFFF".to_string(),
            black: "#000000".to_string(),
            red: "#FF3333".to_string(),
            orange: "#FFAA33".to_string(),
            yellow: "#FFCC33".to_string(),
            green: "#00D05E".to_string(),
            blue: "#3a7ebf".to_string(),
            color1: "#242424".to_string(),
            color2: "#808080".to_string(),
            color3: "#e5e5e5".to_string(),
            color4: "#f2f2f2".to_string(),
        }
    }
}

/// Operator-facing settings that may change between extractions.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct SettingsConfig {
    pub scale: String,
    #[serde(alias = "scaleLabel")]
    pub scale_label: String,
    pub flush: u8,
    pub profile: String,
    #[serde(default = "default_preinfusion_time")]
    pub preinfusion_time: u32,
    #[serde(default = "default_preinfusion_pressure")]
    pub preinfusion_pressure: f64,
    #[serde(default = "default_extraction_time")]
    pub extraction_time: u32,
    #[serde(default = "default_extraction_pressure")]
    pub extraction_pressure: f64,
}

fn default_preinfusion_time() -> u32 {
    10
}
fn default_preinfusion_pressure() -> f64 {
    4.0
}
fn default_extraction_time() -> u32 {
    30
}
fn default_extraction_pressure() -> f64 {
    9.0
}

impl SettingsConfig {
    fn validate(&self) -> Result<(), ConfigError> {
        if self.scale != SCALE_FAHRENHEIT && self.scale != SCALE_CELSIUS {
            return Err(ConfigError::Validation(
                "settings.scale must be 'F' or 'C'".to_string(),
            ));
        }

        if !(1..=3).contains(&self.flush) {
            return Err(ConfigError::Validation(
                "settings.flush must be between 1 and 3".to_string(),
            ));
        }

        if self.profile.trim().is_empty() {
            return Err(ConfigError::Validation(
                "settings.profile must not be empty".to_string(),
            ));
        }

        if self.preinfusion_time == 0 {
            return Err(ConfigError::Validation(
                "settings.preinfusion_time must be greater than 0".to_string(),
            ));
        }

        if self.extraction_time == 0 {
            return Err(ConfigError::Validation(
                "settings.extraction_time must be greater than 0".to_string(),
            ));
        }

        if self.preinfusion_pressure < 0.0 || !self.preinfusion_pressure.is_finite() {
            return Err(ConfigError::Validation(
                "settings.preinfusion_pressure must be a non-negative finite number".to_string(),
            ));
        }

        if self.extraction_pressure < 0.0 || !self.extraction_pressure.is_finite() {
            return Err(ConfigError::Validation(
                "settings.extraction_pressure must be a non-negative finite number".to_string(),
            ));
        }

        Ok(())
    }
}

/// Extraction hardware mapping settings.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExtractionConfig {
    pub pin: u8,
}

/// PID controller tuning and runtime parameters.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct PidConfig {
    pub pin: u8,
    #[serde(alias = "sampleRate")]
    pub sample_rate: f64,
    #[serde(alias = "setPoint")]
    pub set_point: f64,
    #[serde(alias = "deadZoneRange")]
    pub dead_zone_range: f64,
    pub p: f64,
    pub i: f64,
    pub d: f64,
    #[serde(default)]
    pub error: Option<f64>,
}

impl PidConfig {
    /// Default temperature PID configuration used for bootstrap.
    pub fn default_temperature() -> Self {
        Self {
            pin: 25,
            sample_rate: 1.0,
            set_point: 93.0,
            dead_zone_range: 30.0,
            p: 1.025,
            i: 0.001,
            d: 0.0,
            error: Some(15.0),
        }
    }

    /// Default pressure PID configuration used for bootstrap.
    pub fn default_pressure() -> Self {
        Self {
            pin: 24,
            sample_rate: 0.1,
            set_point: 9.0,
            dead_zone_range: 1.0,
            p: 0.5, // Basic proportional term for pressure response
            i: 0.1,
            d: 0.05,
            error: None,
        }
    }

    fn validate(&self, path: &str) -> Result<(), ConfigError> {
        if self.sample_rate <= 0.0 {
            return Err(ConfigError::Validation(format!(
                "{path}.sample_rate must be greater than 0"
            )));
        }

        for (name, value) in [
            ("set_point", self.set_point),
            ("dead_zone_range", self.dead_zone_range),
            ("p", self.p),
            ("i", self.i),
            ("d", self.d),
        ] {
            if !value.is_finite() {
                return Err(ConfigError::Validation(format!(
                    "{path}.{name} must be a finite number"
                )));
            }
        }

        if self.dead_zone_range < 0.0 {
            return Err(ConfigError::Validation(format!(
                "{path}.dead_zone_range must be >= 0"
            )));
        }

        if let Some(error) = self.error {
            if !error.is_finite() || error < 0.0 {
                return Err(ConfigError::Validation(format!(
                    "{path}.error must be a finite number >= 0"
                )));
            }
        }

        Ok(())
    }
}
