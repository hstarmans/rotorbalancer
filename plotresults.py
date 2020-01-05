import pickle
import matplotlib.pyplot as plt


def readplotdata():
    dct = pickle.load(open('results.p', 'rb'))
    for key, value in dct.items():
        print(key)

def plotdata():
    dct = pickle.load(open('results.p', 'rb'))
    tpassed = dct['tpassed']
    values = dct['values']
    x_accel = values[0]
    rps = dct['rps']
    revfraction = []
    for i in range(len(x_accel)):
        revolution = i/len(x_accel)*tpassed*rps
        if revolution < 3:
            revfract = revolution%1
            revfraction.append(revfract)
    plt.plot(revfraction, x_accel[0:len(revfraction)], 'ro')
    plt.show()


plotdata()