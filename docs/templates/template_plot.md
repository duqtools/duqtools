# Plot

The plot subcommand generates plots.

To run the command:

`duqtools plot`

Check out [the command-line interface](/command-line-interface/#plot) for more info on how to use this command.


## The `plot` config

{{ schema['description'] }}

{% for name, prop in schema['properties'].items() %}
`{{ name }}`
: {{ prop['description'] }}
{% endfor %}

!!! note

    Multiple plots can be specified by adding new plot specifications. The example above generates 2 plots, one for the *rho_tor* vs. *density_thermal*, and one for *rho_tor* vs *t_i_average*.


### Example

```yaml title="duqtools.yaml"
{{ yaml_example }}
```
