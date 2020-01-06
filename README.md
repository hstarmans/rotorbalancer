# Rotor balancer

The goal of this project is to make a balancer for rotors, especially for the prisms used in the open hardware fast high resolution laser.

# BOM
MMA8452Q triple axis accelerometer (MMA8451Q can also be bought which is four times more accurate).
The LIS3DH has higher sampling rates.

<p hidden>
Test;
 1. How many samples can you acquire per second  --> 970 measurements
 2. Timestamp and acquire your data
      - what is the max min value if your polygon is on
      - what is the max min value if your polygon is off
     --> can you detect that the polygon is running
 3. Plot your timestamped data, can you see an imbalance?
      --> yes you can see an imbalance in the discrete fourier transform
          you see several peaks at overtones of 100 hertz.
    The DFFT requires you to sample at constant time stamps
 4. Try to determine the phase lag via the cross correlation
<p>
