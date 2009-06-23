#!/usr/bin/env python

'''
The TiltCorrector class implements the methods of the following paper:
Correction of autofocusing errors due to specimen tilt for automated
electron tomography.  Journal of Microscopy, Vol 211, Pt 2, August 2003,
pp. 179-185
It is useful if you need to cross correlate two images that are at
different beam tilts, and you are on a tilted specimen.

The VirtualStageTilter class is used to stretch images that were acquired
on a tilted stage so that they appear to be untilted.
'''

import numpy
import pyami.quietscipy
import scipy.ndimage
from pyami import arraystats, convolver, affine
import math
import leginondata

## defocus calibration matrix format:
##   x-row  y-row
##   x-col  y-col
## stage calibration matrix format:
##   xrow  yrow
##   xcol  ycol

#neil needs to changes here?

class TiltCorrector(object):
	def __init__(self, node):
		self.node = node
		## if tilts are below these thresholds, no need to correct
		self.alpha_threshold = 0.02
		self.bt_threshold = 0.000001
		gauss = convolver.gaussian_kernel(2.0)
		self.filter = convolver.Convolver(kernel=gauss)

	def affine_transform_matrix(self, btmatrix, stagematrix, btxy, alpha):
		'''
		create an affine transform matrix to correct a beam tilted and
		stage tilted image
		'''
		## calculate angle of tiltaxis with respect to image row axis
		tiltaxis = math.atan2(stagematrix[1,0],stagematrix[0,0])
	
		# normalize beam tilt calibration matrix
		knormx = (abs(btmatrix[0,0])+abs(btmatrix[1,0]))/2.0
		krx = btmatrix[0,0] / knormx
		kcx = btmatrix[1,0] / knormx
		knormy = (abs(btmatrix[0,1])+abs(btmatrix[1,1]))/2.0
		kry = btmatrix[0,1] / knormy
		kcy = btmatrix[1,1] / knormy
	
		## convert beamtilt to pixel displacement
		btr = krx * btxy[0] + kry * btxy[1]
		btc = kcx * btxy[0] + kcy * btxy[1]
	
		## create transform matrix
		mat = numpy.zeros((2,2), numpy.float32)
		mat[0,0] = 1 - btr * numpy.sin(tiltaxis)*numpy.sin(alpha)
		mat[0,1] =     btr * numpy.cos(tiltaxis)*numpy.sin(alpha)
		mat[1,0] =    -btc * numpy.sin(tiltaxis)*numpy.sin(alpha)
		mat[1,1] = 1 + btc * numpy.cos(tiltaxis)*numpy.sin(alpha)
		## inverted to calculate input coord from output coord
		mat = numpy.linalg.inv(mat)
		return mat
	
	def getMatrix(self, tem, cam, ht, mag, type):
		matdat = leginondata.MatrixCalibrationData()
		matdat['tem'] = tem
		matdat['ccdcamera'] = cam
		matdat['type'] = type
		matdat['magnification'] = mag
		matdat['high tension'] = ht
		caldatalist = self.node.research(datainstance=matdat, results=1)
		if caldatalist:
			return caldatalist[0]['matrix']
		else:
			excstr = 'No %s matrix for %s, %s, %seV, %sx' % (type, tem, cam, ht, mag)
			raise RuntimeError(excstr)

	def getStageMatrix(self, tem, cam, ht, mag):
		return self.getMatrix(tem, cam, ht, mag, 'stage position')
	
	def getBeamTiltMatrix(self, tem, cam, ht, mag):
		return self.getMatrix(tem, cam, ht, mag, 'defocus')

	def getImageShiftMatrix(self, tem, cam, ht, mag):
		return self.getMatrix(tem, cam, ht, mag, 'image shift')
	
	def getRotationCenter(self, tem, ht, mag):
		# XXX how do I know my node has a btcalclient?
		beam_tilt = self.node.btcalclient.retrieveRotationCenter(tem, ht, mag)
		return beam_tilt

	def itransform(self, shift, scope, camera):
		'''
		Copy of calibrationclient method
		Calculate a pixel vector from an image center which 
		represents the given parameter shift.
		'''
		mag = scope['magnification']
		ht = scope['high tension']
		binx = camera['binning']['x']
		biny = camera['binning']['y']
		par = 'image shift'
		tem = scope['tem']
		cam = camera['ccdcamera']
		newshift = dict(shift)
		vect = (newshift['x'], newshift['y'])
		matrix = self.getImageShiftMatrix(tem, cam, ht, mag)
		matrix = numpy.linalg.inv(matrix)

		pixvect = numpy.dot(matrix, vect)
		pixvect = pixvect / (biny, binx)
		return {'row':pixvect[0], 'col':pixvect[1]}

	def edge_mean(self, im):
		m1 = arraystats.mean(im[0])
		m2 = arraystats.mean(im[-1])
		m3 = arraystats.mean(im[:,0])
		m4 = arraystats.mean(im[:,-1])
		m = (m1+m2+m3+m4) / 4.0
		return m
	
	def correct_tilt(self, imagedata):
		'''
		takes imagedata and calculates a corrected image
		'''
		## from imagedata
		im = imagedata['image']
		alpha = imagedata['scope']['stage position']['a']
		if abs(alpha) < self.alpha_threshold:
			return False
		beamtilt = imagedata['scope']['beam tilt']
		ht = imagedata['scope']['high tension']
		mag = imagedata['scope']['magnification']
		tem = imagedata['scope']['tem']
		cam = imagedata['camera']['ccdcamera']
	
		## from DB
		tiltcenter = self.getRotationCenter(tem, ht, mag)
		# if no tilt center, then cannot do this
		if tiltcenter is None:
			self.node.logger.info('not correcting tilted images, no rotation center found')
			return False
		tx = beamtilt['x'] - tiltcenter['x']
		ty = beamtilt['y'] - tiltcenter['y']
		bt = (tx,ty)
		if max(abs(bt[0]),abs(bt[1])) < self.bt_threshold:
			# don't transform if beam tilt is small enough
			return False

		alphadeg = alpha * 180 / 3.14159
		self.node.logger.info('correcting tilts, stage: %s deg beam: %s,%s' % (alphadeg, tx, ty))

		defocusmatrix = self.getBeamTiltMatrix(tem, cam, ht, mag)
		stagematrix = self.getStageMatrix(tem, cam, ht, mag)

		mat = self.affine_transform_matrix(defocusmatrix, stagematrix, bt, alpha)
		scope = imagedata['scope']
		camera = imagedata['camera']
		## calculate pixel shift to get to image shift 0,0
		imageshift = dict(scope['image shift'])
		#imageshift['x'] *= -1
		#imageshift['y'] *= -1
		pixelshift = self.itransform(imageshift, scope, camera)
		pixelshift = (pixelshift['row'], pixelshift['col'])
		offset = affine.affine_transform_offset(im.shape, im.shape, mat, pixelshift)
		mean=self.edge_mean(im)
		im2 = scipy.ndimage.affine_transform(im, mat, offset=offset, mode='constant', cval=mean)

		#im2 = self.filter.convolve(im2)
		imagedata['image'] = im2
		return True

