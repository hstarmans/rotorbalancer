import marimo

__generated_with = "0.26.0"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import numpy as np
    import pandas as pd

    from rotorbalancer import calc, tools

    return calc, mo, np, pd, tools


@app.cell
def _(mo):
    mo.md(r"""
    # Rotor Balancer — Single-Plane Proof & Signal Explorer

    Explore the recorded 2021 Nano 33 BLE captures (`measurements/`) and run the two-step single-plane Influence Coefficient calculation interactively:

    $$W_{\text{corr}} = -W_t \, \frac{V_0}{V_t - V_0}$$

    1. **Inspect raw time signals** (`ac_meas` acceleration + `ir_meas` active-LOW optical trigger) and the extracted 1×RPM wobble wave.
    2. **Pick a speed band and trial weight** to compare baseline $V_0$ vs. trial $V_t$ and compute the optimal correction mass & angle.
    """)


@app.cell
def _(tools):
    df_base = tools.loadfiles("without_weight")
    df_trial = tools.loadfiles("weight")
    df_trial5 = tools.loadfiles("weight_5")
    return df_base, df_trial, df_trial5


@app.cell
def _(df_base, df_trial, df_trial5, mo):
    all_recordings = (
        [f"without_weight/{name}" for name in df_base["file"]]
        + [f"weight/{name}" for name in df_trial["file"]]
        + [f"weight_5/{name}" for name in df_trial5["file"]]
    )
    recording_picker = mo.ui.dropdown(
        options=all_recordings,
        value="without_weight/100.p",
        label="Recording",
    )
    time_window = mo.ui.range_slider(
        start=0.0,
        stop=1.0,
        step=0.005,
        value=[0.06, 0.145],
        label="Time window (s)",
    )
    mo.hstack([recording_picker, time_window], justify="start", gap=2)
    return recording_picker, time_window


@app.cell
def _(calc, mo, recording_picker, time_window, tools):
    selected_data = calc.read_file(recording_picker.value)
    selected_lockin = calc.lockin_demodulate(selected_data)
    sig_fig = tools.plot_time_signals(
        recording_picker.value,
        t_start=time_window.value[0],
        t_end=time_window.value[1],
        show=False,
    )
    mo.vstack(
        [
            mo.md(
                f"**{recording_picker.value}** — rotor frequency **{selected_lockin['frot']:.2f} Hz**, "
                f"1×RPM wobble **{selected_lockin['amplitude']:.1f} a.u. @ {selected_lockin['phase_deg']:.1f}°** "
                f"({selected_lockin['n_cycles']} revolutions)"
            ),
            sig_fig,
        ]
    )


@app.cell
def _(mo):
    speed_band = mo.ui.range_slider(
        start=47.0,
        stop=56.0,
        step=0.5,
        value=[48.5, 49.5],
        label="Speed band (Hz)",
    )
    trial_mass_mg = mo.ui.number(
        start=1.0,
        stop=500.0,
        step=1.0,
        value=60.0,
        label="Trial mass (mg)",
    )
    mo.hstack([speed_band, trial_mass_mg], justify="start", gap=2)
    return speed_band, trial_mass_mg


@app.cell
def _(calc, df_base, df_trial, mo, np, speed_band, trial_mass_mg):
    f_lo, f_hi = speed_band.value
    base_rows = df_base[df_base["frot"].between(f_lo, f_hi)]
    trial_rows = df_trial[df_trial["frot"].between(f_lo, f_hi)]
    if base_rows.empty or trial_rows.empty:
        bal_output = mo.callout(
            f"Need at least one baseline and one trial run inside {f_lo:.1f}–{f_hi:.1f} Hz.",
            kind="warn",
        )
    else:
        v0_vec = complex(np.mean(base_rows["vector"]))
        vt_vec = complex(np.mean(trial_rows["vector"]))
        bal_res = calc.single_plane_balance(
            v0_vec, vt_vec, trial_mass=float(trial_mass_mg.value) / 1000.0
        )
        bal_output = mo.md(
            f"""
    ### Single-Plane Balancing Calculation ({f_lo:.1f}–{f_hi:.1f} Hz, {len(base_rows)} baseline vs. {len(trial_rows)} trial runs)

    | Quantity | Value |
    | :--- | :--- |
    | Baseline wobble $V_0$ | `{abs(v0_vec):.1f} a.u. @ {np.degrees(np.angle(v0_vec)) % 360:.1f}°` |
    | Trial wobble $V_t$ | `{abs(vt_vec):.1f} a.u. @ {np.degrees(np.angle(vt_vec)) % 360:.1f}°` |
    | Vibration reduction ratio | **`{bal_res["reduction_ratio"]:.1f}×`** |
    | Optimal correction mass (replaces trial weight) | **`{bal_res["correction_mass"] * 1000:.1f} mg`** |
    | Placement angle vs. trial spot | **`{bal_res["relative_angle_deg"]:+.1f}°`** |
    | Additional mass (if keeping trial weight) | `{bal_res["additional_mass"] * 1000:.1f} mg @ {bal_res["additional_angle_deg"]:.1f}°` |
    """
        )
    mo.vstack([bal_output])


@app.cell
def _(df_base, df_trial, df_trial5, mo, pd, tools):
    proof_fig = tools.plot_balancing_summary(show=False)
    all_runs = pd.concat(
        [
            df_base.assign(dataset="without_weight"),
            df_trial.assign(dataset="weight"),
            df_trial5.assign(dataset="weight_5"),
        ],
        ignore_index=True,
    )[["dataset", "file", "frot", "amplitude", "phase_deg", "n_cycles"]]
    mo.vstack(
        [
            mo.md("### Full 30-Run Overview"),
            proof_fig,
            all_runs,
        ]
    )


if __name__ == "__main__":
    app.run()
