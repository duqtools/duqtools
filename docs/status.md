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
: Name of the status file. (default: `jetto.status`)

`in_file`
: Name of the modelling input file, will be used to checkif the subprocess has started. (default: `jetto.in`)

`out_file`
: Name of the modelling output file, will be used tocheck if the software is running. (default: `jetto.out`)

`msg_completed`
: Parse `status_file` for this message to check forcompletion. (default: `Status : Completed successfully`)

`msg_failed`
: Parse `status_file` for this message to check forfailures. (default: `Status : Failed`)

`msg_running`
: Parse `status_file` for this message to check forrunning status. (default: `Status : Running`)

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
