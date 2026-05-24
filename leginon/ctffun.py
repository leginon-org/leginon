import os
import time
import subprocess
from leginon import calibrationclient
from pyami import gctffindfun

class GctffindClient(object):
	def __init__(self, node):
		self.acename = 'gctffind'
		self.aceexe = 'gctffind'
		self.node = node
		self.logger = node.logger

	def runOneImageData(self, imagedata):
		return self.runFromImageData(imagedata)

	def runFromImageData(self, imagedata, amp_contrast=0.07, fieldsize=512, phase_search=(0,0)):
		mrcpath=os.path.join(imagedata['session']['image path'],imagedata['filename']+'.mrc')
		return self._runMrcPathWithImageData(mrcpath, imagedata, amp_contrast, fieldsize, phase_search)

	def runArrayWithImageData(self, a, imagedata, amp_contrast=0.07, fieldsize=512, phase_search=(0,0)):
		mrcpath='temp.mrc'
		return self._runMrcPathWithImageData(mrcpath, imagedata, amp_contrast, fieldsize, phase_search)

	def _runMrcPathWithImageData(self, mrcpath, imagedata, amp_contrast=0.07, fieldsize=512, phase_search=(0,0)):
		pcalclient = calibrationclient.PixelSizeCalibrationClient(self.node)
		psize = imagedata_pixel_size = pcalclient.getImagePixelSize(imagedata)['x']
		inputparams={}
		inputparams['input']=mrcpath
		inputparams['pow_output']='%s-pow.mrc' % imagedata['filename']
		inputparams['ctf_output']='%s.mrc.ctf.txt' % imagedata['filename']
		inputparams['cs']=imagedata['scope']['tem']['cs']*1000 # in mm
		inputparams['volts']=imagedata['scope']['high tension'] # in volts
		inputparams['apix']=psize*1e10 # in angstrum
		inputparams['fieldsize'] = fieldsize
		inputparams['amplitude_contrast'] = amp_contrast #use appion ctfvalues key name
		if min(phase_search) < max(phase_search):
			inputparams['min_phase_shift'] = min(phase_search) # in degrees
			inputparams['max_phase_shift'] = max(phase_search)
		cmd = self.makeCommand(inputparams)
		self.logger.info("run %s on %s" % (self.acename, imagedata['filename']))
		self.run(cmd, inputparams['ctf_output'])
		self.ctfvalues = self.readResult(inputparams['ctf_output'])
		self.ctfvalues.update(inputparams)
		try:
			if 'temp' not in inputparams['ctf_output']:
				# Only keep temp output for diagnosis until the next run that overwrites
				# the results.  
				os.remove(inputparams['ctf_output'])
				os.remove(inputparams['pow_output'])
		except FileNotFoundError as e:
			print('Failed: %s' % e)
			# readResult will handle error if ctf_output is not produced.
			pass
		return self.ctfvalues

	def makeCommand(self, inputparams):
		if 'astig' not in inputparams.keys():
			inputparams['astig'] = 0.1 # generous astig allowed for diverse value.
		return gctffindfun.makeCommand(self.aceexe, inputparams)

	def readResult(self, ctf_output):
		return gctffindfun.readResult(ctf_output)

	def run(self, commandline, ctf_output):
		### run ace
		print(commandline)
		try:
			gctffindfun.run(commandline, self.acename, ctf_output)
		except Exception as e:
			self.logger.warning("%s did not run" % self.acename)

