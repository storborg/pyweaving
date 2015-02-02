from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import os.path
import tempfile

from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF
from PIL import Image, ImageDraw, ImageFont


__here__ = os.path.dirname(__file__)

font_path = os.path.join(__here__, 'data', 'Arial.ttf')


class ImageRenderer(object):
    # TODO:
    # - Add a "drawndown only" option
    # - Add a default tag (like a small delta symbol) to signal the initial
    # shuttle direction
    # - Add option to render the backside of the fabric
    # - Add option to render a bar graph of the thread crossings along the
    # sides
    # - Add option to render 'stats table'
    #   - Number of warp threads
    #   - Number of weft threads
    #   - Number of harnesses/shafts
    #   - Number of treadles
    #   - Warp unit size / reps
    #   - Weft unit size / reps
    #   - Longest warp float
    #   - Longest weft float
    #   - Selvedge continuity
    # - Add option to rotate orientation
    # - Add option to render selvedge continuity
    # - Add option to render inset "scale view" rendering of fabric
    # - Add option to change thread spacing
    # - Support variable thickness threads
    # - Add option to render heddle count on each shaft
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
        if self.liftplan or self.draft.liftplan:
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
        if self.liftplan or self.draft.liftplan:
            self.paint_liftplan(draw)
        else:
            self.paint_tieup(draw)
            self.paint_treadling(draw)

        self.paint_drawdown(draw)
        self.paint_start_indicator(draw)
        del draw

        im = self.pad_image(im)
        return im

    def paint_start_indicator(self, draw):
        endy = ((len(self.draft.shafts) + 6) * self.pixels_per_square) - 1
        starty = (endy - (self.pixels_per_square // 2))
        if self.draft.start_at_lowest_thread:
            # right side
            endx = len(self.draft.warp) * self.pixels_per_square
            startx = endx - self.pixels_per_square
        else:
            # left side
            startx = 0
            endx = self.pixels_per_square
        vertices = [
            (startx, starty),
            (endx, starty),
            (startx + (self.pixels_per_square // 2), endy),
        ]
        draw.polygon(vertices, fill=self.markers)

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

                if shaft == thread.shaft:
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
        if self.liftplan or self.draft.liftplan:
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


svg_preamble = '<?xml version="1.0" encoding="utf-8" standalone="no"?>'
svg_header = '''<svg width="{width}" height="{height}"
    viewBox="0 0 {width} {height}"
    xmlns="http://www.w3.org/2000/svg"
    xmlns:xlink="http://www.w3.org/1999/xlink">'''


class TagGenerator(object):
    def __getattr__(self, name):
        def tag(*children, **attrs):
            inner = ''.join(children)
            if attrs:
                attrs = ' '.join(['%s="%s"' % (key.replace('_', '-'), val)
                                  for key, val in attrs.items()])
                return '<%s %s>%s</%s>' % (name, attrs, inner, name)
            else:
                return '<%s>%s</%s>' % (name, inner, name)
        return tag


SVG = TagGenerator()


class SVGRenderer(object):
    def __init__(self, draft, liftplan=None, scale=10,
                 foreground='#7f7f7f', background='#ffffff',
                 markers='#000000', numbering='#c80000'):
        self.draft = draft

        self.liftplan = liftplan

        self.scale = scale

        self.background = background
        self.foreground = foreground
        self.markers = markers
        self.numbering = numbering

        self.font_family = 'Arial, sans-serif'
        self.font_size = 12

    def make_svg_doc(self):
        width_squares = len(self.draft.warp) + 6
        if self.liftplan or self.draft.liftplan:
            width_squares += len(self.draft.shafts)
        else:
            width_squares += len(self.draft.treadles)

        height_squares = len(self.draft.weft) + 6 + len(self.draft.shafts)

        width = width_squares * self.scale
        height = height_squares * self.scale

        doc = []
        # Use a negative starting point so we don't have to offset everything
        # in the drawing.
        doc.append(svg_header.format(width=width, height=height))

        self.write_metadata(doc)

        self.paint_warp(doc)
        self.paint_threading(doc)

        self.paint_weft(doc)
        if self.liftplan or self.draft.liftplan:
            self.paint_liftplan(doc)
        else:
            self.paint_tieup(doc)
            self.paint_treadling(doc)

        self.paint_drawdown(doc)
        doc.append('</svg>')
        return '\n'.join(doc)

    def write_metadata(self, doc):
        doc.append(SVG.title(self.draft.title))

    def paint_warp(self, doc):
        starty = 0
        grp = []
        for ii, thread in enumerate(self.draft.warp):
            # paint box, outlined with foreground color, filled with thread
            # color
            startx = self.scale * ii
            grp.append(SVG.rect(
                x=startx, y=starty,
                width=self.scale, height=self.scale,
                style='stroke:%s; fill:%s' % (self.foreground,
                                              thread.color.css)))
        doc.append(SVG.g(*grp))

    def paint_weft(self, doc):
        offsety = (6 + len(self.draft.shafts)) * self.scale
        startx_squares = len(self.draft.warp) + 5
        if self.liftplan or self.draft.liftplan:
            startx_squares += len(self.draft.shafts)
        else:
            startx_squares += len(self.draft.treadles)
        startx = startx_squares * self.scale

        grp = []
        for ii, thread in enumerate(self.draft.weft):
            # paint box, outlined with foreground color, filled with thread
            # color
            starty = (self.scale * ii) + offsety
            grp.append(SVG.rect(
                x=startx, y=starty,
                width=self.scale, height=self.scale,
                style='stroke:%s; fill:%s' % (self.foreground,
                                              thread.color.css)))
        doc.append(SVG.g(*grp))

    def paint_fill_marker(self, doc, box):
        startx, starty, endx, endy = box
        # XXX FIXME make box setback generated from scale fraction
        assert self.scale > 8
        doc.append(SVG.rect(
            x=startx + 2,
            y=starty + 2,
            width=self.scale - 4,
            height=self.scale - 4,
            style='fill:%s' % self.markers))

    def paint_threading(self, doc):
        num_threads = len(self.draft.warp)
        num_shafts = len(self.draft.shafts)

        grp = []
        for ii, thread in enumerate(self.draft.warp):
            startx = (num_threads - ii - 1) * self.scale
            endx = startx + self.scale

            for jj, shaft in enumerate(self.draft.shafts):
                starty = (4 + (num_shafts - jj)) * self.scale
                endy = starty + self.scale
                grp.append(SVG.rect(
                    x=startx, y=starty,
                    width=self.scale, height=self.scale,
                    style='stroke:%s; fill:%s' % (self.foreground,
                                                  self.background)))

                if shaft == thread.shaft:
                    # draw threading marker
                    self.paint_fill_marker(grp, (startx, starty, endx, endy))

            # paint the number if it's a multiple of 4
            thread_no = ii + 1
            if ((thread_no != num_threads) and
                (thread_no != 0) and
                    (thread_no % 4 == 0)):
                # draw line
                startx = endx = (num_threads - ii - 1) * self.scale
                starty = 3 * self.scale
                endy = (5 * self.scale) - 1
                grp.append(SVG.line(
                    x1=startx,
                    y1=starty,
                    x2=endx,
                    y2=endy,
                    style='stroke:%s' % self.numbering))
                # draw text
                grp.append(SVG.text(
                    str(thread_no),
                    x=(startx + 3),
                    y=(starty + self.font_size),
                    style='font-family:%s; font-size:%s; fill:%s' % (
                        self.font_family,
                        self.font_size,
                        self.numbering)))
        doc.append(SVG.g(*grp))

    def paint_liftplan(self, doc):
        num_threads = len(self.draft.weft)

        offsetx = (1 + len(self.draft.warp)) * self.scale
        offsety = (6 + len(self.draft.shafts)) * self.scale

        grp = []
        for ii, thread in enumerate(self.draft.weft):
            starty = (ii * self.scale) + offsety
            endy = starty + self.scale

            for jj, shaft in enumerate(self.draft.shafts):
                startx = (jj * self.scale) + offsetx
                endx = startx + self.scale
                grp.append(SVG.rect(
                    x=startx,
                    y=starty,
                    width=self.scale,
                    height=self.scale,
                    style='stroke:%s; fill:%s' % (self.foreground,
                                                  self.background)))

                if shaft in thread.connected_shafts:
                    # draw liftplan marker
                    self.paint_fill_marker(grp, (startx, starty, endx, endy))

            # paint the number if it's a multiple of 4
            thread_no = ii + 1
            if ((thread_no != num_threads) and
                (thread_no != 0) and
                    (thread_no % 4 == 0)):
                # draw line
                startx = endx
                starty = endy
                endx = startx + (2 * self.scale)
                endy = starty
                grp.append(SVG.line(
                    x1=startx,
                    y1=starty,
                    x2=endx,
                    y2=endy,
                    style='stroke:%s' % self.numbering))
                # draw text
                grp.append(SVG.text(
                    str(thread_no),
                    x=(startx + 3),
                    y=(starty - 4),
                    style='font-family:%s; font-size:%s; fill:%s' % (
                        self.font_family,
                        self.font_size,
                        self.numbering)))
        doc.append(SVG.g(*grp))

    def paint_tieup(self, doc):
        offsetx = (1 + len(self.draft.warp)) * self.scale
        offsety = 5 * self.scale

        num_treadles = len(self.draft.treadles)
        num_shafts = len(self.draft.shafts)

        grp = []
        for ii, treadle in enumerate(self.draft.treadles):
            startx = (ii * self.scale) + offsetx
            endx = startx + self.scale

            treadle_no = ii + 1

            for jj, shaft in enumerate(self.draft.shafts):
                starty = (((num_shafts - jj - 1) * self.scale) +
                          offsety)
                endy = starty + self.scale

                grp.append(SVG.rect(
                    x=startx,
                    y=starty,
                    width=self.scale,
                    height=self.scale,
                    style='stroke:%s; fill:%s' % (self.foreground,
                                                  self.background)))

                if shaft in treadle.shafts:
                    self.paint_fill_marker(grp, (startx, starty, endx, endy))

                # on the last treadle, paint the shaft markers
                if treadle_no == num_treadles:
                    shaft_no = jj + 1
                    if (shaft_no != 0) and (shaft_no % 4 == 0):
                        # draw line
                        line_startx = endx
                        line_endx = line_startx + (2 * self.scale)
                        line_starty = line_endy = starty
                        grp.append(SVG.line(
                            x1=line_startx,
                            y1=line_starty,
                            x2=line_endx,
                            y2=line_endy,
                            style='stroke:%s' % self.numbering))
                        grp.append(SVG.text(
                            str(shaft_no),
                            x=(line_startx + 3),
                            y=(line_starty + 2 + self.font_size),
                            style='font-family:%s; font-size:%s; fill:%s' % (
                                self.font_family,
                                self.font_size,
                                self.numbering)))

            # paint the number if it's a multiple of 4 and not the first one
            if (treadle_no != 0) and (treadle_no % 4 == 0):
                # draw line
                startx = endx = (treadle_no * self.scale) + offsetx
                starty = 3 * self.scale
                endy = (5 * self.scale) - 1
                grp.append(SVG.line(
                    x1=startx,
                    y1=starty,
                    x2=endx,
                    y2=endy,
                    style='stroke:%s' % self.numbering))
                # draw text on left side, right justified
                grp.append(SVG.text(
                    str(treadle_no),
                    x=(startx - 3),
                    y=(starty + self.font_size),
                    text_anchor='end',
                    style='font-family:%s; font-size:%s; fill:%s' % (
                        self.font_family,
                        self.font_size,
                        self.numbering)))
        doc.append(SVG.g(*grp))

    def paint_treadling(self, doc):
        num_threads = len(self.draft.weft)

        offsetx = (1 + len(self.draft.warp)) * self.scale
        offsety = (6 + len(self.draft.shafts)) * self.scale

        grp = []
        for ii, thread in enumerate(self.draft.weft):
            starty = (ii * self.scale) + offsety
            endy = starty + self.scale

            for jj, treadle in enumerate(self.draft.treadles):
                startx = (jj * self.scale) + offsetx
                endx = startx + self.scale
                grp.append(SVG.rect(
                    x=startx,
                    y=starty,
                    width=self.scale,
                    height=self.scale,
                    style='stroke:%s; fill:%s' % (self.foreground,
                                                  self.background)))

                if treadle in thread.treadles:
                    # draw treadling marker
                    self.paint_fill_marker(grp, (startx, starty, endx, endy))

            # paint the number if it's a multiple of 4
            thread_no = ii + 1
            if ((thread_no != num_threads) and
                (thread_no != 0) and
                    (thread_no % 4 == 0)):
                # draw line
                startx = endx
                starty = endy
                endx = startx + (2 * self.scale)
                endy = starty
                grp.append(SVG.line(
                    x1=startx,
                    y1=starty,
                    x2=endx,
                    y2=endy,
                    style='stroke:%s' % self.numbering))
                # draw text
                grp.append(SVG.text(
                    str(thread_no),
                    x=(startx + 3),
                    y=(starty - 4),
                    style='font-family:%s; font-size:%s; fill:%s' % (
                        self.font_family,
                        self.font_size,
                        self.numbering)))
        doc.append(SVG.g(*grp))

    def paint_drawdown(self, doc):
        offsety = (6 + len(self.draft.shafts)) * self.scale
        floats = self.draft.compute_floats()

        grp = []
        for start, end, visible, length, thread in floats:
            if visible:
                startx = start[0] * self.scale
                starty = (start[1] * self.scale) + offsety
                endx = (end[0] + 1) * self.scale
                endy = ((end[1] + 1) * self.scale) + offsety
                width = endx - startx
                height = endy - starty
                grp.append(SVG.rect(
                    x=startx,
                    y=starty,
                    width=width,
                    height=height,
                    style='stroke:%s; fill:%s' % (self.foreground,
                                                  thread.color.css)))
        doc.append(SVG.g(*grp))

    def render_to_string(self):
        return self.make_svg_doc()

    def save(self, filename):
        s = svg_preamble + '\n' + self.make_svg_doc()
        with open(filename, 'w') as f:
            f.write(s)


class PDFRenderer(object):
    def __init__(self, draft):
        self.draft = draft

    def save(self, filename):
        with tempfile.NamedTemporaryFile() as f:
            SVGRenderer(self.draft).save(f.name)
            rldrawing = svg2rlg(f.name)
        renderPDF.drawToFile(rldrawing, filename)
