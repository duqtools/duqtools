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

Each of these commands mimick the `duqtools` equivalent, for example, `duqduq create` is the large scale quivalent of `duqtools create`.

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

`duqtools.template.yaml` is a template for the [duqtools create config](../config/create/#the-create-config). It contains a few placeholders for variable data (see [the documentation for `setup`](../config/setup/#placeholder-variables)).

The template uses [jinja2 as a templating language](../config/setup/#jinja2-quickstart).

```yaml title="duqtools.template.yaml"
create:
  runs_dir: /pfs/work/username/jetto_runs/duqduq/{{ run.name }}
  template: /pfs/work/username/jetto/runs/path/to/template/
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
    n_samples: 3
  dimensions:
    - variable: zeff
      operator: add
      values: [0.01, 0.02, 0.03]
    - variable: t_e
      operator: multiply
      values: [0.8, 1.0, 1.2]
system: jetto
```


::: mkdocs-click
    :module: duqtools.large_scale_validation.cli
    :command: cli
    :prog_name: duqduq
    :list_subcommands: True
    :style: table
    :depth: 1
