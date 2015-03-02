from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from .. import Draft


def twill(size=2, warp_color=(0, 0, 100), weft_color=(255, 255, 255)):
    # float=2 --> 2/2 twill
    # float=3 --> 3/3 twill
    # float=4 --> 4/4 twill
    # etc

    # we'll need 2 shafts / treadles per float thread
    shafts = 2 * size
    draft = Draft(num_shafts=shafts, num_treadles=shafts)

    # do tie-up
    for ii in range(shafts):
        for jj in range(size):
            draft.treadles[ii].shafts.add(draft.shafts[(ii + jj) % shafts])

    for ii in range(8 * size):
        draft.add_warp_thread(
            color=warp_color,
            shaft=ii % shafts,
        )

        draft.add_weft_thread(
            color=weft_color,
            treadles=[ii % shafts],
        )

    return draft
