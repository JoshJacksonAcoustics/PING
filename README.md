# PING — Portable Intelligent Noise Grid

> A modular 8-channel microphone array research platform for acoustic source localization, beamforming algorithm comparison, and array geometry investigation.

---

## Overview

PING is an independent acoustic research platform developed by **Joshua Jackson**, building directly on acoustic signal processing research conducted at **NASA Ames Research Center** (2025).

The project originated from a fundamental limitation identified during the author's NASA Ames internship: a multi-microphone testbed for brushless DC motor fault detection could identify *that* a fault existed, but could not determine *which* motor was faulting on a multi-rotor UAV platform. PING was conceived to answer that question using spatial beamforming and direction-of-arrival estimation.

**The central research question:**

> *Could a single microphone array, positioned externally to a UAV, localize acoustic fault signatures to a specific motor without requiring per-motor instrumentation?*

---

## Platform Architecture

### Hardware

| Component | Specification |
|-----------|--------------|
| Microphones | 8x Behringer ECM8000 (omnidirectional measurement) |
| Interface | TASCAM US-16x08 (8-channel simultaneous, 24-bit / 44,100 Hz) |
| Array Radii | 5.0 cm, 8.5 cm, 15.0 cm (interchangeable rings) |
| Geometries | Circular, Linear, Rectangular, Spiral, Random |
| Mounting | 5/8"-27 mic stand compatible, custom 3D printed (Onshape CAD) |
| Printer | Bambu Lab P1S — PETG final mounts, PLA prototypes |

### Array Geometries

| Mount | Geometry | Primary Application |
|-------|----------|-------------------|
| MOUNT-1 | Circular | 360° localization, demonstrations, algorithm benchmarking |
| MOUNT-2 | Linear | Engine bay scans, vehicle fault diagnosis, corridor localization |
| MOUNT-3 | Rectangular | Acoustic imaging, near-field measurements, 2D localization |
| MOUNT-4 | Spiral | Grating lobe reduction research |
| MOUNT-5 | Random | Side lobe behavior comparison with uniform arrays |

### Interchangeable Aperture Rings

| Ring | Radius | Aliasing Frequency | Color |
|------|--------|--------------------|-------|
| RING-A | 5.0 cm | 4,476 Hz | Red |
| RING-B | 8.5 cm | 2,638 Hz | Blue (primary) |
| RING-C | 15.0 cm | 1,494 Hz | Green |

---

## Algorithms Implemented

| Algorithm | Type | Status |
|-----------|------|--------|
| GCC-PHAT | Time delay estimation | ⏳ Planned |
| Delay and Sum (DAS) | Basic beamformer | ⏳ Planned |
| MVDR (Capon) | Adaptive beamformer | ⏳ Planned |
| MUSIC | Subspace method | ⏳ Planned |
| SRP-PHAT | Steered response power | ⏳ Planned |

---

## Startup Protocol — CLAP

PING initializes via **CLAP (Channel Level Assessment Protocol)** — a built-in 8-channel synchronization and sensitivity verification test executed at every startup.

```
$ python main.py

==================================================
PING — Channel Level Assessment Protocol (CLAP)
==================================================

Recording 3s — please clap once near the array

Channel    Peak (dBFS)     RMS (dBFS)      Status
CH 1       -12.4           -18.7           ✅ PASS
CH 2       -11.9           -18.2           ✅ PASS
CH 3       -12.1           -18.5           ✅ PASS
CH 4       -12.6           -18.9           ✅ PASS
CH 5       -11.8           -18.1           ✅ PASS
CH 6       -12.3           -18.6           ✅ PASS
CH 7       -12.0           -18.3           ✅ PASS
CH 8       -12.2           -18.4           ✅ PASS

✅ CLAP: ALL SYSTEMS GO
Calibration loaded — gains applied
PING ready
```

---

## Quick Start

```bash
# Clone the repository
git clone https://github.com/JoshJacksonAcoustics/PING.git
cd PING

# Install dependencies
pip install -r requirements.txt

# Verify hardware connection
python -c "import sounddevice as sd; print(sd.query_devices())"

# Run calibration
python experiments/EXP-002_calibration.py

# Run real-time beamformer
python main.py --config configs/default.yaml --mode realtime
```

---

## Experiments

| ID | Question | Geometry | Algorithm | Status |
|----|----------|----------|-----------|--------|
| EXP-001 | Are all 8 channels sample-accurate? | — | — | ⏳ Planned |
| EXP-002 | Does CLAP reduce sensitivity spread to ±1 dB? | — | — | ⏳ Planned |
| EXP-003 | What is baseline DOA accuracy vs angle and frequency? | Circular/B | MUSIC | ⏳ Planned |
| EXP-004 | How does array radius affect accuracy and frequency range? | Circular/A,B,C | MUSIC | ⏳ Planned |
| EXP-005 | How do the 5 algorithms compare in accuracy and speed? | Circular/B | All | ⏳ Planned |
| EXP-006 | Which array geometry performs best? | All/B | MUSIC | ⏳ Planned |
| EXP-007 | Can MVDR achieve ≥6 dB SNR improvement? | Circular/B | MVDR | ⏳ Planned |
| EXP-008 | Can PING localize a vehicle suspension fault? | Linear/B | DAS | ⏳ Planned |

