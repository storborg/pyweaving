import os.path

from PIL import Image, ImageDraw, ImageFont


__here__ = os.path.dirname(__file__)

font_path = os.path.join(__here__, 'data', 'Arial.ttf')


class ImageRenderer(object):
    def __init__(self, draft, liftplan=None, margin_pixels=20, scale=10,
                 foreground=(127, 127, 127), background=(255, 255, 255),
                 markers=(0, 0, 0), numbering=(200, 0, 0)):
        self.draft = draft

        self.liftplan = liftplan

        self.margin_pixels = margin_pixels
        self.pixels_per_square = scale

        self.background = background
        self.foreground = foreground
        self.markers = markers
        self.numbering = numbering

        self.font_size = int(round(scale * 1.2))

        self.font = ImageFont.truetype(font_path, self.font_size)

    def pad_image(self, im):
        w, h = im.size
        desired_w = w + (self.margin_pixels * 2)
        desired_h = h + (self.margin_pixels * 2)
        new = Image.new('RGB', (desired_w, desired_h), self.background)
        new.paste(im, (self.margin_pixels, self.margin_pixels))
        return new

    def make_pil_image(self):
        width_squares = len(self.draft.warp) + 6
        if self.liftplan:
            width_squares += len(self.draft.shafts)
        else:
            width_squares += len(self.draft.treadles)

        height_squares = len(self.draft.weft) + 6 + len(self.draft.shafts)

        # XXX Not totally sure why the +1 is needed here, but otherwise the
        # contents overflows the canvas
        width = (width_squares * self.pixels_per_square) + 1
        height = (height_squares * self.pixels_per_square) + 1

        im = Image.new('RGB', (width, height), self.background)

        draw = ImageDraw.Draw(im)

        self.paint_warp(draw)
        self.paint_threading(draw)

        self.paint_weft(draw)
        if self.liftplan:
            self.paint_liftplan(draw)
        else:
            self.paint_tieup(draw)
            self.paint_treadling(draw)

        self.paint_drawdown(draw)
        del draw

        im = self.pad_image(im)
        return im

    def paint_warp(self, draw):
        starty = 0
        endy = self.pixels_per_square
        for ii, thread in enumerate(self.draft.warp):
            # paint box, outlined with foreground color, filled with thread
            # color
            startx = self.pixels_per_square * ii
            endx = startx + self.pixels_per_square
            draw.rectangle((startx, starty, endx, endy),
                           outline=self.foreground,
                           fill=thread.color.rgb)

    def paint_fill_marker(self, draw, box):
        startx, starty, endx, endy = box
        draw.rectangle((startx + 2, starty + 2, endx - 2, endy - 2),
                       fill=self.markers)

    def paint_threading(self, draw):
        num_threads = len(self.draft.warp)
        num_shafts = len(self.draft.shafts)

        for ii, thread in enumerate(self.draft.warp):
            startx = (num_threads - ii - 1) * self.pixels_per_square
            endx = startx + self.pixels_per_square

            for jj, shaft in enumerate(self.draft.shafts):
                starty = (4 + (num_shafts - jj)) * self.pixels_per_square
                endy = starty + self.pixels_per_square
                draw.rectangle((startx, starty, endx, endy),
                               outline=self.foreground)

                if shaft in thread.shafts:
                    # draw threading marker
                    self.paint_fill_marker(draw, (startx, starty, endx, endy))

            # paint the number if it's a multiple of 4
            thread_no = ii + 1
            if ((thread_no != num_threads) and
                (thread_no != 0) and
                    (thread_no % 4 == 0)):
                # draw line
                startx = endx = (num_threads - ii - 1) * self.pixels_per_square
                starty = 3 * self.pixels_per_square
                endy = (5 * self.pixels_per_square) - 1
                draw.line((startx, starty, endx, endy),
                          fill=self.numbering)
                # draw text
                draw.text((startx + 2, starty + 2),
                          str(thread_no),
                          font=self.font,
                          fill=self.numbering)

    def paint_weft(self, draw):
        offsety = (6 + len(self.draft.shafts)) * self.pixels_per_square
        startx_squares = len(self.draft.warp) + 5
        if self.liftplan:
            startx_squares += len(self.draft.shafts)
        else:
            startx_squares += len(self.draft.treadles)
        startx = startx_squares * self.pixels_per_square
        endx = startx + self.pixels_per_square

        for ii, thread in enumerate(self.draft.weft):
            # paint box, outlined with foreground color, filled with thread
            # color
            starty = (self.pixels_per_square * ii) + offsety
            endy = starty + self.pixels_per_square
            draw.rectangle((startx, starty, endx, endy),
                           outline=self.foreground,
                           fill=thread.color.rgb)

    def paint_liftplan(self, draw):
        num_threads = len(self.draft.weft)

        offsetx = (1 + len(self.draft.warp)) * self.pixels_per_square
        offsety = (6 + len(self.draft.shafts)) * self.pixels_per_square
        for ii, thread in enumerate(self.draft.weft):
            starty = (ii * self.pixels_per_square) + offsety
            endy = starty + self.pixels_per_square

            for jj, shaft in enumerate(self.draft.shafts):
                startx = (jj * self.pixels_per_square) + offsetx
                endx = startx + self.pixels_per_square
                draw.rectangle((startx, starty, endx, endy),
                               outline=self.foreground)

                if shaft in thread.connected_shafts:
                    # draw liftplan marker
                    self.paint_fill_marker(draw, (startx, starty, endx, endy))

            # paint the number if it's a multiple of 4
            thread_no = ii + 1
            if ((thread_no != num_threads) and
                (thread_no != 0) and
                    (thread_no % 4 == 0)):
                # draw line
                startx = endx
                starty = endy
                endx = startx + (2 * self.pixels_per_square)
                endy = starty
                draw.line((startx, starty, endx, endy),
                          fill=self.numbering)
                # draw text
                draw.text((startx + 2, starty - 2 - self.font_size),
                          str(thread_no),
                          font=self.font,
                          fill=self.numbering)

    def paint_tieup(self, draw):
        offsetx = (1 + len(self.draft.warp)) * self.pixels_per_square
        offsety = 5 * self.pixels_per_square

        num_treadles = len(self.draft.treadles)
        num_shafts = len(self.draft.shafts)

        for ii, treadle in enumerate(self.draft.treadles):
            startx = (ii * self.pixels_per_square) + offsetx
            endx = startx + self.pixels_per_square

            treadle_no = ii + 1

            for jj, shaft in enumerate(self.draft.shafts):
                starty = (((num_shafts - jj - 1) * self.pixels_per_square) +
                          offsety)
                endy = starty + self.pixels_per_square

                draw.rectangle((startx, starty, endx, endy),
                               outline=self.foreground)

                if shaft in treadle.shafts:
                    self.paint_fill_marker(draw, (startx, starty, endx, endy))

                # on the last treadle, paint the shaft markers
                if treadle_no == num_treadles:
                    shaft_no = jj + 1
                    if (shaft_no != 0) and (shaft_no % 4 == 0):
                        # draw line
                        line_startx = endx
                        line_endx = line_startx + (2 * self.pixels_per_square)
                        line_starty = line_endy = starty
                        draw.line((line_startx, line_starty,
                                   line_endx, line_endy),
                                  fill=self.numbering)
                        draw.text((line_startx + 2, line_starty + 2),
                                  str(shaft_no),
                                  font=self.font,
                                  fill=self.numbering)

            # paint the number if it's a multiple of 4 and not the first one
            if (treadle_no != 0) and (treadle_no % 4 == 0):
                # draw line
                startx = endx = (treadle_no * self.pixels_per_square) + offsetx
                starty = 3 * self.pixels_per_square
                endy = (5 * self.pixels_per_square) - 1
                draw.line((startx, starty, endx, endy),
                          fill=self.numbering)
                # draw text on left side, right justified
                textw, texth = draw.textsize(str(treadle_no), font=self.font)
                draw.text((startx - textw - 2, starty + 2),
                          str(treadle_no),
                          font=self.font,
                          fill=self.numbering)

    def paint_treadling(self, draw):
        num_threads = len(self.draft.weft)

        offsetx = (1 + len(self.draft.warp)) * self.pixels_per_square
        offsety = (6 + len(self.draft.shafts)) * self.pixels_per_square
        for ii, thread in enumerate(self.draft.weft):
            starty = (ii * self.pixels_per_square) + offsety
            endy = starty + self.pixels_per_square

            for jj, treadle in enumerate(self.draft.treadles):
                startx = (jj * self.pixels_per_square) + offsetx
                endx = startx + self.pixels_per_square
                draw.rectangle((startx, starty, endx, endy),
                               outline=self.foreground)

                if treadle in thread.treadles:
                    # draw treadling marker
                    self.paint_fill_marker(draw, (startx, starty, endx, endy))

            # paint the number if it's a multiple of 4
            thread_no = ii + 1
            if ((thread_no != num_threads) and
                (thread_no != 0) and
                    (thread_no % 4 == 0)):
                # draw line
                startx = endx
                starty = endy
                endx = startx + (2 * self.pixels_per_square)
                endy = starty
                draw.line((startx, starty, endx, endy),
                          fill=self.numbering)
                # draw text
                draw.text((startx + 2, starty - 2 - self.font_size),
                          str(thread_no),
                          font=self.font,
                          fill=self.numbering)

    def paint_drawdown(self, draw):
        offsety = (6 + len(self.draft.shafts)) * self.pixels_per_square
        floats = self.draft.compute_floats()

        for start, end, visible, length, thread in floats:
            if visible:
                startx = start[0] * self.pixels_per_square
                starty = (start[1] * self.pixels_per_square) + offsety
                endx = (end[0] + 1) * self.pixels_per_square
                endy = ((end[1] + 1) * self.pixels_per_square) + offsety
                draw.rectangle((startx, starty, endx, endy),
                               outline=self.foreground,
                               fill=thread.color.rgb)

    def show(self):
        im = self.make_pil_image()
        im.show()

    def save(self, filename):
        im = self.make_pil_image()
        im.save(filename)


class PDFRenderer(object):
    def __init__(self, draft):
        self.draft = draft

    def save(self, filename):
        raise NotImplementedError
