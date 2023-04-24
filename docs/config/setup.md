# Setup

The setup subcommand takes a config template and turns it into a valid duqtools config.

To run the command:

`duqtools setup`

Check out [the command-line interface](../command-line-interface.md#setup) for more info on how to use this command.

## The `setup` template

Unlike most of the other commands, `duqtools` setup does not require a config file, it *creates* the config file for you.

You can pass the IMAS handle to use as `template_data`, the run name (this defines the name of the run directory) and the template file (defaults to `duqtools.template.yaml`):

```bash
duqtools setup --handle user/db/123/456 --run_name my_run --template duqtools.template.yaml
# -> creates duqtools.yaml
```

Depending on the the template, `duqtools` can automatically fill in some machine specific parameters from the IMAS handle, for example, the start time, end time, B-field and major radius.

### Example `duqtools.template.yaml`:

This is what a template file could look like:

```yaml title="duqtools.template.yaml"
create:
  runs_dir: /afs/eufus.eu/user/g/g2ssmee/jetto_runs/duqduq/{{ run.name }}
  template: /pfs/work/g2aho/jetto/runs/runparallel/jet90350/interpretive_esco02/
  template_data:
    user: {{ handle.user }}
    db: {{ handle.db }}
    shot: {{ handle.shot }}
    run: {{ handle.run }}
  operations:
    - variable: major_radius
      operator: copyto
      value: {{ variables.major_radius | round(4) }}
    - variable: b_field
      operator: copyto
      value: {{ variables.b_field | round(4) }}
    - variable: t_start
      operator: copyto
      value: {{ variables.t_start | round(4) }}
    - variable: t_end
      operator: copyto
      value: {{ (variables.t_start + 0.01) | round(4) }}
  sampler:
    method: latin-hypercube
    n_samples: 25
  dimensions:
    - variable: zeff
      operator: multiply
      values: [0.8, 0.9, 1.0, 1.1, 1.2]
    - variable: t_e
      operator: multiply
      values: [0.8, 0.9, 1.0, 1.1, 1.2]
system: jetto
```


### Placeholder variables

The `duqduq` config template uses [jinja2](https://jinja.palletsprojects.com/en/latest/) as the templating engine. Jinja2 is widely used in the Python ecosystem and outside.

`run`
: This contains attributes related to the current run. You can access the run name (`run.name`).

`handle` (`ImasHandle`)
: The handle corresponds to the IMAS handle passed on the command line. This means you have access to all attributes from [duqtools.api.ImasHandle][], such as `handle.user`, `handle.db`, `handle.run`, and `handle.shot`.

`variables`
: These variable corresponds to pre-defined values in the IDS data. They are defined via as variables with the type `IDS2jetto-variable`. Essentially, each variable of this type is accessible as an attribute of `variables`. These are grabbed from the IDS data on-the-fly in the IMAS handle.
: For more information on how to set this up, see the section on [variables](../../variables/#ids2jetto-variables).

### Jetto V210921

For compatibility with Jintrac v210921 distributions (`system: jetto-v210921`), the `run` class has a few more attributes. These are needed to set the imas locations where the run in/out data can be stored. `duqduq` calculates a suitable range for `run_in_start_at`/`run_out_start_at`. This means any two runs will not write to the same imas location.

```
  data:
    imasdb: {{ handle.db }}
    run_in_start_at: {{ run.data_in_start }}
    run_out_start_at: {{ run.data_out_start }}
```

### Jinja2 quickstart

Jinja2 allows expressions everywhere. Anything between `{{` and  `}}` is evaluated as an [expression](https://jinja.palletsprojects.com/en/latest/templates/#expressions). This means that:

`shot: {{ handle.shot }}` gets expanded to `shot: 12345`

But, it is also possible to perform some operations inside the expression. In the example above we used this to calculate `t_end` from `t_start`.

For example, if `t_start = 10`:

`values: [ {{ variables.t_start + 0.01 }} ]` gets expanded to `values: [ 10.01 ]`.

Another useful feature of jinja2 is [filters](https://jinja.palletsprojects.com/en/latest/templates/#builtin-filters). These are functions that can be used inside expressions to modify the variables. Let's say `t_start = 10.123`, and we want to round to the nearest tenth:

`values: [ {{ variables.t_start | round(1) }} ]` becomes `values: [ 10.1 ]`.

For more information, have a look at the [jinja2 documentation](https://jinja.palletsprojects.com/en/latest/).
