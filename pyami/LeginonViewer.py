#!/usr/bin/env python

from Tkinter import *
from ImageViewer import ImageViewer
from glob import glob

root = Tk()

jim = ImageViewer(root)
jim.pack()

filename = 'test1.mrc'
viewer = jim

def mrc_to_numeric(filename):
	f = open(filename, 'rb')
	mrchdr = MrcHeader(f)
	mrcdat = MrcData()
	mrcdat.useheader(mrchdr)
	mrcdat.fromfile(f)
	f.close()
	data = mrcdat.toNumeric()
	return data

### read mrc image into Numeric array

def data_photo(data):
	## create a photo image and plug it into the viewer
	size = data.shape
	print "SHAPE", size
	photoim = NumericPhotoImage('L',size)
	photoim.use_array(data)
	photoim.paste_array()
	return photoim

def display_photo(viewer,photo,size):
	viewer.create_image(photo, size)

#viewer = jim
#filename = 'test1.mrc'

def display_mrc(viewer,filename):
	### need to figure out why this needs to be global
	global photoim
	data = mrc_to_numeric(filename)
	photoim = data_photo(data)
	display_photo(viewer, photoim, data.shape)

def get_latest(pattern):
	filenames = glob(pattern)
	for name in filenames:
		pass


while 1:
	display_mrc(jim, 'test1.mrc')
	root.update()
	root.after(500)
	display_mrc(jim, 'test2.mrc')
	root.update()
	root.after(500)
