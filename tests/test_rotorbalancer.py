import pickle

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest

from rotorbalancer import calc, main, tools


def test_real_measurements_lockin_all_datasets():
    """Verify synchronous lock-in demodulation across all 30 recorded runs."""
    df_unbal = tools.loadfiles("without_weight")
    df_bal = tools.loadfiles("weight")
    df_bal5 = tools.loadfiles("weight_5")

    assert len(df_unbal) == 10
    assert len(df_bal) == 10
    assert len(df_bal5) == 10

    for df, f_lo, f_hi in (
        (df_unbal, 45.0, 65.0),
        (df_bal, 45.0, 65.0),
        (df_bal5, 28.0, 36.0),
    ):
        assert "file" in df.columns
        assert bool(df["frot"].between(f_lo, f_hi).all())
        assert bool((df["amplitude"] > 0.0).all())
        assert bool(df["phase_deg"].between(0.0, 360.0).all())
        assert bool((df["n_cycles"] >= 20).all())

    unbal_mean = float(np.mean(df_unbal["amplitude"]))
    assert float(np.mean(df_bal["amplitude"])) < 0.3 * unbal_mean
    assert float(np.mean(df_bal5["amplitude"])) < 0.1 * unbal_mean

    with pytest.raises(ValueError, match="trigger edges"):
        calc.lockin_demodulate(
            {"ir_meas": [0, 0, 1, 0], "ac_meas": [0, 1, 0, -1], "sample_freq": 952}
        )


def test_lockin_and_single_plane_balance_synthetic():
    """Verify lockin_demodulate + single_plane_balance recover exact unbalance weight & angle."""
    fs = 2000.0
    frot = 50.0
    t = np.arange(1000, dtype=float) / fs
    ir = np.where(((t + 1e-6) * frot) % 1.0 < 0.15, 0.0, 1.0)

    influence = 400.0 * np.exp(1j * np.radians(63.0))
    w_unbalance = 0.080 * np.exp(1j * np.radians(125.0))
    w_trial = 0.050 * np.exp(1j * np.radians(30.0))

    v0_true = influence * w_unbalance
    vt_true = influence * (w_unbalance + w_trial)

    ac0 = np.real(v0_true * np.exp(1j * 2.0 * np.pi * frot * t))
    act = np.real(vt_true * np.exp(1j * 2.0 * np.pi * frot * t))

    m0 = calc.lockin_demodulate({"ir_meas": ir, "ac_meas": ac0, "sample_freq": fs})
    mt = calc.lockin_demodulate({"ir_meas": ir, "ac_meas": act, "sample_freq": fs})
    bal = calc.single_plane_balance(m0, mt, trial_mass=0.050, trial_angle_deg=30.0)

    # Ideal correction cancels heavy spot at 125 deg -> 0.080 g at 305 deg
    assert bal["correction_mass"] == pytest.approx(0.080, abs=2e-3)
    angle_err = (bal["correction_angle_deg"] - 305.0 + 180.0) % 360.0 - 180.0
    assert abs(angle_err) < 2.0

    # Additional mass added on top of trial weight: 0.080 @ 305 - 0.050 @ 30
    w_add_expected = 0.080 * np.exp(1j * np.radians(305.0)) - w_trial
    assert bal["additional_mass"] == pytest.approx(abs(w_add_expected), abs=2e-3)

    with pytest.raises(ValueError, match="positive"):
        calc.single_plane_balance(m0, mt, trial_mass=0.0)
    with pytest.raises(ValueError, match="zero"):
        calc.single_plane_balance(m0, m0, trial_mass=0.050)


def test_single_plane_balance_real_measurements_cross_speed():
    """Prove 2021 single-plane data gives consistent correction mass & angle across speeds."""
    df_no = tools.loadfiles("without_weight")
    df_tr = tools.loadfiles("weight")

    low_v0 = complex(np.mean(df_no.loc[df_no["frot"].between(48.5, 49.5), "vector"]))
    low_vt = complex(np.mean(df_tr.loc[df_tr["frot"].between(48.5, 49.5), "vector"]))
    high_v0 = complex(np.mean(df_no.loc[df_no["frot"].between(51.5, 53.0), "vector"]))
    high_vt = complex(np.mean(df_tr.loc[df_tr["frot"].between(51.5, 53.0), "vector"]))

    bal_49 = calc.single_plane_balance(low_v0, low_vt, trial_mass=0.060)
    bal_52 = calc.single_plane_balance(high_v0, high_vt, trial_mass=0.060)

    assert 0.068 <= bal_49["correction_mass"] <= 0.073
    assert 0.068 <= bal_52["correction_mass"] <= 0.073
    assert bal_49["correction_mass"] == pytest.approx(
        bal_52["correction_mass"], abs=0.002
    )
    assert bal_49["relative_angle_deg"] == pytest.approx(
        bal_52["relative_angle_deg"], abs=1.5
    )
    assert abs(bal_49["relative_angle_deg"]) < 10.0
    assert bal_49["reduction_ratio"] > 5.0
    assert bal_52["reduction_ratio"] > 5.0


