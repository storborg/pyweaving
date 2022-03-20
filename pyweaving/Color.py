#!/usr/python

# Color support


from math import floor


class Color(object):
    """
    A color type. Internally stored as RGB, and does not support transparency.
     - Accepts Color, rgb triplet or #RRGGBB strings.
     - If shadeable True then check to see if highlight and shadow can be visually seen in drawdown
       if not the calculate new as_drawn color.
     - Accessors are: self.rgb, self.css, self.hex, self.hsl,
     - Renderer will use self.as_drawn, self.highlight, self.shadow

    Args:
        rgb_or_hex (Color, tuple, str): Color, or RGB tuple, or hex string
        shadeable (bool, optional):  If True then possibly recalc as_drawn color so highlights,shadows can be seen
        Defaults to False. Used in rendering.

    Note:
        Will change Black or White primary colors slightly so highlight/shadow colors are visibly different.
    """
    def __init__(self, rgb_or_hex="#000000", shadeable=False):
        self.shadeable = shadeable
        # initialise self.rgb
        if isinstance(rgb_or_hex, type("")) and rgb_or_hex[0] == '#' and len(rgb_or_hex) == 7:
            # self.hex(rgb_or_hex) # we are in __init__ so will not work
            self.hex = rgb_or_hex
        elif isinstance(rgb_or_hex, type(self)):
            self.rgb = rgb_or_hex.rgb
        elif not isinstance(rgb_or_hex, tuple):
            self.rgb = tuple(rgb_or_hex)
        else:
            self.rgb = rgb_or_hex
        # as_drawn may be adjusted to show shading
        # - used by renderer in drawdown,weft,warp
        self.as_drawn = self.rgb
        # initialise self.hsl
        self.hsl = self.rgb2hsl(self.rgb)
        # initialise self.highlight, self.shadow
        self.highlight = self.create_highlight(self.rgb)
        self.shadow = self.create_shadow(self.rgb)
        # Check if as_drawn needs to be changed
        if self.shadeable:
            self.check_self_shadeable()

    def __str__(self):
        return str(self.rgb)

    def __repr__(self):
        return "<Color: %s>" % (self.rgb)

    def __eq__(self, other):
        return self.rgb == other.rgb

    def __ne__(self, other):
        return self.rgb != other.rgb

    def close(self, other, distance=60):
        """
        True if two colors are close to each other usng RGB distance.

        Args:
            other (Color): Compare to this Color.
            distance (int, optional): True if the distance between RGB colors is less than this.
        Returns:
            bool:

        Note:
            Using an overly simplistic rgb test - would be better in a different
            color space (IHS) but close enough for our use.
        """
        return abs(sum(self.rgb) - sum(other.rgb)) < distance

    def rgb2hsl(self, rgb):
        """
        Convert the RGB value into a HSL
        """
        r, g, b = [i / 255 for i in rgb]
        maxc = max(r, g, b)
        minc = min(r, g, b)
        ll = (maxc + minc) / 2
        if(maxc == minc):
            h = s = 0  # achromatic
        else:
            d = maxc - minc
            if ll > 0.5:
                s = d / (2 - maxc - minc)
            else:
                s = d / (maxc + minc)
            if maxc == r:
                if g < b:
                    h = (g - b) / d + 6
                else:
                    h = (g - b) / d
            elif maxc == g:
                h = (b - r) / d + 2
            else:  # maxc == b
                h = (r - g) / d + 4
            h /= 6
        return (h, s, ll)

    def _hue2rgb(self, p, q, t):
        if t < 0:
            t += 1
        if t > 1:
            t -= 1
        if t < 1 / 6:
            return p + (q - p) * 6 * t
        if t < 1 / 2:
            return q
        if t < 2 / 3:
            return p + (q - p) * (2 / 3 - t) * 6
        return p

    def hsl2rgb(self, h, s, ll):
        """
        Convert supplied HSL values into an RGB triplet

        Args:
            h (float): Hue
            s (float): Saturation
            l (float): Lightness

        Returns:
            RGB tuple:
        """
        if s == 0:
            r = g = b = ll  # achromatic
        else:
            if ll < 0.5:
                q = ll * (1 + s)
            else:
                q = ll + s - ll * s
            p = 2 * ll - q
            r = self._hue2rgb(p, q, h + 1 / 3)
            g = self._hue2rgb(p, q, h)
            b = self._hue2rgb(p, q, h - 1 / 3)
        return (min(floor(r * 256), 255),
                min(floor(g * 256), 255),
                min(floor(b * 256), 255))

    def create_highlight(self, rgb, factor=1.4):
        """
        Make a new color that is slightly brighter.

        Args:
            factor (float, optional): factor to make it brighter by.
        """
        h, s, ll = self.rgb2hsl(rgb)
        lighter = min(ll * factor, 1.0)
        return self.hsl2rgb(h, s, lighter)

    def create_shadow(self, rgb, factor=0.8):
        """
        Make a new color that is slightly dimmer.

        Args:
            factor (float, optional): factor to make it dimmer by.
        """
        h, s, ll = self.rgb2hsl(rgb)
        darker = ll * factor
        return self.hsl2rgb(h, s, darker)

    def check_self_shadeable(self):
        """
        If Color is White then can't see shading color as also White. So make original Color dimmer.

         - Save as_drawn
         - Likewise for Black but brighter.
        """
        if self.highlight == self.rgb:
            # can't see highlight so replace as_drawn colour with darker
            self.as_drawn = self.create_shadow(self.rgb, 0.93)
            self.highlight = (255, 255, 255)
        if self.shadow == self.rgb:
            # can't see shadow so replace as_drawn colour with brighter
            self.as_drawn = self.create_highlight(self.rgb, 1.1)
            self.shadow = (0, 0, 0)

    @property
    def css(self):
        """
        str: Present RGB as css styling

        Examples:
            >>> print(Color(0,128,255).css
            rgb(0,128,255)
        """
        return 'rgb(%d, %d, %d)' % self.rgb

    @property
    def hex(self):
        """
        str: Present RGB as hex styling

        Examples:
            >>> print(Color(0,128,255).hex
            #007FFF
        """
        return '#%02x%02x%02x' % self.rgb

    @property
    def intensity(self):
        """
        float: Perceived intensity calc. Range 0 to 1

        Examples:
            >>> print(Color(0,128,255).intensity
            0.40865
        """
        return (0.299 * self.rgb[0] / 255 +
                0.587 * self.rgb[1] / 255 +
                0.114 * self.rgb[2] / 255)

    # save a hex into rgb tuple
    @hex.setter
    def hex(self, hexstring):
        h = hexstring.lstrip('#')
        self.rgb = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
        self.hsl = self.rgb2hsl(self.rgb)
        self.highlight = self.create_highlight(self.rgb)
        self.shadow = self.create_shadow(self.rgb)
        if self.shadeable:
            self.check_self_shadeable()


WHITE = Color((255, 255, 255))
"""Color: Predefined White"""

BLACK = Color((0, 0, 0))
"""Color: Predefined Black"""

MID = Color((120, 120, 120))
"""Color: Predefined Mid Gray"""
