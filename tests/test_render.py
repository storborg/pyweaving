
from unittest import TestCase
from tempfile import NamedTemporaryFile
import sys, os, json

from pyweaving import Draft, Color, Drawstyle, Drawstyles, get_style
from pyweaving.render import ImageRenderer, SVGRenderer

        
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
        #
        draft.title = "Basic Draft"
        draft.draft_title = [draft.title]
        draft.process_draft()
        return draft

    def test_image_basic(self):
        draft = self.make_draft()
        with NamedTemporaryFile(suffix='.png', delete=False) as f:
            tempfname = f.name
            ImageRenderer(draft, get_style('Default')).save(tempfname)
        os.remove(tempfname)  # windows requires delete=False and manual cleanup to work

    def test_image_liftplan(self):
        draft = self.make_draft()
        with NamedTemporaryFile(suffix='.png', delete=False) as f:
            tempfname = f.name
            ImageRenderer(draft, get_style('Default'), show_liftplan=True).save(tempfname)
        os.remove(tempfname)  # windows requires delete=False and manual cleanup to work

    def test_svg_basic(self):
        draft = self.make_draft()
        with NamedTemporaryFile(suffix='.svg', delete=False) as f:
            tempfname = f.name
            SVGRenderer(draft, get_style('Default')).save(tempfname)
        os.remove(tempfname)  # windows requires delete=False and manual cleanup to work

    def test_svg_liftplan(self):
        draft = self.make_draft()
        with NamedTemporaryFile(suffix='.svg', delete=False) as f:
            tempfname = f.name
            SVGRenderer(draft, get_style('Default'), show_liftplan=True).save(tempfname)
        os.remove(tempfname)  # windows requires delete=False and manual cleanup to work
