from datetime import date


class Color(object):
    def __init__(self, rgb):
        if not isinstance(rgb, tuple):
            rgb = tuple(rgb)
        self.rgb = rgb

    def __eq__(self, other):
        return self.rgb == other.rgb


class Thread(object):
    def __init__(self, dir, color=None, shafts=None, treadles=None):
        self.dir = dir
        if color and not isinstance(color, Color):
            color = Color(color)
        self.color = color
        self.shafts = shafts or set()
        if treadles:
            assert dir == 'weft', "only weft threads can have treadles"
            self.treadles = treadles or set()

    def __repr__(self):
        return '<Thread %s color:%s>' % (self.dir, self.color.rgb)


class Shaft(object):
    def __init__(self, index):
        self.index = index


class Treadle(object):
    def __init__(self, index, shafts=None):
        self.index = index
        self.shafts = shafts or set()


class Draft(object):
    """
    Internal data model:

    Fields which are really save-specific:
        - version (1.1)
        - source program
        - source version
        - developers

    Plain fields:
        - date
        - title
        - author
        - address
        - email
        - telephone
        - fax

    Notes:
        - notes -- multi-line, stored in WIF as line-no-referenced

    Weaving:
        * shafts (generate from threading)
        * treadles (generate from tie-up or treadling)
        - rising shed (bool)

    Warp:
        * threads (generate from wrap thread listing)
        * warp palette (generate from warp thread listing)
        - symbol (??)
        - symbol number (??)
        - units (optional, required if spacing or thickness is used)
            -- Decipoints, Inches, or Centimeters in the WIF spec
        - spacing (optional, real)
        - thickness (optional, real)
        - spacing zoom (??)
        - thickness zoom (??)

    Weft:
        * threads (generate from weft thread listing)
        * weft palette (generate from weft thread listing)
        - symbol (??)
        - symbol number (??)
        - units (optional, required if spacing or thickness is used)
            -- Decipoints, Inches, or Centimeters in the WIF spec
        - spacing (optional, real)
        - thickness (optional, real)
        - spacing zoom (??)
        - thickness zoom (??)

    Tieup: (mapping of shafts to treadles)
        - ???

    Threading: (mapping of threads to shafts)
        - ???

    Treadling: (treadles used for each weft row) -- use either this OR
    liftplan?

    Liftplan: (shafts used for each weft row) -- use either this OR treadling?

    """
    def __init__(self, num_shafts, num_treadles=0, rising_shed=True):
        self.liftplan = (num_treadles == 0)
        self.rising_shed = rising_shed

        self.shafts = []
        for ii in range(num_shafts):
            self.shafts.append(Shaft(index=ii))

        self.treadles = []
        for ii in range(num_treadles):
            self.treadles.append(Treadle(index=ii))

        self.warp = []
        self.weft = []

        self.date = date.today().strftime('%s %d, %Y')

        self.title = ''
        self.author = ''
        self.address = ''
        self.email = ''
        self.telephone = ''
        self.fax = ''
        self.notes = ''

    def copy(self):
        pass

    def compute_drawdown_at(self, position):
        """
        Return the thread that is on top (visible) at the specified
        zero-indexed position.
        """
        x, y = position
        warp_thread = self.warp[x]
        weft_thread = self.weft[y]

        if self.liftplan:
            shafts = weft_thread.shafts
        else:
            treadles = weft_thread.treadles
            shafts = set()
            for treadle in treadles:
                shafts.update(treadle.shafts)

        warp_at_rest = shafts.isdisjoint(warp_thread.shafts)
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
        Return an iterator over every float, yielding a tuple for each one:
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
        """
        raise NotImplementedError

    def reduce_active_treadles(self):
        """
        Optimize to use the fewest number of active treadles on any given pick,
        because not every weaver is an octopus. Note that this may mean using
        more total treadles.
        """
        raise NotImplementedError

    def invert_shed(self):
        """
        Convert from rising shed to sinking shed, or vice versa. Note that this
        will actually update the threading/tie-up to preserve the same
        drawdown: if this is not desired, simply change the .rising_shed
        attribute.
        """
        raise NotImplementedError

    def flip_weftwise(self):
        """
        Flip/mirror along the weft axis: e.g. looking at the front of the loom,
        the left side of the fabric becomes the right, and the right becomes
        the left.
        """
        raise NotImplementedError

    def flip_warpwise(self):
        """
        Flip/mirror along the warp axis: e.g. looking at the front of the loom,
        the near side of the fabric becomes the far, and the far becomes
        the near.
        """
        raise NotImplementedError
