#!/usr/python

# Color support


from math import floor, cos, sin, pi, sqrt, atan2  # last 5 for okhsl support


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
        # initialise okhsl
        self.okhsl = self.rgb2okhsl(self.rgb)
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
            RGB tuple: [0..255]ea
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

    def rgb2okhsl(self, rgb):
        """
        Convert the RGB value into a OKHSL
        """
        okhsl = srgb_to_okhsl(rgb)
        okhsl[0] /= 360.0
        return okhsl

    def okhsl2rgb(self, h, s, ll):
        """
        """
        srgb = okhsl_to_srgb([h, s, ll])
        return (srgb[0], srgb[1], srgb[2])

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
        self.okhsl = self.rgb2okhsl(self.rgb)
        self.highlight = self.create_highlight(self.rgb)
        self.shadow = self.create_shadow(self.rgb)
        if self.shadeable:
            self.check_self_shadeable()

# ----------------------------------------------
# srgb_to_okhsl, rgb = okhsl_to_srgb
# derived from Björn Ottosson
# - https://bottosson.github.io/posts/colorpicker/


def toe_inv(x):
    k_1, k_2 = 0.206, 0.03
    k_3 = (1 + k_1) / (1 + k_2)
    return (x * x + k_1 * x) / (k_3 * (x + k_2))


def srgb_transfer_function(a):
    return 12.92 * a if a < 0.0031308 else 1.055 * pow(a, 0.4166666666666667) - .055


def oklab_to_linear_srgb(Lab):
    L, a, b = Lab
    l_ = L + 0.3963377774 * a + 0.2158037573 * b
    m_ = L - 0.1055613458 * a - 0.0638541728 * b
    s_ = L - 0.0894841775 * a - 1.2914855480 * b
    #
    lum = l_ * l_ * l_
    m = m_ * m_ * m_
    s = s_ * s_ * s_

    return [4.0767416621 * lum - 3.3077115913 * m + 0.2309699292 * s,
            -1.2684380046 * lum + 2.6097574011 * m - 0.3413193965 * s,
            -0.0041960863 * lum - 0.7034186147 * m + 1.7076147010 * s]


def compute_max_saturation(a, b):
    """
    Finds the maximum saturation possible for a given hue that fits in sRGB
    Saturation here is defined as S = C/L
    a and b must be normalized so a^2 + b^2 == 1
    """
    # Max saturation will be when one of r, g or b goes below zero.
    # Select different coefficients depending on which component goes below zero first
    # float k0, k1, k2, k3, k4, wl, wm, ws;
    if -1.88170328 * a - 0.80936493 * b > 1:
        # Red component
        k0, k1, k2, k3, k4 = 1.19086277, 1.76576728, 0.59662641, 0.75515197, 0.56771245
        wl, wm, ws = 4.0767416621, -3.3077115913, 0.2309699292
    elif 1.81444104 * a - 1.19445276 * b > 1:
        # Green component
        k0, k1, k2, k3, k4 = 0.73956515, -0.45954404, 0.08285427, 0.12541070, 0.14503204
        wl, wm, ws = -1.2684380046, 2.6097574011, -0.3413193965
    else:
        # Blue component
        k0, k1, k2, k3, k4 = 1.35733652, -0.00915799, -1.15130210, -0.50559606, 0.00692167
        wl, wm, ws = -0.0041960863, -0.7034186147, 1.7076147010
    # Approximate max saturation using a polynomial:
    S = k0 + k1 * a + k2 * b + k3 * a * a + k4 * a * b

    # Do one step Halley's method to get closer
    # this gives an error less than 10e6, except for some blue hues where the dS/dh is close to infinite
    # this should be sufficient for most applications, otherwise do two/three steps
    k_l = 0.3963377774 * a + 0.2158037573 * b
    k_m = -0.1055613458 * a - 0.0638541728 * b
    k_s = -0.0894841775 * a - 1.2914855480 * b

    l_ = 1 + S * k_l
    m_ = 1 + S * k_m
    s_ = 1 + S * k_s

    lum = l_ * l_ * l_
    m = m_ * m_ * m_
    s = s_ * s_ * s_

    l_dS = 3 * k_l * l_ * l_
    m_dS = 3 * k_m * m_ * m_
    s_dS = 3 * k_s * s_ * s_

    l_dS2 = 6 * k_l * k_l * l_
    m_dS2 = 6 * k_m * k_m * m_
    s_dS2 = 6 * k_s * k_s * s_

    f = wl * lum + wm * m + ws * s
    f1 = wl * l_dS + wm * m_dS + ws * s_dS
    f2 = wl * l_dS2 + wm * m_dS2 + ws * s_dS2

    S = S - f * f1 / (f1 * f1 - 0.5 * f * f2)
    #
    return S


