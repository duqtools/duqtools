# Plot

The plot subcommand generates plots.

To run the command:

`duqtools plot`

Check out [the command-line interface](/command-line-interface/#plot) for more info on how to use this command.


## The `plot` config

The options of the plot subcommand are stored under the `plot` key in
the config.

Plots are specified as a list under the `plots` key. Multiple plots
can be defined, and they will be written sequentially as .png files
to the current working directory.


`x`
: IDS of the data to plot on the x-axis, default is rho toroidal norm.

`y`
: IDS of the data to plot on the y-axis

`xlabel`
: Custom label for x-axis

`ylabel`
: Custom label for y-axis


!!! note

    Multiple plots can be specified by adding new plot specifications. The example above generates 2 plots, one for the *rho_tor* vs. *density_thermal*, and one for *rho_tor* vs *t_i_average*.


### Example

```yaml title="duqtools.yaml"
plot:
  plots:
  - x: profiles_1d/0/grid/rho_tor_norm
    y: profiles_1d/0/electrons/density_thermal
  - x: profiles_1d/0/grid/rho_tor_norm
    xlabel: Rho tor.
    y: profiles_1d/0/t_i_average
    ylabel: Ion temperature
```
