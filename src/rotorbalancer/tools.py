import os
from os.path import dirname
from pathlib import Path
import pickle


from . import main
from . import calc

root_folder = Path(dirname(dirname(dirname(__file__))),
                   'measurements')


def runtest(starthz, endhz, stephz, foldername, repeat=1):
    '''store infrared and accelerometer for a range of frequencies

    starthz -- start frequency [Hz]
    endhz -- end frequency [Hz]
    stephz -- step frequency [Hz]
    repeat -- time to repeat measurement
    '''
    for f in range(starthz, endhz, stephz):
        print(f"measuring {f} Hz")
        for i in range(0, repeat):
            print(f"Cycle {i}")
            res = main.main(frequency=f)
            filename = Path(root_folder, foldername, str(f)+str(i)+'.p')
            pickle.dump(res, open(filename, 'wb'))


def loadfiles(folder=None):
    '''load measurements and get dataframe with results

    Keyword arguments are applied to get details functions

    flt -- true applies bandpass butterwoth filter
    verbose -- print debugging information
    arithmic -- arithmic approach for fit
    folder -- specify subfolder in measurements folder

    Returns:
    Dataframe with rows; rotor frequency, force and phase in degrees
    '''
    import pandas as pd
    if folder:
        folder = Path(root_folder, folder)
    else:
        folder = root_folder

    files = [f for f in os.listdir(folder) if f.endswith('.p')]

    df = None
    for f in files:
        # filename = join(folder, str(f)+str(i)+'.p')
        dct = pickle.load(open(Path(folder, f), 'rb'))
        # first 0.1 second selected
        # quickly dampens out so only holds for first 0.1 second
        # dct['ac_meas'] = dct['ac_meas'][50:150]
        # dct['ir_meas'] = dct['ir_meas'][50:150]
        results = pd.DataFrame(calc.rotfreq_and_force(dct),
                               index=[0])
        df = results if df is None else pd.concat([df, results])
    return df


def plotfiles(df):
    '''plot dataframe from load files'''
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(nrows=1,
                             ncols=2,
                             figsize=(12, 8))
    fig.canvas.set_window_title("Degree and force plotted vs rotor frequency")
    # plot two columns with respect to each other
    axes[0].scatter(df['frot'], df['force'])
    axes[0].title.set_text('Force vs rotor frequency')
    axes[0].set(xlabel='Mean rotor frequency (Hz)', ylabel='Force (a.u.)')
    axes[0].grid()
    axes[1].scatter(df['frot'], df['deg'])
    axes[1].title.set_text('Phase vs rotor frequency')
    axes[1].set(xlabel='Mean rotor frequency (Hz)', ylabel='Phase (Degrees)')
    axes[1].grid()
    plt.show()
