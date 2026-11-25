import pickle
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

from . import calc, main

root_folder = Path(__file__).resolve().parents[2] / "measurements"


def runtest(starthz, endhz, stephz, foldername, repeat=1):
    """Capture and pickle accelerometer and IR signals over a frequency sweep."""
    folder_path = root_folder / foldername
    folder_path.mkdir(parents=True, exist_ok=True)
    for freq in range(starthz, endhz, stephz):
        print(f"measuring {freq} Hz")
        for idx in range(repeat):
            print(f"Cycle {idx}")
            res = main.main(frequency=freq)
            filename = folder_path / f"{freq}{idx}.p"
            with open(filename, "wb") as f:
                pickle.dump(res, f)


def loadfiles(folder: str | Path | None = None):
    """Load pickled measurements from ``folder`` into a :class:`pandas.DataFrame`."""
    import pandas as pd

    if folder:
        candidate = Path(folder)
        target_dir = candidate if candidate.is_dir() else root_folder / folder
    else:
        target_dir = root_folder

    files = sorted(target_dir.glob("*.p"))
    if not files:
        return pd.DataFrame()

    rows = []
    for path in files:
        with open(path, "rb") as f:
            dct = pickle.load(f)
        rows.append({"file": path.name, **calc.lockin_demodulate(dct)})
    return pd.DataFrame(rows)


def plotfiles(df, show=True):
    """Plot 1xRPM vibration amplitude and phase versus rotor frequency."""
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(12, 5))
    if fig.canvas.manager is not None:
        fig.canvas.manager.set_window_title("Vibration and phase vs. rotor frequency")

    axes[0].scatter(df["frot"], df["amplitude"])
    axes[0].set_title("1xRPM vibration vs. rotor frequency")
    axes[0].set(xlabel="Mean rotor frequency (Hz)", ylabel="1xRPM amplitude (a.u.)")
    axes[0].grid()

    axes[1].scatter(df["frot"], df["phase_deg"])
    axes[1].set_title("Phase vs. rotor frequency")
    axes[1].set(xlabel="Mean rotor frequency (Hz)", ylabel="Phase (deg)")
    axes[1].grid()

    fig.tight_layout()
    if show:
        plt.show()
    return fig


