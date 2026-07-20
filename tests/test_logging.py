"""
tests/test_logging.py

Unit tests for ping.logging: verifies metadata files are written
correctly, the markdown log is appended to (never overwritten), invalid
status/experiment_id values are rejected, and multiple sessions for the
same experiment_id accumulate rather than collide or overwrite.
"""

import json
import re
from pathlib import Path

import pytest

from ping.config import PINGConfig
from ping.logging import (
    ExperimentLogError,
    log_experiment_session,
    STATUS_LABELS,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = REPO_ROOT / "configs" / "ping_config.yaml"


@pytest.fixture
def config() -> PINGConfig:
    return PINGConfig.from_yaml(DEFAULT_CONFIG_PATH)


def test_log_session_writes_metadata_file(tmp_path, config):
    log_path = tmp_path / "EXPERIMENT_LOG.md"
    metadata_dir = tmp_path / "logs"

    metadata_path = log_experiment_session(
        experiment_id="EXP-001",
        title="Multichannel Synchronization",
        status="PASS",
        config=config,
        notes="Timing offset 0.3 samples, within FR-001.",
        log_path=log_path,
        metadata_dir=metadata_dir,
    )

    assert metadata_path.exists()
    assert metadata_path.parent == metadata_dir

    with metadata_path.open(encoding="utf-8") as f:
        data = json.load(f)

    assert data["experiment_id"] == "EXP-001"
    assert data["status"] == "PASS"
    assert data["config"]["hardware"]["sample_rate"] == 44100
    assert "Timing offset" in data["notes"]


def test_log_session_appends_row_to_markdown(tmp_path, config):
    log_path = tmp_path / "EXPERIMENT_LOG.md"
    metadata_dir = tmp_path / "logs"

    log_experiment_session(
        experiment_id="EXP-001",
        title="Multichannel Synchronization",
        status="PASS",
        config=config,
        notes="First run.",
        log_path=log_path,
        metadata_dir=metadata_dir,
    )

    content = log_path.read_text(encoding="utf-8")
    assert "| ID | Date | Status | Notes |" in content
    assert "EXP-001" in content
    assert "PASS" in content
    assert "First run." in content


def test_log_creates_file_with_header_if_missing(tmp_path, config):
    log_path = tmp_path / "does_not_exist_yet.md"
    metadata_dir = tmp_path / "logs"

    assert not log_path.exists()
    log_experiment_session(
        experiment_id="EXP-002",
        title="CLAP Sensitivity Calibration",
        status="FAIL",
        config=config,
        log_path=log_path,
        metadata_dir=metadata_dir,
    )
    assert log_path.exists()
    assert log_path.read_text(encoding="utf-8").startswith("| ID | Date | Status | Notes |")


def test_existing_log_rows_are_preserved_not_overwritten(tmp_path, config):
    """Simulates the repository's real EXPERIMENT_LOG.md, which already
    contains 'Planned' placeholder rows before any session is logged.
    Those rows must survive untouched.
    """
    log_path = tmp_path / "EXPERIMENT_LOG.md"
    log_path.write_text(
        "| ID | Date | Status | Notes |\n"
        "|----|------|--------|-------|\n"
        "| EXP-001 | TBD | Planned | |\n"
        "| EXP-002 | TBD | Planned | |\n",
        encoding="utf-8",
    )
    metadata_dir = tmp_path / "logs"

    log_experiment_session(
        experiment_id="EXP-001",
        title="Multichannel Synchronization",
        status="PASS",
        config=config,
        log_path=log_path,
        metadata_dir=metadata_dir,
    )

    content = log_path.read_text(encoding="utf-8")
    assert "| EXP-001 | TBD | Planned | |" in content   # untouched original row
    assert "| EXP-002 | TBD | Planned | |" in content   # untouched original row
    assert "PASS" in content                           # new row appended


def test_multiple_sessions_same_experiment_id_both_recorded(tmp_path, config):
    log_path = tmp_path / "EXPERIMENT_LOG.md"
    metadata_dir = tmp_path / "logs"

    path_1 = log_experiment_session(
        experiment_id="EXP-001", title="Sync", status="FAIL",
        config=config, notes="Attempt 1 - channel 4 desynced.",
        log_path=log_path, metadata_dir=metadata_dir,
    )
    path_2 = log_experiment_session(
        experiment_id="EXP-001", title="Sync", status="PASS",
        config=config, notes="Attempt 2 - fixed buffer underrun.",
        log_path=log_path, metadata_dir=metadata_dir,
    )

    assert path_1 != path_2
    assert path_1.exists() and path_2.exists()

    content = log_path.read_text(encoding="utf-8")
    # "EXP-001" legitimately appears twice per row (ID column + the
    # metadata filename embedded in the link), so count matching rows
    # rather than raw substring occurrences.
    exp_001_rows = [line for line in content.splitlines() if line.startswith("| EXP-001")]
    assert len(exp_001_rows) == 2
    assert "FAIL" in content
    assert "PASS" in content


def test_invalid_status_raises(tmp_path, config):
    with pytest.raises(ExperimentLogError, match="status"):
        log_experiment_session(
            experiment_id="EXP-001",
            title="Sync",
            status="SUCCESS",  # not a valid status
            config=config,
            log_path=tmp_path / "log.md",
            metadata_dir=tmp_path / "logs",
        )


def test_invalid_experiment_id_raises(tmp_path, config):
    with pytest.raises(ExperimentLogError, match="experiment_id"):
        log_experiment_session(
            experiment_id="SYNC-TEST",  # doesn't match EXP-### convention
            title="Sync",
            status="PASS",
            config=config,
            log_path=tmp_path / "log.md",
            metadata_dir=tmp_path / "logs",
        )


def test_pipe_character_in_notes_is_escaped(tmp_path, config):
    """A '|' in free-text notes would otherwise break the markdown table."""
    log_path = tmp_path / "EXPERIMENT_LOG.md"
    log_experiment_session(
        experiment_id="EXP-003",
        title="Baseline DOA Accuracy",
        status="WARN",
        config=config,
        notes="Accuracy 4.8 deg | within tolerance but near threshold",
        log_path=log_path,
        metadata_dir=tmp_path / "logs",
    )
    content = log_path.read_text(encoding="utf-8")
    assert r"\|" in content  # confirms the pipe in "notes" was actually escaped

    data_rows = [
        line for line in content.splitlines()
        if line.startswith("| EXP-003")
    ]
    assert len(data_rows) == 1

    # Split on unescaped pipes only (a preceding backslash means "not a
    # column delimiter"), since the escaped '|' inside notes is still a
    # literal '|' character in the raw file - a naive count would be misled.
    fields = re.split(r"(?<!\\)\|", data_rows[0])
    assert len(fields) == 6  # leading '', 4 columns, trailing '' from split


def test_all_status_labels_are_distinct():
    assert len(set(STATUS_LABELS.values())) == len(STATUS_LABELS)