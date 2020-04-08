import MMA8452Q
import polygon
import time
import pickle

sensor = MMA8452Q.Accelsensor()

def donmeasurements(measurements):
    x_accel = []
    y_accel = []
    z_accel = []
    for i in range(measurements):
        [x,y,z] = sensor.get_acceleration()
        x_accel.append(x)
        y_accel.append(y)
        z_accel.append(z)
    return [x_accel, y_accel, z_accel]


def test1():
    '''number of measurements per second

    test the amount samples that can be taken per second
    967 measurements per second on raspberry pi 3
    '''
    
    t = time.time()
    loops = 1000
    donmeasurements(loops)
    texp = (time.time()-t)
    mpersecond = loops / texp
    print("I can do {} measurements per second.".format(mpersecond))


def test2():
    '''
    stable 13, 17, 24
    100 hertz 249, 541, 1114
    300 hertz 437, 1017, 1959
    '''
    measurements = 1000
    rps = 100
    print("stable")
    lst = donmeasurements(measurements)
    for item in lst:
        spread = max(item)-min(item)
        print("spread is {}".format(spread))
    print("rotating polygon at {} hertz, wait 30 sec to stabilize".format(rps))
    polygon.rotate(rps, 'panasonic')
    time.sleep(30)
    lst = donmeasurements(measurements)
    for item in lst:
        spread = max(item)-min(item)
        print("spread is {}".format(spread))
    polygon.rotate(0, 'panasonic')    


def test3():
    measurements = 1000
    rps = 100 
    polygon.rotate(rps, 'panasonic')
    print("waiting 60 seconds for polygon to stabilize")
    time.sleep(60)
    starttime = time.time()
    lst = donmeasurements(measurements)
    tpassed = time.time()-starttime
    dct = {'tpassed':tpassed, 'rps':rps, 'values':lst}
    polygon.rotate(0, 'panasonic')
    pickle.dump(dct, open( "results.p", "wb" ) )
    print("measurements finished")


test3()