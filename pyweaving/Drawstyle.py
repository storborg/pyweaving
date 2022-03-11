#!/usr/python

from copy import deepcopy
import json
from .Color import Color

# Styles support


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

    def __init__(self, name='Default',
                 derived_from=None,
                 layout='american',
                 hide=None,
                 show=None,
                 tick_style={'mod': 4, 'color': (200, 0, 0), 'length': 2, "showtext": True},
                 tieupstyle={'ticks': True, 'style': 'number'},
                 warpstyle={'ticks': True, 'usethread_color': True, 'style': 'number'},
                 weftstyle={'ticks': True, 'usethread_color': True, 'style': 'number'},
                 drawdown_style="box",
                 interlace_width=1,
                 vector_shading_width=1,
                 boxstyle={'size': 20, 'outline_color': (90, 90, 90), 'fill_color': (0, 0, 0), 'vector_width': 0.5},
                 floats_style={'show': False, 'count': 3, 'color': (200, 0, 0)},
                 spacing_style="clarity",
                 clarity_factor=0.8,
                 background=(240, 240, 240),
                 title_font_size_factor=1.5,
                 border_pixels=20,
                 warp_gap=1,
                 drawdown_gap=1,
                 weft_gap=1,
                 tick_gap=1
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
            return"<Drawstyle %s from: %s>" % (self.name, self.derived_from)
        else:
            return"<Drawstyle %s>" % (self.name)

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
            'name':          self.name,
            'derived_from':  self.derived_from,
            'layout':        self.layout,
            'tick_style':    self.tick_style,
            'tieupstyle':    self.tieupstyle,
            'warpstyle':     self.warpstyle,
            'weftstyle':     self.weftstyle,
            'drawdown_style':  self.drawdown_style,
            'interlace_width': self.interlace_width,
            'vector_shading_width':  self.vector_shading_width,
            'boxstyle':        self.boxstyle,
            'floats_style':    self.floats_style,
            'spacing_style':   self.spacing_style,
            'clarity_factor':  self.clarity_factor,
            'background':      self.background,
            'title_font_size_factor':  self.title_font_size_factor,
            'border_pixels':   self.border_pixels,
            'warp_gap':        self.warp_gap,
            'drawdown_gap':    self.drawdown_gap,
            'weft_gap':        self.weft_gap,
            'tick_gap':        self.tick_gap
           }, ensure_ascii=False)
