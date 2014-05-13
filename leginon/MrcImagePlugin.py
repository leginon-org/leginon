#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#


#
# MRC file handler for Python Imaging Library
#

import string
from Mrc import MrcHeader
from PIL import Image, ImageFile


## PIL modes: F

## mrc mode to (PIL mode, raw mode)
mrcmode_pilmode = {0: ('L','L'), 1: ('I','I;16NS'), 2: ('F','F;32NF'), 3: ('I','I;16N')}

pilmode_mrcmode = {'L':0, 'I':1, 'F':2}

class MrcImageFile(ImageFile.ImageFile):

    format = "MRC"
    format_description = "Microscopy Data"

    def _open(self):

        # header
        header = MrcHeader(self.fp)
	if header == None:
		raise SyntaxError, "Not MRC file"
	if header['depth'] > 1:
		raise SyntaxError, "3D data unsupported in PIL"

	self.size = (header['width'], header['height'])

	## how to represent data in PIL
	self.mode = mrcmode_pilmode[header['mode']][0]

	## convert MRC mode to "raw" decoder type:
	rawmode = mrcmode_pilmode[header['mode']][1]

	#tile = (decoder, region, offset, parameters)
	self.tile = [("raw", (0,0)+self.size, header.headerlen, (rawmode,0,1) )]

# Write MRC file
def _save(im, fp, filename, check=0):

	# check if im.mode is compatible with MRC (see Bmp...)

	if check:
		return check

	header = MrcHeader()
	header['width'] = im.size[0]
	header['height'] = im.size[1]
	header['depth'] = 1
	header['mode'] = pilmode_mrcmode[im.mode]
	header.tofile(fp)

	rawmode = mrcmode_rawmode[header['mode']]
	tile = [("raw", (0,0)+im.size, header.headerlen, (rawmode, 0, 1))]
	print 'savetile:', tile
	ImageFile._save(im, fp, tile)

# Registry
Image.register_open("MRC", MrcImageFile)
Image.register_save(MrcImageFile.format, _save)
Image.register_extension("MRC", ".mrc")
