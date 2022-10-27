import matplotlib.pyplot as plt

from duqtools.api import ImasHandle

handle = ImasHandle.from_string('g2vazizi/jet/94875/8000')

x_var = 'rho_tor_norm'
y_var = 'zeff'
time_var = 'time'

dataset = handle.get_variables(variables=(x_var, y_var, time_var))

fig = dataset.plot.scatter(x_var, y_var, hue='time', marker='.')

plt.show()
