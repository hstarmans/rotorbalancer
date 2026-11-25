import pickle
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import numpy as np

root_folder = Path(__file__).resolve().parents[2] / "measurements"


def read_file(fname: str | Path) -> dict[str, Any]:
    """Load a pickled measurement dictionary from ``fname`` or ``measurements/``."""
    candidate = Path(fname)
    if not candidate.is_file():
        candidate = root_folder / fname
    with open(candidate, "rb") as f:
        return pickle.load(f)


def lockin_demodulate(measurement: Mapping[str, Any]) -> dict[str, Any]:
    """Extract the 1xRPM vibration vector via synchronous lock-in demodulation.

    The TCRT5000 digital IR output is active-LOW (``1 -> 0`` falling edge when
    reflective tape passes). Segments ``ac_meas`` between consecutive trigger
    edges and projects each revolution onto ``exp(-1j * theta)``, making
    amplitude and phase immune to RPM drift and FFT bin quantization.
    """
    sample_freq = float(measurement["sample_freq"])
    ir = np.asarray(measurement["ir_meas"], dtype=float)
    ac = np.asarray(measurement["ac_meas"], dtype=float)
    ac = ac - np.mean(ac)

    edges = np.flatnonzero((ir[1:] - ir[:-1]) < -0.5) + 1
    if len(edges) < 2:
        raise ValueError("Need at least two IR trigger edges to lock onto revolutions")

    periods = np.diff(edges)
    vecs = []
    for k in range(len(edges) - 1):
        seg = ac[edges[k] : edges[k + 1]]
        m = len(seg)
        if m == 0:
            continue
        theta = 2.0 * np.pi * np.arange(m, dtype=float) / m
        vecs.append((2.0 / m) * np.sum(seg * np.exp(-1j * theta)))

    if not vecs:
        raise ValueError("No complete revolutions found in measurement")

    v_mean = complex(np.mean(np.asarray(vecs, dtype=complex)))
    frot = float(sample_freq / float(np.mean(periods)))
    return {
        "frot": frot,
        "amplitude": float(abs(v_mean)),
        "phase_deg": float(np.degrees(np.angle(v_mean)) % 360.0),
        "vector": v_mean,
        "n_cycles": len(vecs),
    }


def _as_complex_vector(val: complex | Mapping[str, Any]) -> complex:
    if isinstance(val, Mapping):
        return complex(val["vector"])
    return complex(val)


def single_plane_balance(
    v0: complex | Mapping[str, Any],
    vt: complex | Mapping[str, Any],
    trial_mass: float,
    trial_angle_deg: float = 0.0,
) -> dict[str, Any]:
    """Calculate single-plane correction weight via the Influence Coefficient Method.

    Parameters
    ----------
    v0 : complex | Mapping[str, Any]
        Baseline vibration vector (no trial weight), or dict returned by
        :func:`lockin_demodulate`.
    vt : complex | Mapping[str, Any]
        Trial-run vibration vector (with ``trial_mass`` mounted at
        ``trial_angle_deg``), or dict returned by :func:`lockin_demodulate`.
    trial_mass : float
        Known trial mass (e.g. grams or milligrams; outputs use the same unit).
    trial_angle_deg : float
        Angular location where the trial mass was placed [degrees].
    """
    mass = float(trial_mass)
    if mass <= 0.0:
        raise ValueError("trial_mass must be positive")

    v0_c = _as_complex_vector(v0)
    vt_c = _as_complex_vector(vt)
    wt = mass * complex(np.exp(1j * np.radians(float(trial_angle_deg))))
    delta = vt_c - v0_c
    if abs(delta) < 1e-12:
        raise ValueError("Trial weight caused zero measurable change (Vt == V0)")

    influence = delta / wt
    w_corr = -v0_c / influence
    w_add = w_corr - wt
    rel_angle = float(np.degrees(np.angle(w_corr / wt)))
    reduction = float(abs(v0_c) / abs(vt_c)) if abs(vt_c) > 0.0 else float("inf")
    return {
        "correction_mass": float(abs(w_corr)),
        "correction_angle_deg": float(np.degrees(np.angle(w_corr)) % 360.0),
        "relative_angle_deg": rel_angle,
        "additional_mass": float(abs(w_add)),
        "additional_angle_deg": float(np.degrees(np.angle(w_add)) % 360.0),
        "influence": complex(influence),
        "reduction_ratio": reduction,
    }
