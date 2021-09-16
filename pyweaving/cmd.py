from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import sys
import argparse
import io
import os.path

from . import Draft, instructions, Drawstyle
from .wif import WIFReader, WIFWriter
from .render import ImageRenderer, SVGRenderer
from .generators.tartan import tartan
from .generators.twill import twill

def gen_tartan(opts):
    wif = tartan(opts.sett, opts.repeats)
    WIFWriter(wif).write(opts.outfile)
    
def gen_twill(opts):
    wif = twill(opts.size)
    WIFWriter(wif).write(opts.outfile)
    
def load_draft(infile):
    if infile.endswith('.wif'):
        return WIFReader(infile).read()
    elif infile.endswith('.json'):
        with open(infile, 'r') as f: #!! opt mode
            return Draft.from_json(f.read())
    else:
        raise ValueError(
            "filename %r unrecognized: .wif and .json are supported" %
            infile)


def render(opts):
    draft = load_draft(opts.infile)
    style = Drawstyle()
    if opts.outfile:
        if opts.outfile.endswith('.svg'):
            SVGRenderer(draft).save(opts.outfile)
        else:
            ImageRenderer(draft, style).save(opts.outfile)
    else:
        ImageRenderer(draft).show()


def convert(opts):
    draft = load_draft(opts.infile)
    if opts.outfile.endswith('.wif'):
        WIFWriter(draft).write(opts.outfile)
    elif opts.outfile.endswith('.json'):
        with io.open(opts.outfile, 'w', encoding='utf-8') as f:
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
    print("Date:", draft.date)  # not sure to display this as generally date of wif file spec
    print("Source program:", draft.source_program, "version:",draft.source_version)
    print("***")
    print("Warp Threads:", len(draft.warp))
    print("Weft Threads:", len(draft.weft))
    print("Shafts:", len(draft.shafts))
    print("Treadles:", len(draft.treadles))
    print("Longest Float (Warp):", warp_longest)
    print("Longest Float (Weft):", weft_longest)

def outfile_if_missing_dir(infile, outfile):
    " pull dir from infile if not in outfile "
    indir, inbase = os.path.split(infile)
    outdir, outbase = os.path.split(outfile)
    if infile and outfile and not outdir:
        outfile = os.path.join(indir,outbase)
    return outfile
    
    
def main(argv=sys.argv):
    p = argparse.ArgumentParser(description='Weaving utilities.',
                                # can supply a file of args instead of commandline
                                fromfile_prefix_chars='@')

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
    p_tieup.set_defaults(function=tieup)

    p_stats = subparsers.add_parser(
        'stats',
        help='Print stats for a draft.')
    p_stats.add_argument('infile')
    p_stats.set_defaults(function=stats)
    
    p_tartan = subparsers.add_parser(
        'tartan', 
        help='Create a wif from the tartan generator.')
    p_tartan.add_argument('sett')
    p_tartan.add_argument('--repeats', type=int, default=1)
    p_tartan.add_argument('outfile')
    p_tartan.set_defaults(function=gen_tartan)

    p_twill  = subparsers.add_parser(
        'twill', 
        help='Create a wif from the twill generator.')
    p_twill.add_argument('size', type=int, default=2)
    p_twill.add_argument('outfile')
    p_twill.set_defaults(function=gen_twill)

    opts, args = p.parse_known_args(argv[1:])
    # copy directory to outfile if not supplied
    if  "outfile" in opts and "infile" in opts:
        opts.outfile = outfile_if_missing_dir(opts.infile, opts.outfile)
    return opts.function(opts)
