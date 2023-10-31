
import sys
import argparse

import io  # used in convert() to get around json.dumps issues in python3
import os.path
from os import getcwd
import glob  # finding numerically suffixed files in generate_unique_filename()

from . import Draft, instructions, get_style
from .wif import WIFReader, WIFWriter
from .render import ImageRenderer, SVGRenderer
from .generators.tartan import tartan
from .generators.twill import twill
from .generators.raster import point_threaded, extract_draft, find_common_colors, remap_image_colors


def outfile_if_missing_dir(infile, outfile):
    """
    If no directory defined on outfile, then use the directory from infile.

    Returns:
        outfile (str):
    """
    " use dir from infile if not in outfile "
    indir, inbase = os.path.split(infile)
    outdir, outbase = os.path.split(outfile)
    if infile and outfile and not outdir:
        outfile = os.path.join(indir, outbase)
    return outfile


def ensure_ext(filename, ext):
    """
    Replace the extension on the filename and return.
    """
    return os.path.splitext(filename)[0]+"."+ext


def find_highest_suffixed_file(directory, stub, ext):
    """
    Look in directory for filenames with numeric suffix matching stub
     - find highest count

    Returns:
        highest (int):
    """
    stubname = stub+"-*"+"."+ext
    files = glob.glob(os.path.join(directory, stubname))

    highest = 0
    for f in files:
        name, extn = os.path.splitext(f)
        if name[-2:].isdigit():
            count = int(name[-2:])
            if highest < count:
                highest = count
    return highest


def generate_unique_filename(label, directory, ext):
    """
    Cleanup label and generate a well named file with a unique numeric suffix:
     - finding a numeric suffix that is unique in the directory,
     - replacing the file extension,
     - suffix is in form -NN where NN is a zero leading integer (max 99)
     - will produce names like 'foo-02.png'

    Args:
        label (str): a filename without a directory,
        directory (str): a directory to look into to check for name collisions,
        ext (str): file extension like 'png'
    """
    result = label.replace(",", "_")
    result = result.replace(" ", "_")
    result = result.replace("_-", "-")
    result, _ = os.path.splitext(result)
    # does file exist already ?
    if os.path.exists(result+"."+ext):
        # dup so add suffix name
        last = find_highest_suffixed_file(directory, result, ext)
        # if we have a suffix increment the highest count
        result += "-%02d" % (last + 1)
    result = result+"."+ext
    return result
    
def write_wif_auto(wif, opts, name_part, prefix):
    """
    return result


    Does a few common tasks to sabve a file:
     - cleanup file removing illegal chars
     - use the current working directory if one is not supplied,
     - construct a filename from the prefix, name_part and a
       calculated numeric suffix (if required to ensure the name is unique).

    Save the wif using this name and also render to png if opts.render is True.
    """
    # save wif file
    autoname = name_part.replace("/", "")  # new filename
    current_dir = getcwd() + "\\"
    if opts.outfile == 'auto':
        opts.outfile = generate_unique_filename(prefix + autoname, current_dir, "wif")
    else:
        opts.outfile = ensure_ext(opts.outfile, 'wif')
        # force current_dir if not supplied
        opts.outfile = outfile_if_missing_dir(current_dir, opts.outfile)
    WIFWriter(wif).write(opts.outfile)

    # render png to file as well ?
    if opts.render:
        if opts.renderfile == "auto":
            # generate filename from shape and current_dir directory
            opts.renderfile = generate_unique_filename(prefix + autoname, current_dir, "png")
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
    """
    Create a tartan pattern from a pattern
     - save as wif and optionally render as png
     - incoming sett is a pattern or name of a tartan
    """
    wif = tartan(opts.sett, opts.repeats, opts.direction)
    if wif:
        wif.process_draft()
        # save wif file
        write_wif_auto(wif, opts, opts.sett, 'gen_tartan_')


def gen_twill(opts):
    """
    Create a twill pattern from a pattern
     - save as wif and optionally render as png
     - incoming pattern in form '2/2 3/1' for a combined twill
    """
    wif = twill(opts.shape, opts.repeats)
    if wif:
        wif.process_draft()
        # save wif file
        write_wif_auto(wif, opts, opts.shape, 'gen_twill_')


def gen_from_drawdown(opts):
    """
    Create a draft from an image of a drawdown
     - save as wif and optionally render as png
     - incoming shafts is a target for detecting number of shafts in the image
    """
    wif = extract_draft(opts.imagefile, shafts=opts.shafts, find_core=opts.core)
    if wif:
        wif.process_draft()
        # save wif file
        write_wif_auto(wif, opts, opts.imagefile, 'gen_draft_')


