# Contributing to PING

Thank you for your interest in contributing to PING — Portable Intelligent Noise Grid.

---

## Project Structure and Ownership

PING is an independent acoustic research platform led and primarily developed by **Joshua Jackson**. All research direction, system architecture, hardware design, algorithm implementation, experimental design, validation methodology, and technical documentation are the work of the Project Lead.

**Contributions are welcome in the following areas:**
- Software module implementation (assigned by Project Lead)
- Unit testing and test suite expansion
- GUI development and visualization improvements
- Configuration parsing and CLI improvements
- Bug fixes and code cleanup
- Documentation formatting and improvements

**The following remain exclusively under Project Lead direction:**
- System architecture and design decisions
- Requirements and functional specifications
- Beamforming and signal processing algorithms
- Experimental design and validation methodology
- Hardware CAD and fabrication
- Technical reports and publications
- Repository organization and branch management

---

## How to Contribute

### 1. Get assigned a task
All contributions begin with a task assigned by the Project Lead. Do not open pull requests for unassigned work — open an issue or reach out directly first to discuss what you'd like to work on.

### 2. Fork and branch
Fork the repository and create a branch named descriptively:

```bash
git checkout -b feature/configuration-parser
git checkout -b fix/clap-threshold-bug
git checkout -b test/geometry-unit-tests
```

Never commit directly to `main`.

### 3. Write clean code
Follow the existing code style:
- All functions must have docstrings explaining **why**, not just what
- No magic numbers — every constant must be named and commented
- Type hints on all function signatures
- Follow the four-layer architecture (see PRDS Section 5)

### 4. Write tests
Every new function should have a corresponding test in `tests/`. Run the full test suite before submitting:

```bash
pytest tests/ -v
```

All tests must pass before a pull request will be reviewed.

### 5. Submit a pull request
Open a pull request against `main` with:
- A clear title describing what the PR does
- A description of what was implemented and why
- Reference to the issue or task it addresses
- Confirmation that all tests pass

### 6. Code review
The Project Lead will review all pull requests. Feedback may be given requesting changes before the PR is accepted. PRs are merged solely at the discretion of the Project Lead.

---

## Code Style

- **Language:** Python 3.10+
- **Formatting:** Follow PEP 8
- **Docstrings:** Every function, every class, every module
- **No magic numbers:** Name every constant with a comment explaining its value
- **No hardcoded parameters:** All configurable values belong in `ping_config.yaml`

Example of expected docstring format:

```python
def estimate_doa(signals: np.ndarray, mic_positions: np.ndarray) -> np.ndarray:
    """
    Estimates direction of arrival from multichannel signals.

    Uses the MUSIC algorithm with eigendecomposition of the
    cross-spectral matrix. Assumes far-field plane wave model
    (valid for sources > 0.5m from RING-B array center).

    Args:
        signals: (n_samples, n_channels) calibrated audio array
        mic_positions: (2, n_mics) array of mic coordinates in meters

    Returns:
        spatial_spectrum: (360,) array, one value per degree.
                          Peak indicates estimated source direction.

    Raises:
        ValueError: If signals and mic_positions channel counts don't match
    """
```

---

## Commit Messages

Write clear, descriptive commit messages:

```
# Good
Add Hann windowing to preprocessing pipeline
Fix CLAP threshold detection on low-gain channels
Implement unit tests for circular array geometry

# Bad
fix stuff
update
changes
```

---

## Questions

For questions about architecture decisions, task assignments, or project direction, contact the Project Lead directly:

**Joshua Jackson**
joshjacksonaudio@gmail.com
github.com/JoshJacksonAcoustics

---

*All contributions to PING are made under the understanding that architectural direction, research decisions, and final integration authority rest with the Project Lead.*