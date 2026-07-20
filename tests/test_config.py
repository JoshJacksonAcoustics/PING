"""
tests/test_config.py

Unit tests for ping.config. Covers the happy path against the
repository's default ping_config.yaml, plus the invalid-value and
missing/unexpected-field cases that make config failures loud and early
rather than silent (see config.py module docstring).

Acceptance criteria covered here (per task spec, PRDS Section 7.5):
  - PINGConfig.from_yaml(path) loads a config file
  - All config sections accessible as attributes
  - Raises FileNotFoundError if config file missing
"""

from pathlib import Path

import pytest
import yaml

from ping.config import ConfigValidationError, PINGConfig

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = REPO_ROOT / "configs" / "ping_config.yaml"


@pytest.fixture
def valid_raw_config() -> dict:
    """Loads the repository's default ping_config.yaml as a raw dict, so
    individual tests can mutate a copy to construct invalid variants.
    """
    with DEFAULT_CONFIG_PATH.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _write_config(tmp_path: Path, contents: dict) -> Path:
    path = tmp_path / "test_config.yaml"
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(contents, f)
    return path


def test_default_config_loads_successfully():
    """The repository's own ping_config.yaml must always be valid - this
    is effectively a smoke test that the schema and the default file
    stay in sync.
    """
    config = PINGConfig.from_yaml(DEFAULT_CONFIG_PATH)
    assert config.hardware.sample_rate == 44100
    assert config.array.geometry_type == "circular"
    assert config.algorithm.primary_algorithm == "music"


def test_all_sections_accessible_as_attributes():
    """Explicit acceptance-criteria check: every PRDS Section 7.5 section
    must be reachable as a typed attribute on the returned config.
    """
    config = PINGConfig.from_yaml(DEFAULT_CONFIG_PATH)
    assert hasattr(config, "hardware")
    assert hasattr(config, "array")
    assert hasattr(config, "processing")
    assert hasattr(config, "algorithm")
    assert hasattr(config, "visualization")
    assert hasattr(config, "clap")
    assert hasattr(config, "logging")


def test_missing_file_raises_file_not_found(tmp_path: Path):
    missing_path = tmp_path / "does_not_exist.yaml"
    with pytest.raises(FileNotFoundError):
        PINGConfig.from_yaml(missing_path)


def test_missing_top_level_section_raises(tmp_path, valid_raw_config):
    del valid_raw_config["clap"]
    path = _write_config(tmp_path, valid_raw_config)
    with pytest.raises(ConfigValidationError, match="clap"):
        PINGConfig.from_yaml(path)


def test_unexpected_top_level_section_raises(tmp_path, valid_raw_config):
    valid_raw_config["not_a_real_section"] = {"foo": "bar"}
    path = _write_config(tmp_path, valid_raw_config)
    with pytest.raises(ConfigValidationError, match="not_a_real_section"):
        PINGConfig.from_yaml(path)


def test_missing_field_in_section_raises(tmp_path, valid_raw_config):
    del valid_raw_config["hardware"]["sample_rate"]
    path = _write_config(tmp_path, valid_raw_config)
    with pytest.raises(ConfigValidationError, match="sample_rate"):
        PINGConfig.from_yaml(path)


def test_sample_rate_below_minimum_raises(tmp_path, valid_raw_config):
    valid_raw_config["hardware"]["sample_rate"] = 22050
    path = _write_config(tmp_path, valid_raw_config)
    with pytest.raises(ConfigValidationError, match="FR-002"):
        PINGConfig.from_yaml(path)


def test_invalid_geometry_type_raises(tmp_path, valid_raw_config):
    valid_raw_config["array"]["geometry_type"] = "hexagonal"
    path = _write_config(tmp_path, valid_raw_config)
    with pytest.raises(ConfigValidationError, match="geometry_type"):
        PINGConfig.from_yaml(path)


def test_overlap_out_of_range_raises(tmp_path, valid_raw_config):
    valid_raw_config["processing"]["overlap"] = 1.5
    path = _write_config(tmp_path, valid_raw_config)
    with pytest.raises(ConfigValidationError, match="overlap"):
        PINGConfig.from_yaml(path)


def test_phantom_power_out_of_range_raises(tmp_path, valid_raw_config):
    valid_raw_config["hardware"]["phantom_power_v"] = 12.0
    path = _write_config(tmp_path, valid_raw_config)
    with pytest.raises(ConfigValidationError, match="phantom_power_v"):
        PINGConfig.from_yaml(path)


def test_bandpass_high_below_low_raises(tmp_path, valid_raw_config):
    valid_raw_config["processing"]["bandpass_low_hz"] = 3000.0
    valid_raw_config["processing"]["bandpass_high_hz"] = 2000.0
    path = _write_config(tmp_path, valid_raw_config)
    with pytest.raises(ConfigValidationError, match="bandpass"):
        PINGConfig.from_yaml(path)


def test_mic_count_mismatch_raises(tmp_path, valid_raw_config):
    valid_raw_config["array"]["n_mics"] = 6
    path = _write_config(tmp_path, valid_raw_config)
    with pytest.raises(ConfigValidationError, match="n_mics"):
        PINGConfig.from_yaml(path)


def test_bandpass_above_nyquist_raises(tmp_path, valid_raw_config):
    valid_raw_config["processing"]["bandpass_high_hz"] = 30000.0
    path = _write_config(tmp_path, valid_raw_config)
    with pytest.raises(ConfigValidationError, match="Nyquist"):
        PINGConfig.from_yaml(path)


def test_unexpected_field_in_section_raises(tmp_path, valid_raw_config):
    valid_raw_config["clap"]["extra_field"] = 123
    path = _write_config(tmp_path, valid_raw_config)
    with pytest.raises(ConfigValidationError, match="extra_field"):
        PINGConfig.from_yaml(path)


def test_config_is_immutable():
    """PINGConfig and its sections are frozen dataclasses: once loaded,
    a config must not be mutable mid-experiment, since that would break
    reproducibility guarantees (PRDS Section 7.1).
    """
    config = PINGConfig.from_yaml(DEFAULT_CONFIG_PATH)
    with pytest.raises(AttributeError):
        config.hardware.sample_rate = 48000