from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import datetime
import json
from copy import deepcopy
from collections import defaultdict


__version__ = '0.0.1'


class Color(object):
    """
    A color type. Internally stored as RGB, and does not support transparency.
    """
    def __init__(self, rgb):
        if not isinstance(rgb, tuple):
            rgb = tuple(rgb)
        self.rgb = rgb

    def __eq__(self, other):
        return self.rgb == other.rgb

    @property
    def css(self):
        return 'rgb(%d, %d, %d)' % self.rgb


class WarpThread(object):
    """
    Represents a single warp thread.
    """
    def __init__(self, color=None, shaft=None):
        if color and not isinstance(color, Color):
            color = Color(color)
        self.color = color
        self.shaft = shaft

    def __repr__(self):
        return '<WarpThread color:%s shaft:%s>' % (self.color.rgb, self.shaft)


class WeftThread(object):
    """
    Represents a single weft thread.
    """
    def __init__(self, color=None, shafts=None, treadles=None):
        if color and not isinstance(color, Color):
            color = Color(color)
        self.color = color
        assert not (shafts and treadles), \
            "can't have both shafts (liftplan) and treadles specified"
        self.treadles = treadles or set()
        self.shafts = shafts or set()

    @property
    def connected_shafts(self):
        if self.shafts:
            return self.shafts
        else:
            assert self.treadles
            ret = set()
            for treadle in self.treadles:
                ret.update(treadle.shafts)
            return ret

    def __repr__(self):
        if self.treadles:
            return '<WeftThread color:%s treadles:%s>' % (self.color.rgb,
                                                          self.treadles)
        else:
            return '<WeftThread color:%s shafts:%s>' % (self.color.rgb,
                                                        self.shafts)


class Shaft(object):
    """
    Represents a single shaft of the loom.
    """
    pass


class Treadle(object):
    """
    Represents a single treadle of the loom.
    """
    def __init__(self, shafts=None):
        self.shafts = shafts or set()


class DraftError(Exception):
    pass


