from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from six.moves.configparser import RawConfigParser

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
        self.zerobased = False # at least one author uses 0 based counting for threading/treadlineg/color entries in WARP and WEFT

    def getbool(self, section, option):
        if self.config.has_option(section, option):
            return self.config.getboolean(section, option)
        else:
            return False

    def put_metadata(self, draft):
        # generally date is always 1997 date of wif spec.
        draft.date = self.config.get('WIF', 'Date', fallback="April 20, 1997")
        # Name, author, notes, etc.
        draft.title = self.config.get('TEXT', 'Title', fallback="")
        draft.author = self.config.get('TEXT', 'Author', fallback="")
        draft.address = self.config.get('TEXT', 'Address', fallback="")
        draft.email = self.config.get('TEXT', 'EMail', fallback="")
        draft.telephone = self.config.get('TEXT', 'Telephone', fallback="")
        draft.fax = self.config.get('TEXT', 'FAX', fallback="")
        # Creation date
        # check for line starting "; Creation"
        creation_date = None
        if self.getbool('CONTENTS', 'TEXT'): 
            creation_date = [a for a in self.config.options("TEXT") if a.find("; Creation")==0]
        if creation_date:
            draft.creation_date = creation_date[0][11:]
        # Notes
        if self.getbool('CONTENTS', 'NOTES'):
            for line_no, note in self.config.items('NOTES'):
                if line_no not in [';','#']: # check for comments ourselves
                    draft.notes.append(note)
        # Source program
        draft.source_program = self.config.get('WIF', 'Source Program', fallback="unknown")
        draft.source_version = self.config.get('WIF', 'Source Version', fallback="unknown")
        if draft.source_program.find("Glassner")>-1 and draft.source_version =="1.0":
            self.zerobased = True
            # alas these wif files use a mix of zero and one based thread counting :(
        # setup  draft_title
        if draft.title == "":
            draft.draft_title =[]
        else:
            draft.draft_title = draft.title.split("//")
        if self.filename: draft.draft_title.append("from: "+self.filename)

    def put_warp(self, draft, wif_palette):
        warp_thread_count = self.config.getint('WARP', 'Threads')
        warp_units = self.config.get('WARP', 'Units', fallback='centimeters').lower()
        assert warp_units in self.allowed_units, \
            "Warp Units of %r is not understood" % warp_units
        draft.warp_units = warp_units

        has_warp_colors = self.getbool('CONTENTS', 'WARP COLORS')

        if has_warp_colors:
            warp_color_map = {}
            for thread_no, value in self.config.items('WARP COLORS'):
                if thread_no not in [';','#']: # check for comments ourselves
                    warp_color_map[int(thread_no)] = int(value)
        else:
            warp_color_map = None

        # get backup color if not in [WARP COLORS]
        warp_color = None
        if 'Color' in self.config['WARP']:
             warp_color = self.config.getint('WARP', 'Color')
             if self.zerobased : warp_color+=1
        if not warp_color_map:
            # try to get warp color from WARP section
            has_warp_colors = False

        has_threading = self.getbool('CONTENTS', 'THREADING')
        if not has_threading:
            print("WARNING: This wif file indicates it has no THREADING section. Please edit it to be true")
        threading_map = {}
        if has_threading:
            for thread_no, value in self.config.items('THREADING'):
                if thread_no not in [';','#']: # check for comments ourselves
                    if self.zerobased : thread_no = str(int(thread_no)+1)
                    threading_map[int(thread_no)] = \
                        [int(sn) for sn in value.split(',')]

        warp_spacing = None
        has_warp_spacing = self.getbool('CONTENTS', 'WARP SPACING')
        # get backup spacing if thread not in [WARP SPACING]
        if 'Spacing' in self.config['WARP']:
            warp_spacing = self.config.getfloat('WARP', 'Spacing')
        warp_spacing_map = {}
        if has_warp_spacing:
            for thread_no, value in self.config.items('WARP SPACING'):
                if thread_no not in [';','#']: # check for comments ourselves
                    warp_spacing_map[int(thread_no)] = float(value)
        
        for thread_no in range(1, warp_thread_count + 1):
            # NOTE: Some software will generate WIFs with way more
            # threads in the warp or weft section than mentioned in the
            # threading. To ignore that, make sure that this thread actually
            # has threading specified: otherwise it's unused.
            if thread_no in threading_map:
                if has_warp_colors:
                    if thread_no in warp_color_map.keys():
                        color = wif_palette[warp_color_map[thread_no]]
                    else:
                        color = wif_palette[warp_color]
                else:
                    color = wif_palette[warp_color]

                if has_threading:
                    shafts = set(draft.shafts[shaft_no - 1]
                                 for shaft_no in threading_map[thread_no])
                    assert len(shafts) == 1
                    shaft = list(shafts)[0]
                else:
                    shaft = None

                if warp_spacing:
                    if thread_no in warp_spacing_map.keys():
                        spacing = warp_spacing_map[thread_no]
                    else:
                        spacing = warp_spacing
                else: spacing = None
    
                draft.add_warp_thread(
                    color=color,
                    shaft=shaft,
                    spacing=spacing,
                )

    def put_weft(self, draft, wif_palette):
        weft_thread_count = self.config.getint('WEFT', 'Threads')
        weft_units = self.config.get('WEFT', 'Units', fallback='centimeters').lower()
        assert weft_units in self.allowed_units, \
            "Weft Units of %r is not understood" % weft_units
        draft.weft_units = weft_units

        has_weft_colors = self.getbool('CONTENTS', 'WEFT COLORS')

        if has_weft_colors:
            weft_color_map = {}
            for thread_no, value in self.config.items('WEFT COLORS'):
                if thread_no not in [';','#']: # check for comments ourselves
                    weft_color_map[int(thread_no)] = int(value)
        else:
            weft_color_map = None

        # get backup color if not in [WEFT COLORS]
        weft_color = None
        if 'Color' in self.config['WEFT']:
            weft_color = self.config.getint('WEFT', 'Color')
            if self.zerobased : weft_color+=1
        if not weft_color_map:
            # try to get weft color from WEFT section
            has_weft_colors = False

        has_liftplan = self.getbool('CONTENTS', 'LIFTPLAN')

        if has_liftplan:
            liftplan_map = {}
            for thread_no, value in self.config.items('LIFTPLAN'):
                if thread_no not in [';','#']: # check for comments ourselves
                    # some wif files have illegal thread numbers
                    # so cutoff anything higher than found in THREADING
                    liftplan_map[int(thread_no)] = \
                        [int(sn) for sn in value.split(',') if int(sn)<=len(draft.shafts)] #ideally if not required

        has_treadling = self.getbool('CONTENTS', 'TREADLING')

        if has_treadling:
            treadling_map = {}
            for thread_no, value in self.config.items('TREADLING'):
                if thread_no not in [';','#']: # check for comments ourselves
                    if self.zerobased : thread_no = str(int(thread_no)+1)
                    try:
                        treadles = [int(tn) for tn in value.split(',')]
                    except ValueError:
                        pass
                    else:
                        treadling_map[int(thread_no)] = treadles

        weft_spacing = None
        has_weft_spacing = self.getbool('CONTENTS', 'WEFT SPACING')
        # get backup spacing if thread not in [WEFT SPACING]
        if 'Spacing' in self.config['WEFT']:
            weft_spacing = self.config.getfloat('WEFT', 'Spacing')
        weft_spacing_map = {}
        if has_weft_spacing:
            for thread_no, value in self.config.items('WEFT SPACING'):
                if thread_no not in [';','#']: # check for comments ourselves
                    weft_spacing_map[int(thread_no)] = float(value)

        for thread_no in range(1, weft_thread_count + 1):
            if (has_liftplan and (thread_no in liftplan_map)) or \
                    (has_treadling and (thread_no in treadling_map)):
                if has_weft_colors:
                    if thread_no in weft_color_map.keys():
                        color = wif_palette[weft_color_map[thread_no]]
                    else:
                        color = wif_palette[weft_color]
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
                
                if weft_spacing:
                    if thread_no in weft_spacing_map.keys():
                        spacing = weft_spacing_map[thread_no]
                    else:
                        spacing = weft_spacing
                else: spacing = None
                
                draft.add_weft_thread(
                    color=color,
                    shafts=shafts,
                    treadles=treadles,
                    spacing=spacing,
                )

    def put_tieup(self, draft):
        for treadle_no, value in self.config.items('TIEUP'):
            if treadle_no not in [';','#']: # check for comments ourselves
                if int(treadle_no)-1 < len(draft.treadles):
                    treadle = draft.treadles[int(treadle_no) - 1]
                    shaft_nos = [int(sn) for sn in value.split(',')]
                    for shaft_no in shaft_nos:
                        shaft = draft.shafts[shaft_no - 1]
                        treadle.shafts.add(shaft)

    def read(self):
        """
        Perform the actual parsing, and return a Draft instance.
        """
        # Config like this so we can read the creation date embedded in comments
        self.config = RawConfigParser(comment_prefixes='/', allow_no_value=True)
        #  but because we override comments from ;,# to / we will have to parse comments ourselves.
        #  we did this because creation date is embedded in Fiberworks files as a comment in TEXT section.
        # We need to deal with special case where the config file starts with a comment line. (TempoFiber)
        #  in this case the simple approach will fail when reading from the file.
        # So we need to read the file into a string and use self.config.read_string() instead of self.config.read()
        self.config.optionxform = str # does not force everything to lowercase
        with open(self.filename, 'r') as f:
            file_content = f.read() # Read whole file in the file_content string
        # skip initial comment lines
        commentline_end = file_content.find("\n")
        # print("!",commentline_end)
        while commentline_end==0 or file_content[:commentline_end][0] in [';','#']:
            file_content = file_content[commentline_end+1:]
            commentline_end = file_content.find("\n")
        self.config.read_string(file_content)
        
        rising_shed = self.getbool('WEAVING', 'Rising Shed')
        num_shafts = self.config.getint('WEAVING', 'Shafts')
        num_treadles = self.config.getint('WEAVING', 'Treadles', fallback=0)

        liftplan = self.getbool('CONTENTS', 'LIFTPLAN')
        treadling = self.getbool('CONTENTS', 'TREADLING')
        # ideally TREADLING and LIFTPLAN are mutually exclusive,
        assert not (liftplan and treadling), \
            "WIF contains both liftplan and treadling"
        #!! just ignore them if included
        # assert not (liftplan and (num_treadles > 0)), \
            # "WIF contains liftplan and non-zero treadle count"

        if self.getbool('CONTENTS', 'COLOR PALETTE'):
            palette_range = self.config.get('COLOR PALETTE', 'Range')
            rstart, rend = palette_range.split(',')
            palette_range = int(rstart), int(rend)
        else:
            palette_range = 0, 255 # Assume regular 8bit rgb if no range defined

        if self.getbool('CONTENTS', 'COLOR TABLE'):
            wif_palette = {}
            for color_no, value in self.config.items('COLOR TABLE'):
                if color_no not in [';','#']: # check for comments ourselves
                    channels = [int(ch) for ch in value.split(',')]
                    channels = [int(round(ch * (255. / palette_range[1])))
                                for ch in channels]
                    wif_palette[int(color_no)] = channels
        else:
            wif_palette = None

        draft = Draft(num_shafts=num_shafts,
                      num_treadles=num_treadles,
                      rising_shed=rising_shed,
                      liftplan = liftplan)

        self.put_metadata(draft)
        self.put_warp(draft, wif_palette)
        self.put_weft(draft, wif_palette)
        if treadling:
            self.put_tieup(draft)
        draft.process_draft()
        
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

        config.add_section('CONTENTS')
        config.set('CONTENTS', 'WEAVING', True)
        config.add_section('WEAVING')
        config.set('WEAVING', 'Rising Shed', self.draft.rising_shed)
        config.set('WEAVING', 'Shafts', len(self.draft.shafts))
        config.set('WEAVING', 'Treadles',
                   0 if liftplan else len(self.draft.treadles))

        config.set('CONTENTS', 'TEXT', True)
        config.add_section('TEXT')
        config.set('TEXT', 'Title', self.draft.title)
        config.set('TEXT', 'Author', self.draft.author)
        config.set('TEXT', 'Address', self.draft.address)
        config.set('TEXT', 'EMail', self.draft.email)
        config.set('TEXT', 'Telephone', self.draft.telephone)
        config.set('TEXT', 'FAX', self.draft.fax)
        config.set('TEXT', '; Creation %s'%(self.draft.creation_date))

        if self.draft.notes:
            config.set('CONTENTS', 'NOTES', True)
            config.add_section('NOTES')
            for ii, line in enumerate(self.draft.notes):
                config.set('NOTES', str(ii), line)

    def write_palette(self, config):
        # generate the color table and write it to the config
        # return a wif_palette mapping color instances to numbers.
        colors = set(thread.color.rgb for thread in
                     self.draft.warp + self.draft.weft)
        wif_palette = {}
        config.set('CONTENTS', 'COLOR TABLE', True)
        config.add_section('COLOR TABLE')
        for ii, color in enumerate(colors, start=1):
            val = '%d,%d,%d' % color
            config.set('COLOR TABLE', str(ii), val)
            wif_palette[color] = ii

        config.set('CONTENTS', 'COLOR PALETTE', True)
        config.add_section('COLOR PALETTE')
        config.set('COLOR PALETTE', 'Form', 'RGB')
        config.set('COLOR PALETTE', 'Range', '0,255')
        return wif_palette

    def write_threads(self, config, wif_palette, dir):
        assert dir in ('warp', 'weft')
        threads = getattr(self.draft, dir)
        dir = dir.upper()
        config.set('CONTENTS', dir, True)
        config.add_section(dir)
        config.set(dir, 'Threads', len(threads))
        # XXX This should actually be stored in the draft.
        #config.set(dir, 'Units', 'Inches')
        if dir == 'WARP':
            config.set(dir, 'Units', self.draft.warp_units)
        if dir == 'WEFT':
            config.set(dir, 'Units', self.draft.weft_units)

        config.set('CONTENTS', '%s COLORS' % dir, True)
        config.add_section('%s COLORS' % dir)
        for ii, thread in enumerate(threads, start=1):
            config.set('%s COLORS' % dir,
                       str(ii),
                       wif_palette[thread.color.rgb])

    def write_threading(self, config):
        config.set('CONTENTS', 'THREADING', True)
        config.add_section('THREADING')

        for ii, thread in enumerate(self.draft.warp, start=1):
            shaft_string = str(self.draft.shafts.index(thread.shaft) + 1)
            config.set('THREADING', str(ii), shaft_string)

    def write_liftplan(self, config):
        config.set('CONTENTS', 'LIFTPLAN', True)
        config.add_section('LIFTPLAN')

        for ii, thread in enumerate(self.draft.weft, start=1):
            shaft_nos = [self.draft.shafts.index(shaft) + 1
                         for shaft in thread.connected_shafts]
            shaft_string = ','.join([str(shaft_no) for shaft_no in shaft_nos])
            config.set('LIFTPLAN', str(ii), shaft_string)

    def write_treadling(self, config):
        config.set('CONTENTS', 'TREADLING', True)
        config.add_section('TREADLING')

        for ii, thread in enumerate(self.draft.weft, start=1):
            treadle_nos = [self.draft.treadles.index(treadle) + 1
                           for treadle in thread.treadles]
            treadle_string = ','.join([str(treadle_no) for treadle_no in
                                       treadle_nos])
            config.set('TREADLING', str(ii), treadle_string)

    def write_tieup(self, config):
        config.set('CONTENTS', 'TIEUP', True)
        config.add_section('TIEUP')

        for ii, treadle in enumerate(self.draft.treadles, start=1):
            shaft_nos = [self.draft.shafts.index(shaft) + 1
                         for shaft in treadle.shafts]
            shaft_string = ','.join([str(shaft_no) for shaft_no in shaft_nos])
            config.set('TIEUP', str(ii), shaft_string)

    def write(self, filename, liftplan=False):
        assert self.draft.start_at_lowest_thread

        config = RawConfigParser(allow_no_value=True)#!!
        config.optionxform = str
        
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

        with open(filename, 'w') as f:
            config.write(f)
