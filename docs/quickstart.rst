Quick Start
===========


Install
-------

The recommended installation method is `pip <http://pip.readthedocs.org/>`_.::

    $ pip install pyweaving

You can also download a source package here `directly from the Python Package Index <https://pypi.python.org/pypi/pyweaving>`_.


PyWeaving can be used via the command line or Python code. Generating a new
draft from scratch will generally require writing Python code.


Open a Draft
------------

Lots of great drafts are available in WIF format. A huge repository is `Handweaving.net <http://handweaving.net/>`_. To open a .wif file as an image, do::

    $ pyweaving render draft.wif

To open a draft from Python, do::

    from pyweaving import WIFReader

    draft = WIFReader('draft.wif').read()
