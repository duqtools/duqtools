# Large scale validation

Set up large scale validations using the helper tool *duqduq*.

This page documents the different subcommands available in this cli program.

To get started:

    duqduq --help

For information on how to configure your UQ runs via `duqtools.yaml`, check out the [configuration page](../config).

To start with large scale validation, two files are needed:

1. `data.csv` contains the [template data](#input-data)
2. `duqtools.template.yaml` is the [duqtools config template](#config-template)

Then, run the programs in the intended sequence:

1. [`duqduq setup`](#duqduq-setup)
2. [`duqduq create`](#duqduq-create)
3. [`duqduq submit`](#duqduq-submit)
4. [`duqduq status`](#duqduq-status)
5. [`duqduq merge`](#duqduq-merge)

## Input data

`data.csv` contains a list of IMAS handles pointing. For more info on this file, click [here](../dash/#from-a-csv-file). `duqduq setup` will loop over the entries in this file, and create a new directory (named after the index column) in the current directory with input for duqtools.

```csv title="data.csv"
,user,db,shot,run
run_1,user,jet,12345,0002
run_2,user,jet,98760,0002
run_3,user,jet,2222,0002
run_4,user,jet,3333,0002
run_5,user,jet,4444,0001
```

Each column will be exposed through the `handle` dataclass in the config template below.

## Config template

`duqtools.template.yaml` is a template for the [duqtools create config](../config/create/#the-create-config). It contains a few placeholders for variable data (see [below](#placeholder-variables)).

```yaml title="duqtools.template.yaml"
create:
  runs_dir: /pfs/work/username/jetto_runs/duqduq/{{ run.name }}
  template: /pfs/work/username/jetto/runs/path/to/template/
  template_data:
    user: {{ handle.user }}
    db: {{ handle.db }}
    shot: {{ handle.shot }}
    run: {{ handle.run }}
  sampler:
    method: latin-hypercube
    n_samples: 3
  dimensions:
    - variable: zeff
      operator: add
      values: [0.01, 0.02, 0.03]
    - variable: t_e
      operator: multiply
      values: [0.8, 1.0, 1.2]
    - variable: major_radius
      operator: copyto
      values: [ {{ variables.major_radius | round(4) }} ]
    - variable: b_field
      operator: copyto
      values: [ {{ variables.b_field | round(4) }} ]
    - variable: t_start
      operator: copyto
      values: [ {{ variables.t_start | round(4) }} ]
    - variable: t_end
      operator: copyto
      values: [ {{ (variables.t_start + 0.01) | round(4) }} ]
system: jetto-v220922
```

### Placeholder variables

The `duqduq` config template uses [jinja2](https://jinja.palletsprojects.com/en/latest/) as the templating engine. Jinja2 is widely used in the Python ecosystem and outside.

`run`
: This contains attributes related to the current run. You can access the run name (`run.name`).

`handle` (`ImasHandle`)
: The handle corresponds to the entry from the Imas location in the `data.csv`. This means you have access to all attributes from [duqtools.api.ImasHandle][], such as `handle.user`, `handle.db`, `handle.run`, and `handle.shot`.

`variables`
: These variable corresponds to pre-defined values in the IDS data. They are defined via as variables with the type `IDS2jetto-variable`. Essentially, each variable of this type is accessible as an attribute of `variables`. These are grabbed from the IDS data on-the-fly in the current IMAS handle.
: For more information on how to set this up, see the section on [variables](../variables/#ids2jetto-variables).

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

::: mkdocs-click
    :module: duqtools.large_scale_validation.cli
    :command: cli
    :prog_name: duqduq
    :list_subcommands: True
    :style: table
    :depth: 1
