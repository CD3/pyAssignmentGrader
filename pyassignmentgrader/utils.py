import contextlib
import os
from pathlib import Path


@contextlib.contextmanager
def working_dir(new_dir: Path):
    old_dir = Path().absolute()
    new_dir = new_dir.absolute()
    try:
        os.chdir(new_dir)
        yield new_dir
    finally:
        os.chdir(old_dir)