def find_cusp(a, b):
    """
    finds L_cusp and C_cusp for a given hue
    a and b must be normalized so a^2 + b^2 == 1
    """
    # First, find the maximum saturation (saturation S = C/L)
    S_cusp = compute_max_saturation(a, b)
    # Convert to linear sRGB to find the first point where at least one of r,g or b >= 1
    rgb_at_max = oklab_to_linear_srgb([1, S_cusp * a, S_cusp * b])
    L_cusp = pow(1 / max(max(rgb_at_max[0], rgb_at_max[1]), rgb_at_max[2]), 1 / 3)
    C_cusp = L_cusp * S_cusp
    #
    return [L_cusp , C_cusp]


def find_gamut_intersection(a, b, L1, C1, L0, cusp):
    """
    Finds intersection of the line defined by
    L = L0 * (1 - t) + t * L1;
    C = t * C1;
    a and b must be normalized so a^2 + b^2 == 1
    """
    # Find the intersection for upper and lower half seprately
    if ((L1 - L0) * cusp[1] - (cusp[0] - L0) * C1) <= 0 :
        # Lower half
        t = cusp[1] * L0 / (C1 * cusp[0] + cusp[1] * (L0 - L1))
    else:
        # Upper half
        # First intersect with triangle
        t = cusp[1] * (L0 - 1) / (C1 * (cusp[0] - 1) + cusp[1] * (L0 - L1))
        # Then one step Halley's method
        dL = L1 - L0
        dC = C1

        k_l = 0.3963377774 * a + 0.2158037573 * b
        k_m = -0.1055613458 * a - 0.0638541728 * b
        k_s = -0.0894841775 * a - 1.2914855480 * b

        l_dt = dL + dC * k_l
        m_dt = dL + dC * k_m
        s_dt = dL + dC * k_s

        # If higher accuracy is required, 2 or 3 iterations of the following block can be used:
        L = L0 * (1 - t) + t * L1
        C = t * C1

        l_ = L + C * k_l
        m_ = L + C * k_m
        s_ = L + C * k_s

        lum = l_ * l_ * l_
        m = m_ * m_ * m_
        s = s_ * s_ * s_

        ldt = 3 * l_dt * l_ * l_
        mdt = 3 * m_dt * m_ * m_
        sdt = 3 * s_dt * s_ * s_

        ldt2 = 6 * l_dt * l_dt * l_
        mdt2 = 6 * m_dt * m_dt * m_
        sdt2 = 6 * s_dt * s_dt * s_

        r = 4.0767416621 * lum - 3.3077115913 * m + 0.2309699292 * s - 1
        r1 = 4.0767416621 * ldt - 3.3077115913 * mdt + 0.2309699292 * sdt
        r2 = 4.0767416621 * ldt2 - 3.3077115913 * mdt2 + 0.2309699292 * sdt2

        u_r = r1 / (r1 * r1 - 0.5 * r * r2)
        t_r = -r * u_r

        g = -1.2684380046 * lum + 2.6097574011 * m - 0.3413193965 * s - 1
        g1 = -1.2684380046 * ldt + 2.6097574011 * mdt - 0.3413193965 * sdt
        g2 = -1.2684380046 * ldt2 + 2.6097574011 * mdt2 - 0.3413193965 * sdt2

        u_g = g1 / (g1 * g1 - 0.5 * g * g2)
        t_g = -g * u_g

        b = -0.0041960863 * lum - 0.7034186147 * m + 1.7076147010 * s - 1
        b1 = -0.0041960863 * ldt - 0.7034186147 * mdt + 1.7076147010 * sdt
        b2 = -0.0041960863 * ldt2 - 0.7034186147 * mdt2 + 1.7076147010 * sdt2

        u_b = b1 / (b1 * b1 - 0.5 * b * b2)
        t_b = -b * u_b

        FLT_MAX = 100000000
        t_r = t_r if u_r >= 0 else FLT_MAX
        t_g = t_g if u_g >= 0 else FLT_MAX
        t_b = t_b if u_b >= 0 else FLT_MAX
        t += min(t_r, min(t_g, t_b))
    #
    return t


def to_ST(cusp):
    L = cusp[0]
    C = cusp[1]
    return [C / L, C / (1 - L)]


def get_ST_mid(a, b):
    """
    Returns a smooth approximation of the location of the cusp
    This polynomial was created by an optimization process
    It has been designed so that S_mid < S_max and T_mid < T_max
    """
    S = 0.11516993 + 1 / (7.44778970 + 4.15901240 * b +
                          a * (-2.19557347 + 1.75198401 * b +
                               a * (-2.13704948 - 10.02301043 * b +
                                    a * (-4.24894561 + 5.38770819 * b + 4.69891013 * a))))
    T = 0.11239642 + 1 / (1.61320320 - 0.68124379 * b +
                          a * (0.40370612 + 0.90148123 * b +
                               a * (-0.27087943 + 0.61223990 * b +
                                    a * (0.00299215 - 0.45399568 * b - 0.14661872 * a))))
    return [S, T]


