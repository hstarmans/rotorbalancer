# Rotor balancer
The rotor balancer can be used to balance propellers from flying drones or laser mirror motors.
The instrument is also a tachometer and can record the speed of rotors.
The Nano 33 BLE pulses the motor via hardware pwm and records the accelerometer signal via the onboard LSM9DS1 accelerometer chip.
During rotation the signal of a [TCRT5000 IR LED](https://opencircuit.nl/Product/TCRT5000-Infrarood-lijn-detectie-module) is read out to detect the position of the rotor.
The amplitude of the accelerometer signal is proportional to the unbalanced mass. The phase difference between the infrared LED and the accelerometer indicates the position where a balance weight, aka. putty, has to be placed.
In the case of two plane unbalance, the phase difference between the IR Led and the accelerometer can be dependent upon rotor speed.  
So far, I have only used the single-plane 2 run method to balance the rotor. Multi-plane balancing is not implemented.
<img src="images/setup.jpg" align="center" width =60%/>

# Installation
Compile the firmware with Platform IO, a plugin for VSCode, and upload it to the Arduino Nano 33 BLE.
Connect to the board with a baudrate of 115200. Five options are available; start samples, calibrate IR sensor, spin polygon,
check pulse frequency and set pulse frequency.  
Place an aluminum foil sticker on your rotor. Ensure the infrared sensor detects the sticker and set the threshold using a screwdriver on the TCRT5000 IR LED sensor so it only changes when it detects the sticker. Use other menus to check if the polygon is spinning and set the pulse rate. 
Menus can typically be exited by pressing the 1 key and sending it with enter.
A program to collect measurements is available for python.  
The python program is installed as follows, install requirements;
```console
pip install -r requirements.txt
```
Install package;
```console
pip install -e .
```
Program is run as follows;
```console
python main.py --plot --frequency 20 --filename '20hertz.p'
```
An alternative is to run it via the python interpreter;
```python
from rotorbalancer import tools
tools.runtest(10,11,1,'test')
```
Example measurements can found in the measurements folder. 

# Video
I made a video of the setup for a better impression.  
[<img src="https://img.youtube.com/vi/xFNtZbOfEfQ/maxresdefault.jpg" width="50%">](https://youtu.be/xFNtZbOfEfQ)

# TODO:
Substract the measuremens from an unbalanced prism from a balanced prism.
This might make the results more intuitive.


# Measurements
<img src="images/singleresult.png" align="center" width =100%/><br>
For each measurement, the rotor was pulsed at a certain frequency for 20 seconds.
The motor was then turned off and the acceleration and infrared signal were measured for 1 second.
This was done as the the motor interfered with the measurements. Turning the motor of resulted in cleaner results.  
Sampling is equidistant at 952 Hertz as this was the maximum sampling frequency of the accelerometer.
From the measurements it can be seen that the rotor slows down.
The [centripetal force](https://en.wikipedia.org/wiki/Centripetal_force) is linear proportional to mass.
In single plane balancing it is assumed that the angle of the force is not dependent upon speed. The phase-difference between the ir sensor and the acceloremeter determines the location where putty needs to be applied. The phase difference and amplitude were determined via the getdetails function in [calc.py](calc.py). The minimum and maximum is determined for each cycle. The phase difference between these must be 180 degrees for the measurement to be accurate. The location of the minimum will be the location of the balance weight.  
<img src="images/results.png" align="center" width =100%/>  
The force follows a square law between 40-60 Hertz but not over the whole domain. This could be partly due to 
the fact that the rotor slows down. Other things must play a role as well as there is a noticable change around 78 hertz in both the force and phase plot. The spinning disk probably creates current in the motor which is turned off.  
The phase angle between the minimum amplitude of the accelerometer and the peak of the photodiode is dependent upon speed.
This could be due to multiple plane unbalance but is hard to say due to the electric field. Imagine multiple disks with each their own unbalance. 
Their moment is dependent upon the distance to a pivot point which is different and the force scales squarily with speed. As a result, the angle of the force measured can be dependent upon speed.  
The measurements were done on a prism for which some balancing was already done. A balance weight of 0.060 gram [Weicon resin putty](https://www.weicon.de/en/products/adhesives-and-sealants/2-component-adhesives-and-sealants/epoxy-resin-systems/plastic-metal/298/epoxy-resin-putty) was applied. I used an AG204 Delta range from Mettler to measure the weight of the putty accurately. As a lower cost alternative, pieces of aluminium tape could be used. A small piece of aluminum tape was applied to trigger the IR Led sensor.  
Futher literature can be found in [Science direct](https://www.sciencedirect.com/science/article/pii/S2351988616300185) and at the site of [National Instruments](https://forums.ni.com/t5/Example-Programs/Two-Plane-Balancing-Example-with-DAQmx/ta-p/3996066?profile.language=en).
The measurements are available in the measurements folder. The code for the analysis is available in [test.py](test.py).


# Implementation details
I had to remove modemmanager as this caused problems with [arduino](https://forum.arduino.cc/index.php?topic=575194.0).
```console
sudo apt --purge remove modemmanager
```
The accelerometer libary from [Sparkfun](https://github.com/sparkfun/SparkFun_LSM9DS1_Arduino_Library) is used in a slightly modified form.


# BOM
Prism:  
4 sides, 30x30x2 mm  
Mirror motor:  
Panasonic AN44000A, other moters require different pins to be pulsed.
Mirror motors have 5 pins; PWM, MOTOR_EN, GND, Voltage and LCK_PIN.
PWM is speed control. Relation is not linear for all motors. GND is ground. Voltage is the supply voltage, ideally 24V. LCK_pin is
false if encoder and signal are not in sync.
I cannot confirm the function of LCK_pin and MOTOR_EN. 
They should not not be floating as the frequency is unstable in these case.


  
Accelerometer:  
The accelerometer of the LSM9DS1 is used, as it available on the Arduino Nano 33.  
IR sensor:  
The TCRT5000 IR LED sensor see [DIY LP turntable](https://www.stockholmviews.com/wp/diy-lp-turntable-tachometer/). I bought one [here](https://opencircuit.nl/Product/TCRT5000-Infrarood-lijn-detectie-module)  
Balancing putty:  
In the industry two systems are used. A 2 component epoxy resin putty by [Weicon](https://www.weicon.de/en/products/adhesives-and-sealants/2-component-adhesives-and-sealants/epoxy-resin-systems/plastic-metal/298/epoxy-resin-putty)
A single component UV curable expory resin system, e.g. by [Shenk](http://www.schenck-worldwide.com/PDF/de-de1/Epoxidharz-Unwucht-Korrektursystem.pdf). In german it is called Wuchtkitt. The compound has a ceramic filling and the density is 2 gram per cubic centimer. Component was ordered via [modular](https://www.modulor.de).
An alternative is to use lead or metal tape. Lead has a density of 11 gram per cubic centimer.  
Optical plate:  
Used an optical aluminum breadboard from Thorlabs with M6 screws as base. Do not attach the device to something heavy this make the measurements worse. Typically, you want it decoupled from the external world and place the object under study on foam or hang it on cords. During measurements, the prism was suspended in air with strings.
