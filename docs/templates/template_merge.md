# Merge

The merge subcommand can merge the different runs to a single IMAS db entry, using error
propagation to merge the fields specified.

To run the command:

`duqtools merge`

Check out [the command-line interface](../command-line-interface.md#merge) for more info on how to use this command.


## The `merge` config

{{ schema_MergeConfigModel['description'] }}

{% for name, prop in schema_MergeConfigModel['properties'].items() %}
`{{ name }}`
: {{ prop['description'] }}
{% endfor %}

For example:

```yaml title="duqtools.yaml"
merge:
  data: runs.yaml
  output:
    db: jet
    run: 9999
    shot: 94785
  plan:
  - data_variables:
    - t_i_ave
    - zeff
    grid_variable: rho_tor_norm
    time_variable: time
  template:
    db: jet
    run: 1
    shot: 94785
    user: stef
```

## Template and output locations

Both are specified using the IMAS scheme.

{% for name, prop in schema_ImasBaseModel['properties'].items() %}
`{{ name }}`
: {{ prop['description'] }}
{% endfor %}

For example:

```yaml title="duqtools.yaml"
template:
  user: g2ssmee
  db: jet
  shot: 91234
  run: 1
output:
  db: jet
  shot: 91234
  run: 100
```

!!! note

    Although the user can be specified for the output location, it is best left blank. In this case, the current user is filled in automatically and you will not run into issues with write permissions.


## Merge plan

{{ schema_MergeStep['description'] }}

{% for name, prop in schema_MergeStep['properties'].items() %}
`{{ name }}`
: {{ prop['description'] }}
{% endfor %}

For example:

```yaml title="duqtools.yaml"
template:
  user: g2ssmee
  db: jet
  shot: 91234
  run: 1
output:
  db: jet
  shot: 91234
  run: 100
```

For example:

```yaml title="duqtools.yaml"
plan:
- grid_variable: rho_tor_norm
  variables:
  - time
  - t_i_ave
  - zeff
```


!!! note

    In the current version of duqtools, the *time* coordinate variable must be specified here, even though it won't be merged. This will change in a future version of duqtools.
