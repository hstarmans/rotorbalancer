import pickle
import scipy.fftpack
from scipy.signal import correlate, butter, lfilter
from scipy.optimize import curve_fit


import numpy as np


def butter_bandpass(lowcut, highcut, fs, order=5):
    '''butter bandpass

    Code copied from 
    https://stackoverflow.com/questions/12093594/how-to-implement-band-pass-butterworth-filter-with-scipy-signal-butter

    Keyword arguments:
    order -- order of the butter filter
    lowcut -- low frequency cut in Hz
    highcut -- high frequency cut in Hz
    fs -- frequency in Hz at which samples were taken

    Returns
    Scipy.signal butter filter
    '''
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return b, a


def butter_bandpass_filter(data, lowcut, highcut, fs, order=5):
    '''butter bandpass filter

    Code copied from 
    https://stackoverflow.com/questions/12093594/how-to-implement-band-pass-butterworth-filter-with-scipy-signal-butter

    Keyword arguments:
    data -- data to be filtered
    lowcut -- low frequency cut in Hz
    highcut -- high frequency cut in Hz
    fs -- frequency in Hz at which samples were taken
    order -- order of the butter filter

    Returns
    filtered signal
    '''
    b, a = butter_bandpass(lowcut, highcut, fs, order=order)
    y = lfilter(b, a, data)
    return y


def plotdata(results, saveplot=False):
    '''plots frequency, time from results collected

    Four plots are made; time plot of accelerometer signal, amplitude spectrum of accelerometer signal
    time plot of infrared signal, amplitude specturm of infrared signal.

    Keyword arguments:
    results -- dictionary resulting from the main.main function
    saveplot -- wether the plot has to be saved to disk
    '''
    # on headless system, a plot cannot be made so library should not
    # be required
    import matplotlib.pyplot as plt
    def plottime(data, ax):
        t = [t*(1/results['sample_freq']) for t in range(len(data))]
        ax.plot(t, data)
        ax.grid()
        ax.set_xlabel('Time')

    def plotfrequency(data, ax):
        T = 1/results['sample_freq']
        N = len(data)
        xf = np.linspace(0.0, 1.0/(2.0*T), N//2)
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


def fitsinusoid(signal, fest, fs, debug=False):
    '''fits a sinusoid on top of a signal

    This sinusoidtion tries to exploit all accelerometer measurements.
    Code was inspired from;
    https://electronics.stackexchange.com/questions/311098/ways-of-estimating-phase-shift

    Keyword arguments:
    signal -- signal to fit sinusoid on
    fest -- estimated frot of the sinusoid
    fs -- sample frot
    debug -- create fake signal with debug as phase shift

    Returns:
    The frot and the phase shift found
    '''
    N = len(signal)
    T = 1/fs
    x = np.linspace(0.0, N*T, N)

    if debug:
        print("debug activated")
        phasediff = np.pi*debug
        #phasediff = 0
        #timeshift = round(debug/T)
        x = np.linspace(0.0, N*T, N)
        signal = np.sin(fest*2*np.pi*x+phasediff)

    sinusoid = lambda x, A, phasediff: A*np.sin(fest*2*np.pi*x+phasediff)

    popt, pcov = curve_fit(sinusoid, x, signal, bounds=([0.8*max(np.abs(signal)), 0],
            [1.2*max(np.abs(signal)), 2*np.pi]))
    A, phase = *popt,
    return A, phase


def getdetails(measurement, flt=True, verbose=True, arithmic=False):
    '''estimate rotor rotor frequency, force and putty location from measurements

    Rotor frot is estimated from the time difference between subsequent
    rising edges of the infrared signal.
    Accelerometer phase is estimated from the maximum and minimum position in 
    each cycle. The difference between these two signals should be 180 degrees.
    Measurments are repeatable but the results will can so far not be linked to 
    the real putty location or weight.

    Keyword arguments:
    measurement -- dictionary resulting from the main.main function
    filter -- if true aplies bandpass butterworth filter
    verbose -- if true prints information
    arithmic -- if true use arithmic approach false use function fit

    Returns:
    Dictionary with keys rotor frequency in hertz, force in arbritrary units
    and phase in degrees
    '''
    results = dict.fromkeys({'frot','force','deg'})
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
    if np.abs(np.max(cycle_time)-np.min(cycle_time))>2 and verbose:
        print("Min freq {:.2f} ".format(measurement['sample_freq']/max(cycle_time)))
        print("Max freq {:.2f} ".format(measurement['sample_freq']/min(cycle_time)))
        print("WARNING: Rotor frequency seems not constant")
        # check the signal --> something could be off
    results['frot'] = measurement['sample_freq'] / samples_per_period
    # filter improves repeatability of phase shift for different speeds
    if flt:
        low = 0.9*measurement['sample_freq']/max(cycle_time)
        high = 1.1*measurement['sample_freq']/min(cycle_time)
        ac_meas = list(butter_bandpass_filter(measurement['ac_meas'], low,
                       high, measurement['sample_freq'], order=6))
    else:
        ac_meas = measurement['ac_meas']
    pos_max, pos_min = [], []
    force = []
    Al, phasel = [], []
    for index in range(len(start_ind)-1):
        lst = ac_meas[start_ind[index]:start_ind[index+1]]
        if arithmic:
            pos_max.append(lst.index(max(lst))/len(lst)*360)
            pos_min.append(lst.index(min(lst))/len(lst)*360)
            force.append((max(lst)-min(lst))/2)
        else:
            frotest = measurement['sample_freq'] / len(lst)
            A, phase = fitsinusoid(lst, frotest, measurement['sample_freq'])
            Al.append(A)
            phasel.append(phase)
    if arithmic:
        results['force'] = np.mean(force)
        max_deg = np.mean(pos_max)
        min_deg = np.mean(pos_min)
        if np.abs(np.abs(max_deg-min_deg)-180)>5 and verbose:
            print("Max degree {:.2f}".format(max_deg))
            print("Min degree {:.2f}".format(min_deg))
            print("WARNING: Degree measurement seems inaccurate")
        results['deg'] = min_deg
    else:
        results['force'] = np.mean(Al)    
        results['deg'] = np.mean(phasel)/(2*np.pi)*360
 
    if verbose:
        print("Rotor frequency is {:.0f} Hz".format(results['frot']))
        print("Force is {:.2f} a.u.".format(results['force'] ))
        print("Phase is {:.2f} degrees".format(results['deg']))
    return results


def crosscorrelate(results, low, high, rotor, debug = False):
    '''obtains the difference in phase between the accelerometer an ir signal
    
    The function has been tested and produces reproducable results.
    The result is not very accurate. With a sample frequency of 952 Hertz and a rotor frequency of 
    100 Hertz, rouglhy 9.5 measurements are available per period so the outcome in degrees is not accurate
    Therefore the function get details was developped and this is used as alternative.
    In the code there is also the option to use a fake signal.
    Code was copied from;
    https://stackoverflow.com/questions/6157791/find-phase-difference-between-two-inharmonic-

    Keyword arguments:
    results -- dictionary resulting from the main.main function
    low -- low frequency cut in Hz, used to filter noise, should be lower than rotor frequency
    high -- high frequency cut in Hz, used to filter noise, should higher than rotor frequency
    rotor -- frequency at which the rotor is thought to rotate
    debug -- makes fake ac_meas and ir_meas signals, used to test code
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

