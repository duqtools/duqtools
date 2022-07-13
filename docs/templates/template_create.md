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

### Example

```yaml title="duqtools.yaml"
{{ yaml_example }}
```

### IDS operations

These instructions operate on the template model. Note that these are compound operations, so they are expanded to fill the matrix with possible entries for data modifications (depending on the sampling method).

#### Arithmetic operations

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

#### Error bound sampling

{{ sampler_schema['description'] }}

{% for name, prop in sampler_schema['properties'].items() %}
`{{ name }}`
: {{ prop['description'] }}
{% endfor %}

Example:

```yaml title="duqtools.yaml"
ids: profiles_1d/0/q
sampling: normal
bounds: symmetric
n_samples: 5
```

!!! note

     Note that the example above adds 5 (`n_samples`) entries to the matrix. This is independent from the hypercube sampling above.
