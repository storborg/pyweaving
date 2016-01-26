from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import os.path
import time
import json

from six.moves import input


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

    def print_pick_stats(self):
        last_picks = self.pick_times[-self.average_over:]
        if len(last_picks) >= self.average_over:
            elapsed_secs = last_picks[-1] - last_picks[0]
        else:
            elapsed_secs = last_picks[-1] - self.start_time
        picks_per_second = len(last_picks) / elapsed_secs
        picks_per_minute = picks_per_second * 60.
        picks_to_go = self.total_picks - len(self.pick_times)
        est_remaining_secs = picks_to_go / picks_per_second
        print("Weaving %0.2f picks/min, %d picks left, est remaining: %s" %
              (picks_per_minute, picks_to_go,
               describe_interval(est_remaining_secs)))

    def print_session_stats(self):
        elapsed_secs = self.pick_times[-1] - self.start_time
        picks_done = len(self.pick_times)
        picks_per_second = picks_done / elapsed_secs
        picks_per_minute = picks_per_second * 60.
        print("%d picks total, average %0.2f picks/min." %
              (picks_done, picks_per_minute))


def wait_for_key():
    input('... ')


def load_save_file(save_filename):
    with open(save_filename) as f:
        return json.load(f)


def write_save_file(save_filename, obj):
    with open(save_filename, 'w') as f:
        json.dump(obj, f)


def weaving(draft, repeats, start_repeat, start_pick, save_filename=None):
    """
    Print weaving instructions. Liftplan only for now.

    current_pick, start_repeat, and start_pick are 1-indexed.
    """
    print("\n---- WEAVING INSTRUCTIONS ----\n")

    picks_per_repeat = len(draft.weft)

    if save_filename and os.path.exists(save_filename):
        print("Resuming progress from %s." % save_filename)
        state = load_save_file(save_filename)
        current_repeat = state['current_repeat']
        current_pick = state['current_pick']
    else:
        current_repeat = start_repeat
        current_pick = start_pick

    total_picks = (((repeats - current_repeat) * picks_per_repeat) +
                   (picks_per_repeat - current_pick)) + 1

    stats = StatCounter(total_picks)
    stats.start()

    if save_filename:
        if not os.path.exists(save_filename):
            print("Saving progress to %s." % save_filename)
        else:
            print("Progress will be saved.")
    else:
        print("Not saving progress.")

    print("NOTE: Assumes that the lowest-numbered thread is on the right -->.")

    while True:
        if (current_pick - 1) == len(draft.weft):
            if current_repeat == repeats:
                break
            # Restart pattern
            print("-" * 79)
            print("REPEAT %d COMPLETE" % current_repeat)
            print("Restarting pattern...")
            print("-" * 79)
            current_repeat += 1
            current_pick = 1

        from_right = draft.start_at_lowest_thread ^ ((current_pick - 1) % 2)

        weft_thread = draft.weft[current_pick - 1]
        weft_color = weft_thread.color
        last_color = draft.weft[current_pick - 2].color
        if weft_color != last_color:
            print("COLOR CHANGE! %s -> %s" % (last_color, weft_color))
        print("\nREPEAT %d, PICK %d\n" % (current_repeat, current_pick))
        if from_right:
            print((" " * 40) + "<--- SHUTTLE %s" % weft_color)
        else:
            print("%s SHUTTLE --->" % weft_color)
        print_shafts(draft, weft_thread.connected_shafts)

        if save_filename:
            write_save_file(save_filename, {
                'current_repeat': current_repeat,
                'current_pick': current_pick,
            })

        try:
            wait_for_key()
        except EOFError:
            stats.print_session_stats()
            print("Ending session.")
            return

        current_pick += 1
        stats.pick()
        stats.print_pick_stats()

    print("DONE!")


default_color_table = {}
default_colors = [
    'red',
    'yellow',
    'blue',
    'white',
]
for ii in range(64):
    default_color_table[ii] = default_colors[ii % len(default_colors)]


def threading(draft, repeats=1, color_table=default_color_table):
    """
    Print threading instructions.
    """
    print("\n---- THREADING INSTRUCTIONS ----\n")
    total_count = 0
    for ii, shaft in enumerate(draft.shafts, start=1):
        count = len([thread for thread in draft.warp if thread.shaft == shaft])
        count *= repeats
        total_count += count
        color = color_table[ii - 1]
        print("Heddles on shaft %d: %d\t\t%s" % (ii, count, color))

    print("Total heddles required: %d" % total_count)

    for __ in range(repeats):
        for ii, warp_thread in enumerate(draft.warp, start=1):
            shaft_no = draft.shafts.index(warp_thread.shaft) + 1
            heddle_color = color_table[shaft_no - 1]
            print("\nWarp thread %d: shaft %d\tthread: %s\theddle: %s" % (
                ii, shaft_no, warp_thread.color.rgb, heddle_color))
            wait_for_key()

    print("DONE!")


def tieup(draft):
    """
    Print tie-up instructions.
    """
    raise NotImplementedError
