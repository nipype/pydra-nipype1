"""
>>> from pydra import ShellCommandTask
>>> import pydra.tasks.nipype1
"""
try:
    from ._version import __version__
except ImportError:
    pass

from .utils import Nipype1Task

__all__ = ["Nipype1Task"]
