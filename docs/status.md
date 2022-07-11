# Status

The status subcommand reports the status of the UQ runs.

To run the command:

`duqtools status`

::: mkdocs-click
    :module: duqtools.cli
    :command: cli_status
    :style: table
    :depth: 2

## The `status` config

The options of the status subcommand are stored under the `status` key in the config. These only need to be changed if the modeling softare changes.


```yaml title="duqtools.yaml"
status:
  status_file: jetto.status
  msg_completed: 'Status : Completed successfully'
  msg_failed: 'Status : Failed'
  msg_running: 'Status : Running'
  out_file: jetto.out
  in_file: jetto.in
```

`status_file`: Name of the status file, for jetto: `jetto.status`

`msg_completed`: Parse `status_file` for this message to check whether the process has completed.

`msg_failed`: Parse `status_file` for this message to check whether the process has failed.

`msg_running`: Parse `status_file` for this message to check whether the process is still running.

`out_file`: Name of the modelling output file, will be used to check if the software is running

`in_file`: Name of the modelling output file, will be used to check if the software has started

Both `out_file` and `in_file` may be parsed to track the progress of the individual runs.
