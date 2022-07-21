# Create

The create subcommand creates the UQ run files.

To run the command:

`duqtools create`

Check out [the command-line interface](/command-line-interface/#create) for more info on how to use this command.


## The `create` config

{{ schema['description'] }}

{% for name, prop in schema['properties'].items() %}
`{{ name }}`
: {{ prop['description'] }}
{% endfor %}

For example:

```yaml title="duqtools.yaml"
{{ yaml_example }}
```


## Specify the template data

By default the template IMAS data to modify is extracted from the path specified in the `template` field.

```yaml title="duqtools.yaml"
template: /pfs/work/stef/jetto/runs/duqtools_template
```

In some cases, it may be useful to re-use the same set of model settings, but with different input data. If the `template_data` field is specified, these data will be used instead. To do so, specify `template_data` with the fields below:

{% for name, prop in imas_basemodel_schema['properties'].items() %}
`{{ name }}`
: {{ prop['description'] }}
{% endfor %}

For example:

```yaml title="duqtools.yaml"
template: /pfs/work/g2ssmee/jetto/runs/duqtools_template
template_data:
  user: g2ssmee
  db: jet
  shot: 91234
  run: 5
```


## Data location

{{ data_loc_schema['description'] }}

{% for name, prop in data_loc_schema['properties'].items() %}
`{{ name }}`
: {{ prop['description'] }}
{% endfor %}

For example:

```yaml title="duqtools.yaml"
{{ data_loc_yaml }}
```

## Dimensions

These instructions operate on the template model. Note that these are compound operations, so they are expanded to fill the matrix with possible entries for data modifications (depending on the sampling method).

### Arithmetic operations

{{ ops_schema['description'] }}

{% for name, prop in ops_schema['properties'].items() %}
`{{ name }}`
: {{ prop['description'] }}
{% endfor %}

For example:

```yaml title="duqtools.yaml"
ids: zeff
operator: add
values: [0.01, 0.02, 0.03]
```

will generate 3 entries, `zeff += 0.01`, `zeff += 0.02`, and `zeff += 0.03`.

```yaml title="duqtools.yaml"
ids: profiles_1d/0/t_i_average
operator: multiply
values: [1.1, 1.2, 1.3]
```

will generate another 3 entries, `t_i_average *= 1.1`, `t_i_average *= 1.2`, and `t_i_average *= 1.3`.

With these 2 entries, the parameter hypercube would consist of 9 entries total (3 for `zeff`
times 3 for `t_i_average`).
With the default `sampler: latin-hypercube`, this means 9 new data files will be written.

!!! note

    The python equivalent is essentially `np.<operator>(ids, value, out=ids)` for each of the given values.

### Specify value ranges

Although it is possible to specify value ranges explicitly in an operator, sometimes it may be easier to specify a range.

There are two ways to specify ranges in *duqtools*.

#### By number of samples

{{ linspace_schema['description'] }}

{% for name, prop in linspace_schema['properties'].items() %}
`{{ name }}`
: {{ prop['description'] }}
{% endfor %}

This example generates a range from 0.7 to 1.3 with 10 steps:

```yaml title="duqtools.yaml"
ids: profiles_1d/0/t_i_average
operator: multiply
values:
  start: 0.7
  stop: 1.3
  num: 10
```

#### By stepsize

{{ arange_schema['description'] }}

{% for name, prop in linspace_schema['properties'].items() %}
`{{ name }}`
: {{ prop['description'] }}
{% endfor %}

This example generates a range from 0.7 to 1.3 with steps of 0.1:

```yaml title="duqtools.yaml"
ids: profiles_1d/0/t_i_average
operator: multiply
values:
  start: 0.7
  stop: 1.3
  step: 0.1
```

### Sampling between error bounds

The following example takes `electrons/temperature`, and generates a range from $-2\sigma$ to $+2\sigma$ with defined steps:

```yaml title="duqtools.yaml"
ids: profiles_1d/0/electrons/temperature
operator: add
values: [-2, -1, 0, 1, 2]
scale_to_error: True
```

The following example takes `t_i_average`, and generates a range from $-3\sigma$ to $+3\sigma$ with 10 equivalent steps:

```yaml title="duqtools.yaml"
ids: profiles_1d/0/t_i_average
operator: add
values:
  start: -3
  stop: 3
  num: 10
scale_to_error: True
```

!!! note

    When you specify a sigma range, make sure you use `add` as the operator. While the other operators are also supported, they do not make much sense in this context.
