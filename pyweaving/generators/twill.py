from . import Draft, Thread


def twill():
    # just generates 2/2 twill for now

    # we'll need 4 shafts and 4 treadles
    draft = Draft(num_shafts=4, num_treadles=4)

    # do tie-up
    for ii in range(4):
        draft.treadles[ii].shafts.add(draft.shafts[ii])
        draft.treadles[ii].shafts.add(draft.shafts[(ii + 1) % 4])

    for ii in range(20):
        draft.warp.append(Thread(
            dir='warp',
            color=(0, 160, 0),
            shafts=set([draft.shafts[ii % 4]]),
        ))

        draft.weft.append(Thread(
            dir='weft',
            color=(160, 0, 0),
            treadles=set([draft.treadles[ii % 4]]),
        ))

    return draft
