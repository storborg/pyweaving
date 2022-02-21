#!/usr/python

### Color support

from math import floor

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
