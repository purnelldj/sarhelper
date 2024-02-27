# sarhelper

## installation

Download and cd into repository and then:

```
python -m venv .venv
source venv/bin/activate
python -m pip install -e .
pre-commit install
```

## process some data

For example, using a simple

```
proc subset=True plot=True save=False
```

## add a new dataset

use `rcm_geotiff_tp.yaml` and `datamodules/rcm_geotiff_tp.py` as templates
