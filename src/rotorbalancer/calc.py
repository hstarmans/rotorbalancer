import pickle
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy.fft import rfft, rfftfreq
from scipy.optimize import curve_fit
from scipy.signal import butter, correlate, find_peaks, lfilter

root_folder = Path(__file__).resolve().parents[2] / "measurements"


def butter_bandpass(lowcut, highcut, fs, order=5):
    """Build a Butterworth bandpass filter numerator/denominator pair.

    Based on https://stackoverflow.com/questions/12093594/how-to-implement-band-pass-butterworth-filter-with-scipy-signal-butter
    """
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype="band")
    return b, a


def butter_bandpass_filter(data, lowcut, highcut, fs, order=5):
    """Apply a Butterworth bandpass filter to ``data``."""
    b, a = butter_bandpass(lowcut, highcut, fs, order=order)
    return lfilter(b, a, data)


def read_file(fname):
    """Load a pickled measurement dict and mean-center ``ac_meas`` and ``ir_meas``."""
    candidate = Path(fname)
    if not candidate.is_file():
        candidate = root_folder / fname
    with open(candidate, "rb") as f:
        dct = pickle.load(f)

    result = dict(dct)
    ac = np.asarray(dct["ac_meas"], dtype=float)
    ir = np.asarray(dct["ir_meas"], dtype=float)
    result["ac_meas"] = ac - np.mean(ac)
    result["ir_meas"] = ir - np.mean(ir)
    return result


def fourier_transform(data):
    """Return frequency bins [Hz] and single-sided FFT amplitudes for IR and AC."""
    sample_freq = float(data["sample_freq"])
    ir = np.asarray(data["ir_meas"], dtype=float)
    ac = np.asarray(data["ac_meas"], dtype=float)
    ir = ir - np.mean(ir)
    ac = ac - np.mean(ac)

    n = len(ir)
    xf = rfftfreq(n, d=1.0 / sample_freq)
    a_ir = (2.0 / n) * np.abs(rfft(ir))
    a_ac = (2.0 / n) * np.abs(rfft(ac))
    return xf, a_ir, a_ac


def rotfreq_and_force(data, verbose=False):
    """Estimate fundamental rotation frequency [Hz], FFT amplitudes, and phase [deg]."""
    xf, a_ir, a_ac = fourier_transform(data)
    fs = float(data["sample_freq"])
    max_search_freq = float(data["puls_freq"]) * 10.0
    band_mask = (xf > 0.0) & (xf <= max_search_freq)
    if not np.any(band_mask):
        band_mask = xf > 0.0

    def get_first_peak(spectrum):
        band_max = float(np.max(spectrum[band_mask])) if np.any(band_mask) else 0.0
        if band_max <= 0.0:
            return -1.0, -1.0
        peaks, _ = find_peaks(spectrum, height=band_max / 2.0)
        peaks = [int(p) for p in peaks if xf[p] > 0.0]
        if not peaks:
            return -1.0, -1.0
        if verbose:
            print(peaks)
        idx = peaks[0]
        return float(xf[idx]), float(spectrum[idx])

    results = {}
    results["freq_ir"], results["A_ir"] = get_first_peak(a_ir)
    results["freq_ac"], results["A_ac"] = get_first_peak(a_ac)

    freq_ir = results["freq_ir"]
    if freq_ir <= 0.0:
        results["phase"] = float("nan")
    else:
        low = 20.0 if freq_ir > 20.0 else min(10.0, 0.5 * freq_ir)
        high = 80.0 if freq_ir < 80.0 else min(0.45 * fs, max(80.0, 1.5 * freq_ir))
        if low <= 0.0 or low >= freq_ir or high <= freq_ir or high >= 0.5 * fs:
            results["phase"] = float("nan")
        else:
            results["phase"] = crosscorrelate(data, low, high, freq_ir, debug=False)
    return results


