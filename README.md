# Rotor Balancer

> **Project Status:** Hardware work is paused, while **single-plane balancing is proven and ready to use** on the Nano 33 BLE + Python workflow. The hardware build and all 30 recorded datasets come from 2021; years later, the Python package, synchronous lock-in demodulation, Influence Coefficient single-plane solver, and automated test suite were completed with AI assistance and verified against the original recordings.

Single-plane rotor balancer and tachometer using an Arduino Nano 33 BLE. Built to balance quadcopter propellers or polygon laser scanner mirror motors.

The Nano 33 BLE pulses the motor via hardware PWM and records acceleration via its onboard LSM9DS1 accelerometer chip while reading a [TCRT5000 IR LED](https://opencircuit.nl/Product/TCRT5000-Infrarood-lijn-detectie-module) optical trigger to track rotor phase.
The amplitude of the accelerometer signal is proportional to the unbalanced mass, and the phase difference between the infrared trigger and the accelerometer indicates where balance putty should be applied.
In the case of two-plane unbalance, the phase difference between the IR LED and the accelerometer can depend on rotor speed.
So far, only the single-plane two-run method is implemented.

<img src="images/setup.jpg" align="center" width="30%"/>

## Installation & Usage

### 1. Firmware (`nano33ble/`)
Compile and upload the firmware in `nano33ble/` using PlatformIO (VS Code plugin) or Arduino CLI to your Arduino Nano 33 BLE, then connect over serial at `115200` baud. Five menu options are available: start sampling, calibrate the IR sensor, spin the polygon, check pulse frequency, and set pulse frequency.

Place a small piece of aluminum tape on the rotor, verify the IR sensor detects it, and adjust the threshold screw on the TCRT5000 module so it triggers cleanly once per revolution. Menu loops typically exit by sending `1`.

### 2. Python Host Tools (`src/rotorbalancer/`)
Install and run with [uv](https://docs.astral.sh/uv/) (Python >= 3.12):

```console
uv sync
uv run rotorbalancer --plot --frequency 20 --filename 20hertz.p
```

Batch sweeps and offline analysis can also be run from Python (see example datasets in `measurements/` and [notebooks/trials.py](notebooks/trials.py)):

```python
from rotorbalancer import tools

# Analyze recorded runs (returns rotor frequency, 1xRPM amplitude, phase, and complex vector)
df = tools.loadfiles("without_weight")
print(df[["frot", "amplitude", "phase_deg"]].describe())

# Or capture a sweep on hardware
# tools.runtest(10, 11, 1, "test")
```

Explore the 2021 measurements and single-plane calculator interactively in [marimo](https://marimo.io/):

```console
uv run --group notebook marimo edit notebooks/trials.py
```

Run tests and linter offline on the included `measurements/` dataset:

```console
uv run pytest -v
uv run ruff check src tests notebooks
```

## Repository Map

| Path | Purpose |
| :--- | :--- |
| [src/rotorbalancer/](src/rotorbalancer/) | Synchronous lock-in & single-plane Influence Coefficient solver (`calc.py`), CLI sampler (`main.py`), batch sweep & plotting tools (`tools.py`) |
| [nano33ble/](nano33ble/) | PlatformIO / Arduino Nano 33 BLE firmware & modified LSM9DS1 library |
| [measurements/](measurements/) | Recorded vibration & IR datasets (`without_weight/`, `weight/`, `weight_5/`) |
| [notebooks/trials.py](notebooks/trials.py) | Interactive marimo notebook exploring the 30 recorded runs and single-plane solver |
| [caddesigns/](caddesigns/) | Nano 33 BLE holder STLs & stabilizer FreeCAD CAD design |
| [tests/](tests/) | Automated `pytest` verification against the recorded datasets and single-plane solver |

## Video
I made a video of the setup for a better impression:

[<img src="https://img.youtube.com/vi/xFNtZbOfEfQ/maxresdefault.jpg" width="30%">](https://youtu.be/xFNtZbOfEfQ)


## Proven Single-Plane Balancing & Measurements

### What we measure
For each run, the rotor is pulsed for 20 seconds to spin up and sampled for 1 second at 952 Hz (the maximum rate of the onboard LSM9DS1 accelerometer). The Arduino records two time signals side by side: **acceleration over time** (how hard the motor assembly shakes) and the **TCRT5000 infrared trigger over time** (active-LOW: the digital output idles `HIGH` and drops `LOW` on each pass of the aluminum tape mark, latched in firmware between accelerometer reads so brief pulses are never missed). Projecting the accelerometer signal onto each revolution between consecutive falling trigger edges directly extracts the clean 1×RPM wobble amplitude and phase angle.

<img src="images/time_signals.png" align="center" width="90%"/><br>

### How single-plane balancing works
For a flat rotor like a 30×30×2 mm prism or a propeller, single-plane balancing removes nearly all unbalance vibration without needing a mechanical model of the mounting stiffness or sensor filter delay:

1. **Spin #1 — Measure the wobble vector $V_0$:** Run the rotor with no added weight. Think of the 1×RPM vibration as a clock-face arrow: its length $|V_0|$ is how hard the rotor shakes, and its angle $\angle V_0$ is when the shake peaks relative to the IR tape mark.
2. **Spin #2 — Add one known trial weight $W_t$ and measure $V_t$:** Stick a small known weight (e.g. `60 mg` putty or measured aluminum tape) at a reference mark on the rim, spin at **roughly the same RPM**, and record the new vector $V_t$.
3. **See how your setup reacts ($V_t - V_0$):** The difference vector automatically captures *both* your rig's mechanical sensitivity and total phase lag.
4. **Cancel $V_0$ completely ($W_{\text{corr}}$):** Solve for the exact correction mass and angle that drive residual 1×RPM vibration to zero (or `additional_mass` if keeping the trial weight attached).

#### Why two runs are enough (complex-number proof)
At a fixed spin speed $\omega$, let $U \in \mathbb{C}$ be the unknown rotor unbalance and let $\alpha \in \mathbb{C}$ represent every unknown linear rig property combined (mounting stiffness, damping, accelerometer gain, mounting angle, sensor/firmware lag, and IR trigger offset):

$$V_0 = \alpha \, U \qquad \text{(Run 1: baseline)}$$

$$V_t = \alpha \, (U + W_t) = V_0 + \alpha \, W_t \qquad \text{(Run 2: with known trial weight } W_t\text{)}$$

Subtracting Run 1 from Run 2 eliminates $U$ and solves directly for the complex influence coefficient $\alpha$:

$$\alpha = \frac{V_t - V_0}{W_t}$$

Setting the post-correction vibration $V_0 + \alpha \, W_{\text{corr}} = 0$ cancels $\alpha$ out of the ratio:

$$W_{\text{corr}} = -\frac{V_0}{\alpha} = -W_t \, \frac{V_0}{V_t - V_0} \qquad\text{and}\qquad W_{\text{add}} = W_{\text{corr}} - W_t$$

Only three practical assumptions apply: both runs share roughly the same speed so $\alpha(\omega)$ stays constant, the rig behaves linearly, and the rotor is thin enough to treat as a single plane.

### Proven results on the 2021 prism dataset
*(Note: The hardware build and all 30 `.p` recordings are from 2021; years later, synchronous lock-in demodulation (`calc.lockin_demodulate`) and the Influence Coefficient single-plane solver (`calc.single_plane_balance`) were added with AI assistance and verified directly against those original files.)*

<img src="images/balancing_proof.png" align="center" width="95%"/><br>

Adding **`0.060 g`** of [Weicon resin putty](https://www.weicon.de/en/products/adhesives-and-sealants/2-component-adhesives-and-sealants/epoxy-resin-systems/plastic-metal/298/epoxy-resin-putty) (weighed on a Mettler Toledo AG204 DeltaRange balance) reduced 1×RPM vibration by **~6.6×** in the 48.5–53 Hz band (as a low-cost alternative to putty, measured strips of aluminum tape work cleanly by area-to-mass ratio). Measure Run 1 and Run 2 at roughly the same speed below the rig's ~60 Hz resonance (seen in `without_weight/101.p` at `58.5 Hz`); away from resonance, two independent speed groups agree to within **`1.4 mg` and `1.2°`**:

| Speed band | $V_0$ (no weight) | $V_t$ (`0.060 g` trial putty) | Calculated optimal weight | Angle vs. trial spot |
| :--- | :--- | :--- | :--- | :--- |
| **`48.5–49.5 Hz`** (4 vs. 3 runs) | `148.1 @ 336.1°` | `20.6 @ 345.4°` | **`0.0695 g`** (`69.5 mg`) | **`+1.5°`** |
| **`51.5–53.0 Hz`** (4 vs. 3 runs) | `188.4 @ 335.3°` | `30.2 @ 349.6°` | **`0.0709 g`** (`70.9 mg`) | **`+2.7°`** |

```python
import numpy as np
from rotorbalancer import calc, tools

df_base = tools.loadfiles("without_weight")
df_trial = tools.loadfiles("weight")

v0 = complex(np.mean(df_base.loc[df_base["frot"].between(48.5, 49.5), "vector"]))
vt = complex(np.mean(df_trial.loc[df_trial["frot"].between(48.5, 49.5), "vector"]))

print(calc.single_plane_balance(v0, vt, trial_mass=0.060))
# Regenerate the figures above:
# tools.plot_time_signals(save_path="images/time_signals.png", show=False)
# tools.plot_balancing_summary(save_path="images/balancing_proof.png", show=False)
```

Further literature can be found on [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S2351988616300185) and [National Instruments](https://forums.ni.com/t5/Example-Programs/Two-Plane-Balancing-Example-with-DAQmx/ta-p/3996066?profile.language=en).


## Implementation Details
On Linux, `ModemManager` interfered with the Arduino serial connection and had to be removed (see [Arduino forum](https://forum.arduino.cc/index.php?topic=575194.0)):
```console
sudo apt --purge remove modemmanager
```
The accelerometer library from [SparkFun](https://github.com/sparkfun/SparkFun_LSM9DS1_Arduino_Library) is included in `nano33ble/lib/` in a slightly modified form.


## Related Open-Source Projects & Future Directions
Single-plane balancing (sufficient for flat prisms and propellers) is the primary goal of this repo, and both **synchronous lock-in demodulation** (`calc.lockin_demodulate`) and the **Influence Coefficient solver** (`calc.single_plane_balance`) are now implemented and tested against the 2021 recordings. Open-source end-to-end balancing projects remain relatively rare compared to commercial rigs, though two complementary references are worth noting:
* **[indeterminatedesign/DynamicBalancer](https://github.com/indeterminatedesign/DynamicBalancer):** Open-source ESP32 + MPU6050 + Hall-effect phase trigger + 3D-printed desktop spin balancer.
* **[MagedMohamedTurk/Turbomachinery-Rotors-Balancing](https://github.com/MagedMohamedTurk/Turbomachinery-Rotors-Balancing):** Python implementation of multi-plane Influence Coefficient balancing equations.

If the hardware side is revisited for a v2, the main practical upgrades would be:
* **Hardware-interrupt IR timestamps + fast SPI IMU:** Timestamp each IR edge with microsecond precision instead of polling at 952 Hz, and pair it with a faster SPI IMU (e.g. ICM-42688-P) for sub-milligram resolution and sub-degree phase accuracy.
* **Calibrated aluminum-tape workflow (semi-automatic):** Translate the calculated correction mass directly into cut length (mm) of calibrated aluminum tape instead of weighing putty or building a mechanical dispenser.
* **Optional 2-plane mode (for long spindles only):** Combine accelerometer (static force) and gyroscope (tilting couple moment) channels from a 6-DOF IMU into a `2 × 2` Influence Coefficient matrix if tall rotors ever need couple balancing.


## BOM
* **Prism:** 4 sides, 30×30×2 mm
* **Mirror motor:** Panasonic AN44000A (other motors require different pinouts). Has 5 pins: `PWM` (speed control, not linear for all motors), `MOTOR_EN`, `GND`, `Voltage` (ideally 24 V), and `LCK_PIN` (low when encoder and reference clock are out of sync). `LCK_PIN` and `MOTOR_EN` are kept fixed for repeatability.
* **Accelerometer:** LSM9DS1 onboard the Arduino Nano 33 BLE.
* **IR sensor:** TCRT5000 IR LED module (see [DIY LP turntable](https://www.stockholmviews.com/wp/diy-lp-turntable-tachometer/), bought at [OpenCircuit](https://opencircuit.nl/Product/TCRT5000-Infrarood-lijn-detectie-module)).
* **Balancing putty:** Two-component epoxy resin putty from [Weicon](https://www.weicon.de/en/products/adhesives-and-sealants/2-component-adhesives-and-sealants/epoxy-resin-systems/plastic-metal/298/epoxy-resin-putty) or single-component UV-curable putty from [Schenck](http://www.schenck-worldwide.com/PDF/de-de1/Epoxidharz-Unwucht-Korrektursystem.pdf) (German: *Wuchtkitt*, ceramic-filled, ~2 g/cm³, ordered via [Modulor](https://www.modulor.de); turns green after mixing and cures hard over several hours). Alternatively, use lead or metal tape (lead density ~11 g/cm³).
* **Mounting plate:** 3D-printed holder plate ([caddesigns/stabilizer.FCStd](caddesigns/stabilizer.FCStd)) mounted on a Thorlabs aluminum breadboard with M6 screws. As a general tip, avoid rigidly bolting the test unit to a heavy structure — compliant mounting (such as foam) increases vibration sensitivity.
