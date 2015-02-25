from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from .. import Draft
from PIL import Image


def point_threaded(im, warp_color=(0, 0, 0), weft_color=(255, 255, 255),
                   shafts=40, max_float=8, repeats=2):
    """
    Given an image, generate a point-threaded drawdown that attempts to
    represent the image. Results in a drawdown with bilateral symmetry from a
    non-symmetric source image.
    """
    draft = Draft(num_shafts=shafts, liftplan=True)

    im.thumbnail((shafts, im.size[1]), Image.ANTIALIAS)
    im = im.convert('1')

    w, h = im.size
    assert w == shafts
    warp_pattern_size = ((2 * shafts) - 2)
    for __ in range(repeats):
        for ii in range(warp_pattern_size):
            if ii < shafts:
                shaft = ii
            else:
                shaft = warp_pattern_size - ii
            draft.add_warp_thread(color=warp_color, shaft=shaft)

    imdata = im.getdata()

    for __ in range(repeats):
        for yy in range(h):
            offset = yy * w
            pick_shafts = set()
            for xx in range(w):
                pixel = imdata[offset + xx]
                if not pixel:
                    pick_shafts.add(xx)
            draft.add_weft_thread(color=weft_color, shafts=pick_shafts)

    return draft
