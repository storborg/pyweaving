from .. import Draft, Thread


def twill(size=2):
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
        draft.warp.append(Thread(
            dir='warp',
            color=(0, 0, 100),
            shafts=set([draft.shafts[ii % shafts]]),
        ))

        draft.weft.append(Thread(
            dir='weft',
            color=(255, 255, 255),
            treadles=set([draft.treadles[ii % shafts]]),
        ))

    return draft
