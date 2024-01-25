# Duqtools on Eurofusion Gateway

This demo will guide you through setting up duqtools on the Gateway, and perform an example UQ run using duqtools.

## Module setup

Duqtools needs a couple of modules on the gateway to be loaded.

Load modules:

```bash
module purge
module load cineca
module use /gss_efgw_work/work/g2fjc/jintrac/default/modules
module load jintrac
module use /gss_efgw_work/work/g2fjc/cmg/jams/default/modules
module load jams
```

Duqtools currently works with MDSPlus only. Make sure you run the MDSPLUS backend:

```bash
export JINTRAC_IMAS_BACKEND=MDSPLUS
```

This needs to be done every time. To make sure the modules are auto-loaded, add the lines above to `~/.bashrc`.

## Install duqtools

Duqtools is available from [pypi](https://pypi.org/project/pipi). To install:

```bash
pip install duqtools
```

To upgrade:

```bash
pip install duqtools -U
```

To make sure that it is installed correctly, you can run:

```bash
duqtools version
```

Which will show the version:

```
duqtools 3.0.2 (rev: edf23051d3131ce22be1307f0a2b14cc46f9bff4)
```

## Setting up a run

Create a new directory:

```bash
mkdir duqtools_demo
cd duqtools demo
```

Initialize a duqtools config:

```bash
duqtools init
```

Duqtools will always tell you what it is going to do, and it will not overwrite any files without your approval.

```
Operations in the Queue:
========================
- Copying config to : duqtools.yaml

Do you want to apply all 1 operations? [y/N]: y
Applying Operations
Copying config to : duqtools.yaml:
Progress: 100%|███████████████████████████████████| 1/1 [00:00<00:00, 46.59it/s]
```

Press <kbd>y</kbd> and <kbd>Enter</kbd> to continue.

This will create a new file called `duqtools.yaml`. This is the main file you will be modifying to set up a duqtools run. For more information about how to modify the file, for a description of the variables, have a look at the [rest of the documentation](./config/index.md).

## Example `duqtools.yaml`

Below is a sample configuration that you can use. Make sure to update your username (`YOURUSERNAME`) in `runs_dir`.

To open the file, you could use `nedit`:

```bash
gedit duqtools.yaml
```

There are three things that you could change if you want to try with your own data:

- `runs_dir`: All output data will be stored in directory. On gateway, this must be a directory that JINTRAC can write to, e.g. on the work share in the `jetto/runs` subdirectory.
- `template`: This directory holds the template jetto run that will be used as the base for UQ.
- `template_data`: This imasdb path points to the IMAS data that will be updated.

```yaml
create:
  runs_dir: /pfs/work/YOURUSERNAME/jetto/runs/duqtools_demo
  template: /afs/eufus.eu/user/g/g2ssmee/public/interpretive_esco02
  template_data:
    user: g2aho
    db: jet
    shot: 90350
    run: 2
  sampler:
    method: latin-hypercube
    n_samples: 3
  dimensions:
    - variable: zeff
      operator: multiply
      values: [0.8, 0.9, 1.0, 1.1, 1.2]
    - variable: t_e
      operator: multiply
      values: [0.8, 0.9, 1.0, 1.1, 1.2]
system:
  name: jetto
```

## Starting duqtools

To start duqtools, run:

```bash
duqtools.create
```

This will read `duqtools.yaml`, and set up the run. Date are stored in the `runs_dir`.
You will see something like this:

```
Operations in the Queue:
========================
- Creating run : /pfs/work/g2ssmee/jetto/runs/run_0000
- Creating run : /pfs/work/g2ssmee/jetto/runs/run_0001
- Creating run : /pfs/work/g2ssmee/jetto/runs/run_0002

Do you want to apply all 21 operations? [y/N]: y
Applying Operations
Creating run : /pfs/work/g2ssmee/jetto/runs/run_0002:
Progress: 100%|█████████████████████████████████| 21/21 [00:08<00:00,  2.48it/s]
```

## Submitting to the cluster

You can use the following command to submit all 3 runs to slurm.

```bash
duqtools submit
```

Output:

```
Operations in the Queue:
========================
- Submitting : Job('/gss_efgw_work/work/g2ssmee/jetto/runs/run_0000')
- Submitting : Job('/gss_efgw_work/work/g2ssmee/jetto/runs/run_0001')
- Submitting : Job('/gss_efgw_work/work/g2ssmee/jetto/runs/run_0002')

Do you want to apply all 3 operations? [y/N]: y
Applying Operations
Submitting : Job('/gss_efgw_work/work/g2ssmee/jetto/runs/run_0002'):
Progress: 100%|███████████████████████████████████| 3/3 [00:00<00:00,  5.64it/s]
```

You can monitor the status of your runs using the usual slurm commands, e.g. `squeue -u g2ssmee`.

If you want to probe the status of the runs, you can use

```bash
duqtools status
```

Output:

```
Total number of directories with submit script     : 3
Total number of directories with unsubmitted jobs  : 3
Total number of directories with status script     : 0
Total number of directories with completed status  : 0
Total number of directories with failed status     : 0
Total number of directories with running status    : 0
Total number of directories with unknown status    : 0
```

## Analysis and merging of the data

Output is stored in a csv file with the paths to the data, `data.csv`.
For data analysis, duqtools has a simple [dashboard to visualize these data](./dash.md).

Note that this needs a somewhat recent version of firefox, which is available on the Gateway via this module:

```bash
module load firefox/latest
```

Start the dashboard using:

```bash
duqtools dash
```

This will open a webserver that you can open in your browser copying the url.

```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://130.186.25.51:8501
```
