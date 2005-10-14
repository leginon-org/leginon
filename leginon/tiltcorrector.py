#!/usr/bin/env python

import numarray
import numarray.nd_image
import numarray.linear_algebra
import imagefun
import math

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
		self.alpha_threshold = 0.0001
		self.bt_threshold = 0.0001

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
	def affine_transform_offset(self, shape, affine_matrix):
		'''
		calculation of affine transform offset
		for now we assume center of image
		'''
		carray = numarray.array(shape, numarray.Float32)
		carray.shape = (2,)
		carray = carray / 2.0
		carray2 = numarray.matrixmultiply(affine_matrix, carray)
		offset = carray - carray2
		return offset

	def getStageMatrix(self, tem, cam, ht, mag):
		matdat = data.MatrixCalibrationData()
		matdat['tem'] = tem
		matdat['ccdcamera'] = cam
		matdat['type'] = 'stage position'
		matdat['magnification'] = mag
		matdat['high tension'] = ht
		caldatalist = self.node.research(datainstance=matdat, results=1)
		if caldatalist:
			return caldatalist[0]['matrix']
		else:
			excstr = 'No stage matrix for %s, %s, %seV, %sx' % (tem, cam, ht, mag)
			raise RuntimeError(excstr)
	
	def getBeamTiltMatrix(self, tem, cam, ht, mag):
		matdat = data.MatrixCalibrationData()
		matdat['tem'] = tem
		matdat['ccdcamera'] = cam
		matdat['type'] = 'defocus'
		matdat['magnification'] = mag
		matdat['high tension'] = ht
		caldatalist = self.node.research(datainstance=matdat, results=1)
		if caldatalist:
			return caldatalist[0]['matrix']
		else:
			excstr = 'No defocus matrix for %s, %s, %seV, %sx' % (tem, cam, ht, mag)
			raise RuntimeError(excstr)
	
	def getRotationCenter(self, tem, cam, ht, mag):
		rotdat = data.RotationCenterData()
		rotdat['tem'] = tem
		rotdat['ccdcamera'] = cam
		rotdat['magnification'] = mag
		rotdat['high tension'] = ht
		caldatalist = self.node.research(datainstance=rotdat, results=1)
		if caldatalist:
			return caldatalist[0]['beam tilt']
		else:
			excstr = 'No rotation center for %s, %s, %seV, %sx' % (tem, cam, ht, mag)
			raise RuntimeError(excstr)
	
	def correct_tilt(imagedata):
		'''
		takes imagedata and calculates a corrected image
		'''
		## from imagedata
		im = imagedata['image']
		alpha = imagedata'scope']['stage position']['a']
		if abs(alpha) < self.alpha_threshold:
			return
		beamtilt = imagedata['scope']['beam tilt']
		ht = imagedata['scope']['high tension']
		mag = imagedata['scope']'magnification']
		tem = imagedata['scope']['tem']
		cam = imagedata['scope']['ccdcamera']
	
		## from DB
		tiltcenter = self.getRotationCenter(tem, cam, ht, mag)
		tx = beamtilt['x'] - tiltcenter['x']
		ty = beamtilt['y'] - tiltcenter['y']
		bt = {'x': tx, 'y': ty}
		if max(abs(bt['x']),abs(bt['y'])) < self.bt_threshold:
			# don't transform if beam tilt is small enough
			return

		defocusmatrix = self.getBeamTiltMatrix(tem, cam, ht, mag)
		stagematrix = self.getStageMatrix(tem, cam, ht, mag)

		mat = self.affine_transform_matrix(defocusmatrix, stagematrix, bt, alpha)
		offset = self.affine_transform_offset(im.shape, mat)
		im2 = numarray.nd_image.affine_transform(im, mat, offset=offset)
		imagedata['image'] = im2
		return
