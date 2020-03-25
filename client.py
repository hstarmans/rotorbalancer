# Author: Rik Starmans
# Date: 18-3-2020
# Description: program to upload arduino code and plot results
from subprocess import run
from time import sleep
import serial


FILENAME = 'Nano33_ble/Nano33_ble.ino'
PORT = '/dev/ttyACM0'
BAUDRATE = 115200


def upload():
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
            raise Exception('Did not reiceve text; "{}"'.format(text))
    return received


def main(upload=False):
    if upload:
        upload()
    ser = serial.Serial(PORT, BAUDRATE, timeout=3)
    test_received(ser, 'Press 1 to start samples.')
    ser.write('1'.encode())
    received = test_received(ser, 'Process time')
    measurement_time = float(received.split(' ')[2])
    print("Sleeping {} seconds".format(measurement_time))
    slept = 0
    while slept<measurement_time:
        sleep(5)
        slept += 5
        print(" Completed {} %".format(slept/measurement_time*100))
    received = test_received(ser, 'Rotor frequency')
    rotor_frequency = int(received.split(' ')[2])   
    print("Rotor frequency {} Hz".format(rotor_frequency))
    received = test_received(ser, 'Sample frequency')
    sample_frequency = int(received.split(' ')[2])  
    print("Sample frequency {} Hz".format(sample_frequency))
    received = test_received(ser, 'Samples collected')
    samples = int(received.split(' ')[2])
    print("Samples collected {}".format(samples))
    ac_meas, ir_meas = []
    for sample in range(samples*2): # you receive accelerometer and ir
        res = int(ser.readline().decode().strip())
        ac_meas.append(res) if sample%2 else ir_meas.append(res)
    results = {'ac_meas':ac_meas, 'ir_meas':ir_meas, 'rot_freq':rotor_frequency, 
               'sample_freq':sample_frequency}
    test_received(ser, 'Measurement completed')
    print('Execution successful')
    ser.close()
    return results