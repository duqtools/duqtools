from duqtools.api import ImasHandle, alt_line_chart

handle = ImasHandle.from_string('g2vazizi/jet/94875/8000')

x_var = 'rho_tor_norm'
y_var = 't_i_ave'

dataset = handle.get_variables(variables=(x_var, y_var))

chart = alt_line_chart(dataset, x=x_var, y=y_var)

chart.save('chart.html', scale_factor=2.0)
