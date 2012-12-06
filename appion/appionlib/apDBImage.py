#!/usr/bin/env python
from leginon import leginondata
#appion
from appionlib import apDatabase

#=========================
def correctImage(imgdata):
	"""
	Correct an image using the old method:
	- no bias correction
	- dark correction is not time dependent in the normal mode
	"""
	rawimgarray = imgdata['image']
	sessionname = imgdata['session']['name']
	darkarray, normarray = apDatabase.getDarkNorm(sessionname, imgdata['camera'])
	correctedimgarray = normarray * (rawimgarray - darkarray)
	return correctedimgarray

def makeUniqueImageFilename(old_imagedata,old_presetname,new_presetname):
		'''
		Make a unique image filename in the same session
		'''
		old_imagefilename = old_imagedata['filename']
		bits = old_imagefilename.split(old_presetname)
		before_string = old_presetname.join(bits[:-1])
		new_imagefilename = new_presetname.join((before_string,bits[-1]))
		existing_images = leginondata.AcquisitionImageData(session=old_imagedata['session'],filename=new_imagefilename).query()
		if len(existing_images) == 0:
			return new_imagefilename
		else:
			version = '_v%02d' % len(existing_images)
			return new_imagefilename+version
