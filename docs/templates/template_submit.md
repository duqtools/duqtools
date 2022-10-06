# Submit

The submit subcommand submits all the runs to the job queuing system.

To run the command:

`duqtools submit`

Check out [the command-line interface](/command-line-interface#clean) for more info on how to use this command.


## The `submit` config

{{ schema_SubmitConfigModel['description'] }}

{% for name, prop in schema_SubmitConfigModel['properties'].items() %}
`{{ name }}`
: {{ prop['description'] }}
{% endfor %}

!!! note

    In addition, `submit` uses `status.status_file` to prevent re-submitting a running job.

### Example

```yaml title="duqtools.yaml"
submit:
  submit_command: sbatch
  submit_script_name: .llcmd
```
