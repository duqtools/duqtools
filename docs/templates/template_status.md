# Status

The status subcommand reports the status of the UQ runs.

To run the command:

`duqtools status`

Check out [the command-line interface](../command-line-interface.md#status) for more info on how to use this command.

<script id="asciicast-7XzFEahphaZdewNw7LBE2IuZc" src="https://asciinema.org/a/7XzFEahphaZdewNw7LBE2IuZc.js" async></script>

## The `status` config

{{ schema_StatusConfigModel['description'] }}

{% for name, prop in schema_StatusConfigModel['properties'].items() %}
`{{ name }}`
: {{ prop['description'] }}
{% endfor %}

!!! note

    Both `out_file` and `in_file` may be parsed to track the progress of the individual runs.

### Example

```yaml title="duqtools.yaml"
status:
  in_file: jetto.in
  msg_completed: 'Status : Completed successfully'
  msg_failed: 'Status : Failed'
  msg_running: 'Status : Running'
  out_file: jetto.out
  status_file: jetto.status
```
