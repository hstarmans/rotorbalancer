# Rotor balancer

The goal of this project is to make a balancer for rotors.

# Method
Vibrations caused by a spinning rotor are measured with an accelerometer. 
I did an experiment where I spun the rotor at 100 Hertz and recorded the vibrations for 1 second at 800 Hertz sampling frequency.
Sampling of the signal must be equidistant or otherwise the discrete fourier transform can not be calculated.
The amplitude of the discrete fourier transform at a 100 hertz is used to determine the balance weight.
This amplitude can be linearly compared to the height of the amplitude determined from a known balance weight.
As the [centrepetal force](https://en.wikipedia.org/wiki/Centripetal_force) is linear proportional to mass.
A practical example is given by a case study in [Science direct](https://www.sciencedirect.com/science/article/pii/S2351988616300185).
Note, above steps are only sufficient for single plane balancing. In two plane balancing the procedure is more [complicated](https://forums.ni.com/t5/Example-Programs/Two-Plane-Balancing-Example-with-DAQmx/ta-p/3996066?profile.language=en).
Using the above, the mass required for balancing the rotor can be determined. To determine the position of the mass, the position of the rotor must be measured. For examply by using a [photo tachometer](https://hackaday.com/2017/03/17/how-to-use-a-photo-tachometer/). The phase-difference of the periodic signal recorded with the laser sensor can be compared with the periodic signal of the acceloremeter. The cross correction of the two signals can be determined and from it the phase difference, an example in Python is given [here](https://stackoverflow.com/questions/6157791/find-phase-difference-between-two-inharmonic-waves).
Other methods of determining the phase difference between two signals are listed [here](https://stackoverflow.com/questions/27545171/identifying-phase-shift-between-signals). In the open-hardware laser scanner, the position of the rotor can be determined by recording the number of facets counted with the photo diode.
The challenge, however, is that the rotor is not fixed. The position of the rotor is therefore measured during rotation with a
photo camera with a global shutter.

# BOM
I used the MMA8452Q triple axis accelerometer. The MMA8451Q can also be bought and is four times more accurate.
The LIS3DH has higher sampling rates.

<!--
Test;
 1. How many samples can you acquire per second -> 970
 2. Timestamp and acquire your data
      - what is the max min value if your polygon is on
      - what is the max min value if your polygon is off
     -> can you detect that the polygon is running -> yes
 3. Plot your timestamped data, can you see an imbalance?
-->