class VirtualStageTilter(object):
	def __init__(self, node):
		self.node = node
		self.alpha_threshold = 0.02

	def maketrans(self, x1, y1, x2, y2, x3, y3, u1, v1, u2, v2, u3, v3):
		'''
		A method to create an affine transform matrix without thinking too hard.
		Stolen from Craigs libcv code.
		Given three points x,y, and their transformed points u,v, create
		the transform between them (or is it inverse transform?)

		Some day when we get smart, we can find a way to generate the affine
		trans matrix directly from the stage calibration matrix without the
		intermediate step of creating some fake points like this.
		'''
		det = 1.0/(u1*(v2-v3)-v1*(u2-u3)+(u2*v3-u3*v2))
		IT = numpy.zeros((3,3), numpy.float32)
		IT[0][0] = ((v2-v3)*x1+(v3-v1)*x2+(v1-v2)*x3)*det
		IT[0][1] = ((v2-v3)*y1+(v3-v1)*y2+(v1-v2)*y3)*det
		IT[0][2] = 0
		IT[1][0] = ((u3-u2)*x1+(u1-u3)*x2+(u2-u1)*x3)*det
		IT[1][1] = ((u3-u2)*y1+(u1-u3)*y2+(u2-u1)*y3)*det
		IT[1][2] = 0
		IT[2][0] = ((u2*v3-u3*v2)*x1+(u3*v1-u1*v3)*x2+(u1*v2-u2*v1)*x3)*det
		IT[2][1] = ((u2*v3-u3*v2)*y1+(u3*v1-u1*v3)*y2+(u1*v2-u2*v1)*y3)*det
		IT[2][2] = 1
		return IT

	def affine_transform_matrix(self, stagematrix, alpha):
		'''
		create an affine transform matrix that will simulate a stage tilt
		'''
		## calculate stretch factor due to alpha tilt
		stretch = 1.0 / numpy.cos(alpha)

		## calculate angle of tiltaxis with respect to image row axis
		tiltaxis = math.atan2(stagematrix[1,0],stagematrix[0,0])

		## pixel vector for x move
		xpixel = self.stageToPixel(stagematrix, 1.0, 0.0)
		ypixel1 = self.stageToPixel(stagematrix, 0.0, 1.0)
		ypixel2 = stretch*ypixel1[0], stretch*ypixel1[1]
		
		it = self.maketrans(0,0,xpixel[0],xpixel[1],ypixel1[0],ypixel1[1],0,0,xpixel[0],xpixel[1],ypixel2[0],ypixel2[1])

		## create transform matrix
		mat = it[:2,:2]

		## inverted to calculate input coord from output coord
		#mat = numpy.linalg.inv(mat)
		return mat

	def stageToPixel(self, matrix, x, y):
		inverse_matrix = numpy.linalg.inv(matrix)
		position_vector = numpy.array((x, y))
		pixel = numpy.dot(inverse_matrix, position_vector)
		return pixel
	
	## calculation of offset for affine transform
	def affine_transform_offset(self, shape, affine_matrix, imageshift):
		'''
		calculation of affine transform offset
		for now we assume center of image
		'''
		carray = numpy.array(shape, numpy.float32)
		carray.shape = (2,)
		carray = carray / 2.0

		carray = carray + imageshift

		carray2 = numpy.dot(affine_matrix, carray)
		imageshift2 = numpy.dot(affine_matrix, carray)

		offset = carray - carray2
		return offset

	def getMatrix(self, tem, cam, ht, mag, type):
		matdat = leginondata.MatrixCalibrationData()
		matdat['tem'] = tem
		matdat['ccdcamera'] = cam
		matdat['type'] = type
		matdat['magnification'] = mag
		matdat['high tension'] = ht
		caldatalist = self.node.research(datainstance=matdat, results=1)
		if caldatalist:
			return caldatalist[0]['matrix']
		else:
			excstr = 'No %s matrix for %s, %s, %seV, %sx' % (type, tem, cam, ht, mag)
			raise RuntimeError(excstr)

	def getStageMatrix(self, tem, cam, ht, mag):
		try:
			matrix = self.getMatrix(tem, cam, ht, mag, 'stage position')
		except RuntimeError, estr:
			try:
				self.node.logger.warning(estr)
			except:
				print estr
			matrix = self.makeFakeStageMatrix(tem, cam, mag)
		return matrix	

	def makeFakeStageMatrix(self, tem, cam, mag):
		q = leginondata.PixelSizeCalibrationData(tem=tem, ccdcamera=cam, magnification=mag)
		results = q.query(results=1)
		if results:
			pixelsize=results[0]['pixelsize']
		else:
			pixelsize= 1.0/mag
		matrixlist = map((lambda x:x*pixelsize), [1,0,0,1])
		stagematrix = numpy.array(matrixlist)
		stagematrix = stagematrix.reshape((2,2))
		estr = 'Use fake stage position matrix to stretch the image'
		try:
			self.node.logger.warning(estr)
		except:
			print estr
		return stagematrix
	
	def getImageShiftMatrix(self, tem, cam, ht, mag):
		return self.getMatrix(tem, cam, ht, mag, 'image shift')
	
	def itransform(self, shift, scope, camera):
		'''
		Copy of calibrationclient method
		Calculate a pixel vector from an image center which 
		represents the given parameter shift.
		'''
		mag = scope['magnification']
		ht = scope['high tension']
		binx = camera['binning']['x']
		biny = camera['binning']['y']
		par = 'image shift'
		tem = scope['tem']
		cam = camera['ccdcamera']
		newshift = dict(shift)
		vect = (newshift['x'], newshift['y'])
		matrix = self.getImageShiftMatrix(tem, cam, ht, mag)
		matrix = numpy.linalg.inv(matrix)

		pixvect = numpy.dot(matrix, vect)
		pixvect = pixvect / (biny, binx)
		return {'row':pixvect[0], 'col':pixvect[1]}

	def edge_mean(self, im):
		m1 = arraystats.mean(im[0])
		m2 = arraystats.mean(im[-1])
		m3 = arraystats.mean(im[:,0])
		m4 = arraystats.mean(im[:,-1])
		m = (m1+m2+m3+m4) / 4.0
		return m
	
	def getZeroTiltArray(self, imagedata):
		'''
		takes imagedata and calculates a corrected image
		'''
		## from imagedata
		im = imagedata['image']
		alpha = imagedata['scope']['stage position']['a']
		ht = imagedata['scope']['high tension']
		mag = imagedata['scope']['magnification']
		tem = imagedata['scope']['tem']
		cam = imagedata['camera']['ccdcamera']

		if abs(alpha) < self.alpha_threshold:
			return None
		stagematrix = self.getStageMatrix(tem, cam, ht, mag)
		mat = self.affine_transform_matrix(stagematrix, alpha)
		scope = imagedata['scope']
		camera = imagedata['camera']
		## calculate pixel shift to get to image shift 0,0
		imageshift = dict(scope['image shift'])
		#pixelshift = self.itransform(imageshift, scope, camera)
		#pixelshift = (pixelshift['row'], pixelshift['col'])
		pixelshift = (0.0, 0.0)
		offset = self.affine_transform_offset(im.shape, mat, pixelshift)
		mean=self.edge_mean(im)
		im2 = scipy.ndimage.affine_transform(im, mat, offset=offset, mode='constant', cval=mean)
		return im2

	def undo_tilt(self, imagedata):
		im2 = self.getZeroTiltArray(imagedata)
		if im2 is None:
			return False
		imagedata['image'] = im2
		try:
			self.node.logger.info('image stretched to reverse alpha tilt')
		except:
			# print the same when GUI not exists
			print 'image stretched to reverse alpha tilt'
		return True

