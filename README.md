# fusion-dUQtools
Dynamic uncertainty quantification for Tokomak reactor simulations modelling

## Development

Install using:

```console
conda create -n duqtools python=3.7
conda activate duqtools
pip install -e .[develop]
```

On [eufus](https://wiki.eufus.eu/doku.php):

```console
python -m venv env
source env/bin/activate
python -m pip install -e .[develop]
```

Run tests:

```console
pytest
```