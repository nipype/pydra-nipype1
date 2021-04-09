# Nipype 1 Tasks for Pydra

[Pydra](https://nipype.github.io/pydra/) is a redesign of the Nipype dataflow
engine, and the core of the emerging
[Nipype 2 ecosystem](https://github.com/nipype).

This is a task package, a set of Pydra Tasks that inhabits the
`pydra.tasks.*` namespace, to ease wrapping Nipype 1 Interfaces.

Additional tools for migrating from Nipype 1 to Pydra may find their home here.

## Installation

```
pip install pydra-nipype1
```

## Usage

```
from pydra.tasks.nipype1.utils import Nipype1Task
from nipype.interfaces import fsl

thresh = Nipype1Task(fsl.Threshold())
res = thresh(in_file=fname, thresh=0.5)
```

## For developers

Install repo in developer mode from the source directory. It is also useful to
install pre-commit to take care of styling via black:

```
pip install -e .[dev]
pre-commit install
```
