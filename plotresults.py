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


# NOT AS SUITED AS CORRELATE
# def fitpolynomals(results, low, high, freq, debug=False):
#     # https://electronics.stackexchange.com/questions/311098/ways-of-estimating-phase-shift
#     ac_meas = results['ac_meas']
#     ir_meas = results['ir_meas']

#     N = len(ac_meas)
#     T = 1/results['sample_freq']
#     x = np.linspace(0.0, N*T, N)

#     if debug:
#         print("debug activated")
#         phasediff = np.pi*debug
#         #phasediff = 0
#         #timeshift = round(debug/T)
#         x = np.linspace(0.0, N*T, N)
#         ir_meas = np.sin(freq*2*np.pi*x+phasediff)
#         #ir_meas = np.roll(ir_meas, timeshift)
#         ac_meas = np.sin(freq*2*np.pi*x)


#     # band pass filter
#     ac_meas = butter_bandpass_filter(ac_meas, low, high, results['sample_freq'], order=6)
#     ir_meas = butter_bandpass_filter(ir_meas, low, high, results['sample_freq'], order=6)
#     # mean centering, SDV scaling
#     ac_meas = ac_meas-np.mean(ac_meas)
#     ac_meas = ac_meas/np.std(ac_meas)
#     ir_meas =  ir_meas-np.mean(ir_meas)
#     ir_meas = ir_meas/np.std(ir_meas )


#     def func(x, freq, phasediff):
#         # https://electronics.stackexchange.com/questions/311098/ways-of-estimating-phase-shift
#         return np.sin(freq*2*np.pi*x+phasediff)

#     popt1, pcov1 = curve_fit(func, x, ac_meas, bounds=([low,-np.pi],[high,np.pi]))
#     popt2, pcov2 = curve_fit(func, x, ir_meas, bounds=([low,-np.pi],[high,np.pi]))

#     print("Freq found is {}".format(np.mean([popt1[0], popt2[0]])))
#     verschil = popt2[1]-popt1[1]
#    print("Phase diff is {}".format(verschil))
#    #return popt1, popt2


def crosscorrelate(results, low, high, rotor, debug = False):
    '''
    function to test the difference in phase between the accelerometer 
    signal and photo tachomater, fake signal is used at the moment\
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


def checker(freq6001, freq6002, freq4001, freq4002):
    """
    check script; suppose you have 4 measurements
                   1 at 100 hertz
                   2 at 100 hertz
                   3 at 67 hertz
                   4 at 67 hertz
    
    looks at several differences, seems to work best for 100 hertz
    note; here 600 is 100 and 400 is 67
    """ 

    ac4001 = butter_bandpass_filter(freq4001['ac_meas'],60, 75, 952, order=6)
    ac4002 = butter_bandpass_filter(freq4002['ac_meas'],60, 75, 952, order=6)
    ir4001 = butter_bandpass_filter(freq4001['ir_meas'],60, 75, 952, order=6)
    ir4002 = butter_bandpass_filter(freq4002['ir_meas'],60, 75, 952, order=6)
    print(correlate(ac4001, ac4002).argmax())
    print(correlate(ir4001, ir4002).argmax())

    print(correlate(ir4001, ac4001).argmax())
    print(correlate(ir4002, ac4002).argmax())

    ac6001 = butter_bandpass_filter(freq6001['ac_meas'],90, 110, 952, order=6)
    ac6002 = butter_bandpass_filter(freq6002['ac_meas'],90, 110, 952, order=6)
    ir6001 = butter_bandpass_filter(freq6001['ir_meas'],90, 110, 952, order=6)
    ir6002 = butter_bandpass_filter(freq6002['ir_meas'],90, 110, 952, order=6)

    print(correlate(ac6001, ac6002).argmax())
    print(correlate(ir6001, ir6002).argmax())
    # modulo (1/66.67)/(1/952)
    # modulo (1/100)/(1/952)

    print(correlate(ir6001, ac6001).argmax())
    print(correlate(ir6002, ac6002).argmax())