import pickle
from os.path import join

from . import main
from . import calc

folder = 'measurements'


def runtest():
    '''run main.main function over range of frequencies and multiple times'''
    for f in range(11, 101, 10):
        print("measuring {}".format(f))
        for i in range(0, 1):
            print("cycle {}".format(i))
            res = main.main(frequency=f)
            filename = join(folder, str(f)+str(i)+'.p')
            pickle.dump(res, open(filename, 'wb'))


def loadfiles(flt, verbose, arithmic):
    '''load measurements and get dataframe with results

    Keyword arguments are applied to get details functions
    Returns:
    Dataframe with rows; rotor frequency, forse and phase in degrees
    '''
    import pandas as pd
    df = None
    for f in range(10, 21):
        for i in range(0, 10):
            filename = join(folder, str(f)+str(i)+'.p')
            dct = pickle.load(open(filename, 'rb'))
            # first 0.1 second selected
            # quickly dampens out so only holds for first 0.1 second
            # dct['ac_meas'] = dct['ac_meas'][50:150]
            # dct['ir_meas'] = dct['ir_meas'][50:150]
            results = pd.DataFrame(calc.getdetails(dct,
                                                   flt=flt,
                                                   verbose=verbose,
                                                   arithmic=arithmic),
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