def gen_image(opts):
    """
    Create a draft from a pictorial image. Uses a point draw.
     - save as wif and optionally render as png
    """
    wif = point_threaded(opts.imagefile, shafts=opts.shafts, repeats=opts.repeats)
    if wif:
        wif.process_draft()
        # save wif file
        write_wif_auto(wif, opts, opts.imagefile, 'gen_image_')


def find_colors(opts):
    """
    Will print out the most common colors found in an image.
    """
    colors, swatch, col_total = find_common_colors(opts.imagefile, int(opts.count),
                                                   swatch_size=int(opts.size))  # test with image_scaled_size=100)
    if colors:
        msg = ""
        if int(opts.count) != len(colors):
            msg = "We could not find %d distinct clusters of color." % (int(opts.count))
        print("Found %d colors (From %d unique) in %s. %s" % (len(colors), col_total, opts.imagefile, msg))
        if int(opts.count) != len(colors):
            print("Even though %d colors were requested. Only %d clusters of color were found" % (opts.count, len(colors)))
        print(" - the random nature of initial sampling can lead to slightly different results each time")
        for c in colors:
            print(c.hex, c)
    if swatch:
        # save wif file
        dotpos = opts.imagefile.rfind(".")
        current_dir = getcwd() + "\\"
        newname = generate_unique_filename("%s-colorrefx%d" % (opts.imagefile[:dotpos], len(colors)), current_dir, "png")
        print("Writing image:", newname)
        swatch.save(newname)
        return swatch

def remap_image(opts):
    """
    Remap colors in an image to those in a refcol file.
    Also rescale image to width and aspect ratio.
    - If no colref then reduce first to --count colors
    - If no width then rescale to aspect and existing width. (ignore if aspect = 1
    - only count is mandatory
    """
    filename = opts.imagefile
    colcount = opts.count
    imagewidth = int(opts.width)
    #
    divpos= opts.aspect.find("/")
    aspect = 1
    if divpos >0:
        num = opts.aspect[:divpos]
        den = opts.aspect[divpos+1:]
        aspect = float(num)/float(den)
    else: # single num
        aspect = float(opts.aspect)
    if imagewidth == 0:
        # unsupplied so use image_width
        # read imagefile and get width
        pass
    if opts.aspect == '1/1':
        # unsupplied so maintain current aspect ratio
        pass
    if opts.colref:
        colref = opts.colref
    else: # none supplied
        # so reduce first and use that as remap target.
        opts.size=20
        colref = find_colors(opts) # its a PIL image
    # image_width may be 0, colref may be filename or PIL Image.
    newimage = remap_image_colors(filename, imagewidth, aspect, colref, colcount, filter=opts.filter)
    # Save
    current_dir = getcwd() + "\\"
    newname = os.path.splitext(filename)
    # newimage.save(newname[0]+"_remapped"+newname[1])
    newname = generate_unique_filename(newname[0]+"_remapped", current_dir, "png")
    print("Writing image:", newname)
    newimage.save(newname)
    

def load_draft(infile):
    """
    Load the draft file in wif or json format.
     - return the Draft or false if not found or wrong type
    """
    if os.path.exists(infile):
        if infile.endswith('.wif'):
            return WIFReader(infile).read()
        elif infile.endswith('.json'):
            with open(infile, 'r') as f:  # !! opt mode
                return Draft.from_json(f.read())
        else:
            raise ValueError(
                "filename %r unrecognized: .wif and .json are supported" %
                infile)
    else:
        print("File not found:", infile)
        return False


def render(opts):
    """
    Render to svg or png based on file extension
     - if no outfile then show without saving
    """
    draft = load_draft(opts.infile)
    if draft:
        style = get_style(opts.style)
        if style:
            if opts.floats > 0:
                style.set_floats(opts.floats - 1)
            if opts.outfile:
                localdir, fileid = os.path.split(opts.outfile)
                if fileid[:4] == 'auto':  # Generate an automatic and safe (unique) name.
                    imagetype = fileid[4:]  # png or svg
                    current_dir = getcwd() + "\\"
                    # Bug here:
                    # if infile has a dir (os.path.split())
                    # then that dir will be changed if it has a space in it to an underscore.
                    # which will not find the directory.
                    if imagetype == 'svg':
                        opts.outfile = generate_unique_filename(opts.infile, current_dir, imagetype)
                    else:  # use or override to png
                        opts.outfile = generate_unique_filename(opts.infile, current_dir, 'png')
                else:  # outfile is not auto so just use it
                    pass
                #
                print("out", opts.outfile)
                if opts.outfile.endswith('.svg'):
                    SVGRenderer(draft, style, opts.liftplan, opts.structure).save(opts.outfile)
                elif opts.outfile.endswith('.png'):
                    ImageRenderer(draft, style, opts.liftplan, opts.structure).save(opts.outfile)
                else:
                    print("File extension not recognised", opts.outfile)
            else:  # no outfile specified - show it
                ImageRenderer(draft, style, opts.liftplan, opts.structure).show()


