import pickle
import matplotlib.pyplot as plt
import scipy.fftpack
from scipy.signal import square, sawtooth, correlate
import numpy as np


def readplotdata():
    '''
    displays keys of dictionary
    '''
    dct = pickle.load(open('results.p', 'rb'))
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
    dct = pickle.load(open('results.p', 'rb'))
    tpassed = dct['tpassed']
    print("RPS is {}".format(dct['rps']))
    values = dct['values']
    x_res = values[0]
    x_accel = [x_res[i] for i in range(len(x_res)-1) if x_res[i]!=x_res[i+1]]
    # time plot
    # time = [t*(tpassed/len(x_accel)) for t in range(len(x_accel))]
    # plt.plot(time, x_accel, 'ro')
    # plt.show()
    # discrete fourier transform
    yf = scipy.fftpack.fft(x_accel)
    T = tpassed/len(x_accel)  # THIS IS NOT CORRECT, sensor is 800 hertz
    N = len(x_accel)
    xf = np.linspace(0.0, 1.0/(2.0*T), N/2)
    #plt.plot(xf, 2.0/N*np.abs(yf[:N//2]))
    plt.plot(xf, 2.0/N*np.angle(yf[:N//2]))
    plt.show()


def crosscorrelate():
    '''
    function to test the difference in phase between the accelerometer 
    signal and photo tachomater, fake signal is used at the moment
    '''
    dct = pickle.load(open('results.p', 'rb'))
    tpassed = dct['tpassed']
    values = dct['values']
    result = values[0]
    freq = 100 # hertz, simulated
    phasediff = 0
    N = len(result)
    T = tpassed/N  # THIS IS NOT CORRECT, sensor is 800 hertz
    x = np.linspace(0.0, N*T, N)
    artificial = np.sin(freq*2*np.pi*x+phasediff)
    # calculate cross correlation of the two signal
    xcorr = correlate(result, artificial)
    # The peak of the cross-correlation gives the shift between the two signals
    # The xcorr array goes from -nsamples to nsamples
    dt = np.linspace(-x[-1], x[-1], 2*N-1)
    recovered_time_shift = dt[xcorr.argmax()]
    # # force the phase shift to be in [-pi:pi]
    # recovered_phase_shift = 2*np.pi*(((0.5 + recovered_time_shift/period) % 1.0) - 0.5)
    print(recovered_time_shift)
    # see https://stackoverflow.com/questions/6157791/find-phase-difference-between-two-inharmonic-waves
    # you need a phase shift as you require degrees, see post


crosscorrelate()