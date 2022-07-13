# Status

The status subcommand reports the status of the UQ runs.

To run the command:

`duqtools status`

Check out [the command-line interface](/command-line-interface/#status) for more info on how to use this command.


## The `status` config

The options of the `status` subcommand are stored under the `status` key
in the config.

These only need to be changed if the modeling software changes.


`status_file`
: Name of the status file.

`in_file`
: Name of the modelling input file, will be used to check if the subprocess has started.

`out_file`
: Name of the modelling output file, will be used to check if the software is running.

`msg_completed`
: Parse `status_file` for this message to check for completion.

`msg_failed`
: Parse `status_file` for this message to check for failures.

`msg_running`
: Parse `status_file` for this message to check for running status.


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
