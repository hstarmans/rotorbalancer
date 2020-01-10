import pickle
import matplotlib.pyplot as plt
import scipy.fftpack
from scipy.signal import square, sawtooth, correlate
import numpy as np


def readplotdata():
    '''
    displays keys of dictionary
    '''
    dct = pickle.load(open('20hertzprism.p', 'rb'))
    for key, value in dct.items():
        print(key)
    # values = dct['values']
    # x_accel = values[0]
    # print(x_accel[1:30])


def plotdata():
    '''
    plots data in time
    calculates discrete fourier transform plots amplitude or phase
    '''
    dct = pickle.load(open('20hertzmirror.p', 'rb'))
    tpassed = dct['tpassed']
    print("RPS is {}".format(dct['rps']))
    values = dct['values']
    x_res = values[1]
    print(x_res)
    x_accel = [x_res[i] for i in range(len(x_res)-1) if x_res[i]!=x_res[i+1]]
    # time plot
    # time = [t*(tpassed/len(x_accel)) for t in range(len(x_accel))]
    # plt.plot(time, x_accel, 'ro')
    # plt.show()
    # discrete fourier transform
    print(x_accel)
    yf = scipy.fftpack.fft(x_accel)
    T = tpassed/len(x_accel)  # THIS IS NOT CORRECT, sensor is 800 hertz
    N = len(x_accel)
    xf = np.linspace(0.0, 1.0/(2.0*T), N/2)
    fig, ax = plt.subplots()
    ax.plot(xf, 2.0/N*np.abs(yf[:N//2]))
    ax.set(xlabel='frequency (Hz)', ylabel='ticks (1000 ticks is g)')
    ax.grid()
    fig.savefig("20hertzmirror.png")
    # plt.plot(xf, 2.0/N*np.angle(yf[:N//2]))
    plt.show()


def crosscorrelate():
    '''
    function to test the difference in phase between the accelerometer 
    signal and photo tachomater, fake signal is used at the moment\
     --> see https://stackoverflow.com/questions/6157791/find-phase-difference-between-two-inharmonic-waves
    '''
    dct = pickle.load(open('20hertzprism.p', 'rb'))
    tpassed = dct['tpassed']
    values = dct['values']
    # reguralize datasets
    result = np.array(values[0])
    result -= result.mean()
    result /= result.std()
    # parameters used for artificial signal
    freq = 96 # hertz, simulated
    phasediff = 0
    #timeshift = 0
    # --recovered phae shift 0.09
    N = len(result)
    T = tpassed/N  # THIS IS NOT CORRECT, sensor is 800 hertz
    x = np.linspace(0.0, N*T, N)
    # quick test with artificial signal
    artificial = np.sin(freq*2*np.pi*x+phasediff)
    #artificial = np.roll(artificial, timeshift)
    # quick test with original signal
    #artificial = np.roll(result, timeshift)
    # calculate cross correlation of the two signal
    xcorr = correlate(artificial, result)
    # delta time array to match xcorrr
    dt = np.arange(1-N, N)
    recovered_time_shift = dt[xcorr.argmax()]
    # force the phase shift to be in [-pi:pi]
    recovered_phase_shift = 2*np.pi*(((0.5 + recovered_time_shift/T) % 1.0) - 0.5)
    print("Recovered time shift {}".format(recovered_time_shift))
    print("Recovered phase shift {}".format(recovered_phase_shift))
    

plotdata()