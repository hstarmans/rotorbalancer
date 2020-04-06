# template function to detect phase shift


import numpy as np


def getdetails(measurement):
    previous = None
    start_ind = [] 
    # detect rising edges & store indices
    for indx, val in enumerate(measurement['ir_meas']):
        if (previous != None) & (val-previous == 1):
            start_ind.append(indx)
    samples_per_period = (start_ind[-1]-start_ind[0])/len(start_ind)
    frequency = measurement['sample_freq'] / samples_per_period
    print("Frequency is {}".format(frequency))
    # for each period detect position minimum and maximum
    pos_max, pos_min = [], []
    for index in range(len(start_ind)-1):
        lst = measurement['ac_meas'][start_ind[index]:start_ind[index+1]]
        pos_max.append(lst.index(max(lst))-start_ind[index])
        pos_min.append(lst.index(min(lst))-start_ind[index])
    def todegrees(positions):
        pos_time = np.mean(positions)/measurement['sample_freq'] 
        degrees  = pos_time/(1/frequency)*360
        return degrees
    print("Max Degrees {}".format(todegrees(pos_max)))
    print("Min Degrees {}".format(todegrees(pos_min)))

