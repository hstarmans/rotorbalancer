# planning
#   --> houder uitprinten
#   --> cross correlatie opnieuw uitrekenen
#   --> grootte imbalans bepalen

import pickle
import matplotlib.pyplot as plt
import scipy.fftpack
from scipy.signal import correlate, butter, lfilter
import numpy as np


def butter_bandpass(lowcut, highcut, fs, order=5):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return b, a



def butter_bandpass_filter(data, lowcut, highcut, fs, order=5):
    b, a = butter_bandpass(lowcut, highcut, fs, order=order)
    y = lfilter(b, a, data)
    return y



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
    
    # mean centering
    ac_meas = results['ac_meas']-np.mean(results['ac_meas'])
    ir_meas = results['ir_meas']-np.mean(results['ir_meas'])

    # band pass filter
    #ac_meas = butter_bandpass_filter(ac_meas, 300, 307, results['sample_freq'], order=6)
    #ir_meas = butter_bandpass_filter(ir_meas, 300, 307, results['sample_freq'], order=6)

    
    fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(12,8))
    fig.canvas.set_window_title("Frequency and time plots")
    plottime(ac_meas, axes[0,0])
    axes[0,0].title.set_text('Acceleration vs time')
    plotfrequency(ac_meas, axes[0,1])
    axes[0,1].title.set_text('Acceleration spectrum')
    #axes[0,1].set_ylabel('ticks (1000 ticks is g')
    plottime(ir_meas, axes[1,0])
    axes[1,0].title.set_text('Infrared voltage vs time')
    plotfrequency(ir_meas, axes[1,1])
    axes[1,1].title.set_text('Infrared spectrum')
    plt.tight_layout()
    plt.show()
    if saveplot:
        fig.savefig("results.png")


def crosscorrelate(results, debug = False):
    '''
    function to test the difference in phase between the accelerometer 
    signal and photo tachomater, fake signal is used at the moment\
     --> see https://stackoverflow.com/questions/6157791/find-phase-difference-between-two-inharmonic-waves
    '''
    # mean centering, SDV scaling
    ac_meas = results['ac_meas']-np.mean(results['ac_meas'])
    ac_meas = ac_meas/np.std(results['ac_meas'])
    ir_meas = results['ir_meas']-np.mean(results['ir_meas'])
    ir_meas = ir_meas/np.std(results['ir_meas'])

    # band pass filter
    #ac_meas = butter_bandpass_filter(ac_meas, 90, 110, results['sample_freq'], order=6)
    #ir_meas = butter_bandpass_filter(ir_meas, 90, 110, results['sample_freq'], order=6)


    # parameters used for artificial signal
    # --recovered phae shift 0.09
    freq = 101 # hertz, used to calculate phase shift
    N = len(ac_meas)
    T = 1/results['sample_freq']
    x = np.linspace(0.0, N*T, N)
    # there two ways of debugging;
    #   -- recover phase and time shift from artificial signal
    #   -- move measured signal and see if you can recover this shift
    if debug:
        print("debug activated")
        phasediff = 0
        ir_meas = np.sin(freq*2*np.pi*x+phasediff)
    #timeshift = 10    
    #ir_meas = np.roll(ir_meas, timeshift)
    # quick test with original signal
    #artificial = np.roll(result, timeshift)
    # calculate cross correlation of the two signal
    xcorr = correlate(ir_meas, ac_meas)
    # delta time array to match xcorrr
    dt = np.arange(1-N, N)
    recovered_time_shift = dt[xcorr.argmax()]
    # force the phase shift to be in [-pi:pi]
    recovered_phase_shift = 2*np.pi*(((0.5 + recovered_time_shift/freq) % 1.0) - 0.5)
    print("Recovered time shift {}".format(recovered_time_shift))
    print("Recovered phase shift {}".format(recovered_phase_shift))