def plot_balancing_summary(save_path: str | Path | None = None, show: bool = True):
    """Generate a 2-panel single-plane balancing proof figure from ``measurements/``."""
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.projections.polar import PolarAxes

    df_no = loadfiles("without_weight")
    df_tr = loadfiles("weight")
    df_tr5 = loadfiles("weight_5")

    sub_no = df_no[df_no["frot"].between(48.5, 53.0)]
    sub_tr = df_tr[df_tr["frot"].between(48.5, 53.0)]
    v0 = complex(np.mean(sub_no["vector"]))
    vt = complex(np.mean(sub_tr["vector"]))
    bal = calc.single_plane_balance(v0, vt, trial_mass=0.060)

    fig = plt.figure(figsize=(13.0, 5.8), dpi=150)
    gs = fig.add_gridspec(1, 2, width_ratios=[1.0, 1.15], wspace=0.28)
    ax_polar = cast(PolarAxes, fig.add_subplot(gs[0, 0], projection="polar"))
    ax_speed = fig.add_subplot(gs[0, 1])

    # Left panel: Polar clock-face vibration vectors in the 48.5-53 Hz band
    th_no = np.angle(sub_no["vector"])
    r_no = np.abs(sub_no["vector"])
    th_tr = np.angle(sub_tr["vector"])
    r_tr = np.abs(sub_tr["vector"])

    ax_polar.scatter(
        th_no,
        r_no,
        color="#e06666",
        alpha=0.55,
        s=40,
        label="No weight runs (48.5-53 Hz)",
    )
    ax_polar.scatter(
        th_tr, r_tr, color="#4a86e8", alpha=0.65, s=40, label="Trial weight 60 mg runs"
    )

    th0, r0 = float(np.angle(v0)), float(abs(v0))
    tht, rt = float(np.angle(vt)), float(abs(vt))
    x0, y0 = r0 * float(np.cos(th0)), r0 * float(np.sin(th0))
    xt, yt = rt * float(np.cos(tht)), rt * float(np.sin(tht))
    xm, ym = 0.5 * (x0 + xt), 0.5 * (y0 + yt)
    thm, rm = float(np.arctan2(ym, xm)), float(np.hypot(xm, ym))

    ax_polar.annotate(
        "",
        xy=(th0, r0),
        xytext=(0.0, 0.0),
        arrowprops={
            "arrowstyle": "->,head_width=0.35,head_length=0.55",
            "color": "#b71c1c",
            "lw": 2.8,
        },
    )
    ax_polar.annotate(
        "",
        xy=(tht, rt),
        xytext=(0.0, 0.0),
        arrowprops={
            "arrowstyle": "->,head_width=0.35,head_length=0.55",
            "color": "#0d47a1",
            "lw": 2.8,
        },
    )
    ax_polar.annotate(
        "",
        xy=(tht, rt),
        xytext=(th0, r0),
        arrowprops={
            "arrowstyle": "->,head_width=0.28,head_length=0.45",
            "color": "#555555",
            "lw": 1.6,
            "ls": "--",
        },
    )
    ax_polar.set_rlabel_position(135)
    ax_polar.annotate(
        f"V0 mean\n{r0:.0f} @ {np.degrees(th0) % 360:.1f} deg",
        xy=(th0, r0),
        xytext=(np.radians(-62.0), 185.0),
        color="#b71c1c",
        fontsize=8.5,
        fontweight="bold",
        ha="center",
        va="top",
        arrowprops={"arrowstyle": "-", "color": "#b71c1c", "lw": 1.0, "alpha": 0.7},
    )
    ax_polar.annotate(
        f"Vt mean (-{bal['reduction_ratio']:.1f}x)\n{rt:.1f} @ {np.degrees(tht) % 360:.1f} deg",
        xy=(tht, rt),
        xytext=(np.radians(48.0), 132.0),
        color="#0d47a1",
        fontsize=8.5,
        fontweight="bold",
        ha="center",
        va="bottom",
        arrowprops={"arrowstyle": "->", "color": "#0d47a1", "lw": 1.1},
    )
    ax_polar.annotate(
        "Effect of 60 mg\n(Vt - V0)",
        xy=(thm, rm),
        xytext=(np.radians(-110.0), 130.0),
        color="#444444",
        fontsize=8.0,
        ha="center",
        va="center",
        bbox={
            "boxstyle": "round,pad=0.2",
            "facecolor": "white",
            "alpha": 0.9,
            "edgecolor": "#cccccc",
        },
        arrowprops={"arrowstyle": "->", "color": "#555555", "lw": 1.0},
    )
    ax_polar.set_ylim(0, max(235.0, r0 * 1.35))
    ax_polar.set_title(
        "Single-Plane Clock-Face Vectors (48.5-53 Hz)", pad=18, y=1.04, fontsize=10.5
    )
    ax_polar.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.10),
        ncol=2,
        frameon=False,
        fontsize=8.5,
    )

    # Right panel: 1xRPM vibration vs frequency across all 30 runs
    ax_speed.axvspan(
        56.5, 61.5, color="#ffe082", alpha=0.35, label="~60 Hz suspension resonance"
    )
    ax_speed.scatter(
        df_no["frot"],
        df_no["amplitude"],
        color="#c62828",
        marker="o",
        s=55,
        alpha=0.85,
        label="No weight (10 Hz pulse)",
    )
    ax_speed.scatter(
        df_tr["frot"],
        df_tr["amplitude"],
        color="#1565c0",
        marker="s",
        s=55,
        alpha=0.85,
        label="With 60 mg putty (10 Hz pulse)",
    )
    ax_speed.scatter(
        df_tr5["frot"],
        df_tr5["amplitude"],
        color="#2e7d32",
        marker="^",
        s=58,
        alpha=0.85,
        label="With 60 mg putty (5 Hz pulse)",
    )
    ax_speed.annotate(
        f"~{bal['reduction_ratio']:.1f}x reduction\n(48.5-53 Hz)",
        xy=(50.8, 30.0),
        xytext=(41.5, 115.0),
        fontsize=8.5,
        fontweight="bold",
        color="#1565c0",
        arrowprops={"arrowstyle": "->", "color": "#1565c0", "lw": 1.3},
    )
    ax_speed.annotate(
        "Resonance outlier\n(58.5 Hz, A=540)",
        xy=(58.54, 539.9),
        xytext=(42.5, 470.0),
        fontsize=8.5,
        color="#8d6e00",
        arrowprops={"arrowstyle": "->", "color": "#8d6e00", "lw": 1.2},
    )
    ax_speed.set_xlim(29.0, 61.5)
    ax_speed.set_ylim(-10.0, 580.0)
    ax_speed.set_xlabel("Rotor frequency (Hz)")
    ax_speed.set_ylabel("1xRPM vibration amplitude (a.u.)")
    ax_speed.set_title(
        "1xRPM Vibration vs. Rotor Speed (All 30 Runs)", pad=18, y=1.04, fontsize=10.5
    )
    ax_speed.grid(True, linestyle=":", alpha=0.6)
    ax_speed.legend(loc="upper left", fontsize=8.0, frameon=True, framealpha=0.9)

    fig.suptitle(
        f"Single-Plane Balancing Proof on 2021 Prism Data "
        f"(optimal correction: {bal['correction_mass'] * 1000:.1f} mg at "
        f"{bal['relative_angle_deg']:+.1f} deg vs. trial weight)",
        fontsize=11.5,
        fontweight="bold",
        y=0.98,
    )
    fig.subplots_adjust(top=0.83, bottom=0.16, left=0.06, right=0.97)
    if save_path is not None:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    if show:
        plt.show()
    return fig


