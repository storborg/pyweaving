
from .. import Draft, Color, __version__, find_repeats
from PIL import Image
from copy import deepcopy


class Image_draft(object):
    """
    Builds a draft from an image of a drawdown
     - Assumes the supplied image contains square areas which represent a weaving draft drawdown.
     - Uses Black and white (anything non-black) when detecting color.
     - We need to know expected number of warp threads to sample correctly.
     - needs to know how many warp threads across. Can also stretch image if in form of WxH

    Args:
        imagefile (str): an image filename
        size_description (str): integer width of warps (w) or warps and height in form wxh
        minimal (bool, optional): attempt to remove repeats if True , defaults to True
        hreflect (bool, optional): reflect the image horizinatally, defaults to False
        samples_per_cell (int, optional): sampling to remove noise, 3-10, defaults to 5
        noise_threshold (float, optional): threshold when grouping colors, range 0-1, defaults to 0.1
        feedback (bool, optional): write a sampleref image showing sample positions on image, defaults to True
    """

    def __init__(self, imagefile, size_description, minimal=True, hreflect=True,
                 samples_per_cell=5, noise_threshold=0.1, feedback=True):
        self.filename = imagefile
        warpthreads, weftthreads = self.parse_size(size_description)
        self.minimal = minimal
        self.hreflect = hreflect  # is drawdown to read RtoL (True)
        self.samples_per_cell = samples_per_cell
        self.noise_threshold = noise_threshold
        self.warpcount = 0  # set in sample_image
        self.weftcount = 0  # set in sample_image
        self.warps = []     # !!remove?
        self.treadles = []  # !!remove?
        self.as_rows = []   # holds samples as color indices and as arrays of rows
        self.as_cols = []   # holds samples as color indices and as arrays of columns
        # Process
        self.image = Image.open(imagefile).convert('RGB')
        self.samples = self.sample_image(warpthreads, weftthreads, self.samples_per_cell, feedback)
        self.colors = self.extract_colors(self.samples)
        # reduce colors if very close
        self.rationalise_colors(self.noise_threshold)  # replaces self.samples
        # reformat as rows and cols - eady for shafts, treadles
        self.make_indexed_samples(self.samples, self.colors, self.hreflect)
        # print("rows",len(self.as_rows),self.as_rows)
        # print("cols",len(self.as_cols),self.as_cols)
        # data now stable
        # reduce to smallest non-repeating section
        if minimal:
            self.find_core()
        # build the draft - warp, weft, tieup(treadles)
        self.draft = self.build_draft()

    def __repr__(self):
        if self.draft:
            return "<Image_Draft %s, %dx%d, %dwarps, %dtreadles>" % (self.filename, self.warpcount, self.weftcount,
                                                                     len(self.draft.warp), len(self.draft.treadles))
        else:
            return "<Image_Draft %s, %dx%d>" % (self.filename, self.warpcount, self.weftcount)

    def parse_size(self, description):
        """
        Parse width and height from N or NxM format

        Args:
            description (W | WxH) int
        Returns:
            (width, None|Height):
        """
        if description.isdigit():
            return int(description), None
        else:
            if description.find("x") > -1:
                w, h = description.split('x')
                if w.isdigit() and h.isdigit():
                    return int(w), int(h)
                else:
                    print("Could not parse W or WxH from", description)

    def sample_image(self, warpcount, weftcount, scount, debug=False):
        """
        Sample image to get clean colour from original
         - if debug set then export an aimge showing sample locations as red dots

        Args:
            warpcount (int): How many squares across are in the image.
            weftcount (int): None or integer. None assumes exactly sq pixels as defined by warpcount.
            scount (int): Howmany pixels wide to sample each square (3-7)
            debug (bool): write out a sampleref file showing where sample was made. So user can bettwer define WxH
        """
        sample_width = warpcount * scount
        if weftcount:
            # got w,h so use resize
            self.image = self.image.resize((sample_width, weftcount*scount), Image.NEAREST)
            print(self.image.size)
        else:  # only got warpsize - so assume sq pixels
            # resample image in-place
            self.image.thumbnail((sample_width, self.image.size[1]), Image.NEAREST)
        if debug:
            self.image.save('foo.png')
        result = []
        start = scount // 2
        for y in range(start, self.image.size[1], scount):
            line = []
            for x in range(start, self.image.size[0], scount):
                rgb = self.image.getpixel((x, y))
                # print(x,y,rgb)
                self.image.putpixel((x, y), (200, 0, 0))
                line.append(rgb)
            result.append(line)
        if debug:
            dotpos = self.filename.rfind(".")
            if dotpos:
                newname = self.filename[:dotpos] + "-samplesref." + self.filename[dotpos + 1:]
                self.image.save(newname)
        self.warpcount = len(result[0])
        self.weftcount = len(result)
        return result

    def extract_colors(self, samples):
        """
        Find unique colors in samples and create color index table, Sort the colors.

        Args:
            samples: list of all samples to extract color from
        Returns:
            list of discovered samples (indexed by brighness)
        """
        result = []
        for row in samples:
            for x in row:
                if x not in result:
                    result.append(x)
        return sorted(set(result))  # use set to force unique

    def _closest_color(self, c, legit_colors):
        " Find the closest color in the index table "
        # abs(sum(self.rgb) - sum(other.rgb))
        distances = [sum([abs(col[i]-c[i]) for i in range(3)]) for col in legit_colors]
        closest_col_index = distances.index(min(distances))
        return legit_colors[closest_col_index]

    def rationalise_colors(self, legit_cutoff=0.1):
        """
        Quantise colors that are very close to each other.
         - then replace self.samples using minimal color choices.

        Args:
            legit_cutoff (float, optional): Low number to remove noisy images. Range is 0..1 probability
        """
        # look at freq color is in all data - if low - assume noise and replace with closest
        histogram_values = []
        for row in self.samples:
            for c in row:
                if c not in histogram_values:
                    histogram_values.append(c)
        # gather frequencies
        histogram_frequencies = [0]*len(histogram_values)
        for row in self.samples:
            for c in row:
                index = histogram_values.index(c)
                histogram_frequencies[index] += 1
        num_samples = self.warpcount * self.weftcount
        histogram_frequencies = [f / num_samples for f in histogram_frequencies]
        histogram = list(zip(histogram_values, histogram_frequencies))
        # print("Found colors (col,freq):\n",histogram)
        # which are legit colors (most frequently used)
        legit_colors = [c for c, f in histogram if f > legit_cutoff]
        # print("Legit colors:",legit_colors)
        # find closest replacement
        newsamples = []
        for row in self.samples:
            newrow = []
            for c in row:
                if c in legit_colors:
                    newrow.append(c)
                else:
                    newrow.append(self._closest_color(c, legit_colors))
            newsamples.append(newrow)
        self.samples = newsamples

    def make_indexed_samples(self, samples, colors, hreflect):
        """
        Step through converting colours to indexes.
         - setup as_rows and as_cols with the indexed colors

        Args:
            samples (list): all the samples with color at each index
            colors (list): list of all colors to index into
            hreflect (bool): To horizontally reflect the image.
        """
        row_order = []
        col_order = []
        for row in samples:
            line = []
            for x in row:
                c_index = colors.index(x)
                line.append(c_index)
            if hreflect:
                line = line[::-1]
            row_order.append(line)
        #
        col_order = list(zip(*row_order))
        self.as_rows = row_order
        self.as_cols = col_order

    def find_core(self):
        """
        Find if there is a major repeat of an entire section.
          - replace self.as_cols, self.as_rows with minimal set
        """
        # assumes ascols, asrows have been color reduced so no noise and true rep of draft
        # set the identity size as default. I.e. no repeat to trim
        row_indexes = [0, len(self.as_rows)]
        col_indexes = [0, len(self.as_cols)]
        chop_rows = False
        chop_cols = False
        # in a sq pattern that is repeated we will see
        # - several repeats of the same length
        # - several minor repeats which do not matter here.
        # To decide the size of the major repeat:
        # - it will be the biggest = so max(row_repeats.keys())
        # - the length of the seq will equal len of repeat
        row_repeats = find_repeats(self.as_rows)
        if row_repeats:  # no repeats = nothing to do
            # find the largest repeat
            max_row_rep = max(row_repeats.keys())
            entry = row_repeats[max_row_rep][0]  # first entry in the biggest repeat
            # print("row=", entry)
            # print(len(entry[0]),entry[1][1]-entry[1][0])
            if len(entry[0]) == entry[1][1] - entry[1][0]:
                row_indexes = row_repeats[max_row_rep][0][1]
                chop_rows = True
        # cols
        col_repeats = find_repeats(self.as_cols)
        if col_repeats:
            max_col_rep = max(col_repeats.keys())
            entry = col_repeats[max_col_rep][0]  # first entry in the biggest repeat
            # print("col=", entry)
            # print(len(entry[0]),entry[1][1]-entry[1][0])
            if len(entry[0]) == entry[1][1] - entry[1][0]:
                col_indexes = col_repeats[max_col_rep][0][1]
                chop_cols = True
        # print("asrows:",row_indexes)
        # print("ascols:",col_indexes)
        # Anything to reduce ?
        if chop_rows or chop_cols:
            newrows = []
            for row in self.as_rows[col_indexes[0]:col_indexes[1]]:
                newrows.append(row[row_indexes[0]:row_indexes[1]])
            self.as_rows = newrows
            self.as_cols = list(zip(*newrows))
            #
            self.warpcount = len(self.as_cols)
            self.weftcount = len(self.as_rows)

    def build_draft(self):
        """
        Find the unique warps, determine tieup and treadles.

        Returns:
            Draft:
        """
        unique_shafts = []
        dup_shafts = []
        # find unique columns(warp) patterns
        for i, col in enumerate(self.as_cols):
            if col not in unique_shafts:
                unique_shafts.append(col)
            else:  # keep an index of which were duplicated
                dup_shafts.append(i)
        num_shafts = len(unique_shafts)
        # same for row(weft) patterns but nno need to record dups
        unique_treadles = []
        for row in self.as_rows:
            if row not in unique_treadles:
                unique_treadles.append(row)
        num_treadles = len(unique_treadles)
        # print(num_shafts, num_treadles, dup_shafts)
        # print(unique_shafts)
        # print(unique_treadles)

        # map shafts to uniques for 1:1 shaft construction
        shaft_refs = []
        for i, col in enumerate(self.as_cols):
            shaft_refs.append(unique_shafts.index(col))
        # print("shaft_refs",shaft_refs)

        # build the draft
        draft = Draft(num_shafts=num_shafts, num_treadles=num_treadles)
        # build the treadles
        for y, row in enumerate(unique_treadles):
            short_row = deepcopy(row)
            for i, s in enumerate(dup_shafts):
                short_row.pop(s - i)  # because its shorter each time we pop
            row_shafts = [draft.shafts[i] for i, c in enumerate(short_row) if c == 0]
            draft.treadles[y].shafts = row_shafts
        # print("draft treadles",draft.treadles)

        # make a straight draw (missing dups) on warp using shafts
        for s in shaft_refs:
            # darkest color
            draft.add_warp_thread(color=self.colors[0], shaft=draft.shafts[s])

        # add the wefts using the treadles
        for y, row in enumerate(self.as_rows):
            # use the unique version of the row
            shaft_index = unique_treadles.index(row)
            draft.add_weft_thread(color=self.colors[-1], treadles=[shaft_index])
        #
        draft.title = "Draft from: "+self.filename
        draft.draft_title = [draft.title]
        draft.source_program = 'PyWeaving'
        draft.source_version = __version__
        return draft


