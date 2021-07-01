# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.5.2
#   kernelspec:
#     display_name: Python [conda env:dalry]
#     language: python
#     name: conda-env-dalry-py
# ---

# %matplotlib widget
from rotorbalancer import calc

# Let's look at a plot of the polygon motor with AN44000A chip and an unbalanced 30x30x2 mm square prism.  
# A clear peak is present at 50 Hertz for both the acceleration and infrared spectrum.
# The rotor is pulsed at a frequency of 10 Hertz.

dct = calc.read_file('without_weight/100.p')
calc.plotdata(dct)
calc.rotfreq_and_force(dct)

# The measurement is stable within 10 percent margin.  
# The rotor drifts between 50-60 Hertz.  It does not reach the same frequency every time.

from rotorbalancer import tools
tools.loadfiles('without_weight').describe()

# Adding a balance weight, reduces the amplitude.  
# The amplitude is not always detected correcly from the accelerometer plot.  
# This can be seen at the large standard deviation from the frequency plot.

from rotorbalancer import tools
tools.loadfiles('weight').describe()

# At 5 Hertz, the rotor is more stable.

from rotorbalancer import tools
tools.loadfiles('weight_5').describe()
