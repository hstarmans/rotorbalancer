import pickle
import matplotlib.pyplot as plt
import scipy.fftpack
from scipy.signal import correlate, butter, lfilter
from scipy.optimize import curve_fit


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
    plots frequency, time from results collected
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
        ax.set(xlabel='Frequency (Hz)')
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


def getdetails(measurement):
    '''
    estimate rotor frequency and putty location from measurements
    '''
    previous = -1
    start_ind = [] 
    cycle_time = []
    # detect rising edges & store indices
    for indx, val in enumerate(measurement['ir_meas']):
        if (previous != -1) & (val-previous == 1):
            start_ind.append(indx)
        previous = val
        # or do np roll and substract
        if len(start_ind)>1:
            cycle_time.append(start_ind[-1]-start_ind[-2])
    samples_per_period = np.mean(cycle_time)
    if np.abs(np.max(cycle_time)-np.min(cycle_time))>2:
        print(max(cycle_time))
        print(min(cycle_time))
        print("WARNING: Rotor frequency seems inaccurate")
        # check the signal --> something could be off
    frequency = measurement['sample_freq'] / samples_per_period
    print("Rotor frequency is {:.0f} Hz".format(frequency))
    
    # filter imporves results
    ac_meas = list(butter_bandpass_filter(measurement['ac_meas'], 0.8*frequency,
                   1.2*frequency, measurement['sample_freq'], order=6))
    pos_max, pos_min = [], []
    force = []
    for index in range(len(start_ind)-1):
        lst = ac_meas[start_ind[index]:start_ind[index+1]]
        pos_max.append(lst.index(max(lst)))
        pos_min.append(lst.index(min(lst)))
        force.append(max(lst))
    force = np.mean(force)
    print("Force is {:.2f} a.u.".format(force))
    def todegrees(positions):
        pos_time = np.mean(positions)/measurement['sample_freq'] 
        degrees  = pos_time/(1/frequency)*360
        return degrees
    max_deg = todegrees(pos_max)
    min_deg = todegrees(pos_min)
    if np.abs(np.abs(max_deg-min_deg)-180)>5:
        print(max_deg)
        print(min_deg)
        print("WARNING: Degree measurement seems inaccurate")
    print("Place putty at {:.0f} degrees".format(min_deg))


def crosscorrelate(results, low, high, rotor, debug = False):
    '''
    function to test the difference in phase between the accelerometer 
    signal and photo tachomater, fake signal can be used for debugging
     --> see https://stackoverflow.com/questions/6157791/find-phase-difference-between-two-inharmonic-waves
    '''
    ac_meas = results['ac_meas']
    ir_meas = results['ir_meas']
    freq = rotor # hertz, used to calculate phase shift
    N = len(ac_meas)
    T = 1/results['sample_freq']
    if debug:
        print("debug activated")
        phasediff = np.pi*debug
        #timeshift = round(debug/T)
        x = np.linspace(0.0, N*T, N)
        ir_meas = np.sin(freq*2*np.pi*x+phasediff)
        #ir_meas = np.roll(ir_meas, timeshift)
        ac_meas = np.sin(freq*2*np.pi*x)
    # band pass filter
    ac_meas = butter_bandpass_filter(ac_meas, low, high, results['sample_freq'], order=6)
    ir_meas = butter_bandpass_filter(ir_meas, low, high, results['sample_freq'], order=6)
    # mean centering, SDV scaling
    ac_meas = ac_meas-np.mean(ac_meas)
    ac_meas = ac_meas/np.std(ac_meas)
    ir_meas =  ir_meas-np.mean(ir_meas)
    ir_meas = ir_meas/np.std(ir_meas )
    # calculate cross correlation of the two signal
    xcorr = correlate(ir_meas, ac_meas)
    # delta time array to match xcorrr
    t = np.linspace(0.0, N*T, N, endpoint=False)
    dt = np.linspace(-t[-1], t[-1], 2*N-1)
    #dt = np.arange(1-N, N)
    recovered_time_shift = dt[xcorr.argmax()]
    # force the phase shift to be in [-pi:pi]
    recovered_phase_shift = 2*np.pi*(((0.5 + recovered_time_shift/(1/freq) % 1.0) - 0.5))
    print("Recovered time shift {}".format(recovered_time_shift))
    print("Recovered phase shift {} radian".format(recovered_phase_shift))
    print("Recovered phase shift {} degrees".format(np.degrees(recovered_phase_shift)))