### Secondary Experiments (v2.0)

| ID | Question | Status |
|----|----------|--------|
| EXP-009 | Acoustic scene classification ≥70% accuracy? | ⏳ v2.0 |
| EXP-010 | Can PING localize two simultaneous sources? | ⏳ v2.0 |
| EXP-011 | Real-time acoustic camera overlay on video? | ⏳ v2.0 |
| EXP-012 | Can PING identify which UAV motor is faulting externally? | ⏳ v2.0 |

---

## Software Architecture

PING is a structured Python package organized into four layers:

```
PING/
│
├── ping/                          # Core package
│   ├── hardware/                  # TASCAM interface (Layer 1)
│   ├── signal_processing/         # Acquisition, filtering, FFT (Layer 2)
│   ├── beamforming/               # DOA algorithms (Layer 3)
│   ├── calibration/               # CLAP protocol (Layer 2)
│   ├── geometry/                  # Array geometries (Layer 2)
│   └── visualization/             # Heatmap, plots (Layer 4)
│
├── experiments/                   # Structured experiment scripts
├── configs/                       # YAML configuration files
├── data/                          # Calibration gains, recordings
├── results/                       # Figures, experiment reports
├── docs/                          # Technical report, theory documents
├── hardware/                      # CAD files, photos
├── tests/                         # pytest unit and integration tests
├── main.py                        # Entry point
└── requirements.txt
```

**Design principles:**
- Separation of concerns — each layer communicates only with adjacent layers
- Standardized interfaces — swapping geometry or algorithm is one line change
- Reproducibility — fixed seeds, config-driven, complete data logging
- No magic numbers — every constant is named and documented

---

## Project Documentation

| Document | Description |
|----------|-------------|
| [PRDS v0.1](docs/PING_PRDS_v0.1.docx) | Project Requirements and Design Specification — full system design document |
| [Theory: Beamforming](docs/theory/beamforming.md) | Mathematical derivation of DAS, MVDR, and MUSIC |
| [Theory: GCC-PHAT](docs/theory/gcc_phat.md) | Time delay estimation theory |
| [Theory: Array Geometry](docs/theory/array_geometry.md) | Spatial aliasing derivation, geometry comparison |
| [Experiment Log](data/EXPERIMENT_LOG.md) | Running log of all experiment sessions |

---

## Cost and Accessibility

PING demonstrates that research-grade acoustic array experimentation can be conducted for under $1,000 in new equipment:

| Category | Cost |
|----------|------|
| 8x Behringer ECM8000 microphones | $232 |
| 8x XLR cables | $24 |
| Bambu Lab P1S 3D printer | $399 |
| Filament, hardware, misc | $111 |
| **Total new equipment** | **$766** |

*For comparison: commercial acoustic array systems range from $8,000 to $200,000+.*

---

## Project Team

| Role | Name | Responsibilities |
|------|------|-----------------|
| Project Lead / Lead Systems Engineer / Lead Software Developer | Joshua Jackson | Project conception, system architecture, requirements engineering, hardware design, signal processing, beamforming algorithms, experimental design, validation, documentation, primary software development |
| Software Development Contributor | Brian Harris | Selected software module implementation under project direction |

---

## Background and Motivation

During an acoustic health monitoring internship at **NASA Ames Research Center** (2025), the author developed a multi-microphone testbed for brushless DC motor fault detection on electric UAV systems. The testbed used four independent microphones at fixed positions with FFT-based spectral analysis and CNN fault classification.

The fundamental limitation: each microphone was treated as an independent measurement point. No spatial localization existed. On a multi-rotor platform, anomalies could be detected but not attributed to a specific motor.

PING was designed to address this gap — building the spatial awareness capability that the NASA Ames testbed lacked.

**Related publication:**
> Jackson, J. (2025). *Acoustic Fault Detection for Uncrewed Aerial Platforms Using Physics-Informed Neural Networks.* NASA Ames Research Center Intern Poster Session, Moffett Field, CA.

---

## Future Vision

**PING v2.0** — Acoustic scene classification with real-time confidence scores:
> *"Source at 47° — Motor Bearing Fault (71% confidence)"*

**PING v3.0** — Distributed Acoustic Sensor Network (DASN):
> Three synchronized PING units triangulating acoustic events (gunshots, UAV motors, wildlife) across extended outdoor environments to within 5 meters at 500-meter range.

---

## Author

**Joshua Jackson**
Acoustics & Signal Processing Engineer
NASA Ames Research Center Intern (2025)

[joshjacksonaudio@gmail.com](mailto:joshjacksonaudio@gmail.com) | [LinkedIn](https://linkedin.com/in/joshua-jackson-40a46225a) | [GitHub](https://github.com/JoshJacksonAcoustics)

---

*PING is an independent research project. All research direction, system architecture, hardware design, algorithm implementation, experimental design, validation, and documentation are the work of the Project Lead.*
