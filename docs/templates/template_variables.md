# Variables

To access different variables, duqtools must know how to navigate the IMAS specification. The variable lookup table maps variable names, and specifies their dimensions. The lookup file is stored in yaml format, typically with the name `variables.yaml`. Duqtools includes a default [variables.yaml](https://github.com/duqtools/duqtools/blob/main/src/duqtools/data/variables.yaml), but you can also define your own.

Duqtools looks for the `variables.yaml` file in the following locations, in this order:

1. Via environment variable `$DUQTOOLS_VARIABLES`
2. If not defined, look for `$XDG_CONFIG_HOME/duqtools/variables.yaml`
3. If `$XDG_CONFIG_HOME` is not defined, look for `$HOME/.config/duqtools/variables.yaml`
4. If not defined, fall back to the included [variables.yaml](https://github.com/duqtools/duqtools/blob/main/src/duqtools/data/variables.yaml), which contains a sensible list of defaults.

## Squashing data

In the list below, you will find variables prefixed `$`. This means that these variables are squashed when loaded by *duqtools* to make sure that their dimensions are consistent. For example, grid variables like `rho_tor_norm` differ slightly between time steps. Therefore we first assign this to a placeholder dimension by prefixing `$`: `$rho_tor_norm`. Duqtools knows to squash this dimension and make `rho_tor_norm` consistent for all time steps. It does this by rebasing all data to the grid of the first time step. We call this squashing, because it removes a dimension from the dataset and turns it into a coordinate.

## Default variables

The default duqtools variables are listed below.

{% for name in ids_vars %}
- [IDS: {{ name }}](#ids-{{ name }})
{% endfor %}
{% for name in other_vars %}
- [{{ name }}s](#{{ name | lower }}s)
{% endfor %}

{% for name, var_group in ids_vars.items() %}
### IDS: {{ name }}

{% for var in var_group %}

#### {{ var.name }}
```yaml
{{ var | to_yaml_str }}
```
{% endfor %}
{% endfor %}


{% for name, var_group in other_vars.items() %}
### {{ name }}s

{% for var in var_group %}

#### {{ var.name }}
```yaml
{{ var | to_yaml_str }}
```

{% endfor %}
{% endfor %}
