[![Documentation Status](https://readthedocs.org/projects/duqtools/badge/?version=latest)](https://duqtools.readthedocs.io/en/latest/?badge=latest)
[![Tests](https://github.com/CarbonCollective/fusion-dUQtools/actions/workflows/test.yaml/badge.svg)](https://github.com/CarbonCollective/fusion-dUQtools/actions/workflows/test.yaml)


# Duqtools

*Duqtools* is a tool for **D**ynamic **U**ndertainty **Q**uantification for Tokamak reactor simulations modelling.

Features:

- Set up 100s of simulation runs from a single template
- Launch stardard sets of sensitivy tests with minimal programming
- Batch job submission and status tracking
- Supports the Standardized Interface Data Structures (IDSs) data directory
- Compare and visualize 100s of simulations in one overview
- Display simulation results as confidence ranges and distributions

*Duqtools* is currently under active development. It runs on linux only and requires the [ITER](http://iter.org/) Integrated Modeling and Analysis Suite ([IMAS](https://confluence.iter.org/display/IMP)).

The source code is available from [Github](https://github.com/CarbonCollective/fusion-dUQtools).

Suggestions, improvements, and edits are most welcome.


## Development

*Duqtools* targets Python 3.7, which is the version available on [eufus](https://wiki.eufus.eu/doku.php).

Install using Conda:

```console
conda create -n duqtools python=3.7
conda activate duqtools
pip install -e .[develop]
```

Install using `virtualenv`:

```console
python3 -m venv env
source env/bin/activate
python3 -m pip install -e .[develop]
```

Run tests:

```console
pytest
```

Make docs:

```console
mkdocs serve
```
