from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from unittest import TestCase
from tempfile import NamedTemporaryFile

from .. import Draft, Color
from ..render import ImageRenderer, SVGRenderer


class TestRender(TestCase):

    def make_draft(self):
        draft = Draft(num_shafts=2, num_treadles=2)
        color = Color((200, 0, 0))
        draft.add_warp_thread(
            color=color,
            shaft=0,
        )
        draft.add_warp_thread(
            color=color,
            shaft=1,
        )
        draft.add_weft_thread(
            color=color,
            treadles=[0],
        )
        draft.add_weft_thread(
            color=color,
            treadles=[1],
        )
        draft.treadles[0].shafts = [draft.shafts[0]]
        draft.treadles[1].shafts = [draft.shafts[1]]
        return draft

    def test_image_basic(self):
        draft = self.make_draft()
        with NamedTemporaryFile(suffix='.png') as f:
            ImageRenderer(draft).save(f.name)

    def test_image_liftplan(self):
        draft = self.make_draft()
        with NamedTemporaryFile(suffix='.png') as f:
            ImageRenderer(draft, liftplan=True).save(f.name)

    def test_svg_basic(self):
        draft = self.make_draft()
        with NamedTemporaryFile() as f:
            SVGRenderer(draft).save(f.name)

    def test_svg_liftplan(self):
        draft = self.make_draft()
        with NamedTemporaryFile() as f:
            SVGRenderer(draft, liftplan=True).save(f.name)
