from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from operator import itemgetter

from .. import Color


def diff_rgb(a, b):
    return [ch_b - ch_a for ch_a, ch_b in zip(a, b)]


def add_rgb(a, b):
    return [ch_b + ch_a for ch_a, ch_b in zip(a, b)]


def manhattan_distance(a, b):
    return sum(abs(b_el - a_el) for a_el, b_el in zip(a, b))


def closest(want_rgb, *available_rgb):
    # This is about the slowest approach imaginable for this
    distances = [(manhattan_distance(want_rgb, this_rgb), this_rgb)
                 for this_rgb in available_rgb]
    distances.sort(key=itemgetter(0))
    return distances[0][1]


def dithered_gradient(start_color, end_color, count):
    """
    Make a dithering sequence which simulates a gradient between two colors
    across ``count`` threads. Returns a list of length ``count`` where each
    element is the color to be used for the corresponding thread.
    """
    inc_rgb = [float(ch2 - ch1) for ch1, ch2 in
               zip(start_color.rgb, end_color.rgb)]
    error_rgb = 0.0, 0.0, 0.0
    threads = []
    for ii in range(count):
        dist = (ii + 0.5) / count
        ideal_rgb = [(inc_ch * dist) + start_ch for inc_ch, start_ch in
                     zip(inc_rgb, start_color.rgb)]
        with_error_rgb = [ideal_ch + error_ch
                          for ideal_ch, error_ch in
                          zip(ideal_rgb, error_rgb)]
        this_rgb = closest(with_error_rgb, start_color.rgb, end_color.rgb)
        threads.append(Color(this_rgb))
        error_rgb = add_rgb(error_rgb, diff_rgb(this_rgb, ideal_rgb))

    return threads
