import pickle
from pathlib import Path

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


def loadfiles(folder=None, method="fft", **kwargs):
    """Load pickled measurements from ``folder`` into a :class:`pandas.DataFrame`.

    Parameters
    ----------
    folder : str | Path | None
        Subfolder inside ``measurements/`` (or direct path). Defaults to ``measurements/``.
    method : {'fft', 'details'}
        Analysis function applied to each file (``calc.rotfreq_and_force`` or ``calc.getdetails``).
    **kwargs
        Extra keyword arguments forwarded when ``method='details'``.
    """
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
        if method == "fft":
            res = calc.rotfreq_and_force(dct)
        elif method == "details":
            res = calc.getdetails(dct, verbose=False, **kwargs)
        else:
            raise ValueError(f"Unsupported method {method!r}; choose 'fft' or 'details'")
        rows.append(res)
    return pd.DataFrame(rows)


def plotfiles(df, show=True):
    """Plot force/amplitude and phase versus rotor frequency from :func:`loadfiles`."""
    import matplotlib.pyplot as plt

    if "frot" in df.columns:
        freq_col, force_col, phase_col = "frot", "force", "deg"
    else:
        freq_col, force_col, phase_col = "freq_ir", "A_ac", "phase"

    fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(12, 8))
    if fig.canvas.manager is not None:
        fig.canvas.manager.set_window_title("Degree and force plotted vs rotor frequency")

    axes[0].scatter(df[freq_col], df[force_col])
    axes[0].set_title("Force vs rotor frequency")
    axes[0].set(xlabel="Mean rotor frequency (Hz)", ylabel="Force (a.u.)")
    axes[0].grid()

    axes[1].scatter(df[freq_col], df[phase_col])
    axes[1].set_title("Phase vs rotor frequency")
    axes[1].set(xlabel="Mean rotor frequency (Hz)", ylabel="Phase (Degrees)")
    axes[1].grid()

    fig.tight_layout()
    if show:
        plt.show()
    return fig
