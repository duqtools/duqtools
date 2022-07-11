# Plot

The plot subcommand generates plots.

To run the command:

`duqtools plot`


::: mkdocs-click
    :module: duqtools.cli
    :command: cli_plot
    :style: table
    :depth: 2


## The `plot` config

The options of the plot subcommand are stored under the `plot` key in the config. The plots will be stored as png files in the current directory.

For example:

```yaml title="duqtools.yaml"
plots:
  - x:
    y: profiles_1d/0/electrons/density_thermal
    xlabel:
    ylabel:
  - x: profiles_1d/0/grid/rho_tor
    y: profiles_1d/0/t_i_average
    xlabel: Rho tor.
    ylabel: Ion temperature
```


`x`: Path of the data to plot on the x-axis, default is rho-toroidal.

`y`: Path of the data to plot on the y-axis

`xlabel`: # custom label for x-axis

`ylabel`: # custom label for y-axis

!!! note

    Multiple plots can be specified by adding new plot specifications. The example above generates 2 plots, one for the *rho_tor* vs. *density_thermal*, and one for *rho_tor* vs *t_i_average*.
