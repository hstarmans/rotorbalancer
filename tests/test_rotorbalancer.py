import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest

from rotorbalancer import calc, main, tools


def test_real_measurements_rotfreq_and_balancing():
    """Verify FFT frequency and balancing amplitude drop across all 30 recorded runs."""
    df_unbal = tools.loadfiles("without_weight", method="fft")
    df_bal = tools.loadfiles("weight", method="fft")
    df_bal5 = tools.loadfiles("weight_5", method="fft")

    assert len(df_unbal) == 10
    assert len(df_bal) == 10
    assert len(df_bal5) == 10

    assert df_unbal["freq_ir"].between(45.0, 65.0).all()
    assert df_bal["freq_ir"].between(45.0, 65.0).all()
    assert df_bal5["freq_ir"].between(28.0, 36.0).all()

    assert df_bal["A_ac"].mean() < 0.4 * df_unbal["A_ac"].mean()
    assert df_bal5["A_ac"].mean() < 0.2 * df_unbal["A_ac"].mean()


def test_real_measurements_getdetails_sine_and_arithmic():
    """Verify revolution segmentation works cleanly in both curve-fit and arithmic modes."""
    for folder, f_lo, f_hi in (
        ("without_weight", 45.0, 65.0),
        ("weight", 45.0, 65.0),
        ("weight_5", 28.0, 36.0),
    ):
        df = tools.loadfiles(folder, method="details")
        assert len(df) == 10
        assert df["frot"].between(f_lo, f_hi).all()
        assert (df["force"] > 0.0).all()
        assert df["deg"].between(0.0, 360.0).all()

    dct = calc.read_file("without_weight/100.p")
    arith = calc.getdetails(dct, verbose=False, arithmic=True)
    assert 45.0 <= arith["frot"] <= 65.0
    assert arith["force"] > 0.0
    assert 0.0 <= arith["deg"] <= 360.0

    with pytest.raises(ValueError, match="rising edges"):
        calc.getdetails(
            {"ir_meas": [0, 0, 1, 0], "ac_meas": [0, 1, 0, -1], "sample_freq": 952},
            verbose=False,
        )


@pytest.mark.parametrize(
    ("n_samples", "expected_df"),
    [
        (1000, 1.0),
        (2000, 0.5),
        (500, 2.0),
    ],
)
def test_issue4_multiresolution_fft_frequency(n_samples, expected_df):
    """Regression test for Issue #4: rotfreq_and_force must scale peak index by df."""
    fs = 1000.0
    t = np.arange(n_samples, dtype=float) / fs
    ir_meas = (np.sin(2.0 * np.pi * 50.0 * t) > 0.0).astype(float)
    ac_meas = 10.0 * np.sin(2.0 * np.pi * 50.0 * t + 0.5)
    sample = {
        "ir_meas": ir_meas,
        "ac_meas": ac_meas,
        "puls_freq": 10,
        "sample_freq": fs,
    }

    xf, _, _ = calc.fourier_transform(sample)
    assert xf[1] - xf[0] == pytest.approx(expected_df)

    res = calc.rotfreq_and_force(sample)
    assert res["freq_ir"] == pytest.approx(50.0, abs=1e-6)
    assert res["freq_ac"] == pytest.approx(50.0, abs=1e-6)
    assert np.isfinite(res["phase"])


def test_fitsinusoid_and_crosscorrelate_phase_recovery():
    """Verify sinusoid fit and cross-correlation recover known synthetic phase offsets."""
    fs = 1000.0
    t = np.arange(400, dtype=float) / fs
    sig = 2.5 * np.sin(2.0 * np.pi * 50.0 * t + 1.2)
    amp, phase = calc.fitsinusoid(sig, fest=50.0, fs=fs)
    assert amp == pytest.approx(2.5, abs=0.05)
    assert phase == pytest.approx(1.2, abs=0.05)

    # Cross-correlation quantizes to 1/fs steps (18 deg/sample at 50 Hz, fs=1000 Hz)
    dummy = {"ac_meas": sig, "ir_meas": sig, "sample_freq": fs}
    phase_deg = calc.crosscorrelate(dummy, low=20.0, high=80.0, rotor=50.0, debug=0.25)
    assert abs(phase_deg) == pytest.approx(45.0, abs=10.0)
    exact_step_deg = calc.crosscorrelate(
        dummy, low=20.0, high=80.0, rotor=50.0, debug=0.3
    )
    assert abs(exact_step_deg) == pytest.approx(54.0, abs=2.0)


def test_headless_plotting(tmp_path):
    """Verify plotdata and plotfiles render cleanly without GUI display backends."""
    dct = calc.read_file("without_weight/100.p")
    out_png = tmp_path / "spectrum.png"
    fig1 = calc.plotdata(dct, saveplot=out_png, show=False)
    assert out_png.is_file()
    plt.close(fig1)

    fig2 = tools.plotfiles(tools.loadfiles("without_weight", method="fft"), show=False)
    fig3 = tools.plotfiles(tools.loadfiles("without_weight", method="details"), show=False)
    plt.close(fig2)
    plt.close(fig3)


def test_cli_parser_and_upload_invocation(monkeypatch):
    """Verify CLI parser flags and that upload=True invokes upload_firmware cleanly."""
    args = main.parser().parse_args(
        [
            "--plot",
            "--upload",
            "--frequency",
            "15",
            "--port",
            "/dev/ttyACM0",
            "--filename",
            "run.p",
        ]
    )
    assert args.plot is True
    assert args.upload is True
    assert args.frequency == 15
    assert args.port == "/dev/ttyACM0"
    assert args.filename == "run.p"

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
        def __init__(self):
            self._lines = iter(lines)
            self.writes = []

        def readlines(self):
            return []

        def readline(self):
            return (next(self._lines) + "\n").encode("utf-8")

        def write(self, data):
            self.writes.append(data)

    upload_calls = []
    fake_ser = FakeSerial()
    monkeypatch.setattr(main, "upload_firmware", lambda **kw: upload_calls.append(kw))
    monkeypatch.setattr(main, "getserial", lambda port=None: fake_ser)
    monkeypatch.setattr(main, "sleep", lambda _s: None)

    results = main.main(frequency=10, plot=False, upload=True, port="/dev/ttyACM0")
    assert upload_calls == [{"port": "/dev/ttyACM0"}]
    assert results["puls_freq"] == 10
    assert results["sample_freq"] == 400
    assert len(results["ac_meas"]) == samples
    assert len(results["ir_meas"]) == samples
