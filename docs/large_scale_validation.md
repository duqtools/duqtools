# Large scale validation

Set up large scale validations using the helper tool *duqduq*.

This page documents the different subcommands available in this cli program.

To get started:

    duqduq --help

For information on how to configure your UQ runs via `duqtools.yaml`, check out the [configuration page](../config).

To start with large scale validation, two files are needed:

1. `data.csv`
2. `duqtools.template.yaml`

## Input data

1. `data.csv` - This file contains a list of IMAS handles pointing. For more info, click [here](../dash/#from-a-csv-file). `duqduq setup` creates a new directory (named after the index column) in the current directory with input for duqtools.

```csv title="data.csv"
,user,db,shot,run
run_1,user,jet,12345,0002
run_2,user,jet,98760,0002
run_3,user,jet,2222,0002
run_4,user,jet,3333,0002
run_5,user,jet,4444,0001
```

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

The `duqduq` config template uses [jinja2](https://jinja.palletsprojects.com/en/3.0.x/) as the templating language.

`run`
: This contains attributes related to the current run. You can access the run name (`run.name`).

`handle` (`ImasHandle`)
: The handle corresponds to the entry from the Imas location in the `data.csv`. This means you have access to all attributes from [duqtools.api.ImasHandle][], such as `handle.user`, `handle.db`, `handle.run`, and `handle.shot`.

`variables`
: These variable corresponds to pre-defined values in the IDS data.

-> Link to where the variables are defined (variable.yaml)
-> Explain how jinja2 works in a nutshell

### Jetto V210921

For compatibility with Jintrac v210921 distributions (`system: jetto-v210921`), the `run` class has a few more attributes. These are needed to set the imas locations where the run in/out data can be stored. `duqduq` calculates a suitable range for `run_in_start_at`/`run_out_start_at`. This means any two runs will not write to the same imas location.

```
  data:
    imasdb: {{ handle.db }}
    run_in_start_at: {{ run.data_in_start }}
    run_out_start_at: {{ run.data_out_start }}
```

::: mkdocs-click
    :module: duqtools.large_scale_validation.cli
    :command: cli
    :prog_name: duqduq
    :list_subcommands: True
    :style: table
    :depth: 1