def convert(opts):
    """
    Convert wif to json or back.
     - (Also can wif to wif if need to rewrite file)
    """
    draft = load_draft(opts.infile)
    if draft:
        if opts.outfile.endswith('.wif'):
            WIFWriter(draft).write(opts.outfile)
        elif opts.outfile.endswith('.json'):
            with io.open(opts.outfile, 'w', encoding='utf-8') as f:
                f.write(draft.to_json())


def thread(opts):
    """
    Print Basic instructions on Threading
    """
    draft = load_draft(opts.infile)
    if draft:
        instructions.threading(draft, opts.repeats)


def weave(opts):
    """
    Help Weaver to weave this draft one pick at a time.
    Assumes a 4 shaft table loom and liftplan only.
    Allows weaver to stop and start again later at the correct pick.
    """
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
    """
    Print instructions on tieup
    """
    draft = load_draft(opts.infile)
    if draft:
        instructions.tieup(draft)


def stats(opts):
    """
    Basic report on nature of draft.
     - terminal output
    """
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
            for n in draft.notes:
                print("", n)
        print("Creation Date:", draft.creation_date)
        print("Source program:", draft.source_program, "version:", draft.source_version)
        print("***")
        print("Warp Threads:", len(draft.warp))
        print("Weft Threads:", len(draft.weft))
        print("Shafts:", len(draft.shafts))
        print("Treadles:", len(draft.treadles))
        print("Longest Float (Warp):", warp_longest)
        print("Longest Float (Weft):", weft_longest)


