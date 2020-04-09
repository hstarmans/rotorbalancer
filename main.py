# Author: Rik Starmans
# Date: 18-3-2020
# Description: program to upload arduino code and plot results
from subprocess import run
from time import sleep
import serial
import argparse
import pickle

import calc


FILENAME = 'Nano33_ble/Nano33_ble.ino'
PORT = '/dev/ttyACM0'
BAUDRATE = 115200


def upload():
    '''
    upload the firmware to the ide via python
    '''
    # https://github.com/arduino/Arduino/blob/master/build/shared/manpage.adoc
    # board is specified by settting the Nano33 board to default in the IDE
    cmd = ['arduino', '--upload', '--port', PORT, FILENAME]
    arduino = run(cmd)
    if arduino.returncode:
        raise Exception("Exit code not zero, operation failed")
    sleep(3) # wait for board to boot


def test_received(ser, text):
    received, iteration = '', 0
    while text not in received:
        received, iteration = ser.readline().decode().strip(), iteration+1
        if iteration>10:
            ser.close()
            print("Received {}".format(received))
            raise Exception('Did not receive text; "{}"'.format(text))
    return received


def set_frequency(frequency):
    '''
    set the hardware pwm frequency
    '''
    ser = serial.Serial(PORT, BAUDRATE, timeout=1)
    test_received(ser, 'Press 5 to set pulse frequency.')
    ser.write('5'.encode())
    test_received(ser, 'Set pulse frequency in Hz.')
    ser.write(str(frequency).encode())
    test_received(ser, 'Accepted.')
    ser.close()


def main(frequency=20, plot=False, upload=False):
    """
    collects sample from the client
    upload: if true firmware is uploaded
    plot: if true results are plotted
    frequency: frequency used
    """
    print("Setting frequency to {} Hz".format(frequency))
    set_frequency(frequency)
    ser = serial.Serial(PORT, BAUDRATE, timeout=1)
    if upload:
        upload()
    test_received(ser, 'Press 1 to start samples.')
    ser.write('1'.encode())
    received = test_received(ser, 'Process time')
    measurement_time = float(received.split(' ')[2])
    print("Waiting {} seconds for operation to complete".format(measurement_time))
    slept = 0
    sleep_step = 5 # seconds
    while slept<measurement_time:
        slept += sleep_step
        if slept>measurement_time:
            sleep(measurement_time-slept+sleep_step)
            slept = measurement_time
        else:
            sleep(sleep_step)
        print(" Completed {:.2f} %".format(slept/measurement_time*100))
    received = test_received(ser, 'Pulse frequency')
    rotor_frequency = int(received.split(' ')[2])   
    print("Pulse frequency {} Hz".format(rotor_frequency))
    received = test_received(ser, 'Sample frequency')
    sample_frequency = int(received.split(' ')[2])  
    print("Sample frequency {} Hz".format(sample_frequency))
    received = test_received(ser, 'Samples collected')
    samples = int(received.split(' ')[2])
    print("Samples collected {}".format(samples))
    ac_meas, ir_meas = [], []
    for sample in range(samples*2): # you receive accelerometer and ir
        res = int(ser.readline().decode().strip())
        ac_meas.append(res) if sample%2 else ir_meas.append(res)
    results = {'ac_meas':ac_meas, 'ir_meas':ir_meas, 'puls_freq':rotor_frequency, 
               'sample_freq':sample_frequency}
    test_received(ser, 'Measurement completed')
    sleep(1)
    ser.close()
    try:
        calc.getdetails(results)
    except ValueError:
        print("IR seems not properly triggered and overexposed.")
    if plot:
        calc.plotdata(results)
    return results


def parser():
    '''
    default parser
    '''
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument('--plot', action="store_true", default=False, help='Plot results')
    parser.add_argument('--upload', action="store_true", default=False, help='Upload firmware')
    parser.add_argument('--frequency', action="store", default=20, type=int, help='Set frequency in Hz')
    parser.add_argument('--filename', action="store", default=None, type=str, help='Filename to store results with pickle.')
    return parser


if __name__ == "__main__":
    parser = parser()
    args = parser.parse_args()
    results = main(args.frequency, args.plot, args.upload)
    if args.filename:
        pickle.dump(results, open(args.filename, 'wb'))