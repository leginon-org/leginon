#!/usr/bin/env python
import Mrc
import Image
import NumericImage
import re


"""
Convert MRC -> JPEG
"""

def mrc2jpg2out(filename, quality=100):
	'Convert MRC -> JPEG [quality]'
	ndata = Mrc.mrc_to_numeric(filename)
	num_img = NumericImage.NumericImage(ndata)
	num_img.jpeg(None, quality)
	
if __name__ == '__main__':
	import sys

	filename = sys.argv[1]
	mrc2jpg2out(filename)
