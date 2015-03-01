from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from unittest import TestCase

from .. import Draft, Color


class TestDraft(TestCase):
    def test_basic_tabby(self):
        draft = Draft(num_shafts=2, num_treadles=2)
        black = Color((0, 0, 0))
        draft.add_warp_thread(
            color=black,
            shaft=0,
        )
        draft.add_warp_thread(
            color=black,
            shaft=1,
        )
        draft.add_weft_thread(
            color=black,
            shafts=[0],
        )
        draft.add_weft_thread(
            color=black,
            shafts=[1],
        )
