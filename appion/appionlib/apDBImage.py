#!/usr/bin/env python

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
