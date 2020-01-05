import pigpio

print("start client with sudo pigpiod")

def rotatepolygon(name='sharp', speed):
    """rotate polygon
    
    two polygon motors are supported;
       - the sharp AR160 polygon motor with the NBC3111 chip
       - the PANASONIC with the AN44000A chip

    Keyword arguments:
    name -- panasonic or sharp
    speed -- speed of the polygon motor in Hertz
    """
    if name not in ['panasonic', 'sharp']:
        raise Exception("Motor not supported")
    
    if name == 'panasonic':
        # only drive enable pin rest of the pins dont matter
        # duty cycle between 0 and 1E6, 5E5 is 50%
        # enable pin must be flipped this is the pin nr 3 from the right
        # if polygon is in front of you
        pi.hardware_PWM(13, speed, 500000)