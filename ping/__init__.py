"""
ping
====

PING (Portable Intelligent Noise Grid) - a modular 8-channel microphone array research platform for acoustic source localization, beamforming algorithm comparison, and array geometry investigation.

See docs/PING_PRDS_v0.1.docx for the full project specification. This package follows the four-layer architecture defined in PRDS section 5:

    Layer 1 - ping.hardware (device I/O only)
    Layer 2 - ping.signal_processing, ping.calibration, ping.geometry
    Layer 3 - ping.beamforming
    Layer 4 - ping.visualization, experiments/
    
ping.config is a cross-cutting utility used by all four layers and does not itself belong to any layer.
"""