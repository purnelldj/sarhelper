# sarhelper

For creating pipelines for SAR data processing. Working currently with GEE, SNAPPy

## installation

Download and cd into repository and then:

```
python -m venv .venv
source venv/bin/activate
python -m pip install -e .
```
To install snappy, need to first download the GUI. Look for docs on how to install snappy with python executable.

## usage

The main entry point `src/proc.py` can be run using

```
proc
```
then change parameters from command line

```
proc dataset=gees1_rp
```

## add a new dataset

See `gees1_rp.yaml` and `datamodules/gee.py` as examples.
