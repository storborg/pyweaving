#!/usr/python

# Draft and associated Classes


import datetime
import json
from copy import deepcopy
from collections import defaultdict

from .Color import Color


class WarpThread(object):
    """
    Represents a single warp thread. Its Color, Spacing, and which Shaft it is on.

    Args:
        color (Color|RGB tuple|hexstring): Thread color
        shaft (Shaft): Shaft this thread is on,
        spacing (float): size of spacing of this thread.
    """
    def __init__(self, color=None, shaft=None, spacing=None):
        if color and not isinstance(color, Color):
            color = Color(color, True)
        self._color = color
        self.shaft = shaft
        self.spacing = spacing
        self.css_label = None  # for SVG styles

    @property
    def color(self):
        """
        Color of this thread

        Args:
        color (Color):
        """
        return self._color

    @color.setter
    def color(self, color):
        if color and not isinstance(color, Color):
            color = Color(color, True)
        # print("setter method called", color)
        self._color = color

    def __repr__(self):
        return '<WarpThread color:%s shaft:%s>' % (self.color.rgb, self.shaft)


class WeftThread(object):
    """
    Represents a single weft thread. Has Shaft or Treadle depending
    on whether draft is only a Liftplan and has no Treadles.

    Args:
        color (Color|RGB tuple|hexstring): Thread color
        shafts (list of Shaft): If Liftplan only the Shafts this thread is on else None.
        treadles (list of Treadle): Treadles this weft thread is driven by.
        spacing (float): size of spacing of this thread.
    """
    def __init__(self, color=None, shafts=None, treadles=None, spacing=None):
        if color and not isinstance(color, Color):
            color = Color(color, True)
        self._color = color
        self.treadles = treadles or set()   # has treadles if not liftplan
        self.shafts = shafts or set()       # has shafts if a liftplan
        self.spacing = spacing
        self.css_label = None  # for SVG styles

    @property
    def connected_shafts(self):
        """
        The shafts that this weft thread affects. Drawn from Shafts if only a liftplan is described.
        Drawn from Treadles if Treadling defined.
        """
        if self.shafts:
            return self.shafts
        else:
            # assert self.treadles #!!
            ret = set()
            for treadle in self.treadles:
                ret.update(treadle.shafts)
            return ret

    @property
    def color(self):
        """
        Color of this thread

        Args:
        color (Color):
        """
        return self._color

    @color.setter
    def color(self, color):
        if color and not isinstance(color, Color):
            color = Color(color, True)
        self._color = color

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

    Args:
        index (int): 1 based index of this Shaft on the loom.
    """
    def __init__(self, index):
        self.index = index

    def __repr__(self):
        return '<Shaft %d>' % (self.index)


class Treadle(object):
    """
    Represents a single treadle of the loom.

    Args:
        index (int): 1 based index of this Treadle on the loom.
        shafts (list of Shaft): The Shafts this treadle affects.
    """
    def __init__(self, index, shafts=None):
        self.shafts = shafts or set()
        self.index = index

    def __repr__(self):
        return '<Treadle %d, using shafts %s>' % (self.index, sorted([s.index for s in self.shafts]))


class DraftError(Exception):
    pass


class Draft(object):
    """
    The core representation of a weaving draft.

    Args:
        num_shafts (int): how many shafts oin this draft,
        num_treadles (int, optional): how many Treadles in this draft,
        liftplan (bool, optional): True if only a liftplan is described in this draft,
        rising_shed (bool, optional): True if Rising shed draft,
        start_at_lowest_thread (bool, optional): True,
        date (str, optional): Date of Draft creation in datetime format,
        title (str, optional): Draft Title,
        author (str, optional): Draft Author,
        address (str, optional): Author's address,
        email (str, optional): Author's Email,
        telephone (str, optional): Author's Title,
        fax (str, optional): Author's Title,
        notes (list of str, optional): List of text strings
        weft_units (str, optional): inches | centimeters | decimeters
        warp_units (str, optional): inches | centimeters | decimeters
    """
    def __init__(self, num_shafts, num_treadles=0, liftplan=False,
                 rising_shed=True, start_at_lowest_thread=True,
                 date=None, title='', author='', address='',
                 email='', telephone='', fax='', notes=[],
                 weft_units='centimeters', warp_units='centimeters'):
        self.liftplan = liftplan or (num_treadles == 0)
        self.rising_shed = rising_shed
        self.start_at_lowest_thread = start_at_lowest_thread

        self.shafts = []
        for i in range(num_shafts):
            self.shafts.append(Shaft(i+1))

        self.treadles = []
        for i in range(num_treadles):
            self.treadles.append(Treadle(i+1))

        self.warp = []  # holds the WarpThreads
        self.weft = []  # holds the WeftThreads
        # unique yarn spacing,color stats from gather_metrics()
        self.thread_stats = {"weft": [],             # list of (colour,spacing,count)
                             "warp": [],             # list of (colour,spacing,count)
                             "warp_spacings": [],    # list of (spacing,count)
                             "weft_spacings": [],    # list of (spacing,count)
                             "summary": [],          # list of spacings
                             "warp_ratio": [],       # value of Warp/Weft balance
                             "unique_threads":  [],  # number of unique threads used in draft
                             "selvedge_floats": [],  # list of lengths of warp threads on sides
                             }

        # css labels for svg
        self.css_colors = []

        self.warp_units = warp_units
        self.weft_units = weft_units

        # Only used when saving -overwritten on load
        self.creation_date = datetime.datetime.now().strftime("%A, %B %d, %Y, %H:%M")  # '%b %d, %Y')

        self.date = date
        self.title = title
        self.author = author
        self.address = address
        self.email = email
        self.telephone = telephone
        self.fax = fax
        self.notes = notes
        self.collected_notes = []
        self.draft_title = []  # multiple line of title from wif and filename

        self.source_program = None  # "PyWeaving" #! set when saving
        self.source_version = None  # __version__

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
                spacing=thread_obj['spacing'],
            )

        for thread_obj in weft:
            draft.add_weft_thread(
                color=thread_obj['color'],
                shafts=set(draft.shafts[n] for n in thread_obj['shafts']),
                treadles=set(draft.treadles[n] for n in
                             thread_obj['treadles']),
                spacing=thread_obj['spacing'],
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
            'warp_units': self.warp_units,
            'weft_units': self.weft_units,
            'warp': [{
                'color': thread.color.rgb,
                'shaft': self.shafts.index(thread.shaft),
                'spacing': thread.spacing,
            } for thread in self.warp],
            'weft': [{
                'color': thread.color.rgb,
                'treadles': [self.treadles.index(tr)
                             for tr in thread.treadles],
                'shafts': [self.shafts.index(sh)
                           for sh in thread.connected_shafts],
                'spacing': thread.spacing,
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
        }, ensure_ascii=False)

    def copy(self):
        """
        Return a complete copy of this draft.
        """
        return deepcopy(self)

    def add_warp_thread(self, color=None, index=None, shaft=None, spacing=None):
        """
        Add a warp thread to this draft.
         - shaft may be None, an integer or a member of self.shafts

        Args:
            color (Color|RGB tuple|hexstring, optional): Thread color
            index (int, optional): Needs to be unique,
            shaft (Shaft, optional): Shaft this thread is on,
            spacing (float, optional): size of spacing of this thread.
        """
        if isinstance(shaft, int):
            shaft = self.shafts[shaft]

        if index is None:
            thread = WarpThread(color=color,
                                shaft=shaft,
                                spacing=spacing)
            self.warp.append(thread)
        else:  # threads not in numerical order
            if index > len(self.warp):
                for i in range(index - len(self.warp)):  # +1
                    self.warp.append(WarpThread())
            thread = self.warp[index]
            thread.color = color
            thread.shaft = shaft
            thread.spacing = spacing

    def add_weft_thread(self, color=None, index=None,
                        shafts=None, treadles=None, spacing=None):
        """
        Add a weft thread to this draft.
         - shafts may be None, an integer or a member of self.shafts

        Args:
            color (Color|RGB tuple|hexstring): Thread color
            index (int, optional): Needs to be unique,
            shafts (list of Shaft): If Liftplan only the Shafts this thread is on else None.
            treadles (list of Treadle): Treadles this weft thread is driven by.
            spacing (float): size of spacing of this thread.
        """
        shafts = shafts or set()
        shaft_objs = set()
        for shaft in shafts:
            if isinstance(shaft, int):
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
            spacing=spacing,
        )
        if index is None:
            self.weft.append(thread)
        else:
            if index > len(self.weft):
                for i in range(index - len(self.weft)):  # +1
                    self.weft.append(WeftThread())
            thread = self.weft[index]
            thread.color = color
            thread.shaft = shaft_objs
            thread.treadles = treadle_objs,
            thread.spacing = spacing

    def assign_css_labels(self, threads, stats, suffix):
        """
        Assign css labels to unique threads in warp and weft independently.
        I.e. Find all the unique color/spacing combinations and collate to a minimal set.
        Used by SVG renderer only (for efficiency).

            - Called from process_draft()
            - Collect colors in self.css_colors

        Args:
            threads (list): of WarpThreads or WeftThreads to process,
            stats (list): list of warp or weft spacings per thread,
            suffix (str): will be warp or weft. Used to uniquely label.
        """
        # prep css labels
        labels = []
        for i, (c, s, _) in enumerate(stats):
            labels.append([c, s, i, "%scol%d" % (suffix, i)])
        # remember for svg hashing if required
        self.hash_colorkeys = labels
        # assign labels to threads
        for thread in threads:
            color = thread.color
            spacing = thread.spacing
            # find the right color/spacing match
            for c, s, i, name in labels:
                if c == color and s == spacing:
                    thread.css_label = name
                    # remember for svg hashing if required
                    thread.css_hash = i
                    break
        # remember name:color relationship for svg renderer
        self.css_colors.extend([[name, color] for color, _, _, name in labels])

    def _count_colour_spacings(self, threads):
        " threads are self.weft or self.warp - usedby gather_metrics"
        # extract weft color, spacing numbers
        stats = []  # pairs of (thread color, spacing)
        counter = []
        for thread in threads:
            t_data = (thread.color, thread.spacing)
            if t_data not in stats:
                stats.append(t_data)
                counter.append(1)
            else:
                index = stats.index(t_data)
                counter[index] += 1
        return [(c, s, i) for (c, s), i in zip(stats, counter)]

    def _count_spacings(self, thread_stats):
        " simplify thread_stats (c,s,i) to pairs of (spacing,count) - usedby gather_metrics"
        spacings = []
        counter = []
        for c, s, i in thread_stats:
            if s not in spacings:
                spacings.append(s)
                counter.append(i)
            else:
                index = spacings.index(s)
                counter[index] += i
        return list(zip(spacings, counter))

    def gather_metrics(self):
        """
        Loop through warp and weft threads, gathering unique spacings and colors
        so we can show spacings in drawdowns and use in informational stats.

         - also warp/weft balance
         - also list of unique threads from combined warp, weft
         - also warp floats on edges - E.g. will we need floating selvedges

        Keep everything in thread_stats by label:
         - 'weft' = color, spacing for each thread
         - 'warp' = same
         - 'weft_spacings' = sorted list of summary of weft'
         - 'warp_spacings' = same
         - 'summary' = summary of all spacings used (warp and weft)
         - 'warp_ratio' = warp count/ weft count
         - 'unique_threads' = list of all unique threads (col, spacing) in both warp and weft.
         - 'selvedge_floats' = longest float on a warp edge
        """
        # Extract weft color, spacing numbers
        self.thread_stats["weft"] = self._count_colour_spacings(self.weft)
        # simplify to pairs of (spacing,count)
        self.thread_stats["weft_spacings"] = sorted(self._count_spacings(self.thread_stats["weft"]))
        # warp
        self.thread_stats["warp"] = self._count_colour_spacings(self.warp)
        # simplify
        self.thread_stats["warp_spacings"] = sorted(self._count_spacings(self.thread_stats["warp"]))
        # Summary
        all_spacings = [s for (s, i) in self.thread_stats["weft_spacings"] if s]
        for (s, i) in self.thread_stats["warp_spacings"]:
            if s and s not in all_spacings:
                all_spacings.append(s)
        self.thread_stats["summary"] = sorted(all_spacings)

        floats = self.computed_floats
        # Warp/WeftBalance
        warp_count = sum([length + 1 for start, end, visible, length, thread in floats
                         if visible and isinstance(thread, WarpThread)])
        weft_count = sum([length + 1 for start, end, visible, length, thread in floats
                         if visible and isinstance(thread, WeftThread)])
        self.thread_stats["warp_ratio"] = warp_count / max(weft_count, 1)  # !! twill error if badly formed floaty wif

        # Unique threads
        unique_threads = [[t[0], t[1]] for t in self.thread_stats["warp"]]
        for col2, sp2, _ in self.thread_stats["weft"]:
            found = False
            for color, spacing in unique_threads:
                if col2 == color and sp2 == spacing:
                    found = True
                    break
            if not found:
                unique_threads.append((col2, sp2))
        self.thread_stats["unique_threads"] = unique_threads

        # Floating Selvedges required ?
        start, end = 0, len(self.warp) - 1
        longest = [length for s, e, visible, length, thread in floats
                   if (s[0] == start or s[0] == end) and isinstance(thread, WarpThread)]
        self.thread_stats["selvedge_floats"] = longest

    def compute_drawdown_at(self, position):
        """
        Return the thread that is on top (visible) at the specified
        zero-indexed position.

        Args:
            position (tuple X,Y): position as (x,y) pair
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

    def process_draft(self):
        """
        After reading/creating a draft - do these processes to fill in some reporting datastructures
         - compute_floats(), gather_metrics(), assign_css_labels(),
         - collects notes into collected_notes
        """
        self.computed_floats = list(self.compute_floats())
        self.metrics = self.gather_metrics()
        # uniquely name each unique thread (warp,weft independent)
        self.assign_css_labels(self.warp, self.thread_stats["warp"], "warp")
        self.assign_css_labels(self.weft, self.thread_stats["weft"], "weft")
        # collate notes
        for n in self.notes:
            if n and n.lower() != "nil":
                self.collected_notes.append(n)
        if self.source_program:
            self.collected_notes.append("(source program: %s.  Version: %s)" % (self.source_program, self.source_version))
        if self.creation_date:
            self.collected_notes.append("(created on %s)" % (self.creation_date))

    def compute_floats(self):
        """
        Return an iterator over every float, yielding a tuple for each one::
        (start, end, visible, length, thread)

        Todo:
            This ignores the back side of the fabric. But we can get the back by inverting the tieup,
            or setting proper args to compute_longest_floats()
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

    def _longest_float(self, floats, front=True, cls=WarpThread):
        " Used by compute_longest_floats "
        lengths = [length for start, end, visible, length, thread in floats
                   if visible == front and isinstance(thread, cls)]
        # remove any that are same as warp length. Probably gaps in a gamp...
        warp_len = len(self.warp) - 1
        for i in range(lengths.count(warp_len)):
            lengths.remove(warp_len)
        if lengths:  # !!
            return max(lengths)
        else:
            return 0

    def compute_longest_floats(self, front=True, back=False):
        """
        Return tuple containing pair of longest floats for warp, weft.
        on one or both sides

        Args:
            front (bool): True and will process threads visible on the front,
            back (bool): True and will process threads visible on the back.
        """
        floats = self.computed_floats
        longest = []
        if front:
            longest.append(self._longest_float(floats, front, WarpThread))
            longest.append(self._longest_float(floats, front, WeftThread))
        if back:
            longest.append(self._longest_float(floats, back, WarpThread))
            longest.append(self._longest_float(floats, back, WeftThread))
        return longest

    def get_position(self, thread, start, end, boxsize, x_reversed=False):
        """
        Iterate over the threads calculating the proper position
        for any given float to be drawn in the drawdown

         - inefficient
         - should be stored on thread like yarn_width or in compute_floats

        Change compute_floats() to return this also.

        Args:
            thread (WarpThread | WeftThread): thread to test,
            start (int): start index into draft,
            end (int): end index into draft,
            boxsize: used if no spacing on thread,
            x_reversed (bool): False means count from the right hand side.
        """
        num_warp_threads = len(self.warp)
        # reversed for back of cloth
        step = -1
        if x_reversed:
            step = 1
        # if isinstance(thread, WarpThread):
            # print(thread,thread.spacing,thread.yarn_width) #!
        if thread.spacing:
            # starty (step through the wefts)
            w = 0
            for i in range(start[1]):
                w += self.weft[i].yarn_width
            starty = w
            # endy
            w = 0
            for i in range(end[1] + 1):
                w += self.weft[i].yarn_width
            endy = w
            # startx (step through the warps)
            w = 0
            for i in range(num_warp_threads - 1, end[0], -1):
                w += self.warp[i].yarn_width
            startx = w
            # endx
            w = 0
            for i in range(num_warp_threads - 1, start[0] - 1, -1):
                w += self.warp[i].yarn_width
            endx = w

        else:  # no spacing info so use pixels_per_square (boxsize)
            startx = (num_warp_threads - end[0] - 1) * boxsize
            starty = start[1] * boxsize
            endx = (num_warp_threads - start[0]) * boxsize
            endy = (end[1] + 1) * boxsize
        #
        result_start = (startx, starty)
        result_end = (endx, endy)
        return (result_start, result_end)

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

    def get_mini_stats(self):
        """
        Gather list of information for reporting:
         - thread counts, longest floats, color count,
         - warp/weft ratio, floating selvedge status
         - (gather_metric collected most of these)

        Returns:
            (list): of textual stats.
        """
        # Threadcounts
        stats = ["Threadcounts: Warp %d  Weft %d" % (len(self.warp), len(self.weft))]
        unique_thread_count = len(self.thread_stats["unique_threads"])
        # Shaft and treadle counts
        shafts = "%d shafts." % len(self.shafts)
        if not self.liftplan:
            shafts += " %d treadles." % (len(self.treadles))
        stats.append(shafts)
        # Unique yarns
        stats.append("%d unique yarns (color/spacing)" % (unique_thread_count))
        # Longest Floats
        floats = self.compute_longest_floats(True, True)
        front, back = floats[:2], floats[2:]
        stats.append("Longest floats: (warp/back) %d/%d , (weft/back) %d/%d" %
                     (front[0] + 1, back[0] + 1, front[1] + 1, back[1] + 1))
        # Warp/Weft ratio
        warp_ratio = self.thread_stats["warp_ratio"]
        if 0.8 < warp_ratio < 1.2:
            if warp_ratio == 1:  # special case exact balanced weave
                stats.append("Balanced weave warp:weft = 1 : {:d}".format(int(warp_ratio)))
            else:
                stats.append("Balanced weave warp:weft = 1 : {:.1f}".format(warp_ratio))
        elif warp_ratio < 1:
            stats.append("Weft dominant weave 1 : {:.1f}".format(warp_ratio))
        else:  # weft
            stats.append("Warp dominant weave 1 : {:.1f}".format(1 / warp_ratio))
        # Selvedges
        selvedge_floats = self.thread_stats["selvedge_floats"]
        if selvedge_floats and max(selvedge_floats) > 1:
            msg = "Floating Selvedges may be required. Longest edge warp float is: %d" % (max(selvedge_floats) + 1)
        else:
            msg = "Floating Selvedges not required."
        stats.append(msg)
        return stats

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