def test_headless_plotting(tmp_path):
    """Verify all plotting helpers render cleanly without GUI display backends."""
    df = tools.loadfiles("without_weight")
    fig_scatter = tools.plotfiles(df, show=False)

    proof_png = tmp_path / "proof.png"
    fig_proof = tools.plot_balancing_summary(save_path=proof_png, show=False)
    assert proof_png.is_file()

    time_png = tmp_path / "time_signals.png"
    fig_time_file = tools.plot_time_signals(save_path=time_png, show=False)
    assert time_png.is_file()

    # Short live-capture dict (< t_end default) must clamp cleanly
    fs = 400.0
    t = np.arange(40, dtype=float) / fs
    live_dict = {
        "ir_meas": np.where(((t + 1e-6) * 40.0) % 1.0 < 0.15, 0.0, 1.0),
        "ac_meas": 100.0 * np.sin(2.0 * np.pi * 40.0 * t),
        "sample_freq": fs,
    }
    dict_png = tmp_path / "live_dict.png"
    fig_time_dict = tools.plot_time_signals(live_dict, save_path=dict_png, show=False)
    assert dict_png.is_file()

    plt.close(fig_scatter)
    plt.close(fig_proof)
    plt.close(fig_time_file)
    plt.close(fig_time_dict)


def test_cli_parser_and_capture(monkeypatch, tmp_path):
    """Verify CLI parser, upload flag, lock-in summary output, and pickle saving."""
    out_file = tmp_path / "run.p"
    args = main.parser().parse_args(
        [
            "--plot",
            "--upload",
            "--frequency",
            "15",
            "--port",
            "/dev/ttyACM0",
            "--filename",
            str(out_file),
        ]
    )
    assert args.plot is True
    assert args.upload is True
    assert args.frequency == 15
    assert args.port == "/dev/ttyACM0"
    assert args.filename == str(out_file)

    samples = 40
    fs = 400.0
    t = np.arange(samples, dtype=float) / fs
    ir = [1 if np.sin(2.0 * np.pi * 40.0 * ti) > 0 else 0 for ti in t]
    ac = [round(100.0 * np.sin(2.0 * np.pi * 40.0 * ti)) for ti in t]

    lines = [
        "Press 5 to set pulse frequency.",
        "Set pulse frequency",
        "Accepted.",
        "Press 1 to start samples.",
        "Process time 0.0",
        "Pulse frequency 10",
        "Sample frequency 400",
        f"Samples collected {samples}",
    ]
    for i in range(samples):
        lines.append(str(ir[i]))
        lines.append(str(ac[i]))
    lines.append("Measurement completed")

    class FakeSerial:
        def __init__(self, stream):
            self._lines = iter(stream)
            self.writes = []

        def readlines(self):
            return []

        def readline(self):
            return (next(self._lines) + "\n").encode("utf-8")

        def write(self, data):
            self.writes.append(data)

    upload_calls = []
    fake_ser = FakeSerial(lines)
    monkeypatch.setattr(main, "upload_firmware", lambda **kw: upload_calls.append(kw))
    monkeypatch.setattr(main, "getserial", lambda port=None: fake_ser)
    monkeypatch.setattr(main, "sleep", lambda _s: None)

    results = main.cli(
        [
            "--upload",
            "--frequency",
            "10",
            "--port",
            "/dev/ttyACM0",
            "--filename",
            str(out_file),
        ]
    )
    assert upload_calls == [{"port": "/dev/ttyACM0"}]
    assert results["puls_freq"] == 10
    assert results["sample_freq"] == 400
    assert len(results["ac_meas"]) == samples
    assert len(results["ir_meas"]) == samples
    assert out_file.is_file()
    with open(out_file, "rb") as f:
        loaded = pickle.load(f)
    assert loaded == results
