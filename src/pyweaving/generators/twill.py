from .. import Draft, __version__


def twill(shape="2/2", repeats=4, warp_color=(255, 255, 255),
          weft_color=(0, 0, 220)):
    """
    Generate twills from a shape description. Defaults to Z twill
     - E.g. "2/2", "1/3 2/2", "2/4S", 2/4Z"
     - E.g. 1/3 twill reveals 1 weft and three warps
    Also can define threading order:
     - 1/2S means S Twist direction, Z means opp twist direction

    Args:
        shape (str): pairs of twill definitions. E.g. "2/2 1/3", "1/1 3/1S"
        repeats (int, optional): Number of times to repeat the twill pattern.
        warp_color (Color or tuple): Color for the warp.
        weft_color (Color or tuple): Color for the weft.
    Returns:
        Draft:
    """
    shape = shape.strip()  # remove extraneous spaces
    # is direction Z|S supplied
    direction = "Z"
    if shape[-1].upper() in ["S", "Z"]:
        direction = shape[-1].upper()
        shape = shape[:-1]

    shapes = []
    if len(shape) > 3 and shape.find(" ") > -1:
        # likely to be a sequence of twills
        twills = shape.split(" ")
        for twill in twills:
            shapes.append(twill.split("/"))
    else:
        shapes = [shape.split("/")]
    shapes = [[int(a), int(b)] for a, b in shapes]

    size = sum([a+b for a, b in shapes])

    shafts = size
    draft = Draft(num_shafts=shafts, num_treadles=shafts)

    # do tie-up
    for ii in range(shafts):
        index = ii
        for warp, weft in shapes:  # do the sequence of shapes on this treadle
            for jj in range(warp):
                treadle_pos = ii
                if direction == "S":
                    treadle_pos = size-1-ii
                draft.treadles[treadle_pos].shafts.add(draft.shafts[index % size])
                index += 1
            index += weft  # skip these unset treadles

    # Threading
    for ii in range(repeats * size):
        draft.add_warp_thread(
            color=warp_color,
            shaft=ii % shafts,
        )
        # Treadling
        draft.add_weft_thread(
            color=weft_color,
            treadles=[ii % shafts],
        )

    draft.title = shape + " "+direction+" Twill"
    draft.draft_title = [draft.title]
    draft.source_program = 'PyWeaving'
    draft.source_version = __version__
    return draft
