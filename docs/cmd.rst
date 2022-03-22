Command Line Usage
==================

PyWeaving includes a command-line utility that can be used for basic tasks.
Here are some examples. You can also see the utility itself for more info::

    $ pyweaving -h

Will print this Usage text::

	usage: pyweaving [-h] {render,convert,thread,weave,tieup,stats,tartan,twill,drawdown,image} ...
	Weaving utilities for wif files.
	positional arguments:
	  {render,convert,thread,weave,tieup,stats,tartan,twill,drawdown,image}
							Sub-command help
		render              Render a draft.
		convert             Convert between draft file types.
		thread              Show threading instructions for a draft.
		weave               Show weaving instructions for a draft.
		tieup               Show tie-up instructions for a draft.
		stats               Print stats for a draft.
		tartan              Create a wif from the tartan generator (and optionally render).
		twill               Create a wif from the twill generator (and optionally render).
		drawdown            Create a wif from a supplied image of a drawdown (and optionally render).
		image               Create a wif from a supplied image (and optionally render).


Help is available for each of the subcommands
E.g. for render::

	usage: pyweaving render [-h] [--liftplan] [--floats FLOATS] [--style STYLE] [--structure] infile [outfile]
	positional arguments:
	  infile
	  outfile          use autopng or autosvg for a safely autonamed image file

	optional arguments:
	  -h, --help       show this help message and exit
	  --liftplan       Show draft as a liftplan even if defined with a Tieup.
	  --floats FLOATS  Highlight floats above this size.
	  --style STYLE    Use a named style from styles.json in ~/.pyweaving directory.
	  --structure      Warp is Black, Weft is white.


Draft Rendering
---------------

Render Examples::

    $ pyweaving render example.wif (will appear in your computer's pop up image viewer).
    $ pyweaving render example.wif out.png (will save the image to out.png)
    $ pyweaving render example.wif autopng (will save the image to a uniquely named image based on 'example')
    $ pyweaving render example.wif autosvg (will save the draft in svg format for printing quality or viewing in a browser)
    $ pyweaving render example.wif autopng --style shaded (will use the shaded style defined in styles.json in your home directory)
    $ pyweaving render example.wif autopng --floats 5 (will highlight floats over length 5)
    $ pyweaving render example.wif autopng --structure (will overload the colors used in warp and weft with black and white to emphasis structure)
    $ pyweaving render example.wif autopng --lisftplan (will show a liftplan instead of treadling (if defined))
    
Tartan Generator
----------------

pyweaving has a list of known tartans which you can access by name,
 or you can use a sett description to define a tartan manually.
 The --render option only writes png files. render the wif directly for svg options

Usage for tartan::

	usage: pyweaving tartan [-h] [--direction DIRECTION] [--repeats REPEATS] [--render] [--renderfile RENDERFILE] [--style STYLE]
							sett outfile

	positional arguments:
	  sett                  The Tartan pattern "B46,G3,Y1,G4" or a tartan name.
	  outfile               Save to this file or "auto"(default) for an autoname in current directory.

	optional arguments:
	  -h, --help              show this help message and exit
	  --direction DIRECTION   Twill direction S, Z(default).
	  --repeats REPEATS       How many times to repeat the sett.
	  --render                Also render to file.
	  --renderfile RENDERFILE filename or "auto"(default) for an autoname.
	  --style STYLE           Use a named style from styles.json in ~/.pyweaving directory.
  
    $ pyweaving tartan maclean auto (will show a list of known tartans with Maclean in the name)
    $ pyweaving tartan "maclean -rb" mytartan.wif (will save the wif into that file)
    $ pyweaving tartan "maclean -XT" auto (will save that tartan to a similiarly named wif file)
    $ pyweaving tartan "maclean -rb" --repeats 1 auto (will create a tartan with 1 repeat (default is 2))
    $ pyweaving tartan "maclean -rb" --direction S auto (will use an S direction twill (default is Z))
    $ pyweaving tartan "maclean -XT" auto --render (will also save a png file of the rendered draft)
    $ pyweaving tartan "B24_W4_B32_R4_K32_G24_W2" auto (will use that sett to build the tartan)
    $ pyweaving tartan "B/4 DY15 R1 DY/30 . G/4 O15 R1 O/30" auto will produce kincardine_tweed)
    
    

Instructions
------------

These instructions are interactive, and intend to walk you step-by-step through
various processes, providing useful statistics and progress saving along the
way.

Show instructions for threading a draft::

    $ pyweaving thread example.wif

Show instructions for weaving::

    $ pyweaving weave example.wif --liftplan --repeats 50

File Conversion
---------------

Convert between WIF and JSON::

    $ pyweaving convert example.wif example.json

