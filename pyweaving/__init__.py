from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import datetime
import json
from copy import deepcopy
from collections import defaultdict
from math import floor


__version__ = '0.0.8.dev'


# The bulk tartans description file is held in the generators code subdirectory.
#  - need a way to find the code directory
from pathlib import Path
def get_project_root():
    " return path to this file's parent directory on the machine "
    return Path(__file__).parent

class Color(object):
    """
    A color type. Internally stored as RGB, and does not support transparency.
    - can accept, Color(), rgb tuples, or #rrggbb string
    Generates a highlight and shadow variant for shading
    - will change B,W primary color to see this shading
    self.rgb, self.css, self.hex, self.hsl, self.highlight, self.shadow
    """
    def __init__(self, rgb_or_hex, shadeable=False):
        if  isinstance(rgb_or_hex,type("")) and rgb_or_hex[0] =='#' and len(rgb_or_hex)==7:
            self.hex(rgb_or_hex)
        elif  isinstance(rgb_or_hex,type(self)):
            self.rgb = rgb_or_hex.rgb
        elif not isinstance(rgb_or_hex, tuple):
            self.rgb = tuple(rgb_or_hex)
        else:
            self.rgb = rgb_or_hex
        self.rgb2hsl()
        self.create_highlight()
        self.create_shadow()
        self.shadeable = shadeable
        if self.shadeable:
            self.check_self_shadeable()
        

    def __repr__(self):
        return "<Color: %s>" %(str(self))
        
    def __eq__(self, other):
        return self.rgb == other.rgb

    def __ne__(self, other):
        return self.rgb != other.rgb
    
    def close(self, other):
        " rgb distance between two rgb colors "
        return abs(sum(self.rgb) - sum(other.rgb)) < 60
        
    def rgb2hsl(self):
        r,g,b = r,g,b = [i/255 for i in self.rgb]
        maxc = max(r, g, b)
        minc = min(r, g, b)
        l = (maxc + minc) / 2
        if(maxc == minc):
            h = s = 0 # achromatic
        else:
            d = maxc - minc
            if l > 0.5:
                s = d / (2 - maxc - minc)
            else:
                s = d / (maxc + minc)
            if maxc == r:
                if g<b:
                    h = (g - b) / d + 6
                else:
                    h = (g - b) / d 
            elif maxc == g:
                h = (b - r) / d + 2
            else: # maxc==b
                h = (r - g) / d + 4
            h /= 6
        self.hsl = (h, s, l)
        
    def _hue2rgb(self,p, q, t):
        if t < 0: t += 1
        if t > 1: t -= 1
        if t < 1/6: return p + (q - p) * 6 * t
        if t < 1/2: return q
        if t < 2/3: return p + (q - p) * (2/3 - t) * 6
        return p
        
    def hsl2rgb(self, h, s, l):
        if s == 0:
            r = g = b = l # achromatic
        else:
            if l < 0.5:
                q = l * (1 + s)
            else:
                q = l + s - l * s
            p = 2 * l - q
            r = self._hue2rgb(p, q, h + 1/3)
            g = self._hue2rgb(p, q, h)
            b = self._hue2rgb(p, q, h - 1/3)
        return (min(floor(r*256),255), min(floor(g*256),255), min(floor(b*256),255))
        
    def create_highlight(self, factor=1.4):
        h,s,l = self.hsl
        lighter = min(l*factor, 1.0)
        self.highlight = self.hsl2rgb(h,s,lighter)
        
    def create_shadow(self, factor=0.7):
        h,s,l = self.hsl
        darker = l*factor
        self.shadow = self.hsl2rgb(h,s,darker)
    
    def check_self_shadeable(self):
        """ if white then can;t see shading so make dimmer.
            Likewise for Black
        """
        if self.highlight == self.rgb:
            # can't see highlight so replace colour with darker
            self.create_shadow(0.92)
            self.replace(self.shadow)
            # self.replace((240,240,240))
        if self.shadow == self.rgb:
            # can't see shadow so replace colour with brighter
            self.replace((35,35,35))
    
    def replace(self, newcol):
        """ was white or black so change it so shading wil be visible """
        self.rgb = newcol
        self.rgb2hsl()
        self.create_highlight()
        self.create_shadow()
        
    @property
    def intensity(self):
        " Perceived intensity calc "
        return (0.299*self.rgb[0]/255 + 0.587*self.rgb[1]/255 + 0.114*self.rgb[2]/255)

    @property
    def css(self):
        return 'rgb(%d, %d, %d)' % self.rgb
    @property
    def hex(self):
        return '#%02x%02x%02x' % self.rgb
        
    # save a hex into rgb tuple
    @hex.setter
    def hex(self, hexstring):
        h = hexstring.lstrip('#')
        self.rgb = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
        self.rgb2hsl()
        self.create_highlight()
        self.create_shadow()
        if self.shadeable:
            self.check_self_shadeable()

    def __str__(self):
        return str(self.rgb)

