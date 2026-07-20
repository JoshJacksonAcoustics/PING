"""
ping.config
===========

Loads and validates ping_config.yaml into a single, strongly-typed
PINGConfig object.

Why validation instead of a raw dict (yaml.safe_load(...) directly):
A raw dict lets a typo like "sample_rte" or a bad value like overlap=1.5
pass silently into the hardware or algorithm layers, where it may not fail
until partway through a multi-hour experiment. Every PING experiment must
be reproducible (PRDS Section 7.1), which requires that a malformed
configuration fail loudly, at startup, with a specific error - not
silently produce corrupted or unreproducible results downstream.

The seven sections below (hardware, array, processing, algorithm,
visualization, clap, logging) mirror PRDS Section 7.5 exactly. Adding a
new configurable parameter means adding a field here AND to
ping_config.yaml - never adding a bare dict lookup in library code.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

# Geometries implemented (or planned) per PRDS Section 5.3 / Section 6.3.
VALID_GEOMETRY_TYPES = frozenset(
    {"circular", "linear", "rectangular", "spiral", "random"}
)

# Algorithms implemented (or planned) per PRDS Section 5.1 (Layer 3) / Section 12.1.
VALID_ALGORITHMS = frozenset({"gcc_phat", "das", "mvdr", "music", "srp_phat"})

# Window functions supported by ping.signal_processing.preprocessing.
VALID_WINDOW_TYPES = frozenset({"hann", "hamming", "blackman", "rectangular"})


class ConfigValidationError(ValueError):
    """Raised when ping_config.yaml is structurally valid YAML but contains
    a value that violates a PRDS requirement or a physical constraint
    (e.g. a negative sample rate, an unknown geometry type).

    Kept as a distinct exception type (rather than a bare ValueError) so
    that experiment scripts can catch configuration problems specifically
    and report them clearly, rather than confusing them with runtime
    errors from later pipeline stages.
    """


@dataclass(frozen=True)
class HardwareConfig:
    """Layer 1 hardware parameters. See PRDS Section 6.2, FR-001-FR-005."""

    device_name: str
    sample_rate: int          # Hz
    bit_depth: int            # bits
    n_channels: int
    phantom_power_v: float    # Volts
    buffer_size: int          # samples

    def __post_init__(self) -> None:
        if self.sample_rate < 44100:
            raise ConfigValidationError(
                f"hardware.sample_rate={self.sample_rate} Hz is below the "
                "44,100 Hz minimum required by FR-002."
            )
        if self.bit_depth not in (16, 24, 32):
            raise ConfigValidationError(
                f"hardware.bit_depth={self.bit_depth} is not a supported "
                "PCM depth (16, 24, or 32 bits)."
            )
        if self.n_channels <= 0:
            raise ConfigValidationError(
                f"hardware.n_channels={self.n_channels} must be positive."
            )
        if not (44.0 <= self.phantom_power_v <= 52.0):
            raise ConfigValidationError(
                f"hardware.phantom_power_v={self.phantom_power_v} is outside "
                "the 44-52V range verified by HV-001 / FR-005."
            )
        if self.buffer_size <= 0 or (self.buffer_size & (self.buffer_size - 1)) != 0:
            raise ConfigValidationError(
                f"hardware.buffer_size={self.buffer_size} must be a positive "
                "power of two for efficient FFT computation downstream."
            )


@dataclass(frozen=True)
class ArrayConfig:
    """Layer 2 array geometry parameters. See PRDS Section 5.3, Section 6.4."""

    geometry_type: str
    radius_cm: float
    n_mics: int
    speed_of_sound_mps: float

    def __post_init__(self) -> None:
        if self.geometry_type not in VALID_GEOMETRY_TYPES:
            raise ConfigValidationError(
                f"array.geometry_type='{self.geometry_type}' is not one of "
                f"{sorted(VALID_GEOMETRY_TYPES)}."
            )
        if self.radius_cm <= 0:
            raise ConfigValidationError(
                f"array.radius_cm={self.radius_cm} must be positive."
            )
        if self.n_mics <= 1:
            raise ConfigValidationError(
                f"array.n_mics={self.n_mics} must be at least 2 to form an array."
            )
        if self.speed_of_sound_mps <= 0:
            raise ConfigValidationError(
                f"array.speed_of_sound_mps={self.speed_of_sound_mps} must be positive."
            )


@dataclass(frozen=True)
class ProcessingConfig:
    """Layer 2 preprocessing parameters. See PRDS Section 5.4, Section 7.3."""

    window_type: str
    nfft: int
    overlap: float
    bandpass_low_hz: float
    bandpass_high_hz: float

    def __post_init__(self) -> None:
        if self.window_type not in VALID_WINDOW_TYPES:
            raise ConfigValidationError(
                f"processing.window_type='{self.window_type}' is not one of "
                f"{sorted(VALID_WINDOW_TYPES)}."
            )
        if self.nfft <= 0 or (self.nfft & (self.nfft - 1)) != 0:
            raise ConfigValidationError(
                f"processing.nfft={self.nfft} must be a positive power of two."
            )
        if not (0.0 <= self.overlap < 1.0):
            raise ConfigValidationError(
                f"processing.overlap={self.overlap} must be in [0, 1)."
            )
        if self.bandpass_low_hz <= 0 or self.bandpass_high_hz <= self.bandpass_low_hz:
            raise ConfigValidationError(
                f"processing bandpass range [{self.bandpass_low_hz}, "
                f"{self.bandpass_high_hz}] Hz is invalid: low must be > 0 "
                "and less than high."
            )


@dataclass(frozen=True)
class AlgorithmConfig:
    """Layer 3 beamforming parameters. See PRDS Section 5.1, FR-014-FR-016."""

    primary_algorithm: str
    n_sources: int
    angular_resolution_deg: float

    def __post_init__(self) -> None:
        if self.primary_algorithm not in VALID_ALGORITHMS:
            raise ConfigValidationError(
                f"algorithm.primary_algorithm='{self.primary_algorithm}' is "
                f"not one of {sorted(VALID_ALGORITHMS)}."
            )
        if self.n_sources <= 0:
            raise ConfigValidationError(
                f"algorithm.n_sources={self.n_sources} must be positive."
            )
        if not (0 < self.angular_resolution_deg <= 360):
            raise ConfigValidationError(
                f"algorithm.angular_resolution_deg={self.angular_resolution_deg} "
                "must be in (0, 360]."
            )


@dataclass(frozen=True)
class VisualizationConfig:
    """Layer 4 visualization parameters. See PRDS Section 5.4, FR-017."""

    refresh_rate_hz: float
    colormap: str
    show_spectrum: bool

    def __post_init__(self) -> None:
        if self.refresh_rate_hz < 2.0:
            raise ConfigValidationError(
                f"visualization.refresh_rate_hz={self.refresh_rate_hz} is "
                "below the 2 Hz minimum required by FR-017."
            )


@dataclass(frozen=True)
class ClapConfig:
    """CLAP protocol parameters. See PRDS Section 7.6, FR-004, FR-019."""

    duration_s: float
    threshold_dbfs: float
    max_failed_channels: int

    def __post_init__(self) -> None:
        if self.duration_s <= 0:
            raise ConfigValidationError(
                f"clap.duration_s={self.duration_s} must be positive."
            )
        if self.threshold_dbfs >= 0:
            raise ConfigValidationError(
                f"clap.threshold_dbfs={self.threshold_dbfs} must be negative "
                "(it is a dBFS threshold)."
            )
        if self.max_failed_channels < 0:
            raise ConfigValidationError(
                f"clap.max_failed_channels={self.max_failed_channels} "
                "cannot be negative."
            )


@dataclass(frozen=True)
class LoggingConfig:
    """Layer 4 logging parameters. See PRDS Section 7.5, FR-018."""

    save_raw_audio: bool
    save_figures: bool
    output_dir: str

    def __post_init__(self) -> None:
        if not self.output_dir:
            raise ConfigValidationError("logging.output_dir must not be empty.")


_REQUIRED_SECTIONS = (
    "hardware",
    "array",
    "processing",
    "algorithm",
    "visualization",
    "clap",
    "logging",
)

_SECTION_BUILDERS = {
    "hardware": HardwareConfig,
    "array": ArrayConfig,
    "processing": ProcessingConfig,
    "algorithm": AlgorithmConfig,
    "visualization": VisualizationConfig,
    "clap": ClapConfig,
    "logging": LoggingConfig,
}


def _build_section(section_name: str, raw: dict[str, Any]):
    """Instantiates the dataclass for one config section, translating
    missing/unexpected keys into a ConfigValidationError instead of the
    less readable TypeError a bare dataclass(**raw) would raise.
    """
    builder = _SECTION_BUILDERS[section_name]
    expected_fields = {f for f in builder.__dataclass_fields__}
    given_fields = set(raw)

    missing = expected_fields - given_fields
    if missing:
        raise ConfigValidationError(
            f"Section '{section_name}' is missing required field(s): "
            f"{sorted(missing)}."
        )

    unexpected = given_fields - expected_fields
    if unexpected:
        raise ConfigValidationError(
            f"Section '{section_name}' has unrecognized field(s): "
            f"{sorted(unexpected)}. Check for typos against PRDS Section 7.5."
        )

    return builder(**raw)


@dataclass(frozen=True)
class PINGConfig:
    """Top-level, fully validated configuration for a single PING session
    or experiment run. This is the single object passed between layers -
    no layer should read ping_config.yaml directly.

    Each PRDS Section 7.5 section is exposed as a typed attribute:
    ``config.hardware``, ``config.array``, ``config.processing``,
    ``config.algorithm``, ``config.visualization``, ``config.clap``,
    ``config.logging``.
    """

    hardware: HardwareConfig
    array: ArrayConfig
    processing: ProcessingConfig
    algorithm: AlgorithmConfig
    visualization: VisualizationConfig
    clap: ClapConfig
    logging: LoggingConfig

    def __post_init__(self) -> None:
        # Cross-section validation: checks that depend on more than one
        # section and therefore can't live in a single section's __post_init__.
        if self.array.n_mics != self.hardware.n_channels:
            raise ConfigValidationError(
                f"array.n_mics={self.array.n_mics} does not match "
                f"hardware.n_channels={self.hardware.n_channels}. These "
                "must agree since each microphone occupies one hardware "
                "channel."
            )
        if self.processing.bandpass_high_hz > self.hardware.sample_rate / 2:
            raise ConfigValidationError(
                f"processing.bandpass_high_hz={self.processing.bandpass_high_hz} "
                f"exceeds the Nyquist frequency ({self.hardware.sample_rate / 2} Hz) "
                f"for hardware.sample_rate={self.hardware.sample_rate}."
            )

    @classmethod
    def from_yaml(cls, path: str | Path) -> "PINGConfig":
        """Loads, parses, and validates a ping_config.yaml file.

        This is the single entry point every experiment script and CLI
        command should use to obtain configuration (PRDS Section 5.4,
        Step 1: "Startup: load configuration from ping_config.yaml").

        Args:
            path: Path to a YAML file matching the schema in PRDS Section 7.5.

        Returns:
            A fully validated, immutable PINGConfig.

        Raises:
            FileNotFoundError: If path does not exist.
            yaml.YAMLError: If the file is not valid YAML.
            ConfigValidationError: If the YAML is well-formed but violates a
                PRDS requirement, is missing a section/field, or contains an
                unrecognized field.
        """
        config_path = Path(path)
        if not config_path.is_file():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with config_path.open("r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)

        if not isinstance(raw, dict):
            raise ConfigValidationError(
                f"Top level of {config_path} must be a mapping of section "
                "names to section contents."
            )

        missing_sections = set(_REQUIRED_SECTIONS) - set(raw)
        if missing_sections:
            raise ConfigValidationError(
                f"{config_path} is missing required section(s): "
                f"{sorted(missing_sections)}."
            )

        unexpected_sections = set(raw) - set(_REQUIRED_SECTIONS)
        if unexpected_sections:
            raise ConfigValidationError(
                f"{config_path} has unrecognized top-level section(s): "
                f"{sorted(unexpected_sections)}. Expected: {list(_REQUIRED_SECTIONS)}."
            )

        sections = {
            name: _build_section(name, raw[name]) for name in _REQUIRED_SECTIONS
        }

        return cls(**sections)