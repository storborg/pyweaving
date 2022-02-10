from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import os.path
import svgwrite
from PIL import Image, ImageDraw, ImageFont
from math import floor
from . import get_project_root, WHITE, BLACK, MID, WarpThread

homedir = get_project_root()
font_path = os.path.join(homedir, 'data','Arial.ttf')

### Helper function which calculates width of cells and stores in Draft on threads
##   Also modifies modifies style
def calculate_box_sizing(draft, style):
    """ Store the yarn width on each thread,
         calculated from spacings data, on each thread.
    """
    all_spacings = draft.thread_stats["summary"]
    basicbox = style.box_size
    clarity_factor = style.clarity_factor
    sizing = []
    # calculate ratios of boxes
    if all_spacings:
        ratios = [b/all_spacings[0] for b in all_spacings]
        for i,r in enumerate(ratios):
            if style.spacing_style == "clarity":
                sizing.append([all_spacings[i],basicbox  + (i*clarity_factor*basicbox)])
            else: # "accuracy"
                sizing.append([all_spacings[i],all_spacings[i]*basicbox])
                # turn off some style that there is no room for (ugly)
                style.disable_tickmarks()
                style.set_warp_weft_style("solid")
                # self.style.disable_thread_color()

    # store this info in all the threads for easy rendering later (thread.yarn_width)
    # print(sizing) #!
    if sizing:
        for thread in draft.warp:
            spacing = thread.spacing
            for (s,dist) in sizing:
                # print(s==spacing,spacing)
                if s == spacing:
                    thread.yarn_width = dist
                    break # stop looking
        for thread in draft.weft:
            spacing = thread.spacing
            for (s,dist) in sizing:
                # print(s==spacing,spacing)
                if s == spacing:
                    thread.yarn_width = dist
                    break # stop looking
    else: # no spacng in wif so use
        for thread in draft.warp:
            thread.yarn_width = basicbox
        for thread in draft.weft:
            thread.yarn_width = basicbox
    return sizing