WHITE = Color((255,255,255))
BLACK = Color((0,0,0))
MID   = Color((120,120,120))

class Drawstyle(object):
    """ Series of style flags for how to draw the Layout.
        - layout = [swedish | american]
        - hide = [drawdown,tieup,treadling,liftplan,warp,weft,warpcolor,weftcolor]
        - show = [stats, groupings, ]
        #
        - tieupstyle = [ticks, border, [solid|dot|number|XO] ]
        - drawdownstyle = [solid | box | interlace | boxshaded | solidshaded | interlaceshaded]
        - warpstyle,weftstyle = {ticks, usethread_color, [solid|dot|number|XO] }
        - boxstyle = {size:10, outline_color:(R,G,B), fill_color:(R,G,B)}
        - tick_style = [mod:4, color:(200, 0, 0)],
        - floats_style = { show, count, 'color':(R,G,B) }
        - spacing_style = [clarity, thinner]
        future:
          - row_length is howmany threads before a line break to spread down page
          - will need new formatting fields for showing grouped structures
    """
    
    def __init__(self, name = 'Default',
                 derived_from=None,
                 layout='american', hide=None, show=None,
                 tick_style={'mod':4, 'color':(200, 0, 0), 'length':2, "showtext":True},
                 tieupstyle={'ticks': True, 'style': 'number'},
                 warpstyle={'ticks':True, 'usethread_color':True, 'style': 'number'},
                 weftstyle={'ticks':True, 'usethread_color':True, 'style': 'number'},
                 drawdown_style="box",
                 interlace_width=1,
                 vector_shading_width=1,
                 boxstyle={'size':20, 'outline_color':(90, 90, 90), 'fill_color':(0,0,0),'vector_width':0.5},
                 floats_style={'show':False, 'count':3, 'color':(200,0,0)},
                 spacing_style="clarity",
                 clarity_factor=0.8,
                 background=(240, 240, 240),
                 title_font_size_factor = 1.5,
                 border_pixels = 20,
                 warp_gap = 1,
                 drawdown_gap = 1,
                 weft_gap = 1,
                 tick_gap = 1
                 ):
        # Color prep
        tick_style['color'] = Color(tick_style['color'])
        boxstyle['outline_color'] = Color(boxstyle['outline_color'])
        boxstyle['fill_color'] = Color(boxstyle['fill_color'])
        floats_style['color'] = Color(floats_style['color'])
        background = Color(background)
        #
        self.name = name
        self.derived_from = derived_from
        self.layout = layout
        self.tick_style = tick_style
        self.tieupstyle = tieupstyle
        self.warpstyle = warpstyle
        self.weftstyle = weftstyle
        self.drawdown_style = drawdown_style
        self.interlace_width = interlace_width
        self.vector_shading_width = vector_shading_width
        self.boxstyle = boxstyle
        self.floats_style = floats_style
        self.spacing_style = spacing_style
        self.clarity_factor = clarity_factor
        self.title_font_size_factor = title_font_size_factor
        self.background = background
        self.border_pixels = border_pixels
        self.warp_gap = warp_gap
        self.drawdown_gap = drawdown_gap
        self.tick_gap = tick_gap
        self.weft_gap = weft_gap
    
    def __repr__(self):
        if self.derived_from:
            return"<Drawstyle %s from: %s>"%(self.name, self.derived_from)
        else:
            return"<Drawstyle %s>"%(self.name)
    # ticks
    @property
    def tick_mod(self):
        return self.tick_style['mod']
    @property
    def show_ticktext(self):
        return self.tick_style['showtext']
    @property
    def tick_length(self):
        return self.tick_style['length']
    @property
    def tick_color_rgb(self):
        return self.tick_style['color'].rgb
    @property
    def tick_color_hex(self):
        return self.tick_style['color'].hex
    # tieups
    @property
    def tieup_tick_active(self):
        return self.tieupstyle['ticks']
    @property
    def tieup_style(self):
        return self.tieupstyle['style']
    # warps
    @property
    def warp_tick_active(self):
        return self.warpstyle['ticks']
    @property
    def warp_use_thread_color(self):
        return self.warpstyle['usethread_color']
    @property
    def warp_style(self):
        return self.warpstyle['style']
    # wefts 
    @property
    def weft_tick_active(self):
        return self.weftstyle['ticks']
    @property
    def weft_use_thread_color(self):
        return self.weftstyle['usethread_color']
    @property
    def weft_style(self):
        return self.weftstyle['style']        
    # boxstyle
    @property
    def box_size(self):
        return self.boxstyle['size']
    @property
    def outline_color(self):
        return self.boxstyle['outline_color']
    @property
    def boxfill_color(self):
        return self.boxstyle['fill_color']
    @property
    def box_vec_stroke(self):
        return self.boxstyle['vector_width']
    # floats
    @property
    def show_floats(self):
        return self.floats_style['show']
    @property
    def floats_count(self):
        return self.floats_style['count']
    @property
    def floats_color(self):
        return self.floats_style['color']
    def set_floats(self, count):
        self.floats_style['show'] = True
        self.floats_style['count'] = count
    # general setters
    def disable_tickmarks(self):
        self.tieupstyle['ticks'] = False
        self.warpstyle['ticks'] = False
        self.weftstyle['ticks'] = False
    def set_warp_weft_style(self, mode='solid'):
        self.warpstyle['style'] = mode
        self.weftstyle['style'] = mode
    def disable_thread_color(self):
        self.warpstyle['usethread_color'] = False
        self.weftstyle['usethread_color'] = False
    @property
    def copy(self):
        " Make a complete copy of this Drawstyle. "
        return deepcopy(self)
        
    # Loading and saving
    def to_json(self):
        """ Serialize a DrawStyle to its JSON representation.
            Counterpart to from_json()
        """
        self.tick_style['color'] = self.tick_style['color'].rgb
        self.boxstyle['outline_color'] = self.boxstyle['outline_color'].rgb
        self.boxstyle['fill_color'] = self.boxstyle['fill_color'].rgb
        self.floats_style['color'] = self.floats_style['color'].rgb
        self.background = self.background.rgb
        return json.dumps({
            'name'         : self.name,
            'derived_from' : self.derived_from,
            'layout'       : self.layout,
            'tick_style'   : self.tick_style,       #!
            'tieupstyle'   : self.tieupstyle,
            'warpstyle'    : self.warpstyle,
            'weftstyle'    : self.weftstyle,
            'drawdown_style' : self.drawdown_style,
            'interlace_width': self.interlace_width,
            'vector_shading_width'  : self.vector_shading_width,
            'boxstyle'       : self.boxstyle,      #!
            'floats_style'   : self.floats_style,  #!
            'spacing_style'  : self.spacing_style,
            'clarity_factor' : self.clarity_factor,
            'background'     : self.background,    #!
            'title_font_size_factor' : self.title_font_size_factor,
            'border_pixels'  : self.border_pixels,
            'warp_gap'       : self.warp_gap,
            'drawdown_gap'   : self.drawdown_gap,
            'weft_gap'       : self.weft_gap,
            'tick_gap'       : self.tick_gap
           }, ensure_ascii=False)

