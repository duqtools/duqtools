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
  variables:
    - t_i_ave
    - zeff
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
