

from .Color import Color, WHITE, BLACK, MID
from .Drawstyle import Drawstyle
from .Draft import *
from .repeats import *

__version__ = '0.8'


# The bulk tartans description file is held in the generators code directory.
#  - need a way to find the code directory
from pathlib import Path


def get_project_root():
    " return path to this file's parent directory on the machine "
    return Path(__file__).parent
