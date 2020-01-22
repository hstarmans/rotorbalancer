# Rotor balancer

The goal of this project is to make a balancer for rotors.

# Status
It has been shown that the data needed to balance the prism can be collected using an accelerometer and a
a laser tachometer, the DT2234C+. A prism still hasn't been balanced as the signal of the laser tachometer can't be collected.


# Method
Details with pictures can be found on [Hackaday](https://hackaday.io/project/21933-open-hardware-fast-high-resolution-laser/log/172827-rotor-stabilization-experiments).
Vibrations caused by a spinning rotor are measured with an accelerometer.
I did an experiment where I spun the rotor at 100 Hertz and recorded the vibrations for 1 second at 800 Hertz sampling frequency.
Sampling of the signal must be equidistant or otherwise the discrete fourier transform can not be calculated.
The amplitude of the discrete fourier transform at a 100 hertz is used to determine the balance weight.
This amplitude can be linearly compared to the height of the amplitude determined from a known balance weight.
As the [centripetal force](https://en.wikipedia.org/wiki/Centripetal_force) is linear proportional to mass.
A practical example is given by a case study in [Science direct](https://www.sciencedirect.com/science/article/pii/S2351988616300185).
Note, above steps are only sufficient for single plane balancing. In two plane balancing, the procedure is more [complicated](https://forums.ni.com/t5/Example-Programs/Two-Plane-Balancing-Example-with-DAQmx/ta-p/3996066?profile.language=en).
To determine the position of the mass, the position of the rotor must be measured. For example by using a [photo tachometer](https://hackaday.com/2017/03/17/how-to-use-a-photo-tachometer/). The phase-difference of the periodic signal recorded with the laser sensor can be compared with the periodic signal of the acceloremeter. The cross correlation of the two signals can be determined and from it the phase difference, an example in Python is given [here](https://stackoverflow.com/questions/6157791/find-phase-difference-between-two-inharmonic-waves).
Other methods of determining the phase difference between two signals are listed [here](https://stackoverflow.com/questions/27545171/identifying-phase-shift-between-signals). In the open-hardware laser scanner, the position of the rotor can be determined by recording the number of facets counted with the photo diode.
The challenge, however, is that the rotor is not fixed. My first idea was to measure the rotor with
a photo camera having a global shutter. My current idea is a laser tachometer and a white glass marker.

# BOM
Accelerometer: <br>
MMA8452Q triple axis accelerometer. The MMA8451Q can also be bought and is four times more accurate.
The LIS3DH has higher sampling rates. <br>
IR sensor: <br>
The TCRT5000 IR LED sensor was used in a DIY LP turntable [tachometer](https://www.stockholmviews.com/wp/diy-lp-turntable-tachometer/). I bought one [here](https://benselectronics.nl/lijn-en-benaderings-detectie-tcrt5000f48e6f8fa719f5a33a4efaa36b5f7396/?gclid=EAIaIQobChMImsbwqfSW5wIVicx3Ch1p2Q60EAQYBSABEgII_fD_BwE/) <br>
Balancing putty: <br>
In the industry two systems are used. A 2 component epoxy resin putty by [Weicon](https://www.weicon.de/en/products/adhesives-and-sealants/2-component-adhesives-and-sealants/epoxy-resin-systems/plastic-metal/298/epoxy-resin-putty)
A single component UV curable expory resin system, e.g. by [Shenk](http://www.schenck-worldwide.com/PDF/de-de1/Epoxidharz-Unwucht-Korrektursystem.pdf). The compound has a ceramic filling and the density is 2 gram per cubic centimer.
An alternative is to use lead or metal tape. Lead has a density of 11 gram per cubic centimer.




<!--
You can buy a laser tachometer for 18 dollars and do tests with that.
Test;
 1. How many samples can you acquire per second -> 970
 2. Timestamp and acquire your data
      - what is the max min value if your polygon is on
      - what is the max min value if your polygon is off
     -> can you detect that the polygon is running -> yes
 3. Plot your timestamped data, can you see an imbalance?
C++ library for MMA8452Q with byte received confirmation [link](https://github.com/DanDawson/MMA8452-Accelerometer-Library-Spark-Core/blob/master/firmware/MMA8452-Accelerometer-Library-Spark-Core.cpp)
-->
