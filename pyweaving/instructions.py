from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import time


def print_shafts(draft, connected):
    """
    Print the shaft lift state, as for a table loom.
    """
    up_shafts = [' ' if shaft in connected else '#'
                 for shaft in draft.shafts]
    down_shafts = ['#' if shaft in connected else ' '
                   for shaft in draft.shafts]
    up_lines = '  '.join((c * 4) for c in up_shafts)
    down_lines = '  '.join((c * 4) for c in down_shafts)
    print()
    for n in range(5):
        print(up_lines)
    for n in range(5):
        print(down_lines)


def describe_interval(secs):
    """
    Return a string describing the supplied number of seconds in human-readable
    time, e.g. "107 hours, 42 minutes".
    """
    if secs <= 0:
        return 'no time at all'
    hours = secs // 3600
    minutes = (secs - (hours * 3600)) // 60
    parts = []
    if hours > 0:
        if hours == 1:
            parts.append('1 hour')
        else:
            parts.append('%d hours' % hours)
    if minutes > 0:
        if minutes == 1:
            parts.append('1 minute')
        else:
            parts.append('%d minutes' % minutes)
    if not (hours or minutes):
        parts.append('less than a minute')
    return ', '.join(parts)


class StatCounter(object):

    def __init__(self, total_picks, average_over=10):
        self.pick_times = []
        self.total_picks = total_picks
        self.average_over = average_over

    def start(self):
        self.start_time = time.time()

    def pick(self):
        self.pick_times.append(time.time())

    def print_stats(self):
        last_picks = self.pick_times[-self.average_over:]
        if len(last_picks) >= self.average_over:
            elapsed_secs = last_picks[-1] - last_picks[0]
        else:
            elapsed_secs = last_picks[-1] - self.start_time
        picks_per_second = len(last_picks) / elapsed_secs
        picks_per_minute = picks_per_second * 60.
        picks_to_go = self.total_picks - len(self.pick_times)
        est_remaining_secs = picks_to_go / picks_per_second
        print("Weaving %0.2f picks/min, %d picks left, est remaining: %s",
              picks_per_minute, picks_to_go,
              describe_interval(est_remaining_secs))


def wait_for_key():
    raw_input('... ')


def weaving(draft, repeats, start_repeat, start_pick):
    """
    Print weaving instructions. Liftplan only for now.

    start_repeat and start_pick are 1-indexed.
    """
    current_repeat = start_repeat

    # current_pick is 0-indexed
    current_pick = start_pick - 1

    picks_per_repeat = len(draft.weft)
    total_picks = (((repeats - start_repeat) * picks_per_repeat) +
                   (picks_per_repeat - start_pick)) + 1

    stats = StatCounter(total_picks)
    stats.start()

    print("\n---- WEAVING INSTRUCTIONS ----\n")

    print("NOTE: Assumes that the lowest-numbered thread is on the right -->.")

    while True:
        if current_pick == len(draft.weft):
            if current_repeat == repeats:
                break
            # Restart pattern
            print("-" * 79)
            print("REPEAT %d COMPLETE", current_repeat)
            print("Restarting pattern...")
            print("-" * 79)
            current_repeat += 1
            current_pick = 0

        from_right = draft.start_at_lowest_thread ^ (current_pick % 2)

        weft_thread = draft.weft[current_pick]
        print("\nREPEAT %d, PICK %d\n", (current_repeat, current_pick + 1))
        if from_right:
            print((" " * 40) + "<--- SHUTTLE")
        else:
            print("SHUTTLE --->")
        print_shafts(draft, weft_thread.connected_shafts)

        wait_for_key()

        current_pick += 1
        stats.pick()
        stats.print_stats()

    print("DONE!")


def threading(draft, repeats):
    """
    Print threading instructions.
    """
    print("\n---- THREADING INSTRUCTIONS ----\n")
    print("Total heddles required: %d", (len(draft.shafts) * repeats))
    for ii, shaft in enumerate(draft.shafts, start=1):
        count = len([thread for thread in draft.warp if thread.shaft == shaft])
        count *= repeats
        print("Heddles on shaft %d: %d", (ii, count))

    for __ in range(repeats):
        for ii, warp_thread in enumerate(draft.warp, start=1):
            shaft_no = draft.shafts.index(warp_thread.shaft) + 1
            print("\nWarp thread %d: shaft %d", (ii, shaft_no))
            wait_for_key()

    print("DONE!")


def tieup(draft):
    """
    Print tie-up instructions.
    """
    raise NotImplementedError