class ImageRenderer(object):
    # TODO:
    # - Add a "drawndown only" option
    # - Add a default tag (like a small delta symbol) to signal the initial
    # shuttle direction
    # - Add option to render the backside of the fabric
    # - Add option to render a bar graph of the thread crossings along the
    # sides
    # - Add option to render 'stats table'
    #   - Warp unit size / reps
    #   - Weft unit size / reps
    #   - Selvedge continuity
    # - Add option to rotate orientation
    # - Add option to render selvedge continuity
    # - Add option to render inset "scale view" rendering of fabric
    # - Support variable thickness threads

        
    
    def __init__(self, draft, style, show_liftplan=False, show_structure=False):
        
        self.draft = draft
        self.style = style

        self.show_liftplan = show_liftplan   # force liftplan display
        self.show_structure = show_structure

        self.border_pixels = style.border_pixels
        self.pixels_per_square = style.box_size

        self.background = style.background
        self.outline_color = style.outline_color
        self.boxfill_color = style.boxfill_color
        self.tick_color = style.tick_color_rgb

        self.tick_font_size = int(round(self.pixels_per_square * 1.2))
        self.thread_font_size = int(round(self.pixels_per_square * 0.8))
        self.title_font_size = int(round(self.pixels_per_square * self.style.title_font_size_factor))

        self.tick_font = ImageFont.truetype(font_path, self.tick_font_size)
        self.thread_font = ImageFont.truetype(font_path, self.thread_font_size)
        self.title_font = ImageFont.truetype(font_path, self.title_font_size)
  
        
    def pad_image(self, im):
        """ Final image has border added by pasting image into a larger one
        """
        w, h = im.size
        desired_w = w + (self.border_pixels * 2)
        desired_h = h + (self.border_pixels * 2)
        new = Image.new('RGB', (desired_w, desired_h), self.background.rgb)
        new.paste(im, (self.border_pixels, self.border_pixels))
        return new

    def make_pil_image(self):
        """ Determine size of components,
             make image,
             layout each part and draw them,
             add a border round the outside.
        """
        # gather spacings data for stats and calc yarn widths for drawdown
        # - store in threads
        calculate_box_sizing(self.draft, self.style)
        # calculate image width by summing up regions
        warp_area_length = int(sum([t.yarn_width/self.pixels_per_square for t in self.draft.warp]))
        # gather width sizes
        width_squares_estimate = warp_area_length + 1 + 3 # weft+heddles
        width_squares_estimate += self.style.tick_length + self.style.weft_gap  + self.style.drawdown_gap
        if self.show_liftplan or self.draft.liftplan:
            width_squares_estimate += len(self.draft.shafts)
        else:
            width_squares_estimate += len(self.draft.treadles)

        # calculate image height by summing up regions
        weft_area_length = int(sum([t.yarn_width/self.pixels_per_square for t in self.draft.weft]))
        height_squares_estimate = weft_area_length + len(self.draft.shafts) + \
                                  self.style.warp_gap  + self.style.drawdown_gap + \
                                  len(self.draft.draft_title) * 2 + 1 +self.style.tick_length
        # add mini stats
        stats = self.draft.get_mini_stats()
        height_squares_estimate += int((len(stats) * self.tick_font_size * 1.5) / self.pixels_per_square) #(spacing)

        # add Notes
        if self.draft.collected_notes:
            notes_size = len(self.draft.collected_notes) + 2
            height_squares_estimate += int((notes_size * self.tick_font_size * 1.5) / self.pixels_per_square)

        # Create image
        # outline width of +1 is added otherwise contents overflow on right
        width = width_squares_estimate * self.pixels_per_square + 1
        height = height_squares_estimate * self.pixels_per_square + 1
        startpos = (0,0) # in squares
        im = Image.new('RGB', (width, height), self.background.rgb)
        draw = ImageDraw.Draw(im)
        
        # Layout
        titlestart = startpos
        
        # Title
        titleend = self.paint_title(titlestart, draw, self.draft.draft_title)
        # Ministats
        ministatsend = self.paint_ministats((titlestart[0],titleend[1]), stats, draw)
        
        # Warpcolors
        warpstart = [startpos[0], ministatsend[1]]
        heddles_offset = 2
        warpstart[0] += heddles_offset # heddlestats
        warpend = self.paint_warp_colors(warpstart, draw)
        warpstart[0] -= heddles_offset # heddlestats
        
        # Heddle stats
        heddlestart = (warpstart[0], warpend[1]+self.style.warp_gap)
        heddleend = self.paint_heddles_stats(heddlestart, draw)
        
        # Threading
        threadingstart = (heddleend[0], warpend[1]+self.style.warp_gap)
        threadingend = self.paint_threading(threadingstart, draw)
        # Tieup status
        self.paint_tieup_status((warpend[0]+self.style.drawdown_gap, warpstart[1]), draw)
        
        tieupstart = (threadingend[0]+self.style.drawdown_gap, threadingstart[1])
        treadlingstart = (threadingend[0]+self.style.drawdown_gap, threadingend[1]+self.style.drawdown_gap)
        
        # Liftplan or Treadling
        if self.show_liftplan or self.draft.liftplan:
            treadlingend = self.paint_liftplan(treadlingstart, draw)
            tieupend=(0,0)
        else:
            treadlingend = self.paint_treadling(treadlingstart, draw)
            tieupend = self.paint_tieup(tieupstart, draw)
        
        # Weftcolors
        weftstart = (max(treadlingend[0],tieupend[0])+self.style.weft_gap, threadingend[1]+self.style.drawdown_gap)
        weftend = self.paint_weft_colors(weftstart, draw)
        
        # Drawdown
        drawdownstart = (heddleend[0], threadingend[1]+self.style.drawdown_gap)
        drawdownend = self.paint_drawdown(drawdownstart, draw)
        self.paint_start_indicator(drawdownstart, warp_area_length, draw)
        
        # Notes
        notesend = drawdownend
        if self.draft.collected_notes:
            notesend = self.paint_notes((drawdownstart[0],drawdownend[1]), self.draft.collected_notes, draw)
        
        # Pad image
        del draw
        im = self.pad_image(im)
        return im

    def paint_tieup_status(self, startpos, draw):
        " indicate rising or falling, from file "
        state = "(Rising shed)"
        if not self.draft.rising_shed: state = "(Falling shed)"
        offsetx,offsety = startpos
        
        vcenter_adj = (self.pixels_per_square/10) -1 + (self.pixels_per_square-self.thread_font_size)/2
        draw.text((offsetx * self.pixels_per_square, offsety * self.pixels_per_square +vcenter_adj),
                       state,
                       font=self.thread_font, fill=BLACK.rgb)
        
    def paint_title(self, startpos, draw, titles):
        """ Add the title from Notes and the filename load from
        """
        offsetx,offsety = startpos
        longest = titles[0]
        for t in titles:
            if len(t) > len(longest): longest = t
        textw, texth = draw.textsize(longest, font=self.title_font)
        lineheight = self.style.title_font_size_factor *1.2 #(for spacing)
        
        endwidth = offsetx + textw/self.style.box_size
        endheight = int(offsety + lineheight * len(titles))+1
        for i,title in enumerate(titles[:-1]):
            draw.text((offsetx, (offsety + i*lineheight) * self.pixels_per_square),
                       title,
                       align='left',
                       font=self.title_font,
                       fill=BLACK.rgb)
        # do last one (filename) smaller
        draw.text((offsetx, (offsety + (len(titles)-1)*lineheight) * self.pixels_per_square),
                       titles[-1],
                       align='left', font=self.tick_font, fill=BLACK.rgb)
        
        return (endwidth, endheight)
        
    def paint_ministats(self, startpos, stats, draw):
        """ Short series of hopefully useful observations """
        offsetx,offsety = startpos
        longest = stats[0]
        for t in stats:
            if len(t) > len(longest): longest = t
        textw, texth = draw.textsize(longest, font=self.tick_font)
        endwidth = offsetx + textw/self.pixels_per_square
        lineheight = self.style.title_font_size_factor *1.02 #(for spacing)
        endheight = int(offsety + lineheight * len(stats))+1
        
        for i,stat in enumerate(stats):
            draw.text((offsetx, (offsety + i*lineheight) * self.pixels_per_square),
                       stat,align='left',
                       font=self.tick_font, fill=BLACK.rgb)
        return (endwidth, endheight)

    def paint_notes(self, startpos, notes, draw):
        """ The Notes from the wif file.
            - Also show creation date and s/w used
        """
        # notes are a list of strings(lines)
        offsetx,offsety = startpos
        longest = ""
        lines = ["Notes:"]
        for note in notes:
            lines.append(note)
            if len(note) > len(longest): longest = note
        textw, texth = draw.textsize(longest, font=self.tick_font)
        endwidth = offsetx + textw/self.pixels_per_square
        lineheight = self.style.title_font_size_factor *1.02 #(for spacing)
        endheight = int(offsety + lineheight * len(lines)) + 1
        
        for i,line in enumerate(lines):
            draw.text((offsetx, (offsety + (i+1)*lineheight) * self.pixels_per_square),
                       line,align='left',
                       font=self.tick_font, fill=BLACK.rgb)
        return (endwidth, endheight)
            
    def paint_start_indicator(self, startpos, weft_length, draw):
        offsetx,offsety = startpos
        lift = self.pixels_per_square/10 # lift above line
        starty = offsety * self.pixels_per_square - lift
        topy = (starty - (self.pixels_per_square / 2)) - lift
        
        if self.draft.start_at_lowest_thread:
            # right side
            startx = (offsetx + weft_length -1) * self.pixels_per_square
            endx = startx + self.pixels_per_square
        else:
            # left side
            startx = offsetx * self.pixels_per_square
            endx = startx + self.pixels_per_square
        vertices = [ (startx, topy),
                     (endx, topy),
                     (startx + (self.pixels_per_square / 2), starty) ]
        #
        draw.polygon(vertices, fill=self.boxfill_color.rgb)
    
    def paint_heddles_stats(self, startpos, draw):
        " show heddles needed per warp shaft "
        offsetx,offsety = startpos # upper left corner position
        offsety -= 1 # text strats above line
        if self.style.warp_tick_active or self.style.tieup_tick_active:
            starty = (offsety + self.style.tick_length) * self.pixels_per_square
        else:
            starty = offsety * self.pixels_per_square
        startx = offsetx * self.pixels_per_square
        
        vcenter_adj = (self.pixels_per_square/10) -1 + (self.pixels_per_square-self.thread_font_size)/2
        total = 0
        for i in range(len(self.draft.shafts),0,-1):
            # shaft in self.draft.shafts:
            shaft = self.draft.shafts[i-1]
            starty += self.pixels_per_square
            count = len([1 for t in self.draft.warp if t.shaft == shaft])
            total += count
            draw.text((startx, starty+vcenter_adj),
                       "%3d"%(count),
                       font=self.thread_font, fill=BLACK.rgb)
        #
        draw.text((startx, starty + 2 + self.pixels_per_square),
                       "%3d"%(total),
                       font=self.thread_font, fill=BLACK.rgb)
        endwidth  = offsetx + int(3 * self.thread_font_size / self.pixels_per_square)
        endheight = offsety + len(self.draft.shafts) + 1
        return (endwidth, endheight)

    def paint_warp_colors(self, startpos, draw):
        """ Paint each thread as an outlined box, filled with thread color
        - counts backwards as thread one is on RHS
        """
        offsetx,offsety = startpos # upper left corner position
        starty = offsety * self.pixels_per_square
        endy = (offsety+1) * self.pixels_per_square
        endx = offsetx * self.pixels_per_square # start here
        previous = endx
        
        index = len(self.draft.warp)-1
        while index != -1:
            thread = self.draft.warp[index]
            if thread.spacing:
                endx += thread.yarn_width
            else:
                endx += self.style.box_size
            startx = previous
            draw.rectangle((startx, starty, endx, endy),
                           outline=self.outline_color.rgb,
                           fill=thread.color.rgb)
            previous = endx
            index -= 1
        #
        endwidth = int(endx/self.pixels_per_square)
        endheight = offsety + 1
        return (endwidth, endheight)

    def paint_fill_marker(self, draw, box, dotcolor, style, label=None, yarncolor=None):
        startx, starty, endx, endy = box
        textcol = BLACK
        margin = 1

        if yarncolor:
            if yarncolor.intensity < 0.5:
                textcol = WHITE
            draw.rectangle((startx + margin, starty + margin, endx - margin, endy - margin),
                                    fill=yarncolor.rgb)
            if yarncolor.close(self.style.background):
                if style=='solid':# or style =='dot':
                    # yarn color is too close to background and so not visible
                    # so  if 'solid' override to draw 'dot' style instead
                    style = 'dot'
                    yarncolor = None
                # else:
                    # draw.rectangle((startx + margin, starty + margin, endx - margin, endy - margin),
                                    # fill=yarncolor.rgb)
            
        
        if style == 'dot' and not yarncolor:
            margin = floor((endx-startx)/5)
            draw.rectangle((startx + margin, starty + margin, endx - margin, endy - margin),
                            fill=dotcolor.rgb)
        elif style == 'solid' and not yarncolor:
            draw.rectangle((startx + margin, starty + margin, endx - margin, endy - margin),
                            fill=dotcolor.rgb)
        elif style == 'number' or style == 'XO':
            if style == 'number':
                hcenter_adj = len(label) * self.thread_font_size/4
            else: # "XO"
                hcenter_adj = self.thread_font_size/3
            vcenter_adj = (self.style.box_size/10) -1 + (box[3]-box[1]-self.thread_font_size)/2
            draw.text((startx+ (endx-startx)/2-hcenter_adj, starty+vcenter_adj),
                      label,
                      align='center',
                      font=self.thread_font,
                      fill=textcol.rgb)
            

    def paint_threading(self, startpos, draw):
        num_threads = len(self.draft.warp)
        num_shafts = len(self.draft.shafts)
        bgcolor = None
        label = 'O' # default to rising shed
        if not self.draft.rising_shed:
            label = 'X'
        
        # position
        offsetx,offsety = startpos # upper left corner position
        endheight = len(self.draft.shafts) + offsety
        
        start_tick_y = offsety
        tick_length = self.style.tick_length
        if self.style.warp_tick_active or self.style.tieup_tick_active:
            start_warp_y = start_tick_y + tick_length -1
            endheight += tick_length
        else:
            start_warp_y = start_tick_y - 1
        
        distance = offsetx * self.pixels_per_square
        previous = distance
        t_index = len(self.draft.warp)-1 # count this down and use where we see ii
        while t_index != -1:
            thread = self.draft.warp[t_index]
            if thread.spacing:
                distance += thread.yarn_width
            else:
                distance += self.style.box_size
            startx = previous
            endx = distance
            
            if self.style.warp_use_thread_color:
                bgcolor = thread.color

            for jj, shaft in enumerate(self.draft.shafts):
                starty = (start_warp_y + (num_shafts - jj)) * self.pixels_per_square
                endy = starty + self.pixels_per_square
                draw.rectangle((startx, starty, endx, endy),
                               outline=self.outline_color.rgb)

                if shaft == thread.shaft:
                    # draw threading marker
                    if self.style.warp_style == 'number':
                        label = str(jj+1)
                    self.paint_fill_marker(draw, (startx, starty, endx, endy), self.style.boxfill_color, self.style.warp_style, label, bgcolor)

            # horizontal tick, number if it's a multiple of tick_mod and not the first one
            if self.style.warp_tick_active:
                thread_no = t_index + 1
                if ((thread_no != num_threads) and
                    (thread_no != 0) and
                        (thread_no % self.style.tick_mod == 0)):
                    # draw line
                    tstarty = start_tick_y * self.pixels_per_square
                    tendy = ((start_tick_y + tick_length) * self.pixels_per_square) - 1
                    draw.line((startx, tstarty, startx, tendy),
                              fill=self.tick_color)
                    if self.style.show_ticktext:
                        # draw text
                        draw.text((startx + 2, tstarty + 2),
                                  str(thread_no),
                                  font=self.tick_font,
                                  fill=self.tick_color)
            previous = distance
            t_index -= 1
        #
        endwidth = int(distance/self.pixels_per_square)
        return (endwidth, endheight)
        
    def paint_weft_colors(self, startpos, draw):
        """ Paint the Vertical weft color bar
        """
        offsetx,offsety = startpos
        endwidth = offsetx + 1
        if self.style.weft_tick_active:
            endwidth += self.style.tick_length
        startx = offsetx * self.pixels_per_square
        endx = startx + self.pixels_per_square
        
        endy = offsety * self.pixels_per_square # steps down along the weft
        previous = endy
        index = 0
        while index != len(self.draft.weft):
            thread = self.draft.weft[index]
            if thread.spacing:
                endy += thread.yarn_width
            else:
                endy += self.style.box_size
            draw.rectangle((startx, previous, endx, endy),
                           outline=self.outline_color.rgb,
                           fill=thread.color.rgb)
            previous = endy
            index += 1
        #
        endheight = int(endy/self.pixels_per_square)
        return (endwidth, endheight)

    def paint_liftplan(self, startpos, draw):
        num_threads = len(self.draft.weft)
        bgcolor = None
        label = 'O' # default to rising shaft
        if not self.draft.rising_shed:
            label = 'X'
        
        offsetx,offsety = startpos
        endwidth = len(self.draft.shafts) + offsetx
        if self.style.weft_tick_active:
            endwidth += self.style.tick_length
        
        endy = offsety * self.pixels_per_square # steps down along the weft
        previous = endy
        index = 0
        while index != len(self.draft.weft):
            thread = self.draft.weft[index]
            if thread.spacing:
                endy += thread.yarn_width
            else:
                endy += self.style.box_size
            
            for jj, shaft in enumerate(self.draft.shafts):
                startx = (jj + offsetx) * self.pixels_per_square
                endx = startx + self.pixels_per_square
                draw.rectangle((startx, previous, endx, endy),
                               outline=self.outline_color.rgb)

                if shaft in thread.connected_shafts:
                    # draw liftplan marker
                    if self.style.weft_use_thread_color:
                        bgcolor = thread.color
                    if self.style.weft_style == 'number':
                        label = str(jj+1)
                    self.paint_fill_marker(draw, (startx, previous, endx, endy), self.style.boxfill_color, self.style.weft_style, label, bgcolor)

            # vertical tick, number if it's a multiple of tick_mod and not the first one
            if self.style.weft_tick_active:
                thread_no = index+1 #ii + 1
                if ((thread_no != num_threads) and
                    (thread_no != 0) and
                        (thread_no % self.style.tick_mod == 0)):
                    # draw line
                    tick_endx = startx + (self.style.tick_length * self.pixels_per_square)
                    draw.line((endx, endy, tick_endx, endy),
                              fill=self.tick_color)
                    # draw text
                    draw.text((endx + self.tick_font_size/4, endy - 2 - self.tick_font_size),
                              str(thread_no),
                              font=self.tick_font,
                              fill=self.tick_color)
            #
            previous = endy
            index += 1
        #
        endheight = int(endy/self.pixels_per_square)
        return (endwidth, endheight) 

    def paint_tieup(self, startpos, draw):
        offsetx,offsety = startpos
        label = 'O' # default to rising shaft
        if not self.draft.rising_shed:
            label = 'X'

        tick_length = self.style.tick_length
        end_tick = offsety + tick_length
        start_tieup_y = offsety - 1
        if self.style.warp_tick_active or self.style.tieup_tick_active:
            start_tieup_y += tick_length
        endwidth = len(self.draft.treadles) + offsetx
        endheight = len(self.draft.shafts) + startpos[1]
        
        num_treadles = len(self.draft.treadles)
        num_shafts = len(self.draft.shafts)

        for ii, treadle in enumerate(self.draft.treadles):
            startx = (ii + offsetx) * self.pixels_per_square
            endx = startx + self.pixels_per_square

            treadle_no = ii + 1

            for jj, shaft in enumerate(self.draft.shafts):
                starty = (num_shafts - jj + start_tieup_y) * self.pixels_per_square
                endy = starty + self.pixels_per_square

                draw.rectangle((startx, starty, endx, endy),
                               outline=self.outline_color.rgb)

                if shaft in treadle.shafts:
                    if self.style.tieup_style == 'number':
                        label = str(jj+1)
                    self.paint_fill_marker(draw, (startx, starty, endx, endy), self.style.boxfill_color, self.style.tieup_style, label, None)

                # vertical tick, number if it's a multiple of tick_mod and not the first one
                if self.style.tieup_tick_active:
                    if treadle_no == num_treadles:
                        shaft_no = jj + 1
                        if (shaft_no != 0) and (shaft_no % self.style.tick_mod == 0):
                            # draw line
                            line_startx = endx
                            line_endx = line_startx + (self.style.tick_length * self.pixels_per_square)
                            line_starty = line_endy = starty
                            draw.line((line_startx, line_starty,
                                       line_endx, line_endy),
                                       fill=self.tick_color)
                            if self.style.show_ticktext:
                                # draw text
                                draw.text((line_startx + 2, line_starty),
                                           str(shaft_no),
                                           font=self.tick_font,
                                           fill=self.tick_color)
            
            # horizontal ticks, number if it's a multiple of tick_mod and not the first one
            if self.style.tieup_tick_active:
                if (treadle_no != 0) and (treadle_no % self.style.tick_mod == 0):
                    # draw line
                    startx = endx = (treadle_no + offsetx) * self.pixels_per_square
                    starty = offsety * self.pixels_per_square
                    endy = (end_tick * self.pixels_per_square) - 1
                    draw.line((startx, starty, endx, endy),
                              fill=self.tick_color)
                    if self.style.show_ticktext:
                        # draw text on left side, right justified
                        textw, texth = draw.textsize(str(treadle_no), font=self.thread_font)
                        draw.text((startx - textw*1.6, starty + 2),
                                  str(treadle_no),
                                  font=self.tick_font,
                                  fill=self.tick_color)
        #
        return (endwidth, endheight)

    def paint_treadling(self, startpos, draw):
        
        num_threads = len(self.draft.weft)
        bgcolor = None
        label = 'O' # default to rising shed
        if not self.draft.rising_shed:
            label = 'X'
        
        offsetx, offsety = startpos
        endwidth = len(self.draft.treadles) + offsetx
        if self.style.weft_tick_active:
            endwidth += self.style.tick_length
        
        endy = offsety * self.pixels_per_square # steps down along the weft
        previous = endy
        index = 0
        while index != len(self.draft.weft):
            thread = self.draft.weft[index]
            if thread.spacing:
                endy += thread.yarn_width
            else:
                endy += self.style.box_size
            if self.style.weft_use_thread_color:
                bgcolor = thread.color

            for jj, treadle in enumerate(self.draft.treadles):
                startx = (jj + offsetx) * self.pixels_per_square
                endx = startx + self.pixels_per_square
                draw.rectangle((startx, previous, endx, endy),
                               outline=self.outline_color.rgb)

                if treadle in thread.treadles:
                    # draw treadling marker
                    if self.style.weft_style == 'number':
                        label = str(jj+1)
                    self.paint_fill_marker(draw, (startx, previous, endx, endy), self.style.boxfill_color, self.style.weft_style, label, bgcolor)
            # vertical tick, number if it's a multiple of tick_mod and not the first one
            if self.style.weft_tick_active:
                # ii = index
                thread_no = index + 1
                if ((thread_no != num_threads) and
                    (thread_no != 0) and
                        (thread_no % self.style.tick_mod == 0)):
                    # draw line
                    tick_endx = endx + (self.style.tick_length * self.pixels_per_square)
                    draw.line((endx, endy, tick_endx, endy),
                              fill=self.tick_color)
                    if self.style.show_ticktext:
                        # draw text
                        draw.text((endx + self.tick_font_size/4, endy - 2 - self.tick_font_size),
                                  str(thread_no),
                                  font=self.tick_font,
                                  fill=self.tick_color)
            #
            previous = endy
            index += 1
        #
        endheight = int(endy/self.pixels_per_square)
        return (endwidth, endheight)
 
    def paint_drawdown(self, startpos, draw, front=True, asfabric=False):
        """ Draw different styles of drawodown
            - solid, box, interlace - also shaded variants
            - asfabric will use solid and hide overlapping wefts
        """
        num_threads = len(self.draft.warp)
        floats = self.draft.computed_floats
        
        float_color = self.style.floats_color
        float_cutoff = self.style.floats_count
        show_float = self.style.show_floats
        outline_color = self.outline_color.rgb
        
        offsetx,offsety = startpos
        offsetx *= self.pixels_per_square
        offsety *= self.pixels_per_square
        if self.show_structure:
            outline_color = MID.rgb
        
        # shading prep
        indent = self.style.interlace_width # how much indent in the interlace style
        # BG fills in gaps when interlacing
        drawdown_width = sum([t.yarn_width for t in self.draft.warp])
        drawdown_height = sum([t.yarn_width for t in self.draft.weft])
        draw.rectangle((offsetx+indent-1, offsety+indent-1,
                        offsetx+drawdown_width, offsety+drawdown_height),
                        fill=outline_color)
        # shading offset - used when drawing the shadow and highlight thread features
        # works for 10,20 but not 30 (pixels_per_square)
        so2 = max(1, self.pixels_per_square//10)
        so1 = max(1, so2//2)
        
        for start, end, visible, length, thread in floats:
            if visible==front: # visible is front of fabric. If front is false - show back of fabric
                realpos = self.draft.get_position(thread, start, end, self.pixels_per_square, True) #! True also front or !front
                (startx,starty), (endx,endy) = realpos
                startx += offsetx
                starty += offsety
                endx += offsetx
                endy += offsety

                if self.show_structure:
                    # Use warp=black, weft=white
                    if isinstance(thread, WarpThread):
                        fill_color = BLACK.rgb
                    else: fill_color = WHITE.rgb
                    outline_color = MID.rgb
                else: # use the thread colors
                    fill_color = thread.color.rgb
                    outline_color = self.outline_color.rgb
                # highlight the long floats
                if show_float and length >= float_cutoff:
                    fill_color = float_color.rgb
                
                # The drawdown box styles
                if 'solid' in self.style.drawdown_style:
                    draw.rectangle((startx, starty, endx-1, endy-1),
                                    outline=None,
                                    fill=fill_color)
                    if  'shade' in self.style.drawdown_style:
                        # darker thin, lighter thick, natural, darker thick
                        draw.line((startx, starty, endx-so2, starty), # top highlight
                                  fill=thread.color.highlight, width=so2)
                        draw.line((startx, endy-so2, endx-so1, endy-so2), # bot shadow
                                  fill=thread.color.shadow, width=so2)
                        draw.line((startx, starty+so1, startx, endy-so2-so1), # left highlight
                                  fill=thread.color.highlight, width=so2)
                        draw.line((endx-so2, starty, endx-so2, endy-so2), # right shadow
                                      fill=thread.color.shadow, width=so2)
                elif 'box' in self.style.drawdown_style:
                    draw.rectangle((startx, starty, endx, endy),
                                    outline=outline_color,
                                    fill=fill_color)
                    if  'shade' in self.style.drawdown_style:
                        # darker thin, lighter thick, natural, darker thick
                        draw.line((startx+so1, starty+so1, endx-so1, starty+so1), # top shadow
                                  fill=thread.color.shadow, width=so1)
                        draw.line((startx+so1, starty+so2, endx-so1, starty+so2), # top highlight
                                  fill=thread.color.highlight, width=so2)
                        draw.line((startx+so1, endy-so2, endx-so1, endy-so2), # bot shadow
                                  fill=thread.color.shadow, width=so2)
                        draw.line((startx+so1, starty+so1, startx+so1, endy-so2), # left shadow
                                  fill=thread.color.shadow, width=so1)
                        draw.line((startx+so2, starty+so2, startx+so2, endy-so2-so1), # left highlight
                                  fill=thread.color.highlight, width=so2)
                        # lower shadow different
                        if isinstance(thread, WarpThread):
                            draw.line((endx-so1, starty+so1, endx-so1, endy-so2), # right shadow
                                      fill=thread.color.shadow, width=so1)
                        else: # weft thread
                            draw.line((endx-so2, starty+so1, endx-so2, endy-so2), # right shadow
                                      fill=thread.color.shadow, width=so2)
                elif 'interlace' in self.style.drawdown_style:
                    if isinstance(thread, WarpThread):
                        boxx1 = startx + indent
                        boxx2 = endx - indent
                        boxy1 = starty - indent
                        boxy2 = endy + indent
                    else:
                        boxy1 = starty + indent
                        boxy2 = endy - indent
                        boxx1 = startx - indent
                        boxx2 = endx + indent
                
                    draw.rectangle((boxx1, boxy1, boxx2, boxy2),
                                    outline=None,
                                    fill=fill_color)
                    # draw the stepped thread edge lines
                    draw.line((boxx1, boxy1, boxx2, boxy1),
                              fill=outline_color, width=indent)
                    draw.line((boxx1, boxy1, boxx1, boxy2),
                              fill=outline_color, width=indent)
                    draw.line((boxx2, boxy1, boxx2, boxy2),
                              fill=outline_color, width=indent)
                    draw.line((boxx1, boxy2, boxx2, boxy2),
                              fill=outline_color, width=indent)
                    if  'shade' in self.style.drawdown_style:
                        # darker thin, lighter thick, natural, darker thick
                        draw.line((boxx1+so1, boxy1+so1, boxx2-so1, boxy1+so1), # top shadow
                                  fill=thread.color.shadow, width=so1)
                        draw.line((boxx1+so1, boxy1+so2, boxx2-so1, boxy1+so2), # top highlight
                                  fill=thread.color.highlight, width=so2)
                        draw.line((boxx1+so1, boxy2-so2, boxx2-so1, boxy2-so2), # bot shadow
                                  fill=thread.color.shadow, width=so2)
                        #
                        draw.line((boxx1+so1, boxy1+so1, boxx1+so1, boxy2-so2), # left shadow
                                  fill=thread.color.shadow, width=so1)
                        draw.line((boxx1+so2, boxy1+so2, boxx1+so2, boxy2-so2-so1), # left highlight
                                  fill=thread.color.highlight, width=so2)
                        # lower shadow different
                        if isinstance(thread, WarpThread):
                            draw.line((boxx2-so1, boxy1+so1, boxx2-so1, boxy2-so2), # right shadow
                                      fill=thread.color.shadow, width=so1)
                        else: # weft thread
                            draw.line((boxx2-so2, boxy1+so1, boxx2-so2, boxy2-so2), # right shadow
                                      fill=thread.color.shadow, width=so2)
        #
        endwidth = int(endx/self.pixels_per_square)
        endheight = int(endy/self.pixels_per_square)
        return (endwidth, endheight)

    def show(self):
        """ Used if no outfile defined. Show it
        """
        im = self.make_pil_image()
        im.show()

    def save(self, filename):
        im = self.make_pil_image()
        im.save(filename)


### SVG section

def compose_css_box(classname, fill, stroke_col, stroke_thick):
    css = "."+classname+ " {fill:"
    if fill:
        css += svgwrite.rgb(*fill)+";"
    else:
        css += "none;"
    if stroke_col:
        css += " stroke:"+svgwrite.rgb(*stroke_col) +";"
        css += " stroke-alignment: inner; "
        css += " stroke-width:" + str(stroke_thick) + "}\n"
    else: # no outline
        css = "."+classname + " {fill:" + svgwrite.rgb(*fill) + ";}\n"
    return css
    
def compose_css_line(classname, stroke_col, stroke_thick):
    css = "."+classname+ " {stroke:"+svgwrite.rgb(*stroke_col) + "; stroke-width:" + str(stroke_thick) + "}\n"
    return css
    
def compose_css_text(classname, fill, font_size, align="start", dominant_baseline=None):
    """ dominant_baseline=center will center caps text
        align = [start | middle | end]
    """
    css = "."+classname+ " {font-size:"+str(int(font_size)) + "px; font-family:Arial;"
    if  dominant_baseline:
        css += " dominant-baseline:%s; " %(dominant_baseline)
    css += " text-anchor:%s; " %(align)
    css += " fill:" + svgwrite.rgb(*fill)
    css +=  "; stroke:none; stroke-width:0}\n"
    # baseline-shift:-33%
    return css


class SVGRenderer(object):
    def __init__(self, draft, style, show_liftplan=False, show_structure=False):
        
        self.draft = draft
        self.style = style
        
        self.show_liftplan = show_liftplan
        self.show_structure = show_structure
        self.pixels_per_square = style.box_size
        self.border_pixels = style.border_pixels/self.pixels_per_square
       
        self.background = style.background

        self.tick_font_size = int(round(self.pixels_per_square * 1.0))
        self.thread_font_size = int(round(self.pixels_per_square * 0.8))
        self.title_font_size = int(round(self.pixels_per_square * self.style.title_font_size_factor))


    def create_CSS_styles(self, thread_colors, swidth=0.5):
        """ Create css style for classes.
            - only one allowed per svg.
        """
        # Style colors
        bg_col = self.style.background.rgb
        indicator_col = bg_col
        float_col = self.style.floats_color.rgb
        float_high = self.style.floats_color.highlight
        float_shad = self.style.floats_color.shadow
        box_col = self.style.outline_color.rgb
        dot_color = self.style.boxfill_color.rgb
        tick_col = self.style.tick_color_rgb
        box_size = self.style.box_size  # pixels

        css =  compose_css_box("background", bg_col, box_col, 1)       #! ??
        css =  compose_css_box("inducator", indicator_col, None, 0)    # Indicators
        css += compose_css_box("box", None, box_col, swidth)           # Basic box outline
        css += compose_css_box("floats", float_col, box_col, 1)        # Floats
        css += compose_css_box("css_boxfill_color", dot_color, None,0) # solid for warp/weft/tieup 
        css += compose_css_box("css_boxblack", BLACK.rgb, MID.rgb, swidth)  # drawdown structure
        css += compose_css_box("css_boxwhite", WHITE.rgb, MID.rgb, swidth)  # drawdown structure
        
        css += compose_css_line("ticks", tick_col, 1)                              # tick mark line
        css += compose_css_line("indents", box_col, self.style.interlace_width*2)  # tick mark line
        css += compose_css_line("floatshigh", float_high, self.style.vector_shading_width)  # floats highlight
        css += compose_css_line("floatsshad", float_shad, self.style.vector_shading_width)  # floats shadow
        css += compose_css_line("css_boxblackshad", BLACK.rgb, self.style.vector_shading_width)  # structure shadow
        css += compose_css_line("css_boxwhiteshad", WHITE.rgb, self.style.vector_shading_width)  # structure shadow
        
        css += compose_css_text("tick_text", BLACK.rgb, self.tick_font_size)            # regular black text (tick size)
        css += compose_css_text("tick_text_r", BLACK.rgb, self.tick_font_size, "end")# heddles black text (middle justified)
        css += compose_css_text("ticks_text", tick_col, self.tick_font_size)            # color text tick labels
        css += compose_css_text("ticks_text_r", tick_col, self.tick_font_size, "end")   # right justified col tick labels
        css += compose_css_text("thread_text_b", BLACK.rgb, self.thread_font_size, "middle", "central") # numeric/XO thread label
        css += compose_css_text("thread_text_w", WHITE.rgb, self.thread_font_size, "middle", "central") # numeric/XO thread label
        css += compose_css_text("title_text", BLACK.rgb, self.title_font_size)        # title text
        
        # thread_colors
        for name,color in thread_colors:
            rgb = color.rgb
            # regular outlined box for fill markers (yarns)
            css += compose_css_box(name, rgb, box_col, swidth)
            # flat variant for 'solid' drawdowns
            css += compose_css_box(name+"flat", rgb, rgb,swidth*2)
            # and lines for highlights/shadows in shading drawdown
            css += compose_css_line(name+"high", color.highlight, self.style.vector_shading_width)
            css += compose_css_line(name+"high2", color.highlight, self.style.vector_shading_width/2)
            css += compose_css_line(name+"shad", color.shadow, self.style.vector_shading_width)
            css += compose_css_line(name+"shad2", color.shadow, self.style.vector_shading_width/2)
        
        # can be added to dwg or to defs. defs is recommended
        self.dwg.defs.add(self.dwg.style(css))
        # self.dwg.add(self.dwg.style(css))
 
    
    def make_svg_doc(self, filename):
        # gather spacings data for stats and calc yarn widths for drawdown
        calculate_box_sizing(self.draft, self.style)
        
        # calculate image width by summing up regions
        warp_area_length = sum([t.yarn_width/self.pixels_per_square for t in self.draft.warp])
        # gather width sizes
        width_squares_estimate = self.border_pixels*2 + 3 # heddles
        width_squares_estimate += warp_area_length + 1 + self.style.tick_length + self.style.weft_gap  + self.style.drawdown_gap
        if self.show_liftplan or self.draft.liftplan:
            width_squares_estimate += len(self.draft.shafts)
        else:
            width_squares_estimate += len(self.draft.treadles)

        # calculate image height by summing up regions
        weft_area_length = sum([t.yarn_width/self.pixels_per_square for t in self.draft.weft])
        height_squares_estimate = self.border_pixels*2
        height_squares_estimate += weft_area_length + len(self.draft.shafts) + \
                                  self.style.warp_gap  + self.style.drawdown_gap + \
                                  len(self.draft.draft_title) * 2 + 1 +self.style.tick_length
        # add mini stats
        stats = self.draft.get_mini_stats()
        height_squares_estimate += (len(stats) * self.tick_font_size * 1.5) / self.pixels_per_square #(spacing)

        # add Notes
        if self.draft.collected_notes:
            notes_size = len(self.draft.collected_notes) + 2
            height_squares_estimate += (notes_size * self.tick_font_size * 1.5) / self.pixels_per_square

        ## Build the image
        width = width_squares_estimate * self.pixels_per_square
        height = height_squares_estimate * self.pixels_per_square
        self.dwg = svgwrite.Drawing(filename, size=(str(width)+'px', str(height)+'px'),
                                    viewBox=('0 0 %d %d'%(width*1,height*1)),
                                    debug=False)
                                    # debug=True) # True when developing but very very slow to save
        # create styles
        self.create_CSS_styles(self.draft.css_colors, self.style.box_vec_stroke)
        
        # Layout
        # - all sizes in units incrementing by self.pixels_per_square
        startpos = (self.border_pixels, self.border_pixels)

        # Title
        titleend = self.paint_title(startpos, self.draft.draft_title)

        # Ministats
        ministatsend = self.paint_ministats((startpos[0],titleend[1]), stats)
        
        # Warpcolors
        warpstart = [startpos[0], ministatsend[1]]
        heddles_offset = 2
        warpstart[0] += heddles_offset # heddlestats
        warpend = self.paint_warp_colors(warpstart)

        
        # Heddle stats
        heddlestart = (warpstart[0]- heddles_offset, warpend[1]+self.style.warp_gap)
        heddleend = self.paint_heddles_stats(heddlestart)

        # Threading
        threadingstart = (warpstart[0], warpend[1]+self.style.warp_gap)
        threadingend = self.paint_threading(threadingstart)

        # Tieup status
        self.paint_tieup_status((warpend[0]+self.style.drawdown_gap, warpstart[1]))
        
        tieupstart = (threadingend[0]+self.style.drawdown_gap, threadingstart[1])
        treadlingstart = (tieupstart[0], threadingend[1]+self.style.drawdown_gap)
        
        # Liftplan or Treadling
        if self.show_liftplan or self.draft.liftplan:
            treadlingend = self.paint_liftplan(treadlingstart)
            tieupend=(0,0)
        else:
            treadlingend = self.paint_treadling(treadlingstart)
            tieupend = self.paint_tieup(tieupstart)

        # Weftcolors
        weftstart = (max(treadlingend[0],tieupend[0])+self.style.weft_gap, threadingend[1]+self.style.drawdown_gap)
        weftend = self.paint_weft_colors(weftstart)
        
        # Drawdown
        drawdownstart = (heddleend[0], threadingend[1]+self.style.drawdown_gap)
        drawdownend = self.paint_drawdown(drawdownstart)
        self.paint_start_indicator(drawdownstart, warp_area_length)
        
        # Notes
        notesend = drawdownend
        if self.draft.collected_notes:
            notesend = self.paint_notes((drawdownstart[0],drawdownend[1]), self.draft.collected_notes)
        
        return self.dwg

    def paint_tieup_status(self, startpos):
        " indicate rising or falling, from file "
        state = "(Rising shed)"
        if not self.draft.rising_shed: state = "(Falling shed)"
        offsetx,offsety = startpos
        starty = offsety + 1
        grp = self.dwg.g(id='ministats')

        grp.add(self.dwg.text(state,
                              insert=(offsetx * self.pixels_per_square, starty * self.pixels_per_square),
                              class_="tick_text"))
        self.dwg.add(grp)
        
    def paint_title(self, startpos, titles):
        """ Add the title from Notes and the filename load from
        """
        offsetx,offsety = startpos
        grp = self.dwg.g(id='titles')
        
        lineheight = 1.3 #(for spacing)
        starty = (offsety + lineheight) * self.pixels_per_square
        
        for i,title in enumerate(titles[:-1]):
            grp.add(self.dwg.text(title,
                                  insert=(offsetx*self.pixels_per_square, starty + i*lineheight*self.pixels_per_square),
                                  class_="title_text"))
        # do last one (filename) smaller
        grp.add(self.dwg.text(titles[-1],
                              insert=(offsetx*self.pixels_per_square, starty + ((len(titles)-1)*lineheight*self.pixels_per_square)),
                              class_="tick_text"))
        self.dwg.add(grp)
        # We can't find out how long the SVG text is.
        # So can't calc endwidth
        endwidth = offsetx + len(titles[0])*self.pixels_per_square
        endheight = offsety + lineheight * len(titles) + 2
        return (endwidth, endheight)

    def paint_ministats(self, startpos, stats):
        """ Short series of hopefully useful observations """
        offsetx,offsety = startpos
        grp = self.dwg.g(id='ministats')

        lineheight =  1.3 #(for spacing)
        
        for i,stat in enumerate(stats):
            grp.add(self.dwg.text(stat,
                                  insert=(offsetx*self.pixels_per_square, (offsety + i*lineheight) * self.pixels_per_square),
                                  class_="tick_text"))
        self.dwg.add(grp)
        # We can't find out how long the SVG text is.
        # So can't calc endwidth
        endwidth = offsetx + len(stats[0])*self.pixels_per_square
        endheight = offsety + lineheight * len(stats)
        return (endwidth, endheight)
                            
    def paint_notes(self, startpos, notes):
        """ The Notes from the wif file.
            - Also show creation date and s/w used
        """
        # notes are a list of strings(lines)
        offsetx,offsety = startpos
        offsety += 1
        grp = self.dwg.g(id='notes')
        lines = ["Notes:"]
        for note in notes:
            lines.append(note)
        lineheight = 1.3 #(for spacing)
        
        for i,line in enumerate(lines):
            grp.add(self.dwg.text(line,
                                  insert=(offsetx*self.pixels_per_square, (offsety + (i+1)*lineheight) * self.pixels_per_square),
                                  class_="tick_text"))
        self.dwg.add(grp)
        # We can't find out how long the SVG text is.
        # So can't calc endwidth accurately
        endwidth = offsetx + len(lines[0])*self.pixels_per_square
        endheight = offsety + lineheight * len(lines) + 1
        return (endwidth, endheight)
        
    def paint_warp_colors(self, startpos):
        """ Paint each thread as an outlined box, filled with thread color
        - counts backwards as thread one is on RHS
        """
        offsetx,offsety = startpos # upper left corner position
        starty = offsety * self.pixels_per_square
        endy = (offsety+1) * self.pixels_per_square
        endx = offsetx * self.pixels_per_square # start here
        previous = endx
        
        grp = self.dwg.g(id='warp_colors')
        
        index = len(self.draft.warp)-1
        while index != -1:
            thread = self.draft.warp[index]
            if thread.spacing:
                endx += thread.yarn_width
            else:
                endx += self.style.box_size
            startx = previous
            grp.add(self.dwg.rect(insert=(startx, starty), size=(endx-startx, endy-starty),
                                  class_=thread.css_label))
            previous = endx
            index -= 1
        #
        self.dwg.add(grp)
        endwidth = endx/self.pixels_per_square
        endheight = offsety + 1
        return (endwidth, endheight)

    def paint_start_indicator(self, startpos, weft_length):
        offsetx,offsety = startpos
        lift = self.pixels_per_square/10 # lift above line
        starty = offsety * self.pixels_per_square - lift
        topy = (starty - (self.pixels_per_square / 2)) - lift
        
        grp = self.dwg.g(id='start_indicator')
        
        if self.draft.start_at_lowest_thread:
            # right side
            startx = (offsetx + weft_length-1) * self.pixels_per_square
            endx = startx + self.pixels_per_square
        else: # left side
            startx = offsetx * self.pixels_per_square
            endx = startx + self.pixels_per_square
        vertices = [ (startx, topy),
                     (endx, topy),
                     (startx + (self.pixels_per_square / 2), starty)]
        #
        grp.add(self.dwg.polygon(points=vertices, class_="indicator"))
        self.dwg.add(grp)
        
        
    def paint_heddles_stats(self, startpos):
        " show heddles needed per warp shaft "
        offsetx,offsety = startpos # upper left corner position
        grp = self.dwg.g(id='heddles')
        if self.style.warp_tick_active or self.style.tieup_tick_active:
            starty = (offsety + self.style.tick_length) * self.pixels_per_square
            endheight = self.style.tick_length
        else:
            starty = offsety * self.pixels_per_square
            endheight = 0
        startx = (offsetx+1) * self.pixels_per_square
        
        vcenter_adj = (self.pixels_per_square/10)
        total = 0
        for i in range(len(self.draft.shafts),0,-1):
            # shaft in self.draft.shafts:
            shaft = self.draft.shafts[i-1]
            starty += self.pixels_per_square
            count = len([1 for t in self.draft.warp if t.shaft == shaft])
            total += count
            grp.add(self.dwg.text( "%3d"%(count),
                                   insert=(startx,(starty-vcenter_adj)),
                                   class_="tick_text_r"))
        #
        grp.add(self.dwg.text( "%3d"%(total),
                               insert=(startx,(starty-vcenter_adj+self.pixels_per_square)),
                               class_="tick_text_r"))
        #
        self.dwg.add(grp)
        endwidth  = offsetx + 2
        endheight += offsety + len(self.draft.shafts) + 1 #(total)
        return (endwidth, endheight)
        
    def paint_weft_colors(self, startpos):
        """ Paint the Vertical weft color bar
        """
        offsetx,offsety = startpos
        grp = self.dwg.g(id='weft_colors')
        
        endwidth = offsetx + 1
        if self.style.weft_tick_active:
            endwidth += self.style.tick_length
        startx = offsetx * self.pixels_per_square
        endx = startx + self.pixels_per_square
        
        endy = offsety * self.pixels_per_square # steps down along the weft
        previous = endy
        index = 0
        while index != len(self.draft.weft):
            thread = self.draft.weft[index]
            if thread.spacing:
                endy += thread.yarn_width
            else:
                endy += self.style.box_size
            grp.add(self.dwg.rect(insert=(startx, previous), size=(self.pixels_per_square, endy-previous),
                                  class_=thread.css_label))
            previous = endy
            index += 1
        #
        self.dwg.add(grp)
        endheight = endy/self.pixels_per_square
        return (endwidth, endheight)
  
    def paint_fill_marker(self, grp, box, dotcss, style, label=None, thread_col=None):
        startx, starty, endx, endy = box
        sizex = endx-startx
        sizey = endy-starty
        textclass = "thread_text_b"
        margin = 0

        if thread_col:
            # fill with thread color
            if thread_col.color.intensity < 0.5:
                textclass = "thread_text_w"
            grp.add(self.dwg.rect(insert=(startx, starty), size=(sizex, sizey),
                                    class_=thread_col.css_label))
            if thread_col.color.close(self.style.background):
                if style=='solid':# or style =='dot':
                    # yarn color is too close to background and so not visible
                    # so  if 'solid' override to draw 'dot' style instead
                    style = 'dot'
                    thread_col = None  
        
        # dot only ?
        if style == 'dot' and not thread_col:
            margin = floor(sizex*0.4) # dot is 40% of size of box
            grp.add(self.dwg.rect(insert=(startx + margin/2, starty + margin/2), size=(sizex - margin, sizey - margin),
                                  class_=dotcss))
        # solid only?
        elif style == 'solid' and not thread_col:
            grp.add(self.dwg.rect(insert=(startx, starty), size=(sizex, sizey),
                                  class_=dotcss))
        # has a label ?
        elif style == 'number' or style == 'XO':
            grp.add(self.dwg.text(label,
                                  insert=(startx+sizex/2, starty+sizey/2),
                                  class_=textclass))

    def paint_threading(self, startpos):
        num_threads = len(self.draft.warp)
        num_shafts = len(self.draft.shafts)
        bgcolor = None
        label = 'O' # default to rising shed
        if not self.draft.rising_shed:
            label = 'X'
        
        # position
        offsetx,offsety = startpos # upper left corner position
        endheight = len(self.draft.shafts) + offsety
        grp = self.dwg.g(id='threading')
        
        start_tick_y = offsety
        tick_length = self.style.tick_length
        if self.style.warp_tick_active or self.style.tieup_tick_active:
            start_warp_y = (start_tick_y + tick_length -1) * self.pixels_per_square
            endheight += tick_length
        else:
            start_warp_y = (start_tick_y -1)*self.pixels_per_square
        
        distance = offsetx * self.pixels_per_square
        previous = distance
        t_index = len(self.draft.warp)-1 # count this down and use where we see ii
        while t_index != -1:
            thread = self.draft.warp[t_index]
            if thread.spacing:
                distance += thread.yarn_width
            else:
                distance += self.style.box_size
            startx = previous
            endx = distance
            
            if self.style.warp_use_thread_color:
                bgcolor = thread

            for jj, shaft in enumerate(self.draft.shafts):
                starty = (start_warp_y + (num_shafts - jj)* self.pixels_per_square)
                endy = starty + self.pixels_per_square
                # draw thw enclosing box
                grp.add(self.dwg.rect(insert=(startx, starty), size=(endx-startx, endy-starty),
                                      class_="box"))

                if shaft == thread.shaft:
                    # draw threading marker
                    if self.style.warp_style == 'number':
                        label = str(jj+1)
                    self.paint_fill_marker(grp, (startx, starty, endx, endy), "css_boxfill_color", self.style.warp_style, label, bgcolor)

            # horizontal tick, number if it's a multiple of tick_mod and not the first one
            if self.style.warp_tick_active:
                thread_no = t_index + 1
                if ((thread_no != num_threads) and
                    (thread_no != 0) and
                        (thread_no % self.style.tick_mod == 0)):
                    # draw line
                    tstarty = start_tick_y * self.pixels_per_square
                    tendy = (start_tick_y + tick_length) * self.pixels_per_square
                    grp.add(self.dwg.line((startx, tstarty), (startx, tendy),
                                          class_="ticks"))
                    if self.style.show_ticktext:
                        # draw text
                        grp.add(self.dwg.text(str(thread_no),
                                              insert=(startx + 2, tstarty + self.tick_font_size*0.8),
                                              class_="ticks_text"))
            previous = distance
            t_index -= 1
        #
        self.dwg.add(grp)
        endwidth = distance/self.pixels_per_square
        return (endwidth, endheight)

    def paint_liftplan(self, startpos):
        num_threads = len(self.draft.weft)
        bgcolor = None
        label = 'O' # default to rising shaft
        if not self.draft.rising_shed:
            label = 'X'
        grp = self.dwg.g(id='liftplan')
        
        offsetx,offsety = startpos
        endwidth = len(self.draft.shafts) + offsetx
        if self.style.weft_tick_active:
            endwidth += self.style.tick_length
        
        endy = offsety * self.pixels_per_square # steps down along the weft
        previous = endy
        index = 0
        while index != len(self.draft.weft):
            thread = self.draft.weft[index]
            if thread.spacing:
                endy += thread.yarn_width
            else:
                endy += self.style.box_size
            
            for jj, shaft in enumerate(self.draft.shafts):
                startx = (jj + offsetx) * self.pixels_per_square
                endx = startx + self.pixels_per_square
                grp.add(self.dwg.rect(insert=(startx, previous), size=(self.pixels_per_square, endy-previous),
                                      class_="box"))

                if shaft in thread.connected_shafts:
                    # draw liftplan marker
                    if self.style.weft_use_thread_color:
                        bgcolor = thread
                    if self.style.weft_style == 'number':
                        label = str(jj+1)
                    self.paint_fill_marker(grp, (startx, previous, endx, endy), "css_boxfill_color", self.style.weft_style, label, bgcolor)

            # vertical tick, number if it's a multiple of tick_mod and not the first one
            if self.style.weft_tick_active:
                thread_no = index+1 #ii + 1
                if ((thread_no != num_threads) and
                    (thread_no != 0) and
                        (thread_no % self.style.tick_mod == 0)):
                    # draw line
                    tick_endx = endx + (self.style.tick_length * self.pixels_per_square)
                    grp.add(self.dwg.line((endx, endy), (tick_endx, endy),
                                           class_="ticks"))
                    # draw text
                    grp.add(self.dwg.text(str(thread_no),
                                          insert=(endx + self.tick_font_size/4, endy-self.tick_font_size/8),
                                          class_="ticks_text"))
            #
            previous = endy
            index += 1
        #
        self.dwg.add(grp)
        endheight = endy/self.pixels_per_square
        return (endwidth, endheight) 

    def paint_tieup(self, startpos):
        offsetx,offsety = startpos
        label = 'O' # default to rising shaft
        if not self.draft.rising_shed:
            label = 'X'
        grp = self.dwg.g(id='tieup')
        
        tick_length = self.style.tick_length
        end_tick = offsety + tick_length
        start_tieup_y = offsety - 1
        if self.style.warp_tick_active or self.style.tieup_tick_active:
            start_tieup_y += tick_length
        endwidth = len(self.draft.treadles) + offsetx
        endheight = len(self.draft.shafts) + offsety
        
        num_treadles = len(self.draft.treadles)
        num_shafts = len(self.draft.shafts)

        for ii, treadle in enumerate(self.draft.treadles):
            startx = (ii + offsetx) * self.pixels_per_square
            endx = startx + self.pixels_per_square

            treadle_no = ii + 1

            for jj, shaft in enumerate(self.draft.shafts):
                starty = (num_shafts - jj + start_tieup_y) * self.pixels_per_square
                endy = starty + self.pixels_per_square

                grp.add(self.dwg.rect(insert=(startx, starty), size=(self.pixels_per_square,self.pixels_per_square),#startx-endx, starty-endy),
                                      class_="box"))

                if shaft in treadle.shafts:
                    if self.style.tieup_style == 'number':
                        label = str(jj+1)
                    self.paint_fill_marker(grp, (startx, starty, endx, endy), "css_boxfill_color", self.style.tieup_style, label, None)

                # vertical tick, number if it's a multiple of tick_mod and not the first one
                if self.style.tieup_tick_active:
                    if treadle_no == num_treadles:
                        shaft_no = jj + 1
                        if (shaft_no != 0) and (shaft_no % self.style.tick_mod == 0):
                            # draw line
                            line_startx = endx
                            line_endx = line_startx + (self.style.tick_length * self.pixels_per_square)
                            line_starty = line_endy = starty
                            grp.add(self.dwg.line((line_startx, line_starty), (line_endx, line_endy),
                                                  class_="ticks"))
                            if self.style.show_ticktext:
                                # draw text
                                grp.add(self.dwg.text(str(shaft_no),
                                                      insert=(line_startx + self.pixels_per_square/5, line_starty+self.pixels_per_square),
                                                      class_="ticks_text"))
            
            # horizontal ticks, number if it's a multiple of tick_mod and not the first one
            if self.style.tieup_tick_active:
                if (treadle_no != 0) and (treadle_no % self.style.tick_mod == 0):
                    # draw line
                    startx = endx = (treadle_no + offsetx) * self.pixels_per_square
                    starty = offsety * self.pixels_per_square
                    endy = (end_tick * self.pixels_per_square) - 1
                    grp.add(self.dwg.line((startx, starty), (endx, endy),
                                          class_="ticks"))
                    if self.style.show_ticktext:
                        grp.add(self.dwg.text(str(treadle_no),
                                              insert=(startx-self.pixels_per_square/5, starty + self.pixels_per_square),
    
                                              class_="ticks_text_r"))
        #
        self.dwg.add(grp)
        return (endwidth, endheight)

    def paint_treadling(self, startpos):
        """
        """
        num_threads = len(self.draft.weft)
        bgcolor = None
        label = 'O' # default to rising shed
        if not self.draft.rising_shed:
            label = 'X'
        grp = self.dwg.g(id='treadling')
        
        offsetx, offsety = startpos
        endwidth = len(self.draft.treadles) + offsetx
        if self.style.weft_tick_active:
            endwidth += self.style.tick_length
        
        endy = offsety * self.pixels_per_square # steps down along the weft
        previous = endy
        index = 0
        while index != len(self.draft.weft):
            thread = self.draft.weft[index]
            endy += thread.yarn_width
            if self.style.weft_use_thread_color:
                bgcolor = thread

            for jj, treadle in enumerate(self.draft.treadles):
                startx = (jj + offsetx) * self.pixels_per_square
                endx = startx + self.pixels_per_square
                grp.add(self.dwg.rect(insert=(startx, previous), size=(self.pixels_per_square, endy-previous),
                                       class_="box"))

                if treadle in thread.treadles:
                    # draw treadling marker
                    if self.style.weft_style == 'number':
                        label = str(jj+1)
                    self.paint_fill_marker(grp, (startx, previous, endx, endy), "css_boxfill_color", self.style.weft_style, label, bgcolor)
            
            # vertical tick, number if it's a multiple of tick_mod and not the first one
            if self.style.weft_tick_active:
                # ii = index
                thread_no = index + 1
                if ((thread_no != num_threads) and
                    (thread_no != 0) and
                        (thread_no % self.style.tick_mod == 0)):
                    # draw line
                    tick_endx = endx + (self.style.tick_length * self.pixels_per_square)
                    grp.add(self.dwg.line((endx, endy), (tick_endx, endy),
                                          class_="ticks"))
                    if self.style.show_ticktext:
                        # draw text
                        grp.add(self.dwg.text(str(thread_no),
                                              insert=(endx + self.tick_font_size/4, endy-self.tick_font_size/8),
                                              class_="ticks_text"))
            #
            previous = endy
            index += 1
        #
        self.dwg.add(grp)
        endheight = endy/self.pixels_per_square
        return (endwidth, endheight)

    def paint_drawdown(self, startpos, front=True, asfabric=False):
        """ Draw different styles of drawodown
            - solid, box, interlace - also shaded variants
            - asfabric will use solid and hide overlapping wefts
        """
        floats = self.draft.computed_floats
        float_cutoff = self.style.floats_count
        show_float = self.style.show_floats
        
        offsetx,offsety = startpos
        offsetx *= self.pixels_per_square
        offsety *= self.pixels_per_square
        
        grp = self.dwg.g(id='drawdown')
        
        # shading prep
        indent = self.style.interlace_width # how much indent in the interlace style
        hash = 0
        hashes = []
                               
        # shading offset - used when drawing the shadow and highlight thread features
        so = self.style.vector_shading_width
        vstroke = self.style.box_vec_stroke
        iw = self.style.interlace_width
        
        for start, end, visible, length, thread in floats:
            if visible==front: # visible is front of fabric. If front is false - show back of fabric
                realpos = self.draft.get_position(thread, start, end, self.pixels_per_square, True) #! True also front or !front
                (startx,starty), (endx,endy) = realpos
                startx += offsetx
                starty += offsety
                endx += offsetx
                endy += offsety
                
                # Calculate hashing number for unique yarn symbol
                # warp=+1, weft=+0, real_length*10, color/spacing hash*1000, visible = *-1
                if isinstance(thread, WarpThread):
                    hash = 1
                    hash += (endy-starty) * 10
                else: # weft
                    hash = 0
                    hash += (endx-startx) * 10
                hash += thread.css_hash * 1000
                if visible !=front: hash *= -1
                hashid = "th%d"%(hash)
                defsgrp = self.dwg.g(id=hashid) # structure each under a group
                
                # setup css_style (thread color)
                if self.show_structure:
                    # Use warp=black, weft=white
                    if isinstance(thread, WarpThread):
                        css_style = "css_boxblack"
                    else: 
                        css_style = "css_boxwhite"
                else: # use the thread colors
                    css_style = thread.css_label # thread color
                # highlight the long floats
                if show_float and length >= float_cutoff:
                    css_style = "floats"
                highcol = css_style+"high"
                highcol2 = css_style+"high2"
                shadcol = css_style+"shad"
                shadcol2 = css_style+"shad2"
                
                # The drawdown box styles
                if 'solid' in self.style.drawdown_style:
                    # remove stroke from class by using 'flat' version
                    if hashid not in hashes:
                        hashes.append(hashid)
                        defsgrp.add(self.dwg.rect(insert=(0, 0), size=(endx-1-startx, endy-1-starty),
                                                  class_=css_style+"flat"))
                        if  'shade' in self.style.drawdown_style:
                            # darker thin, lighter thick, natural, darker thick
                            defsgrp.add(self.dwg.line((0, 0), (endx-startx-so/2, 0), # top shadow
                                        class_=shadcol2))
                            defsgrp.add(self.dwg.line((0, so/2), (endx-startx-so/2, so/2), # top highlight
                                        class_=highcol))
                            defsgrp.add(self.dwg.line((0, 0), (0, endy-starty-so/2), # left shadow
                                        class_=shadcol2))
                            defsgrp.add(self.dwg.line((so/2, 0), (so/2, endy-starty-so/2), # left highlight
                                        class_=highcol))
                            defsgrp.add(self.dwg.line((0, endy-starty-so/2), (endx-startx-so/2, endy-starty-so/2), # bot shadow
                                        class_=shadcol))
                            defsgrp.add(self.dwg.line((endx-startx-so/2, 0), (endx-startx-so/2, endy-starty-so), # right shadow
                                        class_=shadcol))
                        self.dwg.defs.add(defsgrp)
                    grp.add(self.dwg.use(href="#"+hashid, insert=(startx, starty)))
                                          
                elif 'box' in self.style.drawdown_style:
                    if hashid not in hashes:
                        hashes.append(hashid)
                        defsgrp.add(self.dwg.rect(insert=(0, 0), size=(endx-startx, endy-starty),
                                              class_=css_style))
                        if  'shade' in self.style.drawdown_style:
                            # darker thin, lighter thick, natural, darker thick
                            defsgrp.add(self.dwg.line((vstroke, vstroke), (endx-startx-vstroke, vstroke), # top shadow
                                        class_=shadcol2))
                            defsgrp.add(self.dwg.line((vstroke, vstroke+so/2), (endx-startx-vstroke, vstroke+so/2), # top highlight
                                        class_=highcol))
                            defsgrp.add(self.dwg.line((vstroke, vstroke), (vstroke, endy-starty-vstroke), # left shadow
                                        class_=shadcol2))
                            defsgrp.add(self.dwg.line((vstroke+so/2, vstroke), (vstroke+so/2,  endy-starty-vstroke), # left highlight
                                        class_=highcol))
                            defsgrp.add(self.dwg.line((vstroke, endy-starty-vstroke-so/4), (endx-startx-vstroke, endy-starty-vstroke-so/4), # bot shadow
                                        class_=shadcol))
                            defsgrp.add(self.dwg.line((endx-startx-vstroke-so/4, vstroke), (endx-startx-vstroke-so/4, endy-starty-vstroke), # right shadow
                                        class_=shadcol))
                        self.dwg.defs.add(defsgrp)
                    grp.add(self.dwg.use(href="#"+hashid, insert=(startx, starty)))
                                          
                elif 'interlace' in self.style.drawdown_style:
                    if isinstance(thread, WarpThread):
                        boxx1 = startx + indent
                        boxx2 = endx - indent
                        boxy1 = starty - indent
                        boxy2 = endy + indent
                    else:
                        boxy1 = starty + indent
                        boxy2 = endy - indent
                        boxx1 = startx - indent
                        boxx2 = endx + indent
                    #
                    if hashid not in hashes:
                        hashes.append(hashid)
                        defsgrp.add(self.dwg.rect(insert=(0, 0), size=(boxx2-boxx1, boxy2-boxy1),
                                    class_=css_style))
                        defsgrp.add(self.dwg.line((0, 0), (boxx2-boxx1, 0),
                                    class_="indents"))
                        defsgrp.add(self.dwg.line((0, 0), (0, boxy2-boxy1),
                                    class_="indents"))
                        defsgrp.add(self.dwg.line((boxx2-boxx1, 0), (boxx2-boxx1, boxy2-boxy1),
                                    class_="indents"))
                        defsgrp.add(self.dwg.line((0, boxy2-boxy1), (boxx2-boxx1, boxy2-boxy1),
                                    class_="indents"))
                        if  'shade' in self.style.drawdown_style:
                            # darker thin, lighter thick, natural, darker thick
                            defsgrp.add(self.dwg.line((iw, iw), (boxx2-boxx1-iw, iw), # top shadow
                                        class_=shadcol2))
                            defsgrp.add(self.dwg.line((iw+so/2, iw+so), (boxx2-boxx1-iw, iw+so), # top highlight
                                        class_=highcol))
                            defsgrp.add(self.dwg.line((iw+so/4, iw), (iw+so/4, boxy2-boxy1-iw), # left shadow
                                        class_=shadcol2))
                            defsgrp.add(self.dwg.line((iw+so, iw+so/2), (iw+so, boxy2-boxy1-iw), # left highlight
                                        class_=highcol))
                            defsgrp.add(self.dwg.line((iw, boxy2-boxy1-iw-so/2), (boxx2-boxx1-iw, boxy2-boxy1-iw-so/2), # bot shadow
                                        class_=shadcol))
                            defsgrp.add(self.dwg.line((boxx2-boxx1-iw-so/2, iw), (boxx2-boxx1-iw-so/2, boxy2-boxy1-iw), # right shadow
                                        class_=shadcol))
                        self.dwg.defs.add(defsgrp)
                    grp.add(self.dwg.use(href="#"+hashid, insert=(boxx1, boxy1)))
                    
        #
        print("Out of",len(self.draft.warp)*len(self.draft.weft),"blocks in Drawdown, there are",len(hashes), "unique thread representations.")
        self.dwg.add(grp)
        endwidth = endx/self.pixels_per_square
        endheight = endy/self.pixels_per_square
        return (endwidth, endheight)


    def save(self, filename):
        s = self.make_svg_doc(filename)
        with open(filename, 'w') as f:
            s.write(f, pretty=True, indent=2)
