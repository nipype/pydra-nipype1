import sys
from atexit import register
from contextlib import ExitStack
from functools import lru_cache


if sys.version_info < (3, 9):
    from importlib_resources import as_file, files
else:
    from importlib.resources import as_file, files

_stack = ExitStack()
register(_stack.close)


@lru_cache
def load_resource(anchor, *parts) -> str:
    return str(_stack.enter_context(as_file(files(anchor).joinpath(*parts))))
