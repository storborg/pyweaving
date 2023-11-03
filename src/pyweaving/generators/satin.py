from .. import Draft

# regular satin = {5: [2,3], 8:[3,5]}
# irregular satin = {6:[4,3,2,2,3,4], }


def factorize(num):
    return [n for n in range(1, num + 1) if num % n == 0]


def find_regular_satin_counts(unit_size):
    """ satin count !=1, !=size of unit, != size-1
        also remove values that share factors with unit (e.g.for 8 remove 2,4,6
    """
    possibles = [i for i in range(2, unit_size-1)]
    # find unit factors
    unit_factors = factorize(unit_size)[1:-1]
    # trim obvious possibles
    possibles = [i for i in possibles if i not in unit_factors]
    # find possibles with common factors
    nope = []
    for p in possibles:
        facts = factorize(p)[1:-1]
        for f in facts:
            if f in unit_factors:
                nope.append(p)
    result = [p for p in possibles if p not in nope]
    return result


def satin(unit_size=5, direction='Z', warp_color=(0, 0, 100), weft_color=(255, 255, 255)):
    """ Satins valid from unit >= 4
        4,6 are irregular satins, the rest are balanced.
        def would be unit=5,count=2 (5,2)
    """
    counts = find_regular_satin_counts(unit_size)
    shaft_ids = []
    if counts:  # regular satin
        # fill count with first one - but ideally specified
        shaft_ids = [counts[0]] * unit_size
    else:  # find irregular satin
        pass
        shaft_ids = [4, 3, 2, 2, 3, 4]  # !for a unit=4
    print(shaft_ids)
    #
    draft = Draft(num_shafts=unit_size, num_treadles=unit_size)
    # tieup
    for ii in range(len(shaft_ids)):
        for jj in range(unit_size):
            draft.treadles[ii].shafts.add(draft.shafts[(ii + jj) % shafts])  # !!


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