def point_threaded(image_filename, shafts=40, repeats=2,
                   warp_color=(0, 0, 0), weft_color=(255, 255, 255)):
    """
    Given an image, generate a point-threaded drawdown that attempts to
    represent the image. Results in a drawdown with bilateral symmetry from a
    non-symmetric source image.

    Args:
        image_filename (str): bitmap image to load
        shafts (int): Need a large number, Default=40
        repeats (int, optional): Number of times to repeat the reflected Threading.
        warp_color (Color or tuple): Color for the warp.
        weft_color (Color or tuple): Color for the weft.
    Returns:
        Draft:
    """
    shafts = int(shafts)
    repeats = int(repeats)
    im = Image.open(image_filename).convert('RGB')
    draft = Draft(num_shafts=shafts, liftplan=True)

    # resize the image in place - preserving aspect ratio
    im.thumbnail((shafts, im.size[1]), Image.ANTIALIAS)
    # convert it intop a grayscale image
    im = im.convert('1')
    # im.save('foo.png')

    w, h = im.size
    assert w == shafts
    warp_pattern_size = ((2 * shafts) - 2)
    for __ in range(repeats):
        for ii in range(warp_pattern_size):
            if ii < shafts:
                shaft = ii
            else:
                shaft = warp_pattern_size - ii
            draft.add_warp_thread(color=Color(warp_color), shaft=shaft)
    #
    imdata = im.getdata()

    for __ in range(repeats):
        for yy in range(h):
            offset = yy * w
            pick_shafts = set()
            for xx in range(w):
                pixel = imdata[offset + xx]
                if not pixel:
                    pick_shafts.add(xx)
            draft.add_weft_thread(color=Color(weft_color), shafts=pick_shafts)
    #
    draft.title = image_filename+" Draft"
    draft.draft_title = [draft.title]
    draft.source_program = 'PyWeaving'
    draft.source_version = __version__
    return draft


def extract_draft(image_filename, shafts=8, find_core=False):
    """
    Create a Draft using an imagefile as a representation of the drawdown.
    - Wrapper for Image_draft class.
    """
    im = Image_draft(image_filename, shafts, find_core)
    return im.draft
