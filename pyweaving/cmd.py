from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import sys
import argparse
import io
import os.path
from os import getcwd

from . import Draft, instructions, Drawstyle
from .wif import WIFReader, WIFWriter
from .render import ImageRenderer, SVGRenderer
from .generators.tartan import tartan
from .generators.twill import twill

def outfile_if_missing_dir(infile, outfile):
    " use dir from infile if not in outfile "
    indir, inbase = os.path.split(infile)
    outdir, outbase = os.path.split(outfile)
    if infile and outfile and not outdir:
        outfile = os.path.join(indir,outbase)
    return outfile

def ensure_ext(filename, ext):
    " replace or add ext as required onto filename "
    return os.path.splitext(filename)[0]+"."+ext
    
def generate_unique_filename(label, directory, ext):
    " generate autoname and increment suffix until unique in directory "
    result = label.replace(",","_")
    result = result.replace(" ","_")
    # print("generating",result)
    # check directory for same named file (+ext)
    # if so then try to parse 3 digit number at end and increment
    return result

def gen_tartan(opts):
    """ create a tartan pattern from a pattern 
        - save as wif and optionally render as png
    """
    wif = tartan(opts.sett, opts.repeats, "Z")
    wif.process_draft()
    opts.sett = opts.sett.replace("/","")
    cwd = getcwd()+"\\"
    
    if opts.outfile == 'auto':
        opts.outfile = generate_unique_filename('gen_tartan_'+opts.sett.upper(), cwd, "wif")
    opts.outfile = ensure_ext(opts.outfile, 'wif')
    # force cwd if not supplied
    opts.outfile = outfile_if_missing_dir(cwd, opts.outfile)
    WIFWriter(wif).write(opts.outfile)
    
    if opts.render: # render png to file as well
        if opts.renderfile == "auto":
            # generate filename from sett and cwd directory
            opts.renderfile = generate_unique_filename('gen_tartan_'+opts.sett.upper(), cwd, "png")
        opts.renderfile = ensure_ext(opts.renderfile, 'png')
        # force pwd if not supplied
        opts.renderfile = outfile_if_missing_dir(cwd, opts.renderfile)
        # set the renderstyle
        style = Drawstyle()
        # override renderstyle
        pass
        ImageRenderer(wif, style).save(opts.renderfile)
    # print(opts.outfile, opts.render, opts.renderfile, opts.renderstyle) 
    
    
def gen_twill(opts):
    wif = twill(opts.shape)
    WIFWriter(wif).write(opts.outfile)
    
def load_draft(infile):
    if os.path.exists(infile):
        if infile.endswith('.wif'):
            return WIFReader(infile).read()
        elif infile.endswith('.json'):
            with open(infile, 'r') as f: #!! opt mode
                return Draft.from_json(f.read())
        else:
            raise ValueError(
                "filename %r unrecognized: .wif and .json are supported" %
                infile)
    else:
        print("File not found:", infile)
        return False


def render(opts):
    draft = load_draft(opts.infile)
    if draft:
        style = Drawstyle()
        if opts.floats > 0:
            style.set_floats(opts.floats)
        if opts.outfile:
            if opts.outfile.endswith('.svg'):
                SVGRenderer(draft).save(opts.outfile)
            else:
                ImageRenderer(draft, style, opts.liftplan).save(opts.outfile)
        else:
            ImageRenderer(draft, style, opts.liftplan).show()


def convert(opts):
    draft = load_draft(opts.infile)
    if draft:
        if opts.outfile.endswith('.wif'):
            WIFWriter(draft).write(opts.outfile)
        elif opts.outfile.endswith('.json'):
            with io.open(opts.outfile, 'w', encoding='utf-8') as f:
                f.write(draft.to_json())


def thread(opts):
    draft = load_draft(opts.infile)
    if draft:
        instructions.threading(draft, opts.repeats)


def weave(opts):
    draft = load_draft(opts.infile)
    if draft:
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
    if draft:
        instructions.tieup(draft)


def stats(opts):
    draft = load_draft(opts.infile)
    if draft:
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


    
    
def main(argv=sys.argv):
    p = argparse.ArgumentParser(prog='pyweaving', description='Weaving utilities.',
                                epilog='Generators like "tartan","twill","satin" have a --render option in addition to outfile',
                                # can supply a file of args instead of commandline
                                fromfile_prefix_chars='@')

    subparsers = p.add_subparsers(help='sub-command help')

    p_render = subparsers.add_parser(
        'render', help='Render a draft.')
    p_render.add_argument('infile')
    p_render.add_argument('outfile', nargs='?')
    p_render.add_argument('--liftplan', action='store_true')
    p_render.add_argument('--floats', type=int, default=0)
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
    
    # tartan "K8, B46, K46, G44, Y6, G6, Y12" --render --renderstyle solids --renderfile foo outfile
    p_tartan = subparsers.add_parser(
        'tartan', 
        help='Create a wif from the tartan generator (and optionally render).')
    p_tartan.add_argument('sett', help='The Tartan pattern "B46,G3,Y1,G4".')
    p_tartan.add_argument('--repeats', type=int, default=1,help='How many times to repeat the sett.')
    p_tartan.add_argument('--render', action='store_true',help='Also render to file.')
    p_tartan.add_argument('--renderfile', default='auto',help='filename or "auto"(default) for an autoname.')
    p_tartan.add_argument('--renderstyle', default='blobs', choices=['solids', 'blobs', 'colors', 'numbers'])
    p_tartan.add_argument('outfile', default='auto',help='Save to this file or "auto"(default) for an autoname in current directory.')
    p_tartan.set_defaults(function=gen_tartan)

    p_twill  = subparsers.add_parser(
        'twill', 
        help='Create a wif from the twill generator (and optionally render).')
    p_twill.add_argument('shape')
    p_twill.add_argument('outfile')
    p_twill.set_defaults(function=gen_twill)

    opts, args = p.parse_known_args(argv[1:])
    # copy directory to outfile if not supplied
    if  opts.outfile and "infile" in opts:
        opts.outfile = outfile_if_missing_dir(opts.infile, opts.outfile)
    return opts.function(opts)
