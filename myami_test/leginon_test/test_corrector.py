#!/usr/bin/env python
import unittest
import leginon.correctorclient
import leginon.leginondata
import pyami.imagefun
import numpy
import time

class Logger(object):
	def __init__(self):
		pass

	def info(self,msg):
		print 'INFO: %s' % msg

	def warning(self,msg):
		print 'WARNING: %s' % msg

	def error(self,msg):
		print 'ERROR: %s' % msg

	def debug(self,msg):
		print 'DEBUG: %s' % msg

class TestCorrector(unittest.TestCase):
	def setUp(self):
		self.correct_error = 'No'
		self._setCorrectorClient()

	def _setCorrectorClient(self):
		image_id = int(raw_input('Enter image id to test: '))
		self.c_client = leginon.correctorclient.CorrectorClient()
		self.c_client.logger = Logger()
		print('image_id=%d' % (image_id))
		try:
			r = leginon.leginondata.AcquisitionImageData().direct_query(image_id)
			if not r:
				self.correct_error='image not found'
				return False
			self.imagedata = leginon.leginondata.AcquisitionImageData(initializer=r)
			self.imagedata['image'] = r['image']
		except Exception, e:
			raise
			self.correct_error = e
			return False
		return True

	def testCorrectorPlan(self):
		self.correct_error = 'No'
		self.assertTrue(self._testCorrectorPlan(),msg=self.correct_error)

	def _testCorrectorPlan(self):
		'''
		Testing corrector plan related correction in CorrectorClient.CorrrectCameraImage
		'''
		# each test is its own instance. Therefore, need these again.
		cameradata = self.imagedata['camera']
		t0 = time.time()
		plandata = self.c_client.researchCorrectorPlan(cameradata)
		print('research corrector plan took %.2f seconds' % (time.time()-t0))
		t0 = time.time()
		plandict =  self.c_client.formatCorrectorPlan(plandata)
		print(plandict)
		print('format corrector plan took %.2f seconds' % (time.time()-t0))
		# Escape if image is None
		if self.imagedata.imageshape() is None or self.c_client.isFakeImageObj(self.imagedata):
			# in-place change.  Nothing to return
			print('fake image requires no bad pixel fixing')
			print('****')
			return True
		print('array shape %dx%d' % self.imagedata['image'].shape)
		# correct plan
		if plandict is not None:
			t0 = time.time()
			self.c_client.fixBadPixels(self.imagedata['image'], plandict)
			print('bad pixel fixing took %.2f seconds' % (time.time()-t0))
		# limit intensity range
		t0 = time.time()
		pixelmax = self.imagedata['camera']['ccdcamera']['pixelmax']
		self.imagedata['image'] = numpy.asarray(self.imagedata['image'], numpy.float32)
		print('conversion to float32 took %.2f seconds' % (time.time()-t0))
		if pixelmax is not None:
			t0 = time.time()
			self.imagedata['image'] = numpy.clip(self.imagedata['image'], 0, pixelmax)
			print('image clipping took %.2f seconds' % (time.time()-t0))
		if plandict is not None and plandict['despike']:
			t0 = time.time()
			nsize = plan['despike size']
			thresh = plan['despike threshold']
			pyami.imagefun.despike(self.imagedata['image'], nsize, thresh)
			print('despike took %.2f seconds' % (time.time()-t0))
		print('****')
		return True

	def testNormalizeImage(self):
		self.correct_error = 'No'
		self.assertTrue(self._testNormalizeImage(),msg=self.correct_error)

	def _testNormalizeImage(self):
		t0 = time.time()
		channel = 0
		cameradata = self.imagedata['camera']
		scopedata = self.imagedata['scope']
		dark = self.c_client.retrieveCorrectorImageData('dark', scopedata, cameradata, channel)
		print('retrieve dark image took %.2f seconds' % (time.time()-t0))
		t0 = time.time()
		norm = self.c_client.retrieveCorrectorImageData('norm', scopedata, cameradata, channel)
		print('retrieve norm image took %.2f seconds' % (time.time()-t0))
		if norm is None:
			self.c_client.logger.warning('Cannot find references, image will not be normalized')
			return True
		t0 = time.time()
		rawarray = self.imagedata['image']
		print('read imagedata image took %.2f seconds' % (time.time()-t0))
		if not self.c_client.isFakeImageObj(self.imagedata):
			t0 = time.time()
			normarray = norm['image']
			print('link normarry took %.2f seconds' % (time.time()-t0))
			if dark:
				t0 = time.time()
				darkarray = self.c_client.prepareDark(dark, self.imagedata)
				print('prepare dose-matched dark image took %.2f seconds' % (time.time()-t0))
			else:
				darkarray = numpy.zeros(normarray.shape)
			t0 = time.time()
			r = self.c_client.normalizeImageArray(rawarray,darkarray,normarray, 'GatanK2' in cameradata['ccdcamera']['name'])
			print('doing array normalization took %.2f seconds' % (time.time()-t0))
		else:
			# normalize the fake array, too.
			fake_dark = numpy.zeros((8,8))
			fake_norm = numpy.ones((8,8))
			r = self.c_client.normalizeImageArray(rawarray,fake_dark,fake_norm, 'GatanK2' in cameradata['ccdcamera']['name'])
			print('doing fake 8x8 array normalization took %.2f seconds' % (time.time()-t0))
		t0 = time.time()
		self.imagedata['image'] = r
		self.imagedata['dark'] = dark
		self.imagedata['bright'] = norm['bright']
		self.imagedata['norm'] = norm
		self.imagedata['correction channel'] = channel
		print('assign final imagedata values took %.2f seconds' % (time.time()-t0))
		print('****')
		return True

	def runTest(self):
		#self.testCorrectorClient()
		self.testRetrieveCorrectorPlan()
		#self.testCorrectImage()

def runTestCases():
	'''
	method to be called from module that need to catch and handle the exception.
	'''
	t=TestCorrector()
	t.runTest()

if __name__ == '__main__':
	unittest.main()
