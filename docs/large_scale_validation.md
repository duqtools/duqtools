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
  runs_dir: /pfs/work/username/jetto_runs/duqduq/$RUNS_NAME
  template: /pfs/work/username/jetto/runs/path/to/template/
  template_data:
    user: $TEMPLATE_USER
    db: $TEMPLATE_DB
    shot: $TEMPLATE_SHOT
    run: $TEMPLATE_RUN
  data:
    imasdb: duqduq
    run_in_start_at: $RUN_IN_START
    run_out_start_at: $RUN_OUT_START
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
```

### Placeholder variables

Placeholder variables are prefixed by `$` and in capital letters. Each of these must be present in the config template. These get overwritte by the entries in the `data.csv` file.

`$RUNS_NAME` 
: Name of the run. This maps to the index (first column) of the `data.csv` file.

`$TEMPLATE_USER` 
: This is filled by user of the corresponding entry in the `data.csv` 

`$TEMPLATE_DB` 
: This is filled by database or machine name of the corresponding entry in the `data.csv` 


`$TEMPLATE_SHOT` 
: This is filled by the shot number of the corresponding entry in the `data.csv` 


`$TEMPLATE_RUN` 
: This is filled by the run number of the corresponding entry in the `data.csv` 


`$RUN_IN_START` 
: `duqduq` calculates a suitable range for `run_in_start_at`/`run_out_start_at` so that input and output data are stored to free run numbers.

`$RUN_OUT_START` 
: See `$RUN_IN_START`


::: mkdocs-click
    :module: duqtools.large_scale_validation.cli
    :command: cli
    :prog_name: duqduq
    :list_subcommands: True
    :style: table
    :depth: 1
