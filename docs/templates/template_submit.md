# Submit

The submit subcommand submits all the runs to the job queuing system.

To run the command:

`duqtools submit`

Check out [the command-line interface](/command-line-interface/#clean) for more info on how to use this command.


## The `submit` config

{{ schema['description'] }}

{% for name, prop in schema['properties'].items() %}
`{{ name }}`
: {{ prop['description'] }}
{% endfor %}

!!! note

    In addition, `submit` uses `status.status_file` to prevent re-submitting a running job.

### Example

```yaml title="duqtools.yaml"
{{ yaml_example }}
```
