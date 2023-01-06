#!/usr/bin/python
import sys
import os
import glob
import math
import subprocess
from pyami import mrc,imagefun,fftfun
from leginon import leginondata,calibrationclient

class GctfEstimator(object):
	def __init__(self, gctfexe='gctfCurrent', dbids=[], ln_pattern='tmp'):
		self.count = 0
		self.gctfexe = gctfexe
		self.pcal = calibrationclient.CalibrationClient(None)
		self.ln_pattern = ln_pattern
		self.amp_contrast = 0.07 # amplitude contrast
		self.reset()
		if dbids:
			self.setImagesFromIds(dbids)
			self.setGlobalInputParams(self.images[0])

	def reset(self):
		self.images = []
		self.cleanUp()

	def addImage(self, imagedata):
		self.images.append(imagedata)

	def setImagesFromIds(self, dbids):
		for dbid in dbids:
			imagedata = leginondata.AcquisitionImageData().direct_query(dbid)
			self.addImage(imagedata)

	def setGlobalInputParams(self,imagedata):
		scope= imagedata['scope']
		self.ht = scope['high tension']
		mag = scope['magnification']
		tem = scope['tem']
		self.cs = tem['cs']
		self.nominal_defocus = scope['defocus']
		ccdcamera = imagedata['camera']['ccdcamera']
		pdata = leginondata.PixelSizeCalibrationData(magnification=mag,tem=tem, ccdcamera=ccdcamera).query(results=1)[0]
		self.pixelsize = pdata['pixelsize']*imagedata['camera']['binning']['x']

	def cleanUp(self):
		# clean up
		files = glob.glob('%s*.mrc' % (self.ln_pattern,))
		for f in files:
			os.remove(f)

	def writeTestMrc(self,i, a):
		mrc.write(a, '%s%03d.mrc' % (self.ln_pattern, i))

	def runACE(self, pixelsize, defocus, ht, amp_contrast, cs,path_pattern='test*'):
		defocusH = defocus*1.2
		cmd = "%s --apix %.5f --defL %.0f --defH %.0f --kV %d --Cs %.1f --ac %.3f %s.mrc" % (self.gctfexe, pixelsize*1e10, defocus*1e10, defocusH*1e10, int(ht/1000), cs*1e3, amp_contrast, path_pattern)
		print(cmd)
		proc = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE,)
		proc.stdin.write(cmd.encode('ascii'))
		proc.communicate()

	def getCTFResults(self):
		filepath = 'micrographs_all_gctf.star'
		from appionlib import starFile
		star = starFile.StarFile(filepath)
		star.read()
		dataBlock = star.getDataBlock("data_")
		loopDict  = dataBlock.getLoopDict() # returns a list with a dictionary for each line in the loop
		all_ctfvalues = []
		for i in range(len(loopDict)):
			bits = loopDict[i]
			ctfvalues = {
						'imagenum' : self.images[i].dbid,
						'defocus2' : float(bits['_rlnDefocusV'])*1e-10,
						'defocus1' : float(bits['_rlnDefocusU'])*1e-10,
						'angle_astigmatism' : float(bits['_rlnDefocusAngle']) + 90,  # see bug #4047 for astig conversion
						'amplitude_contrast' : self.amp_contrast,
						'do_EPA' : True,
						'defocusinit' : None,
						'cs' : self.cs,
						'volts' : self.ht,
						'do_local_refine' : False,
						'ctffind4_resolution' : float(bits['_rlnFinalResolution']),
						'extra_phase_shift' : 0.0
					}
			all_ctfvalues.append(ctfvalues)
		return all_ctfvalues	

	def saveBatchImages(self):
		avg_defocus = 0
		for i,imagedata in enumerate(self.images):
			print(imagedata['filename'])
			avg_defocus += imagedata['scope']['defocus']
			self.writeTestMrc(i, imagedata['image'])
		self.nominal_defocus = avg_defocus / len(self.images)

	def runImages(self):
		self.saveBatchImages()
		self.runACE(self.pixelsize, self.nominal_defocus, self.ht, self.amp_contrast, self.cs,self.ln_pattern+'*')
		ctfvalues = self.getCTFResults()
		print(ctfvalues)
		return ctfvalues

	def runOneImageData(self, imagedata):
		'''
		Run through ctf estimation of one image data and return its appion format ctfresult.
		'''
		self.reset()
		self.setGlobalInputParams(imagedata)
		self.addImage(imagedata)
		results = self.runImages()
		try:
			return results[0]
		except IndexError as e:
			raise RuntimeError('ctf estimation failed to produce result')

	def fakeRunOneImageData(self, imagedata):
		'''
		Read Ctf Results without really running. loop though 5 results in output.
		Used in simulator test.
		'''
		self.reset()
		self.setGlobalInputParams(imagedata)
		for i in range(5):
			self.addImage(imagedata)
		results = self.getCTFResults()
		result = results[self.count]
		self.count += 1
		if self.count >= len(results):
			self.count = 0
		return result

if __name__ == '__main__':
	#dbids = [5713064,5713066,5713068,5713071,5713073]
	app = GctfEstimator('gctfCurrent',dbids=dbids)
	#app.runImages()
	imagedata = leginondata.AcquisitionImageData().query(results=1)[0]
	app.runOneImageData(imagedata)
