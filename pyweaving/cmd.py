from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import sys
import argparse

import io               # used in convert() to get around json.dumps issues in python3
import os.path
from os import mkdir
import json
from os import getcwd   # for finding dup files when using the generators

from . import Draft, instructions, Drawstyle
from .wif import WIFReader, WIFWriter
from .render import ImageRenderer, SVGRenderer
from .generators.tartan import tartan
from .generators.twill import twill

Drawstyles = {} # loaded styles go in here

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
    result = os.path.splitext(result)[0]+"."+ext
    # print("generating",result)
    # check directory for same named file (+ext)
    #!! if so then try to parse 3 digit number at end and increment
    return result

def gen_tartan(opts):
    """ create a tartan pattern from a pattern 
        - save as wif and optionally render as png
        - incoming sett is a pattern or name of a tartan
    """
    wif = tartan(opts.sett, opts.repeats, opts.direction)
    if wif:
        wif.process_draft()
    
        # save wif file
        autoname = opts.sett.replace("/","").upper() # new filename
        current_dir = getcwd()+"\\"
        if opts.outfile == 'auto':
            opts.outfile = generate_unique_filename('gen_tartan_'+autoname, current_dir, "wif")
        else:
            opts.outfile = ensure_ext(opts.outfile, 'wif')
            # force current_dir if not supplied
            opts.outfile = outfile_if_missing_dir(current_dir, opts.outfile)
        WIFWriter(wif).write(opts.outfile)
        
        # render png to file as well
        if opts.render:
            if opts.renderfile == "auto":
                # generate filename from sett and current_dir directory
                opts.renderfile = generate_unique_filename('gen_tartan_'+autoname, current_dir, "png")
            else:
                opts.renderfile = ensure_ext(opts.renderfile, 'png')
                # force pwd if not supplied
                opts.renderfile = outfile_if_missing_dir(current_dir, opts.renderfile)
            # set the renderstyle
            style = Drawstyle()
            # override renderstyle
            pass
            ImageRenderer(wif, style).save(opts.renderfile)
    
    
def gen_twill(opts):
    wif = twill(opts.shape)
    wif.process_draft()
    
    current_dir = getcwd()+"\\"
    autoname = opts.shape.replace("/","_").upper() # new filename
    if opts.outfile == 'auto':
        opts.outfile = generate_unique_filename('gen_twill_'+autoname, current_dir, "wif")
    else:
        opts.outfile = ensure_ext(opts.outfile, 'wif')
        # force current_dir if not supplied
        opts.outfile = outfile_if_missing_dir(current_dir, opts.outfile)
    WIFWriter(wif).write(opts.outfile)
    
    # render png to file as well
    if opts.render:
        if opts.renderfile == "auto":
            # generate filename from shape and current_dir directory
            opts.renderfile = generate_unique_filename('gen_twill_'+autoname, current_dir, "png")
        else:
            opts.renderfile = ensure_ext(opts.renderfile, 'png')
            # force pwd if not supplied
            opts.renderfile = outfile_if_missing_dir(current_dir, opts.renderfile)
        # set the renderstyle
        style = Drawstyle()
        # override renderstyle
        pass
        ImageRenderer(wif, style).save(opts.renderfile)
    # print(opts.outfile, opts.render, opts.renderfile, opts.renderstyle) 
    
def load_draft(infile):
    """ Load the draft file in wif or json format.
        - return the Draft or
          false if not found or wrong type
    """
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
    """ Render to svg or png based on file extension
        - if no outfile then show without saving
    """
    draft = load_draft(opts.infile)
    if draft:
        style = get_style(opts.style)
        if opts.floats > 0:
            style.set_floats(opts.floats-1)
        if opts.outfile:
            first4 = opts.outfile[:4]
            imagetype = opts.outfile[4:]
            if first4 == 'auto':
                if imagetype in ['svg','png']:
                    opts.outfile = generate_unique_filename(opts.infile, None, imagetype)
                else: # force to png
                    opts.outfile = generate_unique_filename(opts.infile, None, 'png')
            #
            if opts.outfile.endswith('.svg'):
                SVGRenderer(draft).save(opts.outfile)
            else:
                ImageRenderer(draft, style, opts.liftplan).save(opts.outfile)
        else:
            ImageRenderer(draft, style, opts.liftplan).show()