def plotdata(results, saveplot=False, show=True):
    """Plot time series and amplitude spectra for accelerometer and IR signals."""
    sample_freq = float(results["sample_freq"])
    ac_meas = np.asarray(results["ac_meas"], dtype=float)
    ir_meas = np.asarray(results["ir_meas"], dtype=float)
    xf, a_ir, a_ac = fourier_transform(results)
    time_axis = np.arange(len(ac_meas), dtype=float) / sample_freq

    fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(12, 8))
    if fig.canvas.manager is not None:
        fig.canvas.manager.set_window_title("Frequency and time plots")

    axes[0, 0].plot(time_axis, ac_meas)
    axes[0, 0].grid()
    axes[0, 0].set_xlabel("Time (s)")
    axes[0, 0].set_title("Acceleration vs time")

    axes[0, 1].plot(xf, a_ac)
    axes[0, 1].grid()
    axes[0, 1].set_xlabel("Frequency (Hz)")
    axes[0, 1].set_title("Acceleration spectrum")

    axes[1, 0].plot(time_axis[: len(ir_meas)], ir_meas)
    axes[1, 0].grid()
    axes[1, 0].set_xlabel("Time (s)")
    axes[1, 0].set_title("Infrared voltage vs time")

    axes[1, 1].plot(xf, a_ir)
    axes[1, 1].grid()
    axes[1, 1].set_xlabel("Frequency (Hz)")
    axes[1, 1].set_title("Infrared spectrum")

    fig.tight_layout()
    if saveplot:
        out_path = "results.png" if saveplot is True else str(saveplot)
        fig.savefig(out_path)
    if show:
        plt.show()
    return fig


def fitsinusoid(signal, fest, fs, debug=False):
    """Fit ``A * sin(2 * pi * fest * t + phase)`` and return ``(A, phase_rad)``."""
    sig = np.asarray(signal, dtype=float)
    n = len(sig)
    dt = 1.0 / float(fs)
    x = np.linspace(0.0, n * dt, n, endpoint=False)

    if debug:
        print("debug activated")
        phasediff = np.pi * debug
        sig = np.sin(fest * 2.0 * np.pi * x + phasediff)

    peak = float(np.max(np.abs(sig))) if n > 0 else 0.0
    if peak == 0.0:
        return 0.0, 0.0

    def sinusoid(t_arr, amplitude, phasediff):
        return amplitude * np.sin(fest * 2.0 * np.pi * t_arr + phasediff)

    popt, _ = curve_fit(
        sinusoid,
        x,
        sig,
        bounds=([0.8 * peak, 0.0], [1.2 * peak, 2.0 * np.pi]),
    )
    amplitude, phase = float(popt[0]), float(popt[1])
    return amplitude, phase


