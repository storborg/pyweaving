
import sys
import argparse

import io               # used in convert() to get around json.dumps issues in python3
import os.path
from os import getcwd
import json
import glob # finding numerically suffixed files in generate_unique_filename()

from . import Draft, instructions, Drawstyle, Color, get_project_root
from .wif import WIFReader, WIFWriter
from .render import ImageRenderer, SVGRenderer
from .generators.tartan import tartan
from .generators.twill import twill
from .generators.raster import point_threaded, extract_draft

# support for local styles.json in ./pyweaving
from shutil import copy2
homedir = get_project_root()
data_path = os.path.join(homedir, 'data') # original style.json file is here

Drawstyles = {} # loaded styles go in here


def outfile_if_missing_dir(infile, outfile):
    " use dir from infile if not in outfile "
    indir, inbase = os.path.split(infile)
    outdir, outbase = os.path.split(outfile)
    if infile and outfile and not outdir:
        outfile = os.path.join(indir, outbase)
    return outfile

def ensure_ext(filename, ext):
    " replace or add ext as required onto full filename "
    return os.path.splitext(filename)[0]+"."+ext
    
def find_highest_suffixed_file(directory, stub, ext):
    """ Look in dir for filenames with numeric suffix matching stub
        and find highest count
    """
    stubname = stub+"-*"+"."+ext
    files = glob.glob(os.path.join(directory, stubname))
    
    highest = 0
    for f in files:
        name,extn = os.path.splitext(f)
        if name[-2:].isdigit():
            count = int(name[-2:])
            if highest < count:
                highest = count
    return highest

def generate_unique_filename(label, directory, ext):
    """ Generate autoname and increment suffix until unique in directory
        - suffix is in form -NN where NN is a zero leading integer (max 99)
    """
    result = label.replace(",","_")
    result = result.replace(" ","_")
    result,_ = os.path.splitext(result)
    # does file exist already ?
    if os.path.exists(result+"."+ext):
        # dup so add suffix name
        last = find_highest_suffixed_file(directory, result, ext)
        # if we have a suffix increment the highest count
        result += "-%02d"%(last+1)
    result = result+"."+ext
    return result
    
def write_wif_auto(wif, opts, name_part, prefix):
    """ save wif using name_part as principle label
        Also render if defined
    """
    # save wif file
    autoname = name_part.replace("/","") # new filename
    current_dir = getcwd()+"\\"
    if opts.outfile == 'auto':
        opts.outfile = generate_unique_filename(prefix+autoname, current_dir, "wif")
    else:
        opts.outfile = ensure_ext(opts.outfile, 'wif')
        # force current_dir if not supplied
        opts.outfile = outfile_if_missing_dir(current_dir, opts.outfile)
    WIFWriter(wif).write(opts.outfile)
    
    # render png to file as well ?
    if opts.render:
        if opts.renderfile == "auto":
            # generate filename from shape and current_dir directory
            opts.renderfile = generate_unique_filename(prefix+autoname, current_dir, "png")
        else:
            opts.renderfile = ensure_ext(opts.renderfile, 'png')
            # force pwd if not supplied
            opts.renderfile = outfile_if_missing_dir(current_dir, opts.renderfile)
        # set the renderstyle
        style = get_style(opts.style)
        # override renderstyle
        pass
        ImageRenderer(wif, style).save(opts.renderfile) 

def gen_tartan(opts):
    """ create a tartan pattern from a pattern 
        - save as wif and optionally render as png
        - incoming sett is a pattern or name of a tartan
    """
    wif = tartan(opts.sett, opts.repeats, opts.direction)
    if wif:
        wif.process_draft()
        # save wif file
        write_wif_auto(wif, opts, opts.sett, 'gen_tartan_')
    
    
def gen_twill(opts):
    """ create a twill pattern from a pattern 
        - save as wif and optionally render as png
        - incoming pattern in form '2/2 3/1' for a combined twill
    """
    wif = twill(opts.shape, opts.repeats)
    if wif:
        wif.process_draft()
        # save wif file
        write_wif_auto(wif, opts, opts.shape, 'gen_twill_')
 
