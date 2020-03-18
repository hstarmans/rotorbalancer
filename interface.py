# Author: Rik Starmans
# Date: 18-3-2020
# Description: program to upload arduino code and plot results
from subprocess import run
from time import sleep
import serial


FILENAME = 'Nano33_ble.ino'
PORT = '/dev/ttyACM0'
BOARD = 'Arduino Nano 33 BLE'
BAUDRATE = 115200
MEASURENTTIME = 90


def upload():
    # https://github.com/arduino/Arduino/blob/master/build/shared/manpage.adoc
    cmd = ['arduino', '--upload', '--board', BOARD, '--port', PORT, FILENAME]
    arduino = run(cmd)
    print("The exit code was: %d" % arduino.returncode)


def main():
    upload()
    ser = serial.Serial(PORT, BAUDRATE, timeout=3)
    received, iteration = '', 0
    while received != 'Press 1 to start samples.':
        received, iteration = ser.readline(), iteration+1
        if iteration>10:
            ser.close()
            raise Exception('Did not receive press 1')
    #TODO: add escape if iteration 10 is 
    ser.write('1')
    received, iteration = '', 0
    while 'Measurement time' not in received:
        received, iteration = ser.readline(), iteration+1
        if iteration>10:
            ser.close()
            raise Exception('Measurement time')
    measurement_time = received.split(' ')[2]
    sleep(measurement_time*1.1)
    while 'Writing results' not in received:
        received, iteration = ser.readline(), iteration+1
        if iteration>10:
            ser.close()
            raise Exception('Measurement time')
    samples = int(received.split(' ')[2])
    results = []
    for sample in range(samples):
        results.append(int(ser.readline()))
    while received != 'Measurement completed':
        received, iteration = ser.readline(), iteration+1
        if iteration>10:
            ser.close()
            raise Exception('Measurement not completed')
    print("Execution successful")
    ser.close()
    return samples


