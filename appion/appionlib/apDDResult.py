#!/usr/bin/env python
import os
import math
import glob
from appionlib import appiondata
from appionlib import apProject
from appionlib import apDatabase
from leginon import leginondata
from leginon import ddinfo

class DDResults(object):
	'''
	A stand alone class that contains functions for getting DD frame alignment
	results.
	'''
	def __init__(self, imagedata):
		self.image = imagedata
		if self.image['camera']['align frames'] is False:
			raise ValueError('Not an aligned image')
		apProject.setDBfromProjectId(apProject.getProjectIdFromImageData(self.image))

	def getAlignSiblings(self):
		pairdata = self.getAlignImagePairData()
		siblings = [pairdata['source'],]
		ddrun = pairdata['ddstackrun']
		q = appiondata.ApDDAlignImagePairData(ddstackrun=ddrun,source=pairdata['source'])
		results = q.query()
		for r in results:
			siblings.append(r['result'])
		return siblings

	def getAlignImagePairData(self):
		'''
		This returns DD AlignImagePairData if exists, returns False if not.
		Image set in the class instance need to be the result
		'''
		q = appiondata.ApDDAlignImagePairData(result=self.image)
		results = q.query()
		if results:
			return results[0]
		else:
			raise ValueError('No database record of the align pair')

	def getAlignLogPath(self):
		pair = self.getAlignImagePairData()
		self.rundir = pair['ddstackrun']['path']['path']
		source_imagedata = pair['source']
		imagename = source_imagedata['filename']
		self.framestackpath =  os.path.join(self.rundir,imagename+'_st.mrc')
		self.logfile = self.framestackpath[:-4]+'_Log.txt'
		return self.logfile

	def getPixelShiftsBetweenFrames(self):
		logfile = self.getAlignLogPath()
		if not os.path.isfile(self.logfile):
			raise ValueError('No align log file found')
		nframes = self.image['camera']['nframes']
		positions = ddinfo.readPositionsFromAlignLog(logfile)
		running = nframes - len(positions)+1
		pixel_shifts = ddinfo.calculateFrameShiftFromPositions(positions, running)
		return pixel_shifts

	def getAngstromShiftsBetweenFrames(self):
		pixel_shifts = self.getPixelShiftsBetweenFrames()
		if not pixel_shifts:
			return pixel_shifts
		apix = apDatabase.getPixelSize(self.image)
		return map((lambda x: x*apix), pixel_shifts)

if __name__ == '__main__':
	imagedata = leginondata.AcquisitionImageData().direct_query(1744209)
	print(imagedata['filename'])
	dd = DDResults(imagedata)
	# shift for single aligned sum
	print(dd.getPixelShiftsBetweenFrames())
	cwd = os.getcwd()
	# shift for the whole run
	os.chdir(dd.rundir)
	print(dd.rundir)
	ddinfo.printDriftStats(imagedata['filename'][:-5]+'*',1.04)
	os.chdir(cwd)
