from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import sys
import argparse

from . import Draft, instructions
from .wif import WIFReader, WIFWriter
from .render import ImageRenderer, SVGRenderer


def load_draft(infile):
    if infile.endswith('.wif'):
        return WIFReader(infile).read()
    elif infile.endswith('.json'):
        with open(infile) as f:
            return Draft.from_json(f.read())
    else:
        raise ValueError(
            "filename %r unrecognized: .wif and .json are supported" %
            infile)


def render(opts):
    draft = load_draft(opts.infile)
    if opts.outfile:
        if opts.outfile.endswith('.svg'):
            SVGRenderer(draft).save(opts.outfile)
        else:
            ImageRenderer(draft).save(opts.outfile)
    else:
        ImageRenderer(draft).show()


def convert(opts):
    draft = load_draft(opts.infile)
    if opts.outfile.endswith('.wif'):
        WIFWriter(draft).write(opts.outfile)
    elif opts.outfile.endswith('.json'):
        with open(opts.outfile, 'w') as f:
            f.write(draft.to_json())


def thread(opts):
    draft = load_draft(opts.infile)
    instructions.threading(draft, opts.repeats)


def weave(opts):
    draft = load_draft(opts.infile)
    assert opts.liftplan, "only liftplan supported for now"
    save_filename = '.' + opts.infile + '.save'
    print("SAVE FILENAME is %r" % save_filename)
    instructions.weaving(draft,
                         repeats=opts.repeats,
                         start_repeat=opts.start_repeat,
                         start_pick=opts.start_pick,
                         save_filename=save_filename)


def tieup(opts):
    draft = load_draft(opts.infile)
    instructions.tieup(draft)


def stats(opts):
    draft = load_draft(opts.infile)
    warp_longest, weft_longest = draft.compute_longest_floats()
    print("Title:", draft.title)
    print("Author:", draft.author)
    print("Address:", draft.address)
    print("Email:", draft.email)
    print("Telephone:", draft.telephone)
    print("Fax:", draft.fax)
    print("Notes:", draft.notes)
    print("Date:", draft.date)
    print("***")
    print("Warp Threads:", len(draft.warp))
    print("Weft Threads:", len(draft.weft))
    print("Shafts:", len(draft.shafts))
    print("Treadles:", len(draft.treadles))
    print("Longest Float (Warp):", warp_longest)
    print("Longest Float (Weft):", weft_longest)


def main(argv=sys.argv):
    p = argparse.ArgumentParser(description='Weaving utilities.')

    subparsers = p.add_subparsers(help='sub-command help')

    p_render = subparsers.add_parser(
        'render', help='Render a draft.')
    p_render.add_argument('infile')
    p_render.add_argument('outfile', nargs='?')
    p_render.add_argument('--liftplan', action='store_true')
    p_render.set_defaults(function=render)

    p_convert = subparsers.add_parser(
        'convert',
        help='Convert between draft file types.')
    p_convert.add_argument('infile')
    p_convert.add_argument('outfile')
    p_convert.add_argument('--liftplan', action='store_true')
    p_convert.set_defaults(function=convert)

    p_thread = subparsers.add_parser(
        'thread',
        help='Show threading instructions for a draft.')
    p_thread.add_argument('infile')
    p_thread.add_argument('--repeats', type=int, default=1)
    p_thread.set_defaults(function=thread)

    p_weave = subparsers.add_parser(
        'weave',
        help='Show weaving instructions for a draft.')
    p_weave.add_argument('infile')
    p_weave.add_argument('--liftplan', action='store_true')
    p_weave.add_argument('--repeats', type=int, default=1)
    p_weave.add_argument('--start-repeat', type=int, default=1)
    p_weave.add_argument('--start-pick', type=int, default=1)
    p_weave.set_defaults(function=weave)

    p_tieup = subparsers.add_parser(
        'tieup',
        help='Show tie-up instructions for a draft.')
    p_tieup.add_argument('infile')

    p_stats = subparsers.add_parser(
        'stats',
        help='Print stats for a draft.')
    p_stats.add_argument('infile')
    p_stats.set_defaults(function=stats)

    opts, args = p.parse_known_args(argv[1:])
    return opts.function(opts)