def convert(opts):
    """ Convert wif to json or back.
        (Also can wif to wif if need to rewrite file)
    """
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
        print("Date:", draft.creation_date)  # not sure to display this as generally date of wif file spec
        print("Source program:", draft.source_program, "version:",draft.source_version)
        print("***")
        print("Warp Threads:", len(draft.warp))
        print("Weft Threads:", len(draft.weft))
        print("Shafts:", len(draft.shafts))
        print("Treadles:", len(draft.treadles))
        print("Longest Float (Warp):", warp_longest)
        print("Longest Float (Weft):", weft_longest)


def load_styles(filename='styles.json'):
    " load the styles into Drawstyles dict "
    global Drawstyles
    platform = sys.platform
    if platform.find('win') > -1: # windows
        dir = os.path.join(os.path.expanduser('~'),'Documents','.pyweaving')
    elif platform.find('dar'): # mac
        dir = os.path.join(os.path.expanduser('~'),'.pyweaving')
    else: # linux
        dir = os.path.join(os.path.expanduser('~'),'.pyweaving')
    if not os.path.exists(dir):
        os.makedir(dir)
    infile = os.path.join(dir, 'styles.json')
    
    if os.path.exists(infile):
        print("file exists",infile)
        with open(infile, 'r') as file:
            x = json.load(file)
            for name, attributes in x.items():
                #!! really want to make it with the derived_from style
                #  then just insert the attributes defined
                Drawstyles[name] = Drawstyle(**attributes)
    else:
        print("Could not find styles.json at:", infile)
    
def get_style(name):
    """ load styles if not loaded and
        return the named style
    """
    if not Drawstyles:
        load_styles()
    if name in Drawstyles.keys():
        return Drawstyles[name]
    else:
        print("Could not find Style named:",name)
        
    
def main(argv=sys.argv):
    p = argparse.ArgumentParser(prog='pyweaving', description='Weaving utilities.',
                                epilog='Generators like "tartan","twill","satin" have a --render option in addition to outfile',
                                # can supply a file of args instead of commandline
                                fromfile_prefix_chars='@')

    subparsers = p.add_subparsers(help='sub-command help')

    # Render a wif file
    p_render = subparsers.add_parser(
        'render', help='Render a draft.')
    p_render.add_argument('infile')
    # will just show() if outfile not specified
    p_render.add_argument('outfile', nargs='?', help='use autopng or autosvg for a safely autonamed image file')
    p_render.add_argument('--liftplan', action='store_true')
    p_render.add_argument('--floats', type=int, default=0)
    p_render.add_argument('--style', default='Default')
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
    
    # Tartan generator
    p_tartan = subparsers.add_parser(
        'tartan', 
        help='Create a wif from the tartan generator (and optionally render).')
    p_tartan.add_argument('sett', help='The Tartan pattern "B46,G3,Y1,G4" or a tartan name.')
    p_tartan.add_argument('--direction', default="Z",help='Twill direction S, Z(default).')
    p_tartan.add_argument('--repeats', type=int, default=1,help='How many times to repeat the sett.')
    p_tartan.add_argument('--render', action='store_true',help='Also render to file.')
    p_tartan.add_argument('--renderfile', default='auto',help='filename or "auto"(default) for an autoname.')
    p_tartan.add_argument('--style', default='default')
    p_tartan.add_argument('outfile', default='auto',help='Save to this file or "auto"(default) for an autoname in current directory.')
    p_tartan.set_defaults(function=gen_tartan)

    # Twill generator
    p_twill  = subparsers.add_parser(
        'twill', 
        help='Create a wif from the twill generator (and optionally render).')
    p_twill.add_argument('shape')
    p_twill.add_argument('--render', action='store_true',help='Also render to file. Add auto to get an autonamed imagefile.')
    p_twill.add_argument('--renderfile', default='auto',help='filename or "auto"(default) for an autoname.')
    p_twill.add_argument('--style', default='default')
    p_twill.add_argument('outfile')
    p_twill.set_defaults(function=gen_twill)

    opts, args = p.parse_known_args(argv[1:])
    # copy directory to outfile if not supplied
    if  opts.outfile and "infile" in opts:
        opts.outfile = outfile_if_missing_dir(opts.infile, opts.outfile)
    return opts.function(opts)