def gen_from_drawdown(opts):
    """ create a draft from an image of a drawdown
        - save as wif and optionally render as png
        - incoming shafts is a target for detecting number of shafts in the image
    """
    wif = extract_draft(opts.imagefile, shafts=opts.shafts, find_core=opts.core)
    if wif:
        wif.process_draft()
        # save wif file
        write_wif_auto(wif, opts, opts.imagefile, 'gen_draft_')
        
def gen_image(opts):
    """ create a draft from a pictorial image. Uses a point draw.
        - save as wif and optionally render as png
    """
    wif = point_threaded(opts.imagefile, shafts=opts.shafts, repeats=opts.repeats)
    if wif:
        wif.process_draft()
        # save wif file
        write_wif_auto(wif, opts, opts.imagefile, 'gen_image_')
    
    
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
        if style:
            if opts.floats > 0:
                style.set_floats(opts.floats-1)
            if opts.outfile:
                first4 = opts.outfile[:4]    # is it 'auto'
                imagetype = opts.outfile[4:] # and png or svg
                if first4 == 'auto':
                    current_dir = getcwd()+"\\"
                    if imagetype in ['svg','png']:
                        opts.outfile = generate_unique_filename(opts.infile, current_dir, imagetype)
                    else: # force to png
                        opts.outfile = generate_unique_filename(opts.infile, current_dir, 'png')
                #
                if opts.outfile.endswith('.svg'):
                    SVGRenderer(draft, style, opts.liftplan, opts.structure).save(opts.outfile)
                else:
                    ImageRenderer(draft, style, opts.liftplan, opts.structure).save(opts.outfile)
            else: # no outfile specified - show it
                ImageRenderer(draft, style, opts.liftplan, opts.structure).show()


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
        if draft.notes:
            print("Notes:")
            for n in draft.notes: print("",n)
        print("Creation Date:", draft.creation_date)
        print("Source program:", draft.source_program, "version:",draft.source_version)
        print("***")
        print("Warp Threads:", len(draft.warp))
        print("Weft Threads:", len(draft.weft))
        print("Shafts:", len(draft.shafts))
        print("Treadles:", len(draft.treadles))
        print("Longest Float (Warp):", warp_longest)
        print("Longest Float (Weft):", weft_longest)


