from ConfigParser import RawConfigParser

from . import Draft, Thread


class WIFReader(object):
    """
    FIXME:
        - Use the COLOR PALETTE section, take particular note of Form (RGB) and
        Range (which might be 0-65535 instead of 0-255). Scale accordingly or
        whatever, normalize to our color objects.
    """
    allowed_units = ('decipoints', 'inches', 'centimeters')

    def __init__(self, filename):
        self.filename = filename

    def getbool(self, section, option):
        if self.config.has_option(section, option):
            return self.config.getboolean(section, option)
        else:
            return False

    def put_metadata(self, draft):
        draft.date = self.config.get('WIF', 'Date')
        # XXX Name, author, notes, etc.

    def put_warp(self, draft, wif_palette):
        warp_thread_count = self.config.getint('WARP', 'Threads')
        warp_units = self.config.get('WARP', 'Units').lower()
        assert warp_units in self.allowed_units, \
            "Warp Units of %r is not understood" % warp_units

        # warp_spacing = self.config.get('WARP', 'Spacing')
        # warp_thickness = self.config.get('WARP', 'Thickness')

        has_warp_colors = self.getbool('CONTENTS', 'WARP COLORS')

        if has_warp_colors:
            warp_color_map = {}
            for thread_no, value in self.config.items('WARP COLORS'):
                warp_color_map[int(thread_no)] = int(value)
        else:
            warp_color_map = None

        warp_color = None
        if not warp_color_map:
            # try to get warp color from WARP section
            has_warp_colors = False
            warp_color = self.config.getint('WARP', 'Color')

        has_threading = self.getbool('CONTENTS', 'THREADING')

        if has_threading:
            threading_map = {}
            for thread_no, value in self.config.items('THREADING'):
                threading_map[int(thread_no)] = \
                    [int(sn) for sn in value.split(',')]

        for thread_no in range(1, warp_thread_count + 1):
            # NOTE: Some crappy software will generate WIFs with way more
            # threads in the warp or weft section than mentioned in the
            # threading. To ignore that, make sure that this thread actually
            # has threading specified: otherwise it's unused.
            if thread_no in threading_map:
                if has_warp_colors:
                    color = wif_palette[warp_color_map[thread_no]]
                else:
                    color = wif_palette[warp_color]

                if has_threading:
                    shafts = set(draft.shafts[shaft_no - 1]
                                 for shaft_no in threading_map[thread_no])
                else:
                    shafts = set()

                draft.warp.append(Thread(
                    dir='warp',
                    color=color,
                    shafts=shafts,
                ))

    def put_weft(self, draft, wif_palette):
        weft_thread_count = self.config.getint('WEFT', 'Threads')
        weft_units = self.config.get('WEFT', 'Units').lower()
        assert weft_units in self.allowed_units, \
            "Weft Units of %r is not understood" % weft_units
        # weft_spacing = self.config.get('WEFT', 'Spacing')
        # weft_thickness = self.config.get('WEFT', 'Thickness')

        has_weft_colors = self.getbool('CONTENTS', 'WEFT COLORS')

        if has_weft_colors:
            weft_color_map = {}
            for thread_no, value in self.config.items('WEFT COLORS'):
                weft_color_map[int(thread_no)] = int(value)
        else:
            weft_color_map = None

        weft_color = None
        if not weft_color_map:
            # try to get weft color from WEFT section
            has_weft_colors = False
            weft_color = self.config.getint('WEFT', 'Color')

        has_liftplan = self.getbool('CONTENTS', 'LIFTPLAN')

        if has_liftplan:
            liftplan_map = {}
            for thread_no, value in self.config.items('LIFTPLAN'):
                liftplan_map[int(thread_no)] = \
                    [int(sn) for sn in value.split(',')]

        has_treadling = self.getbool('CONTENTS', 'TREADLING')

        if has_treadling:
            treadling_map = {}
            for thread_no, value in self.config.items('TREADLING'):
                try:
                    treadles = [int(tn) for tn in value.split(',')]
                except ValueError:
                    pass
                else:
                    treadling_map[int(thread_no)] = treadles

        for thread_no in range(1, weft_thread_count + 1):
            if (has_liftplan and (thread_no in liftplan_map)) or \
                    (has_treadling and (thread_no in treadling_map)):
                if has_weft_colors:
                    color = wif_palette[weft_color_map[thread_no]]
                else:
                    color = wif_palette[weft_color]

                if has_liftplan:
                    shafts = set(draft.shafts[shaft_no - 1]
                                 for shaft_no in liftplan_map[thread_no])
                else:
                    shafts = set()

                if has_treadling:
                    treadles = set(draft.treadles[treadle_no - 1]
                                   for treadle_no in treadling_map[thread_no])
                else:
                    treadles = set()

                draft.weft.append(Thread(
                    dir='weft',
                    color=color,
                    shafts=shafts,
                    treadles=treadles,
                ))

    def put_tieup(self, draft):
        for treadle_no, value in self.config.items('TIEUP'):
            treadle = draft.treadles[int(treadle_no) - 1]
            shaft_nos = [int(sn) for sn in value.split(',')]
            for shaft_no in shaft_nos:
                shaft = draft.shafts[shaft_no - 1]
                treadle.shafts.add(shaft)

    def read(self):
        self.config = RawConfigParser()
        self.config.read(self.filename)

        rising_shed = self.getbool('WEAVING', 'Rising Shed')
        num_shafts = self.config.getint('WEAVING', 'Shafts')
        num_treadles = self.config.getint('WEAVING', 'Treadles')

        liftplan = self.getbool('CONTENTS', 'LIFTPLAN')
        treadling = self.getbool('CONTENTS', 'TREADLING')
        assert not (liftplan and treadling), \
            "WIF contains both liftplan and treadling"
        assert not (liftplan and (num_treadles > 0)), \
            "WIF contains liftplan and non-zero treadle count"

        if self.getbool('CONTENTS', 'COLOR PALETTE'):
            # XXX
            # palette_form = self.config.get('COLOR PALETTE', 'Form')
            palette_range = self.config.get('COLOR PALETTE', 'Range')
            rstart, rend = palette_range.split(',')
            palette_range = int(rstart), int(rend)
        else:
            # palette_form = 'RGB'
            palette_range = 0, 255

        if self.getbool('CONTENTS', 'COLOR TABLE'):
            wif_palette = {}
            for color_no, value in self.config.items('COLOR TABLE'):
                channels = [int(ch) for ch in value.split(',')]
                channels = [int(round(ch * (255. / palette_range[1])))
                            for ch in channels]
                wif_palette[int(color_no)] = channels
        else:
            wif_palette = None

        draft = Draft(num_shafts=num_shafts,
                      num_treadles=num_treadles,
                      rising_shed=rising_shed)

        self.put_metadata(draft)
        self.put_warp(draft, wif_palette)
        self.put_weft(draft, wif_palette)
        self.put_tieup(draft)

        return draft


class WIFWriter(object):

    def __init__(self, filename):
        self.filename = filename

    def write(self):
        config = RawConfigParser()

        config.write(self.filename)
