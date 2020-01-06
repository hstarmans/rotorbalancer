import pickle
import matplotlib.pyplot as plt
import scipy.fftpack
import numpy as np


def readplotdata():
    dct = pickle.load(open('results.p', 'rb'))
    for key, value in dct.items():
        print(key)
    # values = dct['values']
    # x_accel = values[0]
    # print(x_accel[1:30])

def plotdata():
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
    T = tpassed/len(x_accel)
    N = len(x_accel)
    xf = np.linspace(0.0, 1.0/(2.0*T), N/2)
    #plt.plot(xf, 2.0/N*np.abs(yf[:N//2]))
    plt.plot(xf, 2.0/N*np.angle(yf[:N//2]))
    plt.show()


plotdata()