#!/usr/bin/env python
import os
from leginon import leginondata
#appion
from appionlib import apDatabase, apDisplay
from leginon import correctorclient

class ApCorrectorClient(correctorclient.CorrectorClient):
	def __init__(self, session, is_upload=False):
		super(ApCorrectorClient,self).__init__()
		self.logger = apDisplay.LeginonLogger()
		self.session = session
		self.is_upload = is_upload

	def getReferenceSession(self):
		if not self.is_upload:
			return super(ApCorrectorClient,self).getReferenceSession()
		else:
			return self.session
		
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
		version_number = 0
		while True:
			if version_number == 0:
				version_text = ''
			else:
				version_text = '_v%02d' % version_number
			new_name = new_imagefilename+version_text
			new_image_path = os.path.join(old_imagedata['session']['image path'],new_name+'.mrc')
			if not os.path.isfile(new_image_path):
				break
			else:
				version_number += 1
		apDisplay.printColor('New image filename is: %s' % new_name,'magenta')
		return new_name