def plot_time_signals(
    source: str | Path | Mapping[str, Any] = "without_weight/100.p",
    t_start: float = 0.06,
    t_end: float = 0.145,
    save_path: str | Path | None = None,
    show: bool = True,
):
    """Plot zoomed accelerometer and IR time signals with the extracted 1xRPM wobble wave."""
    import matplotlib.pyplot as plt
    import numpy as np

    if isinstance(source, Mapping):
        dct = source
        label_name = "live capture"
    else:
        dct = calc.read_file(source)
        label_name = Path(source).as_posix()

    fs = float(dct["sample_freq"])
    ac = np.asarray(dct["ac_meas"], dtype=float)
    ac = ac - np.mean(ac)
    ir = np.asarray(dct["ir_meas"], dtype=float)
    t = np.arange(len(ac), dtype=float) / fs

    t_end = min(float(t_end), float(t[-1]))
    t_start = 0.0 if float(t_start) >= t_end else float(t_start)

    res = calc.lockin_demodulate(dct)
    edges = np.flatnonzero((ir[1:] - ir[:-1]) < -0.5) + 1

    wave_t_parts, wave_y_parts = [], []
    for k in range(len(edges) - 1):
        t0 = edges[k] / fs
        t1 = edges[k + 1] / fs
        if t1 < t_start or t0 > t_end:
            continue
        t_seg = np.linspace(t0, t1, 80, endpoint=False)
        theta = np.linspace(0.0, 2.0 * np.pi, 80, endpoint=False)
        wave_seg = np.real(res["vector"] * np.exp(1j * theta))
        in_win = (t_seg >= t_start) & (t_seg <= t_end)
        if np.any(in_win):
            wave_t_parts.append(t_seg[in_win])
            wave_y_parts.append(wave_seg[in_win])

    t_wave = np.concatenate(wave_t_parts) if wave_t_parts else np.array([], dtype=float)
    y_wave = np.concatenate(wave_y_parts) if wave_y_parts else np.array([], dtype=float)

    mask = (t >= t_start) & (t <= t_end)
    edge_times = edges / fs
    edge_times = edge_times[(edge_times >= t_start) & (edge_times <= t_end)]

    fig, (ax_ac, ax_ir) = plt.subplots(
        2,
        1,
        figsize=(10.5, 5.2),
        dpi=150,
        sharex=True,
        gridspec_kw={"height_ratios": [1.55, 1.0], "hspace": 0.16},
    )

    ax_ac.plot(
        t[mask],
        ac[mask],
        color="#5b84b1",
        lw=1.3,
        alpha=0.8,
        label="Raw accelerometer signal",
    )
    ax_ac.plot(
        t_wave,
        y_wave,
        color="#c62828",
        lw=2.3,
        label=f"Extracted 1xRPM wobble ({res['amplitude']:.0f} a.u. @ {res['frot']:.1f} Hz)",
    )
    for idx, te in enumerate(edge_times):
        ax_ac.axvline(
            te,
            color="#888888",
            ls="--",
            lw=0.9,
            alpha=0.65,
            label="IR trigger edge (1 revolution)" if idx == 0 else None,
        )
    ax_ac.set_ylabel("Acceleration (a.u.)")
    ax_ac.set_title(
        f"What We Measure: Raw Time Signals ({label_name})",
        fontsize=11,
        fontweight="bold",
        pad=10,
    )
    ax_ac.grid(True, linestyle=":", alpha=0.55)
    ax_ac.legend(loc="upper right", fontsize=8.5, frameon=True, framealpha=0.92)

    ax_ir.step(
        t[mask],
        ir[mask],
        where="post",
        color="#2e7d32",
        lw=1.9,
        label="TCRT5000 IR output (active-LOW on tape)",
    )
    ax_ir.fill_between(t[mask], ir[mask], 1.0, step="post", color="#2e7d32", alpha=0.22)
    for te in edge_times:
        ax_ir.axvline(te, color="#888888", ls="--", lw=0.9, alpha=0.65)
    ax_ir.set_yticks([0, 1])
    ax_ir.set_yticklabels(["0 (TRIGGER)", "1 (IDLE)"])
    ax_ir.set_ylim(-0.15, 1.38)
    ax_ir.set_xlabel("Time (s)")
    ax_ir.set_ylabel("IR sensor")
    ax_ir.set_xlim(t_start, t_end)
    ax_ir.grid(True, linestyle=":", alpha=0.55)
    ax_ir.legend(loc="upper right", fontsize=8.5, frameon=True, framealpha=0.92)

    if save_path is not None:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    if show:
        plt.show()
    return fig