class WarpThread(object):
    """
    Represents a single warp thread.
    """
    def __init__(self, color=None, shaft=None, spacing=None):
        if color and not isinstance(color, Color):
            color = Color(color, True)
        self.color = color
        self.shaft = shaft
        self.spacing = spacing
        self.css_label = None # for SVG styles

    def __repr__(self):
        return '<WarpThread color:%s shaft:%s>' % (self.color.rgb, self.shaft)


class WeftThread(object):
    """
    Represents a single weft thread.
    """
    def __init__(self, color=None, shafts=None, treadles=None, spacing=None):
        if color and not isinstance(color, Color):
            color = Color(color, True)
        self.color = color
        self.treadles = treadles or set()
        self.shafts = shafts or set()
        self.spacing = spacing
        self.css_label = None # for SVG styles

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
    def __init__(self, index):
        self.index = index
        
    def __repr__(self):
        return '<Shaft %d>' % (self.index)


class Treadle(object):
    """
    Represents a single treadle of the loom.
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

        self.warp = [] # holds the WarpThreads
        self.weft = [] # holds the WeftThreads
         # unique yarn spacing,color stats from gather_metrics()
        self.thread_stats = {"weft":[],           # list of (colour,spacing,count)
                             "warp":[],           # list of (colour,spacing,count)
                             "warp_spacings":[],  # list of (spacing,count)
                             "weft_spacings":[],  # list of (spacing,count)
                             "summary":[],        # list of spacings
                             "warp_ratio":[],     # value of Warp/Weft balance
                             "unique_threads" :[],# number of unique threads used in draft
                             "selvedge_floats":[],# list of lengths of warp threads on sides
                            }
        
        # css labels for svg
        self.css_colors = []
        
        self.warp_units = warp_units
        self.weft_units = weft_units
        
        # Only used when saving -overwritten on load
        self.creation_date = datetime.datetime.now().strftime("%A, %B %d, %Y, %H:%M")#'%b %d, %Y')
        
        self.date = date
        self.title = title
        self.author = author
        self.address = address
        self.email = email
        self.telephone = telephone
        self.fax = fax
        self.notes = notes
        self.collected_notes = []
        self.draft_title = [] # multiple line of title from wif and filename
        
        self.source_program = None#"PyWeaving" #! set when saving
        self.source_version = None#__version__

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
            'warp_units':self.warp_units,
            'weft_units':self.weft_units,
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
        Make a complete copy of this draft.
        """
        return deepcopy(self)

    def add_warp_thread(self, color=None, index=None, shaft=0, spacing=None):
        """
        Add a warp thread to this draft.
        """
        if not isinstance(shaft, Shaft):
            shaft = self.shafts[shaft]
        thread = WarpThread(
            color=color,
            shaft=shaft,
            spacing=spacing,
        )
        if index is None:
            self.warp.append(thread)
        else:
            self.warp.insert(index, thread)

    def add_weft_thread(self, color=None, index=None,
                        shafts=None, treadles=None, spacing=None):
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
            spacing=spacing,
        )
        if index is None:
            self.weft.append(thread)
        else:
            self.weft.insert(index, thread)

    def assign_css_labels(self, threads, stats, suffix):
        """ assign css labels to unique threads in warp and weft independently.
            Used by SVG renderer
            called from process_draft()
        """
        # prep css labels
        labels = []
        for i,(c,s,_) in enumerate(stats):
            labels.append([c,s,i,"%scol%d"%(suffix,i)])
        # remember for svg hashing if required
        self.hash_colorkeys = labels
        # assign labels to threads
        for thread in threads:
            color = thread.color
            spacing = thread.spacing
            # find the right color/spacing match
            for c,s,i,name in labels:
                if c==color and s==spacing:
                    thread.css_label = name
                    # remember for svg hashing if required
                    thread.css_hash = i
                    break
        # remember name:color relationship for svg renderer
        self.css_colors.extend([[name,color] for color,_,_,name in labels])
        
    def _count_colour_spacings(self, threads):
        " threads are self.weft or self.warp -usedby gather_metrics"
        # extract weft color, spacing numbers
        stats = [] # pairs of (thread color, spacing)
        counter = []
        for thread in threads:
            t_data = (thread.color, thread.spacing)
            if t_data not in stats:
                stats.append(t_data)
                counter.append(1)
            else:
                index = stats.index(t_data)
                counter[index] += 1
        return [(c,s,i) for (c,s),i in zip(stats,counter)]
        
    def _count_spacings(self, thread_stats):
        " simplify thread_stats (c,s,i) to pairs of (spacing,count) -usedby gather_metrics"
        spacings = []
        counter = []
        for c,s,i in thread_stats:
            if s not in spacings:
                spacings.append(s)
                counter.append(i)
            else:
                index = spacings.index(s)
                counter[index] += i
        return list(zip(spacings, counter))
        
    def gather_metrics(self):
        """ loop through warp and weft threads gathering unique spacings and colors
            so we can show spacings in drawdowns and use in stats
            - also warp/weft balance
            - also list of unique threads from combined warp,weft
            - also warp floats on edges - do we need floating selvedges
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
        all_spacings = [ s for (s,i) in self.thread_stats["weft_spacings"] if s]
        for (s,i) in self.thread_stats["warp_spacings"]:
            if s and s not in all_spacings:
                all_spacings.append(s)
        self.thread_stats["summary"] = sorted(all_spacings)

        floats = self.computed_floats
        # Warp/WeftBalance
        warp_count = sum([length+1 for start, end, visible, length, thread in floats
                                   if visible==True and isinstance(thread, WarpThread)])
        weft_count = sum([length+1 for start, end, visible, length, thread in floats
                                   if visible==True and isinstance(thread, WeftThread)])
        self.thread_stats["warp_ratio"] =  warp_count/max(weft_count,1) #!!twill error if badly formed floaty wif
        
        # Unique threads
        unique_threads = [[t[0],t[1]] for t in self.thread_stats["warp"]]
        for col2,sp2,_ in self.thread_stats["weft"]:
            found = False
            for color,spacing in unique_threads:
                if col2 == color and sp2 == spacing:
                    found = True
                    break
            if not found:
                unique_threads.append((col2,sp2))
        self.thread_stats["unique_threads"] = unique_threads
        
        # Floating Selvedges required ?
        start,end = 0,len(self.warp)-1
        longest = [length for s, e, visible, length, thread in floats
                             if (s[0]==start or s[0]==end) and isinstance(thread, WarpThread)]
        self.thread_stats["selvedge_floats"] = longest

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

    def process_draft(self):
        " after reading do these processes to fill in some reporting datastructures "
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
            self.collected_notes.append("(source program: %s.  Version: %s)"%(self.source_program,self.source_version))
        if self.creation_date:
            self.collected_notes.append("(created on %s)"%(self.creation_date))
        
    def compute_floats(self):
        """
        Return an iterator over every float, yielding a tuple for each one::
            (start, end, visible, length, thread)
        FIXME: This ignores the back side of the fabric. Should it?
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
        "  -usedby compute_longest_floats "
        lengths = [length for start, end, visible, length, thread in floats
                            if visible==front and isinstance(thread, cls)]
        # remove any that are same as warp length. Probably gaps in a gamp...
        warp_len = len(self.warp)-1
        for i in range(lengths.count(warp_len)):
            lengths.remove(warp_len)
        return max(lengths)

    def compute_longest_floats(self, front=True, back=False):
        """ Return tuple containing pair of longest floats for warp, weft.
             on one or both sides
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
        """ Iterate over the threads calculating the proper position
            for any given float to be drawn in the drawdown
                - inefficient
                - should be stored on thread like yarn_width or in compute_floats #!
                 change compute_floats() to return this also
        """
        num_warp_threads = len(self.warp)
        # reversed for back of cloth
        begin = num_warp_threads
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
            for i in range(end[1]+1):
                w += self.weft[i].yarn_width
            endy = w
            # startx (step through the warps)
            w = 0
            for i in range(num_warp_threads-1, end[0], -1):
                w += self.warp[i].yarn_width
            startx = w
            # endx
            w = 0
            for i in range(num_warp_threads-1, start[0]-1, -1):
                w += self.warp[i].yarn_width
            endx = w

        else: # no spacing info so use pixels_per_square (boxsize)
            startx = (num_warp_threads - end[0]-1) * boxsize 
            starty = start[1] * boxsize
            endx = (num_warp_threads - start[0]) * boxsize
            endy = (end[1] + 1) * boxsize
        #
        result_start = (startx, starty)
        result_end   = (endx, endy)
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
        """ gather list of:
            - thread counts, longest floats, color count,
            - warp/weft ratio, floating selvedge status
            (gather_metric gets most of these)
        """
        # Threadcounts
        stats = ["Threadcounts: Warp %d  Weft %d"%(len(self.warp), len(self.weft))]
        unique_thread_count = len(self.thread_stats["unique_threads"])
        # Shaft and treadle counts
        shafts = "%d shafts."% len(self.shafts)
        if not self.liftplan:
            shafts += " %d treadles."%(len(self.treadles))
        stats.append(shafts)
        # Unique yarns
        stats.append("%d unique yarns (color/spacing)"%(unique_thread_count))
        # Longest Floats
        floats = self.compute_longest_floats(True, True)
        front, back = floats[:2], floats[2:]
        stats.append("Longest floats: (warp/back) %d/%d , (weft/back) %d/%d" % 
                    (front[0]+1, back[0]+1, front[1]+1, back[1]+1))
        # Warp/Weft ratio
        warp_ratio = self.thread_stats["warp_ratio"]
        if 0.8 < warp_ratio < 1.2:
            if warp_ratio == 1: # special case exact balanced weave
                stats.append("Balanced weave warp:weft = 1 : {:d}".format(int(warp_ratio)))
            else:
                stats.append("Balanced weave warp:weft = 1 : {:.1f}".format(warp_ratio))
        elif warp_ratio < 1:
            stats.append("Weft dominant weave 1 : {:.1f}".format(warp_ratio))
        else: # weft 
            stats.append("Warp dominant weave 1 : {:.1f}".format(1/warp_ratio))
        # Selvedges
        selvedge_floats = self.thread_stats["selvedge_floats"]
        if selvedge_floats and max(selvedge_floats) > 1:
            msg = "Floating Selvedges may be required. Longest edge warp float is: %d"%(max(selvedge_floats)+1)
        else: msg = "Floating Selvedges not required."
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