def get_Cs(L, a_, b_):
    cusp = find_cusp(a_, b_)
    C_max = find_gamut_intersection(a_, b_, L, 1, L, cusp)
    ST_max = to_ST(cusp)
    # Scale factor to compensate for the curved part of gamut shape
    k = C_max / min((L * ST_max[0]), (1 - L) * ST_max[1])
    ST_mid = get_ST_mid(a_, b_)
    # Use a soft minimum function, instead of a sharp triangle shape to get a smooth value for chroma.
    C_a = L * ST_mid[0]
    C_b = (1 - L) * ST_mid[1]
    C_mid = 0.9 * k * sqrt(sqrt(1 / (1 / (C_a * C_a * C_a * C_a) + 1 / (C_b * C_b * C_b * C_b))))
    # for C_0, the shape is independent of hue, so ST are constant. Values picked to roughly be the average values of ST.
    C_a = L * 0.4
    C_b = (1 - L) * 0.8
    # Use a soft minimum function, instead of a sharp triangle shape to get a smooth value for chroma.
    C_0 = sqrt(1 / (1 / (C_a * C_a) + 1 / (C_b * C_b)))
    #
    return [C_0, C_mid, C_max]


def okhsl_to_srgb(hsl):
    h, s, lum = hsl
    h /= 360
    if lum == 1.0:
        return [1, 1, 1]
    elif lum == 0.0:
        return [0, 0, 0]
    #
    a_ = cos(2 * pi * h)
    b_ = sin(2 * pi * h)
    L = toe_inv(lum)

    C_0, C_mid, C_max = get_Cs(L, a_, b_)

    mid = 0.8
    mid_inv = 1.25

    if s < mid:
        t = mid_inv * s
        k_1 = mid * C_0
        k_2 = (1 - k_1 / C_mid)
        C = t * k_1 / (1 - k_2 * t)
    else:
        t = (s - mid) / (1 - mid)
        k_0 = C_mid
        k_1 = (1 - mid) * C_mid * C_mid * mid_inv * mid_inv / C_0
        k_2 = (1 - (k_1) / (C_max - C_mid))
        C = k_0 + t * k_1 / (1 - k_2 * t)
    #
    rgb = oklab_to_linear_srgb([L, C * a_, C * b_])
    return [int(srgb_transfer_function(rgb[0]) * 255),
            int(srgb_transfer_function(rgb[1]) * 255),
            int(srgb_transfer_function(rgb[2]) * 255)]


# -----------------------------------------------------------------------

def toe(x):
    k_1, k_2 = 0.206, 0.03
    k_3 = (1 + k_1) / (1 + k_2)
    return 0.5 * (k_3 * x - k_1 + sqrt((k_3 * x - k_1) * (k_3 * x - k_1) + 4 * k_2 * k_3 * x))


def linear_srgb_to_oklab(c):
    r, g, b = c
    lum = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    l_ = pow(lum, 1 / 3)
    m_ = pow(m, 1 / 3)
    s_ = pow(s, 1 / 3)

    return [0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_,
            1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_,
            0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_]


def srgb_transfer_function_inv(a):
    return pow((a + .055) / 1.055, 2.4) if .04045 < a else a / 12.92


def srgb_to_okhsl(rgb):
    """
    """
    r, g, b = [v / 255 for v in rgb]
    if r == 0 and g == 0 and b == 0:  # div by zero, error avoidance...
        r = 0.0001
    lab = linear_srgb_to_oklab([srgb_transfer_function_inv(r),
                                srgb_transfer_function_inv(g),
                                srgb_transfer_function_inv(b)])
    C = sqrt(lab[1] * lab[1] + lab[2] * lab[2])
    a_ = lab[1] / C
    b_ = lab[2] / C
    #
    L = lab[0]
    h = 0.5 + 0.5 * atan2(-lab[2], -lab[1]) / pi

    C_0, C_mid, C_max = get_Cs(L, a_, b_)
    # Inverse of the interpolation in okhsl_to_srgb
    mid = 0.8
    mid_inv = 1.25
    #
    if C < C_mid:
        k_1 = mid * C_0
        k_2 = (1 - k_1 / C_mid)
        t = C / (k_1 + k_2 * C)
        s = t * mid
    else:
        k_0 = C_mid
        k_1 = (1 - mid) * C_mid * C_mid * mid_inv * mid_inv / C_0
        k_2 = (1 - (k_1) / (C_max - C_mid))

        t = (C - k_0) / (k_1 + k_2 * (C - k_0))
        s = mid + (1 - mid) * t
    #
    lum = toe(L)
    return [h * 360, s, lum]


WHITE = Color((255, 255, 255))
"""Color: Predefined White"""

BLACK = Color((0, 0, 0))
"""Color: Predefined Black"""

MID = Color((120, 120, 120))
"""Color: Predefined Mid Gray"""
