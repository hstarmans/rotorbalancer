# Author: Rik Starmans
# Date: 18-3-2020
# Description: program to upload arduino code and plot results
from subprocess import run
from time import sleep
import serial
import serial.tools.list_ports
import argparse
import pickle

from . import calc

# Placer holder for the Pyserial connection to the Nano33ble
# set by getserial
SER = None


def upload(filename='Nano33_ble/Nano33_ble.ino'):
    '''upload firmware to the board via the arduino commmand line interface

    Documentation details of arduino command line can be found at
    https://github.com/arduino/Arduino/blob/master/build/shared/manpage.adoc
    Program can also be configured by running the IDE.

    Keyword arguments:
    filename -- location of file to upload
    '''
    cmd = ['arduino', '--upload', '--port', getports()[0], filename]
    arduino = run(cmd)
    if arduino.returncode:
        raise Exception("Exit code not zero, operation failed")
    sleep(3)  # wait for board to boot


def test_received(text):
    '''check of text is received on serial port

    Keyword arguments:
    text -- text as string expected to be received on serial line

    Returns:
    The full line of text this keyword was in as string
    '''
    received, iteration = '', 0
    ser = getserial()
    while text not in received:
        received, iteration = ser.readline().decode().strip(), iteration+1
        if iteration > 15:
            print("Received {}".format(received))
            raise Exception('Did not receive text; "{}"'.format(text))
    return received


def getports(name='COM5'):  # Nano 33 BLE on raspberry
    '''get serial port for the NANO 33 BLE

    name -- specifier of device.. can differ for e.g. be COM5 or Nano 33 BLE

    Returns:
    List with ports which have a Nano 33 BLE attached
    '''
    arduino_ports = [p.device for p in serial.tools.list_ports.comports()
                     if name in p.description]
    if not len(arduino_ports):
        raise Exception("Arduino Nano 33 BLE not detected")
    return arduino_ports


def getserial():
    '''get serial object for the NANO 33 BLE

    The result is also set as global as a serial object.
    Closing and opening the port too many
    times can break connection with the board.
    This prevents it from being opened to many times.

    Returns
    pyserial object
    '''
    global SER
    if not SER:
        SER = serial.Serial(getports()[0], 115200, timeout=1)
    return SER


def set_frequency(frequency):
    '''set the hardware pwm frequency of the Nano 33BLE

    The frequency of the oscillator is use to move the motor.

    Keyword arguments:
    frequency -- frequency of the oscillitor in Hz
    '''
    if frequency < 10:
        raise Exception("Out of range, change clock divider in firmware")
    ser = getserial()
    test_received('Press 5 to set pulse frequency.')
    ser.write('5'.encode())
    test_received('Set pulse frequency')
    ser.write(str(frequency).encode())
    test_received('Accepted.')


def main(frequency=20, plot=False, upload=False):
    """collects samples from the client

    Keyword arguments:
    upload -- if true firmware is recompiled and uploaded to the board
    plot -- if true acceleromater an infrared signal are plotted vs time
            the amplitude of their Fourier transform is also shown
    frequency -- frequency used of the oscillator in Hertz

    Returns:
    Python dictionary with keys;
        ac_meas -- accelerometer measurements as list
        ir_meas -- infrared measurements as list
        purse_freq -- the frequency at which the rotor was driven
        sample frequency -- sample frequency of the signal typically 952 Hz
    """
    ser = getserial()
    # read all lines to clear buffer
    ser.readlines()
    print("Setting frequency to {} Hz".format(frequency))
    set_frequency(frequency)
    if upload:
        upload()
    test_received('Press 1 to start samples.')
    ser.write('1'.encode())
    received = test_received('Process time')
    measurement_time = float(received.split(' ')[2])
    print("Waiting {} seconds for operation" +
          " to complete".format(measurement_time))
    slept = 0
    sleep_step = 5  # seconds
    while slept < measurement_time:
        slept += sleep_step
        if slept > measurement_time:
            sleep(measurement_time-slept+sleep_step)
            slept = measurement_time
        else:
            sleep(sleep_step)
        print(" Completed {:.2f} %".format(slept/measurement_time*100))
    received = test_received('Pulse frequency')
    rotor_frequency = int(received.split(' ')[2])
    print("Pulse frequency {} Hz".format(rotor_frequency))
    received = test_received('Sample frequency')
    sample_frequency = int(received.split(' ')[2])
    print("Sample frequency {} Hz".format(sample_frequency))
    received = test_received('Samples collected')
    samples = int(received.split(' ')[2])
    print("Samples collected {}".format(samples))
    ac_meas, ir_meas = [], []
    for sample in range(samples*2):  # you receive accelerometer and ir
        res = int(ser.readline().decode().strip())
        ac_meas.append(res) if sample % 2 else ir_meas.append(res)
    results = {'ac_meas': ac_meas,
               'ir_meas': ir_meas,
               'puls_freq': rotor_frequency,
               'sample_freq': sample_frequency}
    test_received('Measurement completed')
    sleep(1)
    try:
        calc.getdetails(results, flt=False, verbose=True, arithmic=True)
    except ValueError:
        print("IR seems not properly triggered and overexposed.")
    if plot:
        calc.plotdata(results)
    return results


def parser():
    '''creates parser for the command line interface of this script

    Returns:
    Argument parses
    '''
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument('--plot',
                        action="store_true",
                        default=False, help='Plot results')
    parser.add_argument('--upload',
                        action="store_true",
                        default=False, help='Upload firmware')
    parser.add_argument('--frequency',
                        action="store",
                        default=20,
                        type=int,
                        help='Set frequency in Hz')
    parser.add_argument('--filename',
                        action="store",
                        default=None,
                        type=str,
                        help='Filename to store results with pickle.')
    return parser


if __name__ == "__main__":
    parser = parser()
    args = parser.parse_args()
    results = main(args.frequency, args.plot, args.upload)
    if args.filename:
        pickle.dump(results,
                    open(args.filename, 'wb'))
