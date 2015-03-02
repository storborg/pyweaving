from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from unittest import TestCase

from ..generators import twill, dither, raster, tartan


class TestGenerators(TestCase):
    def test_plain_twill(self):
        draft = twill.twill(2)
        self.assertEqual(len(draft.shafts), 4)
