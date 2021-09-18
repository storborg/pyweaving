from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import re

from .. import Draft

# test here:
# - https://www.tartanregister.gov.uk/searchDesigns#TartanDisplay


color_map = {
    'A' : (92,  140, 168),  # azure / light blue
    'G' : (0,   104,  24),  # green
    'LG': (134, 198, 124),  # light green
    'DG': (0,    64,  40),  # dark green
    'B' : (44,   44, 128),  # blue
    'LB': (152, 200, 232),  # light blue
    'DB': (0,     0, 100),  # dark blue
    'K' : (0,     0,   0),  # black
    'W' : (248, 248, 248),  # white
    'LN': (224, 224, 224),  # light neutral (gray)
    'N' : (176, 176, 176),  # neutral (gray)
    'DN': (20,   40,  60),  # dark neutral
    'Y' : (232, 192,   0),  # yellow
    'LY': (249, 245, 200),  # light yellow
    'DY': (208, 152,   0),  # dark yellow
    'R' : (200,   0,  44),  # red
    'LR': (232, 120, 120),  # light red
    'DR': (128,   0,  40),  # dark red
    'O' : (128,   0,  40),  # orange
    'DO': (190, 220,  50),  # dark orange
    'P' : (120,   0, 120),  # purple
    'C' : (208,  80,  84),  # ??? light red of some kind
    'P' : (90,    0, 140),  # purple
    'LP': (196, 156, 216),  # light purple
    'DP': (68,    0,  68),  # dark purple
    'LT': (160, 124,  88),  # light brown (Tan)
    'T' : (96,   64,   0),  # Brown (Tan)
    'DT': (76,   52,  40),  # dark Brown
}

def extract_colors(sett):
    """ get color sequence for the tartan sett
        - mirror if required
    """
    colors = []
    sett_simple = sett.replace("/","").upper()
    for piece in re.split('[,_ ]', sett_simple):
        m = re.match('([A-Z]+)(\d+)', piece.strip())
        if m.group(1) in color_map.keys():
            colors.append( ( color_map[m.group(1)],
                             int(m.group(2))
                            ))
        else:
            print("Color indicator",m.group(1),"not defined in color_map")
    # if / in the pattern then reflect it.
    if sett.find('/') > -1:
        # tartan is same design mirrored
        colors.extend(reversed(colors[1:-1]))
    return colors

def tartan(sett, repeats=1, direction="s"):
    colors = []
    direction = direction.upper()
    warp_colors = []
    weft_colors = []
    
    # are there separate warp and weft threadcounts
    if sett.find(".") > -1:
        # two parts warp+weft
        warpsett, weftsett = sett.split(".")
        warpsett = warpsett.strip()
        weftsett = weftsett.strip()
    else:
        warpsett = sett.strip()
        weftsett = None
    #
    warp_colors = extract_colors(warpsett)
    if weftsett:
        weft_colors = extract_colors(weftsett)

    print("Threads per repeat: %d" %
          sum(count for color, count in warp_colors))

    # Tartan is always 2/2 twill
    # - need 4 shafts and 4 treadles
    shaft_count = 4
    draft = Draft(num_shafts=shaft_count, num_treadles=shaft_count)

    # do tie-up
    for ii in range(shaft_count):
        draft.treadles[shaft_count-1 - ii].shafts.add(draft.shafts[ii])
        draft.treadles[shaft_count-1 - ii].shafts.add(draft.shafts[(ii + 1) % shaft_count])

    thread_no = 0
    # warp
    for ii in range(repeats):
        for color, count in warp_colors:
            for jj in range(count): # (count//2) for visualisation
                s = thread_no % shaft_count
                if direction=="Z":
                    s = shaft_count - s -1
                draft.add_warp_thread(
                    color=color,
                    shaft=s,
                )
                thread_no += 1
    # weft
    thread_no = 0
    if not weft_colors:
        weft_colors = warp_colors
    #
    for ii in range(repeats):
        for color, count in weft_colors:
            for jj in range(count): # (count//2) for visualisation
                t = thread_no % shaft_count
                draft.add_weft_thread(
                    color=color,
                    treadles=[t],
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

kincardine_tweed = 'B/4 DY15 R1 DY/30 . G/4 O15 R1 O/30'
MacMillan_Ancient = "G2_K1_G18_K1_G2_K1_R12_G4_Y6_K1_Y6_K1"