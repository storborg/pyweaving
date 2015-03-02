from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from unittest import TestCase

from .. import Color
from ..generators import twill, dither


class TestGenerators(TestCase):
    def test_plain_twill(self):
        draft = twill.twill(2)
        self.assertEqual(len(draft.shafts), 4)

    def test_dithered_gradient(self):
        start = Color((0, 0, 0))
        end = Color((255, 255, 255))
        colors = dither.dithered_gradient(start, end, 10)
        self.assertEqual(len(colors), 10)
