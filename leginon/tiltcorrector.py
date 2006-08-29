#!/usr/bin/env python

import numarray
import numarray.nd_image
import numarray.linear_algebra
import imagefun
import math
import data
import convolver

## defocus calibration matrix format:
##   x-row  y-row
##   x-col  y-col
## stage calibration matrix format:
##   xrow  yrow
##   xcol  ycol

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
		mat = numarray.zeros((2,2), numarray.Float32)
		mat[0,0] = 1 - btr * numarray.sin(tiltaxis)*numarray.sin(alpha)
		mat[0,1] =     btr * numarray.cos(tiltaxis)*numarray.sin(alpha)
		mat[1,0] =    -btc * numarray.sin(tiltaxis)*numarray.sin(alpha)
		mat[1,1] = 1 + btc * numarray.cos(tiltaxis)*numarray.sin(alpha)
		## inverted to calculate input coord from output coord
		mat = numarray.linear_algebra.inverse(mat)
		return mat
	
	## calculation of offset for affine transform
	def affine_transform_offset(self, shape, affine_matrix, imageshift):
		'''
		calculation of affine transform offset
		for now we assume center of image
		'''
		carray = numarray.array(shape, numarray.Float32)
		carray.shape = (2,)
		carray = carray / 2.0

		carray = carray + imageshift

		carray2 = numarray.matrixmultiply(affine_matrix, carray)
		imageshift2 = numarray.matrixmultiply(affine_matrix, carray)

		offset = carray - carray2
		return offset

	def getMatrix(self, tem, cam, ht, mag, type):
		matdat = data.MatrixCalibrationData()
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
		matrix = numarray.linear_algebra.inverse(matrix)

		pixvect = numarray.matrixmultiply(matrix, vect)
		pixvect = pixvect / (biny, binx)
		return {'row':pixvect[0], 'col':pixvect[1]}

	def edge_mean(self, im):
		m1 = imagefun.mean(im[0])
		m2 = imagefun.mean(im[-1])
		m3 = imagefun.mean(im[:,0])
		m4 = imagefun.mean(im[:,-1])
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
			return
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
			return
		tx = beamtilt['x'] - tiltcenter['x']
		ty = beamtilt['y'] - tiltcenter['y']
		bt = (tx,ty)
		if max(abs(bt[0]),abs(bt[1])) < self.bt_threshold:
			# don't transform if beam tilt is small enough
			return

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
		offset = self.affine_transform_offset(im.shape, mat, pixelshift)
		mean=self.edge_mean(im)
		im2 = numarray.nd_image.affine_transform(im, mat, offset=offset, mode='constant', cval=mean)

		#im2 = self.filter.convolve(im2)
		imagedata['image'] = im2
		return
