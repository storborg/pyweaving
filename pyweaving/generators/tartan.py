from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import re

from .. import Draft


color_map = {
    'A': (92, 140, 168),  # azure / light blue
    'G': (0, 104, 24),  # green
    'B': (44, 44, 128),  # blue
    'K': (0, 0, 0),  # black
    'W': (224, 224, 224),  # white
    'Y': (232, 192, 0),  # yellow
    'R': (200, 0, 44),  # red
    'P': (120, 0, 120),  # purple
    'C': (208, 80, 84),  # ??? light red of some kind
    'LP': (180, 104, 172),  # light purple
}


def tartan(sett, repeats=1):
    colors = []
    for piece in sett.split(', '):
        m = re.match('([A-Z]+)(\d+)', piece)
        colors.append((
            color_map[m.group(1)],
            int(m.group(2)),
        ))

    # tartan is always the same design mirrored once
    colors.extend(reversed(colors))

    print("Threads per repeat: %d" %
          sum(count for color, count in colors))

    # tartan is always 2/2 twill
    # we'll need 4 shafts and 4 treadles
    draft = Draft(num_shafts=4, num_treadles=4)

    # do tie-up
    for ii in range(4):
        draft.treadles[3 - ii].shafts.add(draft.shafts[ii])
        draft.treadles[3 - ii].shafts.add(draft.shafts[(ii + 1) % 4])

    thread_no = 0
    for ii in range(repeats):
        for color, count in colors:
            for jj in range(count):
                draft.add_warp_thread(
                    color=color,
                    shaft=thread_no % 4,
                )
                draft.add_weft_thread(
                    color=color,
                    treadles=[thread_no % 4],
                )
                thread_no += 1

    return draft

# Tartan Setts
gordon_red = ('A12, G12, R18, K12, R18, B18, W4, C16, W4, K32, A12, '
              'W4, B32, W4, G36')

gordon_modern = 'B24, K4, B4, K4, B4, K24, G24, Y4, G24, K24, B24, K4, B4'

gordon_dress = ('W4, B2, W24, B4, W4, K16, B16, K4, B4, K4, B16, K16, '
                'G16, K2, Y4, K2, G16, K16, W4, B4, W24, B2, W4')

gordon_old = 'B24, K4, B4, K4, B4, K24, G24, Y4, G24, K24, B24, K4, B4'

gordon_red_muted = ('A12, G12, R18, K12, R18, B18, W4, C16, W4, K32, A12, '
                    'W4, B32, W4, G36')

gordon_red_old_huntly = ('B28, W2, G16, W2, DG32, A12, W2, B28, W2, G28, '
                         'A12, G12, R16, DG12, R16, DG2')

gordon_old_ancient = 'K8, B46, K46, G44, Y6, G6, Y12'

gordon_of_abergeldie = 'G36, Y2, LP12, K2, W2, R40'

gordon_of_esselmont = 'K8, P46, K46, G44, Y6, G6, Y12'

gordon_roxburgh_district = 'B4, R2, G32, B16, W2, B2, W2, B32'

gordon_roxburgh_red = 'B6, DG52, B6, R6, B40, R6, B6, R52, DG10, W6'

gordon_roxburgh_red_muted = 'B6, DG52, B6, R6, B40, R6, B6, R52, DG10, W6'

gordon_huntly_district = ('G16, R4, G16, R24, B2, R2, B4, R2, B2, R24, B2, '
                          'R2, B4, R2, B2, R24, W2, R6, Y2, B24, R6, B24, '
                          'Y2, R6, W2, R24, G4, R6, G4, R24, G16, R4, G16')

gordon_aberdeen_district = ('W4, LG8, K32, W4, P12, A8, W4, A8, P12, W4, P6, '
                            'R16, LR6, W4, LR6, R16, P6, W4, K24, LG8, K24, '
                            'W4, P6, R16, LR6, W4, LR6, R16, P6, W4, A20, W4, '
                            'R12, LR6, W2, LR6, R12, W4, LG8, K32, W4, R46, '
                            'LR6, W4')

gordon_huntly = 'R4, MB6, FB24, K22, MG22, Y4'
