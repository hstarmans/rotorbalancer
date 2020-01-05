import MMA8452Q
import time

sensor = MMA8452Q.Accelsensor()

t = time.time()
loops = 1000
for i in range(loops):
    sensor.get_acceleration()

texp = (time.time()-t)

mpersecond = loops / texp

print("I can do {} measurements per second.".format(mpersecond))
