# Variables

Jetto and other system related variables and mappings are handled by duqtools.

The variable lookup table maps variable names, and specifies their location in different config files. The lookup file is stored in yaml format, typically with the name `variables*.yaml`. Duqtools includes a default [variables.yaml](https://github.com/duqtools/duqtools/blob/main/src/duqtools/data/variables.yaml), but you can also define your own.

Duqtools looks for files matching `variables*.yaml` in the following locations, in this order:

1. Via environment variable `$DUQTOOLS_VARIABLES`
2. If not defined, look for `$XDG_CONFIG_HOME/duqtools/variables*.yaml`
3. If `$XDG_CONFIG_HOME` is not defined, look for `$HOME/.config/duqtools/variables*.yaml`
4. If not defined, fall back to the included [variables*.yaml](https://github.com/duqtools/duqtools/tree/main/src/duqtools/data), which contains a sensible list of defaults.

!!! note

    To access different data variables, duqtools must know how to navigate the IMAS specification. Since duqtools 3.0.0, [imas2xarray](https://imas2xarray.readthedocs.io) handles the IDS data variables. Please check its documentation for more information.

## System variables

For system variables, check out the system subsection.

- [Jetto](./jetto/jetto_variables.md)