class Draft(object):
    """
    The core representation of a weaving draft.
    """
    def __init__(self, num_shafts, num_treadles=0, liftplan=False,
                 rising_shed=True, start_at_lowest_thread=True,
                 date=None, title='', author='', address='',
                 email='', telephone='', fax='', notes=''):
        self.liftplan = liftplan or (num_treadles == 0)
        self.rising_shed = rising_shed
        self.start_at_lowest_thread = start_at_lowest_thread

        self.shafts = []
        for __ in range(num_shafts):
            self.shafts.append(Shaft())

        self.treadles = []
        for __ in range(num_treadles):
            self.treadles.append(Treadle())

        self.warp = []
        self.weft = []

        self.date = date or datetime.date.today().strftime('%b %d, %Y')

        self.title = title
        self.author = author
        self.address = address
        self.email = email
        self.telephone = telephone
        self.fax = fax
        self.notes = notes

    @classmethod
    def from_json(cls, s):
        """
        Construct a new Draft instance from its JSON representation.
        Counterpart to ``.to_json()``.
        """
        obj = json.loads(s)
        warp = obj.pop('warp')
        weft = obj.pop('weft')
        tieup = obj.pop('tieup')

        draft = cls(**obj)

        for thread_obj in warp:
            draft.add_warp_thread(
                color=thread_obj['color'],
                shaft=draft.shafts[thread_obj['shaft']],
            )

        for thread_obj in weft:
            draft.add_weft_thread(
                color=thread_obj['color'],
                shafts=set(draft.shafts[n] for n in thread_obj['shafts']),
                treadles=set(draft.treadles[n] for n in
                             thread_obj['treadles']),
            )

        for ii, shaft_nos in enumerate(tieup):
            draft.treadles[ii].shafts = set(draft.shafts[n] for n in shaft_nos)

        return draft

    def to_json(self):
        """
        Serialize a Draft to its JSON representation. Counterpart to
        ``.from_json()``.
        """
        return json.dumps({
            'liftplan': self.liftplan,
            'rising_shed': self.rising_shed,
            'num_shafts': len(self.shafts),
            'num_treadles': len(self.treadles),
            'warp': [{
                'color': thread.color.rgb,
                'shaft': self.shafts.index(thread.shaft),
            } for thread in self.warp],
            'weft': [{
                'color': thread.color.rgb,
                'treadles': [self.treadles.index(tr)
                             for tr in thread.treadles],
                'shafts': [self.shafts.index(sh)
                           for sh in thread.connected_shafts],
            } for thread in self.weft],
            'tieup': [
                [self.shafts.index(sh) for sh in treadle.shafts]
                for treadle in self.treadles
            ],
            'date': self.date,
            'title': self.title,
            'author': self.author,
            'address': self.address,
            'email': self.email,
            'telephone': self.telephone,
            'fax': self.fax,
            'notes': self.notes,
        })

    def copy(self):
        """
        Make a complete copy of this draft.
        """
        return deepcopy(self)

    def add_warp_thread(self, color=None, index=None, shaft=0):
        """
        Add a warp thread to this draft.
        """
        if not isinstance(shaft, Shaft):
            shaft = self.shafts[shaft]
        thread = WarpThread(
            color=color,
            shaft=shaft,
        )
        if index is None:
            self.warp.append(thread)
        else:
            self.warp.insert(index, thread)

    def add_weft_thread(self, color=None, index=None,
                        shafts=None, treadles=None):
        """
        Add a weft thread to this draft.
        """
        shafts = shafts or set()
        shaft_objs = set()
        for shaft in shafts:
            if not isinstance(shaft, Shaft):
                shaft = self.shafts[shaft]
            shaft_objs.add(shaft)
        treadles = treadles or set()
        treadle_objs = set()
        for treadle in treadles:
            if not isinstance(treadle, Treadle):
                treadle = self.treadles[treadle]
            treadle_objs.add(treadle)
        thread = WeftThread(
            color=color,
            shafts=shaft_objs,
            treadles=treadle_objs,
        )
        if index is None:
            self.weft.append(thread)
        else:
            self.weft.insert(index, thread)

    def compute_drawdown_at(self, position):
        """
        Return the thread that is on top (visible) at the specified
        zero-indexed position.
        """
        x, y = position
        warp_thread = self.warp[x]
        weft_thread = self.weft[y]

        connected_shafts = weft_thread.connected_shafts
        warp_at_rest = warp_thread.shaft not in connected_shafts
        if warp_at_rest ^ self.rising_shed:
            return warp_thread
        else:
            return weft_thread

    def compute_drawdown(self):
        """
        Compute a 2D array containing the thread visible at each position.
        """
        num_warp_threads = len(self.warp)
        num_weft_threads = len(self.weft)
        return [[self.compute_drawdown_at((x, y))
                 for y in range(num_weft_threads)]
                for x in range(num_warp_threads)]

    def compute_floats(self):
        """
        Return an iterator over every float, yielding a tuple for each one::

            (start, end, visible, length, thread)

        FIXME: This ignores the back side of the fabric. Should it?
        """
        num_warp_threads = len(self.warp)
        num_weft_threads = len(self.weft)

        drawdown = self.compute_drawdown()

        # Iterate over each warp thread, then each weft thread
        # For each thread, find the position of each change in state
        for x, thread in enumerate(self.warp):
            this_vis_state = (thread == drawdown[x][0])
            last = this_start = (x, 0)
            for y in range(1, num_weft_threads):
                check_vis_state = (thread == drawdown[x][y])
                if check_vis_state != this_vis_state:
                    length = last[1] - this_start[1]
                    yield this_start, last, this_vis_state, length, thread
                    this_vis_state = check_vis_state
                    this_start = x, y
                last = x, y
            length = last[1] - this_start[1]
            yield this_start, last, this_vis_state, length, thread

        for y, thread in enumerate(self.weft):
            this_vis_state = (thread == drawdown[0][y])
            last = this_start = (0, y)
            for x in range(1, num_warp_threads):
                check_vis_state = (thread == drawdown[x][y])
                if check_vis_state != this_vis_state:
                    length = last[0] - this_start[0]
                    yield this_start, last, this_vis_state, length, thread
                    this_vis_state = check_vis_state
                    this_start = x, y
                last = x, y
            length = last[0] - this_start[0]
            yield this_start, last, this_vis_state, length, thread

    def compute_longest_floats(self):
        """
        Return a tuple indicating the longest floats for warp, weft.

        FIXME This might be producing incorrect results.
        """
        floats = list(self.compute_floats())
        return (
            max(length
                for start, end, visible, length, thread in floats
                if isinstance(thread, WarpThread)),
            max(length
                for start, end, visible, length, thread in floats
                if isinstance(thread, WeftThread)),
        )

    def reduce_shafts(self):
        """
        Optimize to use the fewest number of shafts, to attempt to make a
        complex draft possible to weave on a loom with fewer shafts. Note that
        this may make the threading more complex or less periodic.
        """
        raise NotImplementedError

    def reduce_treadles(self):
        """
        Optimize to use the fewest number of total treadles, to attempt to make
        a complex draft possible to weave on a loom with a smaller number of
        treadles. Note that this may require that more treadles are active on
        any given pick.

        Cannot be called on a liftplan draft.
        """
        raise NotImplementedError

    def reduce_active_treadles(self):
        """
        Optimize to use the fewest number of active treadles on any given pick,
        because not every weaver is an octopus. Note that this may mean using
        more total treadles.

        Cannot be called on a liftplan draft.
        """
        if self.liftplan:
            raise ValueError("can't reduce treadles on a liftplan draft")
        if True or max(len(thread.treadles) for thread in self.weft) > 1:
            used_shaft_combos = defaultdict(list)
            for thread in self.weft:
                used_shaft_combos[frozenset(thread.connected_shafts)].\
                    append(thread)
            self.treadles = []
            for shafts, threads in used_shaft_combos.items():
                treadle = Treadle(shafts=set(shafts))
                self.treadles.append(treadle)
                for thread in threads:
                    thread.treadles = set([treadle])

    def sort_threading(self):
        """
        Reorder the shaft assignment in threading so that it follows as
        sequential of an order as possible.

        For a liftplan draft, will change the threading and liftplan.

        For a treadled draft, will change the threading and tieup, won't change
        the treadling.
        """
        raise NotImplementedError

    def sort_treadles(self):
        """
        Reorder the treadle assignment in tieup so that it follows as
        sequential of an order as possible in treadling.

        Will change the tieup and treadling, won't change the threading. If
        sorting both threading and treadles, call ``.sort_threading()`` before
        calling ``.sort_treadles()``.

        Cannot be called on a liftplan draft.
        """
        raise NotImplementedError

    def invert_shed(self):
        """
        Convert from rising shed to sinking shed, or vice versa. Note that this
        will actually update the threading/tie-up to preserve the same
        drawdown: if this is not desired, simply change the .rising_shed
        attribute.
        """
        self.rising_shed = not self.rising_shed
        for thread in self.weft:
            thread.shafts = self.shafts - thread.shafts
        for treadle in self.treadles:
            treadle.shafts = self.shafts - treadle.shafts

    def rotate(self):
        """
        Rotate the draft: the weft becomes the warp, and vice versa.
        """
        raise NotImplementedError

    def flip_weftwise(self):
        """
        Flip/mirror along the weft axis: e.g. looking at the front of the loom,
        the left side of the fabric becomes the right, and the right becomes
        the left.
        """
        self.warp.reverse()

    def flip_warpwise(self):
        """
        Flip/mirror along the warp axis: e.g. looking at the front of the loom,
        the near side of the fabric becomes the far, and the far becomes
        the near.
        """
        self.weft.reverse()

    def selvedges_continuous(self):
        """
        Check whether or not both selvedge threads are "continuous" (will be
        picked up on every pick).
        """
        return (self.selvedge_continuous(False) and
                self.selvedge_continuous(True))

    def selvedge_continuous(self, low):
        """
        Check whether the selvedge corresponding to the lowest-number thread is
        continuous.
        """
        # For the low selvedge:
        # If this draft starts at the lowest thread, there needs to be a
        # transition between threads 1 and 2 (0-indexed), threads 3 and 4, etc.
        # Otherwise, there needs to be a transition between 0 and 1, 2 and 3,
        # etc.

        # For the high selvedge:
        # If this draft starts at the highest thread, there needs to be a
        # transition between threads 0 and 1, threads 2 and 3, etc.

        offset = 0 if low ^ self.start_at_lowest_thread else 1
        if low:
            thread = self.warp[0]
        else:
            thread = self.warp[-1]
        for ii in range(offset, len(self.weft) - 1, 2):
            a_state = thread.shaft in self.weft[ii].connected_shafts
            b_state = thread.shaft in self.weft[ii + 1].connected_shafts
            if not a_state ^ b_state:
                return False
        return True

    def make_selvedges_continuous(self, add_new_shafts=False):
        """
        Make the selvedge threads "continuous": that is, threaded and treadled
        such that they are picked up on every pick. This method will try to use
        the liftplan/tieup and switch selvedge threads to alternate shafts. If
        that is impossible and ``add_new_shafts`` new shafts will be added to
        handle the selvedge threads.

        FIXME This method works, but it does not necessarily produce the
        subjectively "best" solution in terms of aesthetics and structure. For
        example, it may result in longer floats than necessary.
        """
        for low_thread in (False, True):
            success = False
            if low_thread:
                warp_thread = self.warp[0]
            else:
                warp_thread = self.warp[-1]
            if self.selvedge_continuous(low_thread):
                success = True
                continue
            for shaft in self.shafts:
                warp_thread.shaft = shaft
                if self.selvedge_continuous(low_thread):
                    success = True
                    break
            if not success:
                if add_new_shafts:
                    raise NotImplementedError
                else:
                    raise DraftError("cannot make continuous selvedges")

    def compute_weft_crossings(self):
        """
        Iterate over each weft row and compute the total number of thread
        crossings in that row. Useful for determining sett.
        """
        raise NotImplementedError

    def compute_warp_crossings(self):
        """
        Iterate over each warp row and compute the total number of thread
        crossings in that row.
        """
        raise NotImplementedError

    def repeat(self, n):
        """
        Given a base draft, make it repeat with N units in each direction.
        """
        initial_warp = list(self.warp)
        initial_weft = list(self.weft)
        for ii in range(n):
            for thread in initial_warp:
                self.add_warp_thread(
                    color=thread.color,
                    shaft=thread.shaft,
                )
            for thread in initial_weft:
                self.add_weft_thread(
                    color=thread.color,
                    treadles=thread.treadles,
                    shafts=thread.shafts,
                )

    def advance(self):
        """
        Given a base draft, make it 'advance'. Essentially:
            1. Repeat the draft N times, where N is the number of shafts, in
            both the warp and weft directions.
            2. On each successive repeat, offset the threading by 1 additional
            shaft and the treadling by one additional treadle.
        """
        initial_warp = list(self.warp)
        initial_weft = list(self.weft)
        num_shafts = len(self.shafts)
        num_treadles = len(self.treadles)
        for ii in range(1, num_shafts):
            print("ADVANCE %d" % ii)
            for thread in initial_warp:
                print("  thread")
                initial_shaft = self.shafts.index(thread.shaft)
                print("    initial shaft: %d" % initial_shaft)
                new_shaft = (initial_shaft + ii) % num_shafts
                print("    new shaft: %d" % new_shaft)
                self.add_warp_thread(
                    color=thread.color,
                    shaft=new_shaft,
                )
            for thread in initial_weft:
                initial_treadles = [self.treadles.index(treadle)
                                    for treadle in thread.treadles]
                new_treadles = [(treadle + ii) % num_treadles
                                for treadle in initial_treadles]
                initial_shafts = [self.shafts.index(shaft)
                                  for shaft in thread.shafts]
                new_shafts = [(shaft + ii) % num_shafts
                              for shaft in initial_shafts]
                self.add_weft_thread(
                    color=thread.color,
                    treadles=new_treadles,
                    shafts=new_shafts,
                )

    def all_threads_attached(self):
        """
        Check whether all threads (weft and warp) will be "attached" to the
        fabric, instead of just falling off.
        """
        raise NotImplementedError