def getdetails(measurement, flt=True, verbose=True, arithmic=False):
    """Estimate rotor frequency [Hz], unbalance force [a.u.], and phase [deg].

    Detects rising edges in ``ir_meas`` to segment individual revolutions, optionally
    bandpass-filters ``ac_meas``, and extracts amplitude and phase via either extrema
    (``arithmic=True``) or sinusoid fitting (``arithmic=False``).
    """
    sample_freq = float(measurement["sample_freq"])
    ir = np.asarray(measurement["ir_meas"], dtype=float)
    start_ind = np.flatnonzero((ir[1:] - ir[:-1]) > 0.5) + 1
    if len(start_ind) < 2:
        raise ValueError("Need at least two IR rising edges to estimate rotor period")

    cycle_time = np.diff(start_ind)
    samples_per_period = float(np.mean(cycle_time))
    min_cycle = float(np.min(cycle_time))
    max_cycle = float(np.max(cycle_time))

    if abs(max_cycle - min_cycle) > 2.0 and verbose:
        print(f"Min freq {sample_freq / max_cycle:.2f} ")
        print(f"Max freq {sample_freq / min_cycle:.2f} ")
        print("WARNING: Rotor frequency seems not constant")

    results: dict[str, float] = {"frot": sample_freq / samples_per_period}

    raw_ac = np.asarray(measurement["ac_meas"], dtype=float)
    if flt:
        low = 0.9 * sample_freq / max_cycle
        high = min(1.1 * sample_freq / min_cycle, 0.49 * sample_freq)
        ac_meas = butter_bandpass_filter(raw_ac, low, high, sample_freq, order=6)
    else:
        ac_meas = raw_ac

    pos_max, pos_min, forces = [], [], []
    amplitudes, phases = [], []
    for i in range(len(start_ind) - 1):
        seg = ac_meas[start_ind[i] : start_ind[i + 1]]
        if len(seg) == 0:
            continue
        if arithmic:
            pos_max.append((int(np.argmax(seg)) / len(seg)) * 360.0)
            pos_min.append((int(np.argmin(seg)) / len(seg)) * 360.0)
            forces.append(float(np.max(seg) - np.min(seg)) / 2.0)
        else:
            frotest = sample_freq / len(seg)
            amplitude, phase = fitsinusoid(seg, frotest, sample_freq)
            amplitudes.append(amplitude)
            phases.append(phase)

    if arithmic:
        results["force"] = float(np.mean(forces))
        max_deg = float(np.mean(pos_max))
        min_deg = float(np.mean(pos_min))
        if abs(abs(max_deg - min_deg) - 180.0) > 5.0 and verbose:
            print(f"Max degree {max_deg:.2f}")
            print(f"Min degree {min_deg:.2f}")
            print("WARNING: Degree measurement seems inaccurate")
        results["deg"] = min_deg
    else:
        results["force"] = float(np.mean(amplitudes))
        results["deg"] = float(np.mean(phases) / (2.0 * np.pi) * 360.0)

    if verbose:
        print(f"Rotor frequency is {results['frot']:.0f} Hz")
        print(f"Force is {results['force']:.2f} a.u.")
        print(f"Phase is {results['deg']:.2f} degrees")
    return results


def crosscorrelate(results, low, high, rotor, debug=False):
    """Return phase difference [deg] between accelerometer and IR signals via cross-correlation."""
    sample_freq = float(results["sample_freq"])
    ac_meas = np.asarray(results["ac_meas"], dtype=float)
    ir_meas = np.asarray(results["ir_meas"], dtype=float)
    freq = float(rotor)
    n = len(ac_meas)
    dt_step = 1.0 / sample_freq

    if debug:
        print("debug activated")
        phasediff = np.pi * debug
        x = np.linspace(0.0, n * dt_step, n, endpoint=False)
        ir_meas = np.sin(freq * 2.0 * np.pi * x + phasediff)
        ac_meas = np.sin(freq * 2.0 * np.pi * x)

    ac_filt = butter_bandpass_filter(ac_meas, low, high, sample_freq, order=6)
    ir_filt = butter_bandpass_filter(ir_meas, low, high, sample_freq, order=6)

    ac_filt = ac_filt - np.mean(ac_filt)
    ir_filt = ir_filt - np.mean(ir_filt)
    ac_std = float(np.std(ac_filt))
    ir_std = float(np.std(ir_filt))
    if ac_std == 0.0 or ir_std == 0.0:
        return float("nan")
    ac_filt = ac_filt / ac_std
    ir_filt = ir_filt / ir_std

    xcorr = correlate(ir_filt, ac_filt)
    t = np.linspace(0.0, n * dt_step, n, endpoint=False)
    dt = np.linspace(-t[-1], t[-1], 2 * n - 1)
    recovered_time_shift = float(dt[int(xcorr.argmax())])
    recovered_phase_shift = (
        2.0 * np.pi * (((0.5 + recovered_time_shift / (1.0 / freq)) % 1.0) - 0.5)
    )
    if debug:
        print(f"Recovered time shift {recovered_time_shift}")
        print(f"Recovered phase shift {recovered_phase_shift} radian")
        print(f"Recovered phase shift {np.degrees(recovered_phase_shift)} degrees")
    return float(np.degrees(recovered_phase_shift))
