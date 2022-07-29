[![Documentation Status](https://readthedocs.org/projects/duqtools/badge/?version=latest)](https://duqtools.readthedocs.io/en/latest/?badge=latest)
[![Tests](https://github.com/CarbonCollective/fusion-dUQtools/actions/workflows/test.yaml/badge.svg)](https://github.com/CarbonCollective/fusion-dUQtools/actions/workflows/test.yaml)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/duqtools)](https://pypi.org/project/duqtools/)
[![PyPI](https://img.shields.io/pypi/v/duqtools.svg?style=flat)](https://pypi.org/project/duqtools/)


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

To install:

    pip install duqtools

The source code is available from [Github](https://github.com/CarbonCollective/fusion-dUQtools).

Suggestions, improvements, and edits are most welcome.


## Development

*Duqtools* targets Python 3.7, which is the version available on [eufus](https://wiki.eufus.eu/doku.php).

Clone the repository into the `duqtools` directory:

```console
git clone https://github.com/CarbonCollective/fusion-dUQtools.git duqtools
```

Install using `virtualenv`:

```console
cd duqtools
python3 -m venv env
source env/bin/activate
python3 -m pip install -e .[develop]
```

Alternatively, install using Conda:

```console
cd duqtools
conda create -n duqtools python=3.7
conda activate duqtools
pip install -e .[develop]
```

### Tests

Duqtools uses [pytest](https://docs.pytest.org/en/7.1.x/) to run the tests. You can run the tests for yourself using:

```console
pytest
```

### Documentation

The documentation uses the [mkdocs](https://www.mkdocs.org/). To build the docs for yourself:

```console
mkdocs serve
```

### Making a release

1. Bump the version (major/minor/patch as needed)

    bumpversion minor

2. Make a new [release](https://github.com/CarbonCollective/fusion-dUQtools/releases). The [upload to pypi](https://github.com/CarbonCollective/fusion-dUQtools/actions/workflows/publish.yaml) is triggered when a release is published.

