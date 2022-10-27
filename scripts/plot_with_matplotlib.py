from duqtools.api import ImasHandle

handle = ImasHandle.from_string('g2vazizi/jet/94875/8000')

x_var = 'rho_tor_norm'
y_var = 'zeff'

dataset = handle.get_variables(variables=(x_var, y_var))

# MPL stuff
