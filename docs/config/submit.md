# Submit

The submit subcommand submits all the runs to the job queuing system.

To run the command:

`duqtools submit`

Check out [the command-line interface](/command-line-interface/#clean) for more info on how to use this command.


## The `submit` config

The options of the `submit` subcommand are stored under the `submit` key
in the config.

The config describes the commands to start the UQ runs.


`submit_script_name`
: Name of the submission script.

`submit_command`
: Submission command.


!!! note

    In addition, `submit` uses `status.status_file` to prevent re-submitting a running job.

### Example

```yaml title="duqtools.yaml"
submit:
  submit_command: sbatch
  submit_script_name: .llcmd
```
