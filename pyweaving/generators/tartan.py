from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import re
import os.path

from .. import Draft, get_project_root, Color

# test here:
# - https://www.tartanregister.gov.uk/searchDesigns#TartanDisplay

# standard colors from Tartan register
STR_colors = {
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
    'P' : (90,    0, 140),  # purple
    'LP': (196, 156, 216),  # light purple
    'DP': (68,    0,  68),  # dark purple
    'LT': (160, 124,  88),  # light brown (Tan)
    'T' : (96,   64,   0),  # Brown (Tan)
    'DT': (76,   52,  40),  # dark Brown
    # should these even be here ?? (not in STR definition)
    'A' : (92,  140, 168),  # azure / light blue
    'C' : (208,  80,  84),  # ??? light red of some kind
}

homedir = get_project_root()
collected_tartans_filename = os.path.join(homedir, 'generators','collected_tartans.txt')

def lookup_colors(sett, override_colors=None):
    """ return sequence of color, count pairs from tartan sett
        - mirror if required
    """
    colors = []
    if override_colors:
        color_map = override_colors
    else:
        color_map = STR_colors
    sett_simple = sett.replace("/","").upper()
    for piece in re.split('[,_ ]', sett_simple):
        m = re.match('([A-Z]+)(\d+)', piece.strip())
        if m.group(1) in color_map.keys():
            colors.append( ( color_map[m.group(1)],  # color (tuple)
                             int(m.group(2))         # count
                            ))
        else:
            print("Color indicator",m.group(1),"not defined in color_map")
    # if / in the pattern then reflect it.
    if sett.find('/') > -1:
        # tartan is same design mirrored
        colors.extend(reversed(colors[1:-1]))
    return colors
    
def sett_in_STR_form(sett):
    " is it likely this is an STR format Sett "
    if sett:
        # if we split it - how many groups in pattern
        # print("Tartan guess", len(re.split('[,_ ]', sett)))
        return len(re.split('[,_ ]', sett)) > 3 # a guestimate
    else:
        return False

def tartan(sett, repeats=1, direction="z"):
    direction = direction.upper()
    warp_colors = []
    weft_colors = []
    override_colors= False
    name = sett
    
    # sett is either a pattern or a name. 
    # - hard to guess so assume its a name and then if fail - a sett
    found, sett, override_colors, pattern = find_named_tartan(sett)
    # if found then use pattern, colors
    # else use sett and ignore the rest
    if found:
        sett = pattern
    if not sett_in_STR_form(sett): # will be zeroed if some matches found in names but not unique
        print("Tartan not found")
    else:
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
        warp_colors = lookup_colors(warpsett, override_colors)
        if weftsett:
            weft_colors = lookup_colors(weftsett, override_colors)

        print("Threads per repeat: %d" %
              sum(count for color, count in warp_colors))

        # Tartan is always 2/2 twill
        # - need 4 shafts and 4 treadles
        shaft_count = 4
        draft = Draft(num_shafts=shaft_count, num_treadles=shaft_count)

        # do tie-up
        for ii in range(shaft_count):
            draft.treadles[ii].shafts.add(draft.shafts[ii])
            draft.treadles[ii].shafts.add(draft.shafts[(ii + 1) % shaft_count])

        thread_no = 0
        # warp
        for ii in range(repeats):
            for color, count in warp_colors:
                for jj in range(count,0,-1): # (count//2) for visualisation
                    s = thread_no % shaft_count
                    if direction=="S":
                        s = shaft_count - s -1
                    draft.add_warp_thread(color=color, shaft=s)
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
        #
        draft.title = name.replace(", ","_").replace(" ","_").replace("__","_")
        draft.title = draft.title.replace(",","_").replace(" ","_")
        draft.draft_title = [draft.title]
        draft.notes.append("from: %s in %s twill"%(sett, direction))
        return draft

def find_named_tartan(desired_name):
    """ Search the file for a unique 'name' and 
        - return the STR style string.
        If more than one, then print out the names of the possibles
         for user selection next time.
    """
    found = False
    matching = []
    colors = None
    pattern = None
    inf = open(collected_tartans_filename, 'r')
    uppername = desired_name.lower()
    for line in inf:
        namepos = line.find("=>")
        if namepos > -1:
            name = line[:namepos].strip()
            if name.lower().find(uppername) > -1:
                # found one possibly imperfect match
                matching.append(name) # remove \n
                pattern = line[:-1]
    # unique ?
    if len(matching) == 1:
        # process it
        found = True
        colors, pattern = _parse_tartan_description(pattern[pattern.find("=")+2:])
    elif len(matching) > 1: # several found
        print("Found %d tartans. Choose the one you want to see."%(len(matching)))
        for n in matching:
            print("",n)
        desired_name = False
    else:
        # either its a name we did not find, or its a sett
        pass
    # return sett_or_name, None if no file found (might have been a sett)
    # return newsett, colors if from a file
    return (found, desired_name, colors, pattern)
    

def _parse_tartan_description(sett_or_name):
    """ in form: name = colors = format
        tartan_name=>y#aaaa00k#000000w#aaaaaa=w1(y6k6)y1
        Return colors - a dictionary like STR_colors above,
        and pattern - which is an STR tartan string
    """
    hexcolors, pattern = sett_or_name.split("=")
    colors = {}
    for i in range(len(hexcolors)//8):
        col = hexcolors[i*8:i*8+8]
        hex = col[2:]
        rgb = tuple(int(hex[i:i+2], 16) for i in (0, 2, 4))
        colors[col[0].upper()] = rgb
    weftpattern = None
    symm = pattern.find("(") > -1 # are we mirroring
    pattern = pattern.replace("(","").replace(")","") # remove the mirroring features
    if pattern.find("]") > -1:
        # two parts
        pattern, weftpattern = pattern.split("]")
    warpparts = re.split(r"([a-z]+)",pattern) # find all the bits
    warpparts = [p.strip().upper() for p in warpparts if p] # clean spaces and cap colors
    warpparts = [warpparts[i]+warpparts[i+1] for i in range(0,len(warpparts),2)] # pair up letter,count
    if weftpattern:
        weftparts = re.split(r"([a-z]+)",weftpattern) # find all the bits
        weftparts = [p.strip().upper() for p in weftparts if p]
        weftparts = [weftparts[i]+weftparts[i+1] for i in range(0,len(weftparts),2)] # pair up letter,count
    # All in letter,number sequence
    # reconstruct
    tartan = ""
    if symm: tartan += "/"
    tartan += " ".join(warpparts)
    if weftpattern:
        tartan += " . "
        tartan +=" ".join(weftparts)
        if symm: tartan += "/"
    return colors, tartan


# kincardine_tweed = "B/4 DY15 R1 DY/30 . G/4 O15 R1 O/30"
# MacMillan_Ancient = "G2_K1_G18_K1_G2_K1_R12_G4_Y6_K1_Y6_K1"
