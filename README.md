| Source | Badges |
| --- | --- |
| ReadTheDocs |[![Documentation Status](https://readthedocs.org/projects/duqtools/badge/?version=latest)](https://duqtools.readthedocs.io/en/latest/?badge=latest) |
| Github | [![Tests](https://github.com/duqtools/duqtools/actions/workflows/test.yaml/badge.svg)](https://github.com/duqtools/duqtools/actions/workflows/test.yaml) ![Coverage](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/stefsmeets/ea916a5b3c3d9bc59065a7304e4ca707/raw/covbadge.json) |
| PyPI | [![PyPI - Python Version](https://img.shields.io/pypi/pyversions/duqtools)](https://pypi.org/project/duqtools/) [![PyPI](https://img.shields.io/pypi/v/duqtools.svg?style=flat)](https://pypi.org/project/duqtools/) |
| SonarCloud | [![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=duqtools_duqtools&metric=sqale_rating)](https://sonarcloud.io/summary/new_code?id=duqtools_duqtools) [![Reliability Rating](https://sonarcloud.io/api/project_badges/measure?project=duqtools_duqtools&metric=reliability_rating)](https://sonarcloud.io/summary/new_code?id=duqtools_duqtools) |
| Zenodo | [![DOI](https://zenodo.org/badge/492734189.svg)](https://zenodo.org/badge/latestdoi/492734189) |

# Duqtools

*Duqtools* is a tool for **D**ynamic **U**ndertainty **Q**uantification for Tokamak reactor simulations modelling.

Features:

- Set up 100s of simulation runs from a single template
- Launch standard sets of sensitivity tests with minimal programming
- Batch job submission and status tracking
- Supports the Standardized Interface Data Structures (IDSs) data directory
- Compare and visualize 100s of simulations in one overview
- Display simulation results as confidence ranges and distributions

*Duqtools* is currently under active development. It runs on linux only and requires the [ITER](http://iter.org/) Integrated Modeling and Analysis Suite ([IMAS](https://confluence.iter.org/display/IMP)).

To install:

```console
pip install duqtools
```

The source code is available from [Github](https://github.com/duqtools/duqtools).

Suggestions, improvements, and edits are most welcome.


## Development

Check out our [Contributing Guidelines](CONTRIBUTING.md#Getting-started-with-development) to get started with development.