def load_styles(filename='styles.json'):
    """ Load the styles into Drawstyles dict.
        If no .pyweaving dir create it and
        copy original syles.json from /data
    """
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
        # copy styles.json master from data dir
        copy2(os.path.join(data_path, 'styles.json'), dir)
    infile = os.path.join(dir, 'styles.json')
    
    if os.path.exists(infile):
        with open(infile, 'r') as file:
            styles = json.load(file)
            for name, attributes in styles.items():
                # Make the Drawstyle() or copy an existing is derived_from
                attributes.pop('name') # pop so we won't be using these again
                parent = attributes.pop('derived_from')
                if parent:
                    style = Drawstyles[parent].copy
                    style.name = name
                    style.derived_from = parent
                else:
                    style = Drawstyle()
                    style.name = name
                # Populate the class by copying defined fields from a temp Drawstyle
                temp = Drawstyle(**attributes)
                for a in attributes.keys(): # using string as accessor
                    setattr(style, a, getattr(temp, a))
                # save it
                Drawstyles[name] = style
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
        possibles = [n for n in Drawstyles.keys() if n.find(name[:len(name)//2]) > -1]
        temp = [n for n in Drawstyles.keys() if n.find(name[len(name)//2:]) > -1]
        for t in temp:
            if t not in possibles:
                possibles.append(t)
        print("Simlarly named styles:",possibles)
        return None
        
    
def main(argv=sys.argv):
    p = argparse.ArgumentParser(prog='pyweaving', 
                                description='Weaving utilities for wif files.',
                                epilog='Generators like "tartan","twill","satin" have a --render option in addition to outfile',
                                # can supply a file of args instead of commandline
                                fromfile_prefix_chars='@')

    subparsers = p.add_subparsers(help='Sub-command help')
    
    # Render a wif file
    p_render = subparsers.add_parser(
        'render', help='Render a draft.')
    p_render.add_argument('infile')
    # will just show() if outfile not specified
    p_render.add_argument('outfile', nargs='?', help='use autopng or autosvg for a safely autonamed image file')
    p_render.add_argument('--liftplan', action='store_true',help='Show draft as a liftplan even if defined with a Tieup.')
    p_render.add_argument('--floats', type=int, default=0,help='Highlight floats above this size.')
    p_render.add_argument('--style', default='Default',help='Use a named style from styles.json in ~/.pyweaving directory.')
    p_render.add_argument('--structure', action='store_true',help='Warp is Black, Weft is white.')
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
    p_tartan.add_argument('--style', default='Default',help='Use a named style from styles.json in ~/.pyweaving directory.')
    p_tartan.add_argument('outfile', default='auto',help='Save to this file or "auto"(default) for an autoname in current directory.')
    p_tartan.set_defaults(function=gen_tartan)

    # Twill generator
    p_twill  = subparsers.add_parser(
        'twill', 
        help='Create a wif from the twill generator (and optionally render).')
    p_twill.add_argument('shape')
    p_twill.add_argument('--repeats', type=int, default=4,help='How many times to repeat the twill.')
    p_twill.add_argument('--render', action='store_true',help='Also render to file. Add auto to get an autonamed imagefile.')
    p_twill.add_argument('--renderfile', default='auto',help='filename or "auto"(default) for an autoname.')
    p_twill.add_argument('--style', default='Default',help='Use a named style from styles.json in ~/.pyweaving directory.')
    p_twill.add_argument('outfile')
    p_twill.set_defaults(function=gen_twill)
    
    # Drawdown generator
    p_drawdown  = subparsers.add_parser(
        'drawdown', 
        help='Create a wif from a supplied image of a drawdown (and optionally render).')
    p_drawdown.add_argument('imagefile')
    p_drawdown.add_argument('--shafts', default='8',help='How many shafts to use. E.g. 8, 8x16')
    p_drawdown.add_argument('--core', action='store_true',help='Reduce to non-repeating core draft')
    p_drawdown.add_argument('--render', action='store_true',help='Also render to file. Add auto to get an autonamed imagefile.')
    p_drawdown.add_argument('--renderfile', default='auto',help='filename or "auto"(default) for an autoname.')
    p_drawdown.add_argument('--style', default='Default',help='Use a named style from styles.json in ~/.pyweaving directory.')
    p_drawdown.add_argument('outfile', default='auto',help='Save to this file or "auto"(default) for an autoname in current directory.')
    p_drawdown.set_defaults(function=gen_from_drawdown)
    
    # Image generator
    p_image  = subparsers.add_parser(
        'image', 
        help='Create a wif from a supplied pictorial image (and optionally render).')
    p_image.add_argument('imagefile')
    p_image.add_argument('--shafts', default='40',help='How many shafts to use. E.g. 40')
    p_image.add_argument('--repeats', default='2',help='How many repeats to create')
    p_image.add_argument('--render', action='store_true',help='Also render to file. Add auto to get an autonamed imagefile.')
    p_image.add_argument('--renderfile', default='auto',help='filename or "auto"(default) for an autoname.')
    p_image.add_argument('--style', default='Default',help='Use a named style from styles.json in ~/.pyweaving directory.')
    p_image.add_argument('outfile', default='auto',help='Save to this file or "auto"(default) for an autoname in current directory.')
    p_image.set_defaults(function=gen_image)

    opts, args = p.parse_known_args(argv[1:])
    # copy directory to outfile if not supplied
    if  'outfile' in opts and opts.outfile and "infile" in opts:
        opts.outfile = outfile_if_missing_dir(opts.infile, opts.outfile)
    if len(argv) > 1:
        return opts.function(opts)
    else:
        p.print_help()
