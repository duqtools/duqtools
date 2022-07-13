# Status

The status subcommand reports the status of the UQ runs.

To run the command:

`duqtools status`

Check out [the command-line interface](/command-line-interface/#status) for more info on how to use this command.


## The `status` config

{{ schema['description'] }}

{% for name, prop in schema['properties'].items() %}
`{{ name }}`
: {{ prop['description'] }}
{% endfor %}

!!! note

    Both `out_file` and `in_file` may be parsed to track the progress of the individual runs.

### Example

```yaml title="duqtools.yaml"
{{ yaml_example }}
```
