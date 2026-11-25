# Author: Rik Starmans
# Description: upload Arduino Nano 33 BLE firmware and collect/plot vibration measurements
import argparse
import pickle
from subprocess import run
from time import sleep

import serial
import serial.tools.list_ports

from . import calc

# Placeholder for the PySerial connection to the Nano 33 BLE (set by getserial)
SER = None


def upload_firmware(filename="nano33ble/src/Nano33_ble.cpp", port=None):
    """Upload firmware to the Arduino Nano 33 BLE via Arduino CLI."""
    target_port = port if port is not None else getports()[0]
    cmd = ["arduino", "--upload", "--port", target_port, filename]
    arduino = run(cmd)
    if arduino.returncode:
        raise RuntimeError(f"Arduino upload exited with code {arduino.returncode}")
    sleep(3)  # wait for board to boot


def test_received(text):
    """Read lines from serial until ``text`` is observed and return that full line."""
    received, iteration = "", 0
    ser = getserial()
    while text not in received:
        received = ser.readline().decode().strip()
        iteration += 1
        if iteration > 15:
            print(f"Received {received}")
            raise TimeoutError(f'Did not receive text: "{text}"')
    return received


def getports(name="Nano"):
    """Return serial ports whose description matches ``name``."""
    arduino_ports = [
        p.device for p in serial.tools.list_ports.comports() if name in p.description
    ]
    if not arduino_ports:
        raise RuntimeError("Arduino Nano 33 BLE not detected (pass --port explicitly)")
    return arduino_ports


def getserial(port=None):
    """Return a cached PySerial connection to the Nano 33 BLE."""
    global SER
    if SER is None:
        target_port = port if port is not None else getports()[0]
        SER = serial.Serial(target_port, 115200, timeout=1)
    return SER


def set_frequency(frequency):
    """Set the hardware PWM pulse frequency of the Nano 33 BLE in Hz."""
    if frequency < 5:
        raise ValueError(
            "Frequency out of range (< 5 Hz); change clock divider in firmware"
        )
    ser = getserial()
    test_received("Press 5 to set pulse frequency.")
    ser.write(b"5")
    test_received("Set pulse frequency")
    ser.write(str(frequency).encode())
    test_received("Accepted.")


def main(frequency=20, plot=False, upload=False, port=None):
    """Collect accelerometer and IR tachometer samples from the Nano 33 BLE."""
    if upload:
        upload_firmware(port=port)
    ser = getserial(port=port)
    ser.readlines()
    print(f"Setting frequency to {frequency} Hz")
    set_frequency(frequency)
    test_received("Press 1 to start samples.")
    ser.write(b"1")
    received = test_received("Process time")
    measurement_time = float(received.split(" ")[2])
    print(f"Waiting {measurement_time} seconds for operation to complete")
    slept = 0.0
    sleep_step = 5.0
    while slept < measurement_time:
        step = min(sleep_step, measurement_time - slept)
        sleep(step)
        slept += step
        print(f" Completed {slept / measurement_time * 100:.2f} %")
    received = test_received("Pulse frequency")
    rotor_frequency = int(received.split(" ")[2])
    print(f"Pulse frequency {rotor_frequency} Hz")
    received = test_received("Sample frequency")
    sample_frequency = int(received.split(" ")[2])
    print(f"Sample frequency {sample_frequency} Hz")
    received = test_received("Samples collected")
    samples = int(received.split(" ")[2])
    print(f"Samples collected {samples}")
    ac_meas, ir_meas = [], []
    for sample in range(samples * 2):  # interleaved IR and accelerometer samples
        res = int(ser.readline().decode().strip())
        ac_meas.append(res) if sample % 2 else ir_meas.append(res)
    results = {
        "ac_meas": ac_meas,
        "ir_meas": ir_meas,
        "puls_freq": rotor_frequency,
        "sample_freq": sample_frequency,
    }
    test_received("Measurement completed")
    sleep(1)
    summary = calc.lockin_demodulate(results)
    print(
        f"Rotor: {summary['frot']:.2f} Hz | "
        f"1xRPM wobble: {summary['amplitude']:.1f} a.u. @ {summary['phase_deg']:.1f} deg"
    )
    if plot:
        from . import tools

        tools.plot_time_signals(results)
    return results


def parser():
    """Build the command-line argument parser."""
    arg_parser = argparse.ArgumentParser(add_help=True)
    arg_parser.add_argument(
        "--plot",
        action="store_true",
        default=False,
        help="Plot results",
    )
    arg_parser.add_argument(
        "--upload",
        action="store_true",
        default=False,
        help="Upload firmware",
    )
    arg_parser.add_argument(
        "--frequency",
        action="store",
        default=20,
        type=int,
        help="Set pulse frequency in Hz",
    )
    arg_parser.add_argument(
        "--port",
        action="store",
        default=None,
        type=str,
        help="Optional serial port path (e.g. /dev/ttyACM0 or COM5)",
    )
    arg_parser.add_argument(
        "--filename",
        action="store",
        default=None,
        type=str,
        help="Filename to store pickled measurement results",
    )
    return arg_parser


def cli(argv=None):
    """CLI entry point for collecting measurements."""
    args = parser().parse_args(argv)
    results = main(
        frequency=args.frequency,
        plot=args.plot,
        upload=args.upload,
        port=args.port,
    )
    if args.filename:
        with open(args.filename, "wb") as f:
            pickle.dump(results, f)
    return results


if __name__ == "__main__":
    cli()
