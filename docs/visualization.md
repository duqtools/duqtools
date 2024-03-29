# Visualization

The plot subcommand can be used as a general purpose IMAS plotting tool.

To run the command:

`duqtools plot`

Check out [the command-line interface](./command-line-interface.md#plot) for more info on how to use this command.

This page shows some examples on how to use the plotting tool.

## Plotting IMAS data

`duqtools plot` can be used as general IMAS plotting tool.

The following command will plot `rho_tor_norm` against `t_i_ave`. The way this works is that `t_i_ave` is retrieved through the [variables module](./variables.md), so it knows where to load the data and the dimensions of the variable.

```bash
duqtools plot -v t_i_ave --handle g2ssmee/jet/94875/8000
```

The tool uses [altair](https://altair-viz.github.io/) to render the visualization, which in is based on on [Vega](https://vega.github.io/vega) and [Vega-Lite](https://vega.github.io/vega-lite). This means the plot is stored as an html file (`chart_x.html`).

Multiple data sets can be plotted by repeating the IMAS path.

```bash
duqtools plot -v t_i_ave \
    --handle jet/94875/8000 \
    --handle jet/94875/8001 \
    --handle jet/94875/8002
```

Note that the username is omitted from the imas path (`--handle jet/94875/8000`). When the user is left out, the current user is assumed. The equivalent way to write this would be: `--handle g2ssmee/jet/94875/8000`.

In addition, you can generate multiple charts by adding more *variables*. This is more efficient for large data sets, because the data has to be loaded only once.

```bash
duqtools plot \
    -v n_e_tot \
    -v t_e \
    --handle jet/94875/8000 \
    --handle jet/94875/8001 \
    --handle jet/94875/8002
```

## Data from UQ runs

You can also read data from `runs.yaml`, which is generated by *duqtools* after a UQ run.

```bash
duqtools plot \
    -v t_i_ave \
    -i runs.yaml
```

In fact, you can freely combine the different inputs, for example if you want to compare your output to some reference data.

```bash
duqtools plot \
    -v t_i_ave \
    -i runs.yaml \
    --handle jet/94875/8000
```

## From a CSV file

Data can also be specified using a CSV file. Check the [dashboard](./dash.md#from-a-csv-file) documentation for more info on how to construct this file.

```bash
duqtools plot \
    -v t_i_ave \
    -i data.csv
```
