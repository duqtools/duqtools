| Source | Badges |
| --- | --- |
| ReadTheDocs |[![Documentation Status](https://readthedocs.org/projects/duqtools/badge/?version=latest)](https://duqtools.readthedocs.io/en/latest/?badge=latest) |
| Github | [![Tests](https://github.com/CarbonCollective/fusion-dUQtools/actions/workflows/test.yaml/badge.svg)](https://github.com/CarbonCollective/fusion-dUQtools/actions/workflows/test.yaml) |
| PyPI | [![PyPI - Python Version](https://img.shields.io/pypi/pyversions/duqtools)](https://pypi.org/project/duqtools/) [![PyPI](https://img.shields.io/pypi/v/duqtools.svg?style=flat)](https://pypi.org/project/duqtools/) |
| SonarCloud | [![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=CarbonCollective_fusion-dUQtools&metric=sqale_rating)](https://sonarcloud.io/summary/new_code?id=CarbonCollective_fusion-dUQtools) [![Reliability Rating](https://sonarcloud.io/api/project_badges/measure?project=CarbonCollective_fusion-dUQtools&metric=reliability_rating)](https://sonarcloud.io/summary/new_code?id=CarbonCollective_fusion-dUQtools) |
| CodeCov.io | [![codecov](https://codecov.io/gh/CarbonCollective/fusion-dUQtools/branch/main/graph/badge.svg?token=TE9SBYJY8L)](https://codecov.io/gh/CarbonCollective/fusion-dUQtools)

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

```console
pip install duqtools
```

The source code is available from [Github](https://github.com/CarbonCollective/fusion-dUQtools).

Suggestions, improvements, and edits are most welcome.


## Development

Check out our [Contributing Guidelines](CONTRIBUTING.md#Getting-started-with-develoment) to get started with development.
