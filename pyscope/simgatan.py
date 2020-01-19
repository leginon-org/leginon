#!/usr/bin/env python
import time
import numpy
import random
random.seed()

class SimGatan(object):
	def __init__(self):
		print 'init'
		self.filter_functions = {}
		self.inserted = False
		self.readmode = 1
		self.exposure_type= 'unprocessed'

	def GetDMVersion(self):
		return 40303

	def GetNumberOfCameras(self):
		return 1

	def GetPluginVersion(self):
		return 50000

	def IsCameraInserted(self, camera):
		return self.inserted

	def InsertCamera(self, camera, state):
		self.inserted = state

	def SetReadMode(self, mode, scaling=1.0):
		pass

	def SetShutterNormallyClosed(self, camera, shutter):
		pass

	def SetK2Parameters(self, readMode, scaling, hardwareProc, doseFrac, frameTime, alignFrames, saveFrames, filt='', useCds=False):
		self.save_frames = saveFrames
		print '**K2 Parameters**'
		print 'readMode', readMode
		print 'scaling', scaling
		print 'hardwareProc', hardwareProc
		print 'doseFrac', doseFrac
		print 'frameTime', frameTime
		print 'alignFrames', alignFrames
		print 'saveFrames', saveFrames
		print 'filt', filt

	def setNumGrabSum(self, earlyReturnFrameCount, earlyReturnRamGrabs):
		# pack RamGrabs and earlyReturnFrameCount in one double
		self.num_grab_sum = (2**16) * earlyReturnRamGrabs + earlyReturnFrameCount
		print 'set num_grab_sum', self.num_grab_sum

	def getNumGrabSum(self):
		return self.num_grab_sum

	def SetupFileSaving(self, rotationFlip, dirname, rootname, filePerImage, doEarlyReturn, earlyReturnFrameCount=0,earlyReturnRamGrabs=0, lzwtiff=False):
		pixelSize = 1.0
		self.setNumGrabSum(earlyReturnFrameCount, earlyReturnRamGrabs)
		if self.save_frames and (doEarlyReturn or lzwtiff):
			# early return flag
			flag = 128*int(doEarlyReturn) + 8*int(lzwtiff)
			numGrabSum = self.getNumGrabSum()
			# set values to pass
		else:
			flag = None
		print '**FileSaving**'
		print 'rotationFlip', rotationFlip
		print 'flag', flag
		print 'filePerImage', filePerImage
		print 'dirname', dirname
		print 'rootname', rootname

	def GetFileSaveResult(self):
		pass

	def SelectCamera(self, cameraid):
		print 'SelectCamera on %d' % cameraid

	def UpdateK2HardwareDarkReference(self, cameraid):
		print 'UpdateK2HardwareDarkReference on %d' % cameraid

	def GetEnergyFilter(self):
		return -1.0

	def SetEnergyFilter(self, value):
		return -1.0

	def GetEnergyFilterWidth(self):
		return -1.0

	def SetEnergyFilterWidth(self, value):
		return -1.0

	def GetEnergyFilterOffset(self):
		return 0.0

	def SetEnergyFilterOffset(self, value):
		return -1.0

	def AlignEnergyFilterZeroLossPeak(self):
		print 'AlignEnergeFileterZeroLossPeak'
		time.sleep(2)

	def PrepareDarkReference(self, cameraid):
		return 0

	def GetImage(self, processing, height, width, binning, top, left, bottom, right, exposure, corrections, shutter=0, shutterDelay=0.0):
		self.exposure_type= processing
		self.exposure_time = exposure/1000.0
		print '**Acquire Parameters**'
		print 'processing', processing
		print 'image shape (%d, %d)' % (height, width)
		print 'acquire binning', binning
		print 'boundary rows: %d:%d, cols: %d:%d' % (top,bottom,left,right)
		print 'exposure %s' % (exposure,)
		print 'corrections %d' % (corrections,)
		print 'shutter id %d' % (shutter,)
		return self.getSyntheticImage((height, width))

	def getSyntheticImage(self,shape):
		dark_mean = 1.0
		bright_scale = 10
		if self.exposure_type != 'dark':
			mean = self.exposure_time * 1000.0 *bright_scale + dark_mean
			sigma = 0.01 * mean
		else:
			mean = dark_mean
			sigma = 0.1 * mean
		image = numpy.random.normal(mean, sigma, shape)
		if self.exposure_type != 'dark':
			row_offset = random.randint(-shape[0]/16, shape[0]/16) + shape[0]/4
			column_offset = random.randint(-shape[1]/16, shape[1]/16) + shape[0]/4
			image[row_offset:row_offset+shape[0]/2,
				column_offset:column_offset+shape[1]/2] += 0.5 * mean
		image = numpy.asarray(image, dtype=numpy.uint16)
		return image

def test1():
	g = SimGatan()
	print g
	ver = g.GetDMVersion()
	print 'Version', ver
	raw_input('enter to quit.')

if __name__ == '__main__':
	test1()
