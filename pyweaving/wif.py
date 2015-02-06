from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from ConfigParser import RawConfigParser

from . import Draft, __version__


class WIFReader(object):
    """
    A reader for a specific WIF file.
    """

    # TODO
    # - add support for metadata: author, notes, etc.
    # - add support for warp/weft spacing and thickness
    # - ensure that we're correctly handling the 'palette form' (might be only
    # RGB?)

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
                    assert len(shafts) == 1
                    shaft = list(shafts)[0]
                else:
                    shaft = None

                draft.add_warp_thread(
                    color=color,
                    shaft=shaft,
                )

    def put_weft(self, draft, wif_palette):
        weft_thread_count = self.config.getint('WEFT', 'Threads')
        weft_units = self.config.get('WEFT', 'Units').lower()
        assert weft_units in self.allowed_units, \
            "Weft Units of %r is not understood" % weft_units

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

                draft.add_weft_thread(
                    color=color,
                    shafts=shafts,
                    treadles=treadles,
                )

    def put_tieup(self, draft):
        for treadle_no, value in self.config.items('TIEUP'):
            treadle = draft.treadles[int(treadle_no) - 1]
            shaft_nos = [int(sn) for sn in value.split(',')]
            for shaft_no in shaft_nos:
                shaft = draft.shafts[shaft_no - 1]
                treadle.shafts.add(shaft)

    def read(self):
        """
        Perform the actual parsing, and return a Draft instance.
        """
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
            palette_range = self.config.get('COLOR PALETTE', 'Range')
            rstart, rend = palette_range.split(',')
            palette_range = int(rstart), int(rend)
        else:
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
        if treadling:
            self.put_tieup(draft)

        return draft


class WIFWriter(object):
    """
    A WIF writer for a draft.
    """

    # TODO
    # - support greater color depth (may require change to Color)

    def __init__(self, draft):
        self.draft = draft

    def write_metadata(self, config, liftplan):
        config.add_section('WIF')
        config.set('WIF', 'Date', self.draft.date)
        config.set('WIF', 'Version', '1.1')
        config.set('WIF', 'Developers', 'storborg@gmail.com')
        config.set('WIF', 'Source Program', 'PyWeaving')
        config.set('WIF', 'Source Version', __version__)

        config.set('CONTENTS', 'WEAVING', 1)
        config.add_section('WEAVING')
        config.set('WEAVING', 'Rising Shed', self.draft.rising_shed)
        config.set('WEAVING', 'Shafts', len(self.draft.shafts))
        config.set('WEAVING', 'Treadles',
                   0 if liftplan else len(self.draft.treadles))

        config.set('CONTENTS', 'TEXT', 1)
        config.add_section('TEXT')
        config.set('TEXT', 'Title', self.draft.title)
        config.set('TEXT', 'Author', self.draft.author)
        config.set('TEXT', 'Address', self.draft.address)
        config.set('TEXT', 'EMail', self.draft.email)
        config.set('TEXT', 'Telephone', self.draft.telephone)
        config.set('TEXT', 'FAX', self.draft.fax)

        if self.draft.notes:
            config.set('CONTENTS', 'NOTES', 1)
            config.add_section('NOTES')
            for ii, line in enumerate(self.draft.notes.split('\n')):
                config.set('NOTES', str(ii), line)

    def write_palette(self, config):
        # generate the color table and write it to the config
        # return a wif_palette mapping color instances to numbers.
        colors = set(thread.color.rgb for thread in
                     self.draft.warp + self.draft.weft)
        wif_palette = {}
        config.set('CONTENTS', 'COLOR TABLE', 1)
        config.add_section('COLOR TABLE')
        for ii, color in enumerate(colors, start=1):
            val = '%d,%d,%d' % color
            config.set('COLOR TABLE', str(ii), val)
            wif_palette[color] = ii

        config.set('CONTENTS', 'COLOR PALETTE', 1)
        config.add_section('COLOR PALETTE')
        config.set('COLOR PALETTE', 'Form', 'RGB')
        config.set('COLOR PALETTE', 'Range', '0,255')
        return wif_palette

    def write_threads(self, config, wif_palette, dir):
        assert dir in ('warp', 'weft')
        threads = getattr(self.draft, dir)
        dir = dir.upper()
        config.set('CONTENTS', dir, 1)
        config.add_section(dir)
        config.set(dir, 'Threads', len(threads))
        # XXX This should actually be stored in the draft.
        config.set(dir, 'Units', 'Inches')

        config.set('CONTENTS', '%s COLORS' % dir, 1)
        config.add_section('%s COLORS' % dir)
        for ii, thread in enumerate(threads, start=1):
            config.set('%s COLORS' % dir,
                       str(ii),
                       wif_palette[thread.color.rgb])

    def write_threading(self, config):
        config.set('CONTENTS', 'THREADING', 1)
        config.add_section('THREADING')

        for ii, thread in enumerate(self.draft.warp, start=1):
            shaft_string = str(self.draft.shafts.index(thread.shaft) + 1)
            config.set('THREADING', str(ii), shaft_string)

    def write_liftplan(self, config):
        config.set('CONTENTS', 'LIFTPLAN', 1)
        config.add_section('LIFTPLAN')

        for ii, thread in enumerate(self.draft.weft, start=1):
            shaft_nos = [self.draft.shafts.index(shaft) + 1
                         for shaft in thread.connected_shafts]
            shaft_string = ','.join([str(shaft_no) for shaft_no in shaft_nos])
            config.set('LIFTPLAN', str(ii), shaft_string)

    def write_treadling(self, config):
        config.set('CONTENTS', 'TREADLING', 1)
        config.add_section('TREADLING')

        for ii, thread in enumerate(self.draft.weft, start=1):
            treadle_nos = [self.draft.treadles.index(treadle) + 1
                           for treadle in thread.treadles]
            treadle_string = ','.join([str(treadle_no) for treadle_no in
                                       treadle_nos])
            config.set('TREADLING', str(ii), treadle_string)

    def write_tieup(self, config):
        config.set('CONTENTS', 'TIEUP', 1)
        config.add_section('TIEUP')

        for ii, treadle in enumerate(self.draft.treadles, start=1):
            shaft_nos = [self.draft.shafts.index(shaft) + 1
                         for shaft in treadle.shafts]
            shaft_string = ','.join([str(shaft_no) for shaft_no in shaft_nos])
            config.set('TIEUP', str(ii), shaft_string)

    def write(self, filename, liftplan=False):
        assert self.draft.start_at_lowest_thread

        config = RawConfigParser()
        config.optionxform = str
        config.add_section('CONTENTS')

        self.write_metadata(config, liftplan=liftplan)

        wif_palette = self.write_palette(config)
        self.write_threads(config, wif_palette, 'warp')
        self.write_threads(config, wif_palette, 'weft')

        self.write_threading(config)
        if liftplan or not self.draft.treadles:
            self.write_liftplan(config)
        else:
            self.write_treadling(config)
            self.write_tieup(config)

        with open(filename, 'wb') as f:
            config.write(f)
