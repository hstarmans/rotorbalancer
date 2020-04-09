# Rotor balancer
The rotor balancer can be used to balance propellers from flying drones or laser mirror motors.
The instrument can also function as a tachometer to record the speed of rotors. The Nano 33 BLE is used to pulse the motor via hardware pwm and record the accelerometer signal via the onboard LSM9DS1 onboard accelerometer chip.
During rotation the signal of a [TCRT5000 IR LED](https://opencircuit.nl/Product/TCRT5000-Infrarood-lijn-detectie-module) is read out to detect the position of the rotor.
The amplitude of the accelerometer signal is proportional to the unbalanced mass and the phase difference between the IR LED and the accelerometer indicates the position where a balance weight, aka. putty, has to be placed.
In the case of two plane unbalance, the phase difference between the IR Led and the accelerometer will be dependent upon rotor speed.


# Installation
Compile the firmware with the Arduino IDE and upload it to the Arduino Nano 33 BLE.
Connect to the board with a baudrate of 115200. Five options will be offered; start samples, calibrate IR sensor, spin polygon,
check pulse frequency and set pulse frequency. <br>
Place an aluminum foil sticker on your rotor. Check if the IR sensor can detect the sticker and set the threshold using a screwdriver on the TCRT5000 IR LED sensor so it only changes when it detects the sticker. Use other menus to check if the polygon is spinning and set the pulse rate. Menus can typically be exited by pressing the 1 key and sending it with enter.
A client side program has been made available in python 3. Command line options are available. <br>
Install requirements;
```console
pip install -r requirements.txt
```
Program can be run as follows;
```console
python main.py --plot --frequency 20 --filename '20hertz.p'
```
Example measurements can found in the measurements folder. 


# Method
Details with pictures can be found on [Hackaday](https://hackaday.io/project/21933-open-hardware-fast-high-resolution-laser/log/172827-rotor-stabilization-experiments).
Vibrations caused by a spinning rotor are measured with an accelerometer.
I did an experiment where I spun the rotor at 100 Hertz and recorded the vibrations for 3 seconds at 952 Hertz sampling frequency.
Sampling of the signal must be equidistant or otherwise the discrete fourier transform can not be calculated.
The amplitude of the discrete fourier transform at a 100 Hertz is used to determine the balance weight.
This amplitude can be linearly compared to the magnitude of the amplitude determined from a known balance weight.
As the [centripetal force](https://en.wikipedia.org/wiki/Centripetal_force) is linear proportional to mass.
In single plane balancing it is assumed that the angle of the force is not dependent upon speed. The phase-difference between the ir sensor and the acceloremeter determines this angle. The phase difference can be determined from the cross correlation of the two [signals](https://stackoverflow.com/questions/6157791/find-phase-difference-between-two-inharmonic-waves). Noise is removed with a Butterworth filter.
This method is available in the code. Currently another method is used. The minimum and maximum force is determined for each cycle. 
The phase difference between these must be 180 degrees for the measurement to be accurate. The location of the minimum will be the location of the balance weight. The phase angle was relatively constant in the range 97-144 Hz but the force did follow a square law as expected from the centrepetal force. It is assumed this is due to nonlinearity in the materials and the imperfect setup. <br>
A balance weight of less than a gram was needed. I used an AG204 Delta range from Mettler to measure the weight of the putty accurately.
Another practical example is given by a case study in [Science direct](https://www.sciencedirect.com/science/article/pii/S2351988616300185).
Note, above steps are only sufficient for single plane balancing. In two plane balancing, the procedure is more [complicated](https://forums.ni.com/t5/Example-Programs/Two-Plane-Balancing-Example-with-DAQmx/ta-p/3996066?profile.language=en).
Imagine multiple disks with each their own unbalance. If the speed is increased all these unbalances will scale linearly. 
Their moment is dependent upon the distance to a pivot point which is different. As a result, the angle of the force measured can be dependent upon speed.


# Implementation details
I had to remove modemmanager as this caused problems with [arduino](https://forum.arduino.cc/index.php?topic=575194.0).
```console
sudo apt --purge remove modemmanager
```
The accelerometer libary from [Sparkfun](https://github.com/sparkfun/SparkFun_LSM9DS1_Arduino_Library) is used in a slightly modified form.


# BOM
Prism:<br>
4 sides, 30x30x2 mm <br>
Mirror motor: <br>
Panasonic AN4000A, other moters require different pins to be pulsed <br>
Accelerometer: <br>
The accelerometer of the LSM9DS1 is used, as it available on the Arduino Nano 33. <br>
IR sensor: <br>
The TCRT5000 IR LED sensor see [DIY LP turntable](https://www.stockholmviews.com/wp/diy-lp-turntable-tachometer/). I bought one [here](https://opencircuit.nl/Product/TCRT5000-Infrarood-lijn-detectie-module) <br>
Balancing putty: <br>
In the industry two systems are used. A 2 component epoxy resin putty by [Weicon](https://www.weicon.de/en/products/adhesives-and-sealants/2-component-adhesives-and-sealants/epoxy-resin-systems/plastic-metal/298/epoxy-resin-putty)
A single component UV curable expory resin system, e.g. by [Shenk](http://www.schenck-worldwide.com/PDF/de-de1/Epoxidharz-Unwucht-Korrektursystem.pdf). In german it is called Wuchtkitt. The compound has a ceramic filling and the density is 2 gram per cubic centimer. Component was ordered via [modular](https://www.modulor.de).
An alternative is to use lead or metal tape. Lead has a density of 11 gram per cubic centimer. 
