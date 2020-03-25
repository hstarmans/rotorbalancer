# planning
#   --> houder uitprinten
#   --> cross correlatie opnieuw uitrekenen
#   --> grootte imbalans bepalen

import pickle
import matplotlib.pyplot as plt
import scipy.fftpack
from scipy.signal import square, sawtooth, correlate
import numpy as np


def plotdata(results, saveplot=False):
    '''
    plots frequency, time from results collected by by client
    '''
    def plottime(data, ax):
        t = [t*(1/results['sample_freq']) for t in range(len(data))]
        ax.plot(t, data)
        ax.grid()
        ax.set_xlabel('Time')

    def plotfrequency(data, ax): 
        T = 1/results['sample_freq']
        N = len(data)
        xf = np.linspace(0.0, 1.0/(2.0*T), N/2)
        yf = scipy.fftpack.fft(data)
        ax.plot(xf, 2.0/N*np.abs(yf[:N//2]))
        ax.set(xlabel='frequency (Hz)')
        ax.grid()

    fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(12,8))
    fig.canvas.set_window_title("Frequency and time plots")
    plottime(results['ac_meas'], axes[0,0])
    axes[0,0].title.set_text('Acceleration vs time')
    plotfrequency(results['ac_meas'], axes[0,1])
    axes[0,1].title.set_text('Acceleration spectrum')
    axes[0,1].set_ylabel('ticks (1000 ticks is g')
    plottime(results['ir_meas'], axes[1,0])
    axes[1,0].title.set_text('Infrared voltage vs time')
    plotfrequency(results['ir_meas'], axes[1,1])
    axes[1,1].title.set_text('Infrared spectrum')
    plt.tight_layout()
    plt.show()
    if saveplot:
        fig.savefig("results.png")


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
    