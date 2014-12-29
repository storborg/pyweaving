import sys

from .wif import WIFReader
from .render import ImageRenderer


def main(args=sys.argv):
    filename = args[1]
    draft = WIFReader(filename).read()
    # out_filename = filename.rsplit('.', 1)[0] + '.png'
    # print "Saving to %s" % out_filename
    ImageRenderer(draft).show()
