# Plot

The plot subcommand generates plots.

To run the command:

`duqtools plot`

Check out [the command-line interface](/command-line-interface/#plot) for more info on how to use this command.


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


`x`
: IDS of the data to plot on the x-axis, default is rho-toroidal.

`y`
: IDS of the data to plot on the y-axis

`xlabel`
: Custom label for x-axis

`ylabel`
: Custom label for y-axis

!!! note

    Multiple plots can be specified by adding new plot specifications. The example above generates 2 plots, one for the *rho_tor* vs. *density_thermal*, and one for *rho_tor* vs *t_i_average*.
