#!/usr/bin/env python

import leginondata
import numpy
from pyami import mrc
import sys
import os


def getImages(session_name):
	ses = leginondata.SessionData(name=session_name)
	qim = leginondata.AcquisitionImageData(session=ses)
	images = qim.query()
	return images

def asdf(a, b, c):
	return a + b + c
	#return str(a) + str(b) + str(c)

def readImage(im):
		path = im['session']['image path']
		filename = im['filename'] + '.mrc'
		fullname = os.path.join(path, filename)
		a = mrc.read(fullname)
		return a

def writeTemp(imdata, newarray):
		path = imdata['session']['image path']
		filename = imdata['filename'] + '.mrc'
		tmppath = os.path.split(path)[:-1] + ('tmp',)
		tmppath = os.path.join(*tmppath)
		fullname = os.path.join(tmppath, filename)
		mrc.write(newarray, fullname)

def run(images):
	for im in images:
		corexp = im['camera']['exposure time']
		corframes = numpy.floor(corexp * 0.025)

		dark = im['dark']
		norm = im['norm']

		if dark is None:
			print 'Uncorrected: ', im['filename']
			continue

		darkexp = dark['camera']['exposure time']
		darkframes = numpy.floor(darkexp * 0.025)

		if darkframes == corframes:
			continue

		corrected = readImage(im)
		dark = readImage(dark)
		norm = readImage(norm)

		# norm * (raw - dark)

		print 'correcting'
		corshape = corrected.shape
		if norm.shape != corshape or dark.shape != corshape:
			print 'shape mismatch:'
			print 'corrected', corshape
			print 'norm', norm.shape
			print 'dark', dark.shape
			continue
		raw = corrected / norm + dark
		newdark = dark / darkframes * corframes
		final = (raw - newdark) * norm
	
		print 'writing'
		writeTemp(im, final)
		print 'done'

	print 'all done'


if __name__ == '__main__':
	sname = sys.argv[1]
	images = getImages(sname)
	run(images)
