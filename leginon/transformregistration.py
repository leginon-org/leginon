#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

from pyami import correlator, peakfinder, ordereddict
import math
import numpy
import scipy.ndimage
import acquisition
import libCVwrapper
import align
import tiltcorrector

class Registration(object):
	'''
	Register image data objects or image arrays and
	return transformation matrix
	'''
	def __init__(self, node):
		self.node = node
		self.stagetiltcorrector = tiltcorrector.VirtualStageTilter(self.node)

	def determinetransformtypes(self, image1, image2):
		ttype = []
		alpha1 = image1['scope']['stage position']['a']
		alpha2 = image2['scope']['stage position']['a']
		if abs(alpha1 - alpha2)* 180.0 / 3.14159 > 2:
			ttype.append('tilt')
		try:
			beta1 = image1['scope']['stage position']['b']
			beta2 = image2['scope']['stage position']['b']
			if abs(beta1 - beta2) * 180.0 / 3.14159 > 2:
				ttype.append('rotate')
		except:
			pass
		return ttype

	def undoTilt(self,imagedata):
		# matrix and shift returned from tiltcorrector is that for image transform
		untilted_array,image2by2matrix,imageshiftvector =self.stagetiltcorrector.getZeroTiltArray(imagedata)
		affinematrix = numpy.matrix(numpy.identity(3, numpy.float))
		affinematrix[:2,:2] = image2by2matrix
		# Matrix for target transform is the inverse of that for image transform 
		# without shift because the target is defined relative to center of the image
		return untilted_array,affinematrix.I

	def registerImageData(self,image1,image2):
		# return target transform matrix
		transformtypes = self.determinetransformtypes(image1,image2)
		prepmatrix1 = numpy.matrix(numpy.identity(3, numpy.float))
		prepmatrix2 = numpy.matrix(numpy.identity(3, numpy.float))
		array1 = image1['image']
		array2 = image2['image']
		for ttype in transformtypes:
			if ttype == 'tilt':
				self.node.logger.info('Virtual untilt images before registering')
				array1, untiltmatrix1 = self.undoTilt(image1)
				array2, untiltmatrix2 = self.undoTilt(image2)
				prepmatrix1 *= untiltmatrix1 
				prepmatrix2 *= untiltmatrix2 
		matrix = self.register(array1, array2)
		finalmatrix = matrix * prepmatrix1 * prepmatrix2.I
		return finalmatrix
			
	def register(self, array1, array2):
		raise NotImplementedError('define "register" method in a subclass of Registration')

class IdentityRegistration(Registration):
	'''Fake registration.  Always returns identity matrix'''
	def register(self, array1, array2):
		return numpy.matrix(numpy.identity(3, numpy.float))

class CorrelationRegistration(Registration):
	'''Register using peak found in phase correlation image.  Good for shift'''
	def __init__(self, *args, **kwargs):
		super(CorrelationRegistration, self).__init__(*args, **kwargs)
		self.correlator = correlator.Correlator()
		self.peakfinder = peakfinder.PeakFinder()

	def register(self, array1, array2):
		self.correlator.setImage(0,array1)
		self.correlator.setImage(1,array2)
		corrimage = self.correlator.phaseCorrelate()
		corrimage = scipy.ndimage.gaussian_filter(corrimage,1)
		self.node.setImage(corrimage, 'Correlation')
		peak = self.peakfinder.subpixelPeak(newimage=corrimage)
		self.node.setTargets([(peak[1],peak[0])], 'Peak')
		shift = correlator.wrap_coord(peak, corrimage.shape)
		matrix = numpy.matrix(numpy.identity(3, numpy.float))
		matrix[2,0] = shift[0]
		matrix[2,1] = shift[1]
		return matrix

class KeyPointsRegistration(Registration):
	'''Register using key point detection.  Good for tilt and some rotation'''
	def register(self, array1, array2):
		# TO DO: Pass parameters
		for minsize in (160,40,10):
			minsize = int(minsize * (array1.shape[0]/4096.0))
			resultmatrix = libCVwrapper.MatchImages(array1, array2, minsize=minsize, maxsize=0.9,  WoB=True, BoW=True)
			if abs(resultmatrix[0,0]) > 0.01 or abs(resultmatrix[0,1]) > 0.01:
				break
		return numpy.matrix(resultmatrix)

class LogPolarRegistration(Registration):
	'''Register using log-polar transformation.  Good for rotation'''
	def register(self, array1, array2):
		result = align.findRotationScaleTranslation(array1, array2)
		rotation, scale, shift, rsvalue, value = result
		matrix = numpy.matrix(numpy.identity(3, numpy.float))
		matrix[0,0] = scale*math.cos(rotation)
		matrix[0,1] = -scale*math.sin(rotation)
		matrix[1,0] = scale*math.sin(rotation)
		matrix[1,1] = scale*math.cos(rotation)
		matrix[2,0] = shift[0]
		matrix[2,1] = shift[1]
		return matrix

