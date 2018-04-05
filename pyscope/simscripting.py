#!/usr/bin/env python
import os
import time
import math
import numpy
import random
from pyami import mrc
random.seed()

camsize = (2048,2048) # row,col

class SupportedCamera(object):
	def __init__(self,name):
		self.Name = name
		self.Height = camsize[0]
		self.Width = camsize[1]
		self.PixelSize = 1.4e-5
		self.is_inserted = False
		self.IsInserted = self.is_inserted

	def Insert(self):
		self.is_inserted = True

	def Retract(self):
		self.is_inserted = False

class CameraSingleAcquisition(object):
	def __init__(self):
		self.Camera = Camera()
		self.CameraSettings = CameraSettings()
		self.SupportedCameras = [SupportedCamera('BM-Falcon'),SupportedCamera('FEI_CAM')]
		self.IsActive = False

	def Acquire(self):
		while self.IsActive:
			print 'waiting for other acquisition to finish'
			time.sleep(0.2)
		self.IsActive = True
		time.sleep(0.5)
		scale=float(2**(self.CameraSettings.ReadoutArea))
		image_shape = (int(camsize[0]/scale),int(camsize[1]/scale))
		ar = self.getSyntheticImage(image_shape)
		image_obj = Image()
		image_obj.AsSafeArray = ar
		self.IsActive = False
		nframes = len(self.CameraSettings.DoseFractionsDefinition.frame_range_list)
		print 'movie nframes', nframes
		if nframes > 0:
			if not os.path.isdir(self.CameraSettings.PathToImageStorage):
				raise RuntimeError('Intermediate File Path Not exists.')
			file_path = os.path.join(self.CameraSettings.PathToImageStorage,self.CameraSettings.SubPathPattern+'.mrc')
			for i in range(nframes):
				if i == 0:
					mrc.write(ar,file_path)
				else:
					ar = self.getSyntheticImage(camsize)
					mrc.append(ar,file_path)
		return image_obj

	def getSyntheticImage(self,shape):
		mean = self.CameraSettings.ExposureTime * 1000.0
		sigma = 0.1 * mean
		image = numpy.random.normal(mean, sigma, shape)
		row_offset = random.randint(-shape[0]/8, shape[0]/8) + shape[0]/4
		column_offset = random.randint(-shape[1]/8, shape[1]/8) + shape[0]/4
		image[row_offset:row_offset+shape[0]/2,
		  column_offset:column_offset+shape[1]/2] *= 1.5
		image = numpy.asarray(image, dtype=numpy.uint16)
		return image

class Image(object):
	def __init__(self):
		self.MetaData = MetaData()

class MetaData(object):
	def __init__(self):
		self.BitsPerPixel = 16
		self.Binning = WidthHeight()
		self.ImageSize = WidthHeight()
		self.PixelValueToCameraCounts = 1
		self.ElectronCounted = False
		self.CountsToElectrons = 1

class WidthHeight(object):
	def __init__(self):
		self.Width = 1
		self.Height = 1

class Binning(WidthHeight):
	pass
	
class DoseFractionsDefinition(object):
	def __init__(self):
		self.frame_range_list = []

	def AddRange(self,fstart, fend):
		self.frame_range_list.append((fstart, fend))

	def Clear(self):
		self.frame_range_list = []

class CameraSettings(object):
	def __init__(self):
		self.ExposureTime = 1.0
		self.Binning = Binning()		
		self.PathToImageStorage = '/Users/acheng/testdata'
		self.SubPathPattern = 'frames'
		self.ReadoutArea = 0
		self.DoseFractionsDefinition = DoseFractionsDefinition()
		self.ElectronCounting = True
		self.base_time = 0.025

	def CalculateNumberOfFrames(self):
		print 'calculate',self.ExposureTime, self.base_time
		# rounding error. int(0.6/0.025) = 23. Multiply by 1000 resolves that.
		return int(self.ExposureTime*1000 / (self.base_time*1000))

class Camera(object):
	def __init__(self):
		self.Name = None

class Acquisitions(object):
	def __init__(self):
		self.CameraSingleAcquisition = CameraSingleAcquisition()

class Instrument(object):
	def __init__(self):
		self.Acquisitions = Acquisitions()

class Connection(object):
	def __init__(self):
		self.Instrument = Instrument()
