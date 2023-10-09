
# import os
import os.path
import sys
import json
from .Color import Color, WHITE, BLACK, MID
from .Drawstyle import Drawstyle
from .Draft import WarpThread, WeftThread, Shaft, Treadle, Draft
from .repeats import find_repeats, find_mirrors, find_mirrors_repeats, prune_pattern

__version__ = '0.5'

# For Sphinx autodoc
__all__ = ["Draft", "Color", "Drawstyle", "WarpThread", "WeftThread", "Shaft", "Treadle", "find_repeats"]

# The bulk tartans description file is held in the generators code directory.
#  - need a way to find the code directory
from pathlib import Path


def get_project_root():
    " return path to this file's parent directory on the machine "
    return Path(__file__).parent


# support for local styles.json in ./pyweaving
from shutil import copy2
homedir = get_project_root()
data_path = os.path.join(homedir, 'data')  # original style.json file is here
Drawstyles = {}  # loaded styles go in here


def load_styles(filename='styles.json'):
    """
    Load the styles into Drawstyles dictionary.
     - If no .pyweaving dir in homedir create it
     - and copy original syles.json from /data
    """
    global Drawstyles
    platform = sys.platform
    if platform.find('win') > -1:  # windows
        dir = os.path.join(os.path.expanduser('~'), 'Documents', '.pyweaving')
    elif platform.find('dar'):  # mac
        dir = os.path.join(os.path.expanduser('~'), '.pyweaving')
    else:  # linux
        dir = os.path.join(os.path.expanduser('~'), '.pyweaving')
    if not os.path.exists(dir):
        os.makedir(dir)
        # copy styles.json master from data dir
        copy2(os.path.join(data_path, 'styles.json'), dir)
    infile = os.path.join(dir, 'styles.json')

    if os.path.exists(infile):
        with open(infile, 'r') as file:
            styles = json.load(file)
            for name, attributes in styles.items():
                # Make the Drawstyle() or copy an existing is derived_from
                attributes.pop('name')  # pop so we won't be using these again
                parent = attributes.pop('derived_from')
                if parent:
                    style = Drawstyles[parent].copy
                    style.name = name
                    style.derived_from = parent
                else:
                    style = Drawstyle()
                    style.name = name
                # Populate the class by copying defined fields from a temp Drawstyle
                temp = Drawstyle(**attributes)
                for a in attributes.keys():  # using string as accessor
                    setattr(style, a, getattr(temp, a))
                # save it
                Drawstyles[name] = style
    else:
        print("Could not find styles.json at:", infile)


def get_style(name):
    """
    Load styles if not loaded and return the named style.
    """
    if not Drawstyles:
        load_styles()
    if name in Drawstyles.keys():
        return Drawstyles[name]
    else:
        print("Could not find Style named:", name)
        possibles = [n for n in Drawstyles.keys() if n.find(name[:len(name) // 2]) > -1]
        temp = [n for n in Drawstyles.keys() if n.find(name[len(name) // 2:]) > -1]
        for t in temp:
            if t not in possibles:
                possibles.append(t)
        print("Simlarly named styles:", possibles)
        return None