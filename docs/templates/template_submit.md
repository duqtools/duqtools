# Submit

The submit subcommand submits all the runs to the job queuing system.

To run the command:

`duqtools submit`

Check out [the command-line interface](../command-line-interface.md#clean) for more info on how to use this command.

<script id="asciicast-c38VezQBpzKnU5r4zpn51A9G1" src="https://asciinema.org/a/c38VezQBpzKnU5r4zpn51A9G1.js" async></script>

## The System specific `submit` config

{{ schema_SubmitConfigModel['description'] }}

{% for name, prop in schema_SubmitConfigModel['properties'].items() %}
`{{ name }}`
: {{ prop['description'] }}
{% endfor %}

!!! note

    In addition, `submit` uses `system.status_file` to prevent re-submitting a running job.

### Example

```yaml title="duqtools.yaml"
system:
  name: jetto
  submit_command: sbatch
  submit_script_name: .llcmd
```
