#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright under
#       Apache2 License
#       For terms of the license agreement
#       see  http://leginon.org
#

from pyami import mrc
import NumericImage
import re


"""
Convert MRC -> JPEG
"""

def mrc2jpeg(filename, quality=100):
	'Convert MRC -> JPEG [quality]'
	nfile = re.sub('\.mrc$','.jpg',file)
	ndata = mrc.read(file)
	num_img = NumericImage.NumericImage(ndata)
	num_img.jpeg(nfile, quality)
	
if __name__ == '__main__':
	import sys

	for file in sys.argv[1:]:
		mrc2jpeg(file)