def main(argv=sys.argv):
    p = argparse.ArgumentParser(prog='pyweaving',
                                description='Weaving utilities for wif files.',
                                epilog='Generators like "tartan","twill","satin" have a --render option in addition to outfile',
                                # can supply a file of args instead of commandline
                                fromfile_prefix_chars='@')

    subparsers = p.add_subparsers(help='Sub-command help')

    # Render a wif file
    p_render = subparsers.add_parser(
        'render', help='Render a draft on-screen or to file.')
    p_render.add_argument('infile', help='The wif file to load.')
    # will just show() if outfile not specified
    p_render.add_argument('outfile', nargs='?', help='use autopng or autosvg for a safely autonamed image file')
    p_render.add_argument('--liftplan', action='store_true', help='Show draft as a liftplan even if defined with a Tieup.')
    p_render.add_argument('--floats', type=int, default=0, help='Highlight floats above this size.')
    p_render.add_argument('--style', default='Default', help='Use a named style from styles.json in ~/.pyweaving directory.')
    p_render.add_argument('--structure', action='store_true', help='Warp is Black, Weft is white.')
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
        help='Show stats for a draft.')
    p_stats.add_argument('infile')
    p_stats.set_defaults(function=stats)

    # Tartan generator
    p_tartan = subparsers.add_parser(
        'tartan',
        help='Create a wif from the tartan generator (optionally render).')
    p_tartan.add_argument('sett', help='The Tartan pattern "B46,G3,Y1,G4" or a tartan name.')
    p_tartan.add_argument('outfile', default='auto', help='Save to this file or "auto"(default) for an autoname in current directory.')
    p_tartan.add_argument('--direction', default="Z", help='Twill direction S, Z(default).')
    p_tartan.add_argument('--repeats', type=int, default=1, help='How many times to repeat the sett.')
    p_tartan.add_argument('--render', action='store_true', help='Also render to file.')
    p_tartan.add_argument('--renderfile', default='auto', help='filename or "auto"(default) for an autoname.')
    p_tartan.add_argument('--style', default='Default', help='Use a named style from styles.json in ~/.pyweaving directory.')
    p_tartan.set_defaults(function=gen_tartan)

    # Twill generator
    p_twill = subparsers.add_parser(
        'twill',
        help='Create a wif from the twill generator (optionally render).')
    p_twill.add_argument('shape', default="2/1 2/2", help='Twill pairs separated by spaces. E.g. 2/2 or "1/2 2/1S"')
    p_twill.add_argument('outfile', default='auto', help='Save to this file or "auto"(default) for an autoname in current directory.')
    p_twill.add_argument('--repeats', type=int, default=4, help='How many times to repeat the twill.')
    p_twill.add_argument('--render', action='store_true', help='Also render to file. Add auto to get an autonamed imagefile.')
    p_twill.add_argument('--renderfile', default='auto', help='filename or "auto"(default) for an autoname.')
    p_twill.add_argument('--style', default='Default', help='Use a named style from styles.json in ~/.pyweaving directory.')
    p_twill.set_defaults(function=gen_twill)

    # Drawdown generator
    p_drawdown = subparsers.add_parser(
        'drawdown',
        help='Create a wif from a supplied image of a drawdown (optionally render).')
    p_drawdown.add_argument('imagefile', help='The image file of the drawdown.')
    p_drawdown.add_argument('outfile', default='auto', help='Save to this file or "auto"(default) for an autoname in current directory.')
    p_drawdown.add_argument('--shafts', default='8', help='How many shafts to use. E.g. 8, or 8x16')
    p_drawdown.add_argument('--core', action='store_true', help='Reduce to non-repeating core draft')
    p_drawdown.add_argument('--render', action='store_true', help='Also render to file. Add auto to get an autonamed imagefile.')
    p_drawdown.add_argument('--renderfile', default='auto', help='filename or "auto"(default) for an autoname.')
    p_drawdown.add_argument('--style', default='Default', help='Use a named style from styles.json in ~/.pyweaving directory.')
    p_drawdown.set_defaults(function=gen_from_drawdown)

    # Image generator
    p_image = subparsers.add_parser(
        'image',
        help='Create a wif from a supplied pictorial image (optionally render).')
    p_image.add_argument('imagefile', help='The image file to load.')
    p_image.add_argument('outfile', default='auto', help='Save to this file or "auto"(default) for an autoname in current directory.')
    p_image.add_argument('--shafts', default='40', help='How many shafts to use. E.g. 40')
    p_image.add_argument('--repeats', default='2', help='How many repeats to create')
    p_image.add_argument('--render', action='store_true', help='Also render to file. Add auto to get an autonamed imagefile.')
    p_image.add_argument('--renderfile', default='auto', help='filename or "auto"(default) for an autoname.')
    p_image.add_argument('--style', default='Default', help='Use a named style from styles.json in ~/.pyweaving directory.')
    p_image.set_defaults(function=gen_image)

    # Colour finder
    p_colors = subparsers.add_parser(
        'colors',
        help='Print out the most common colors in an image and save a color swatch.')
    p_colors.add_argument('imagefile', help='The image file to examine.')
    p_colors.add_argument('--count', type=int, default=6, help='How many colors to find.')
    p_colors.add_argument('--size', type=int, default=20, help='Size(pixels) of each color square in the resulting swatch image.')
    p_colors.set_defaults(function=find_colors)

    # Colour remapper
    p_remap = subparsers.add_parser(
        'remap',
        help='Load and save an image while reducing colors to supplied ref-image and rescale aspect ratio.')
    p_remap.add_argument('imagefile', help='The image file to remap.')
    p_remap.add_argument('--width', type=int, default=0, help='Width(pixels) of saved image.')
    p_remap.add_argument('--aspect', default='1/1', help='Aspect ratio of image. Typically "PPI/EPI"')
    p_remap.add_argument('--colref', help='Image of line of colors.')
    p_remap.add_argument('--count', type=int, default=8, required=True, help='Number of colors in colref image.(required)')
    p_remap.add_argument('--filter', action='store_true', help='Replace isolated pixels with neighbours.')
    p_remap.set_defaults(function=remap_image)

    opts, unknown = p.parse_known_args(argv[1:])
    if unknown:
        print("UNKNOWN keywords found:", unknown)
        print("  - Probably you have misstyped an argument name.")
        print('  - Get help by adding "-h" on the end. E.g. "pyweaving render -h" (assuming your main argument is "render"')
    # copy directory to outfile if not supplied
    if 'outfile' in opts and opts.outfile and "infile" in opts:
        opts.outfile = outfile_if_missing_dir(opts.infile, opts.outfile)

    if len(argv) > 1 and str(opts) != 'Namespace()':
        return opts.function(opts)
    else:
        p.print_help()
