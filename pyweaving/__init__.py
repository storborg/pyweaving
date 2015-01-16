import datetime
import json
from copy import deepcopy
from collections import defaultdict


__version__ = '0.0'


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


class Draft(object):
    """
    The core representation of a weaving draft.
    """
    def __init__(self, num_shafts, num_treadles=0, liftplan=False,
                 rising_shed=True, date=None, title='', author='', address='',
                 email='', telephone='', fax='', notes=''):
        self.liftplan = liftplan or (num_treadles == 0)
        self.rising_shed = rising_shed

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
                if thread.dir == 'warp'),
            max(length
                for start, end, visible, length, thread in floats
                if thread.dir == 'weft')
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

    def add_stable_selvedges(self):
        """
        Add new selvedge threads which are "stable": that is, they are picked
        up on every pick. This method will try to use the liftplan/tieup and
        add threads to existing shafts, but if it is not possible, new shafts
        will be added.
        """
        raise NotImplementedError
