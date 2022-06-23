#!/usr/bin/env python
import os
import math
import glob
import numpy
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
		self.apix = apDatabase.getPixelSize(self.image)
		# ddstack alignment run info
		self.ddstackrun = None
		self.rundir = None

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
		self.ddstackrun = pair['ddstackrun']
		source_imagedata = pair['source']
		imagename = source_imagedata['filename']
		self.framestackpath =  os.path.join(self.rundir,imagename+'_st.mrc')
		self.logfile = self.framestackpath[:-4]+'_Log.txt'
		return self.logfile

	def readPositionsFromAlignLog(self):
		logfile = self.getAlignLogPath()
		if not os.path.isfile(self.logfile):
			raise ValueError('No align log file found')
		try:
			positions = ddinfo.readPositionsFromAlignLog(logfile)
		except IOError as e:
			raise ValueError('align log file %s not readable' % logfile)
		return positions

	def getPixelShiftsBetweenFrames(self):
		positions = self.readPositionsFromAlignLog()
		nframes = self.image['camera']['nframes']
		running = nframes - len(positions)+1
		pixel_shifts = ddinfo.calculateFrameShiftFromPositions(positions, running)
		return pixel_shifts

	def getAngstromShiftsBetweenFrames(self):
		pixel_shifts = self.getPixelShiftsBetweenFrames()
		if not pixel_shifts:
			return pixel_shifts
		return map((lambda x: x*self.apix), pixel_shifts)

	def getFrameTrajectoryFromLog(self):
		'''
		Read frame alignment trajectory from log file. Returns dictionary
		of x,y with a list of relative shift positions
		'''
		positions = self.readPositionsFromAlignLog()
		xydict = {}
		xydict['x'] = map((lambda x: x[0]), positions)
		xydict['y'] = map((lambda x: x[1]), positions)
		return xydict

	def saveFrameTrajectory(self, rundata, xydict, limit=20, reference_index=None, particle=None):
		'''
		Save appiondata ApDDFrameTrajectoryData
		'''
		n_positions = len(xydict['x'])
		limit = min([n_positions,limit])
		if limit < 2:
			raise ValueError('Not enough frames to save trajectory')
		if reference_index == None:
			reference_index = n_positions // 2
		q=appiondata.ApDDFrameTrajectoryData()
		q['image']=self.image
		q['particle']=particle
		q['ddstackrun']=rundata
		q['pos_x']=list(xydict['x'][:limit]) #position relative to reference
		q['pos_y']=list(xydict['y'][:limit]) #position relative to reference
		q['last_x']=xydict['x'][-1]
		q['last_y']=xydict['y'][-1]
		q['number_of_positions']= n_positions
		q['reference_index']= reference_index
		q.insert()
		return q

	def getFrameStats(self):
		'''
		get alignment frame stats for faster graphing.
		'''
		pixel_shifts = self.getPixelShiftsBetweenFrames()
		if not pixel_shifts:
			raise ValueError('no pixel shift found for calculating stats')
		if len(pixel_shifts) < 3:
			raise ValueError('Not enough pixel shifts found for stats calculation')
		pixel_shifts_sort = list(pixel_shifts)
		pixel_shifts_sort.sort()
		median = numpy.median(numpy.array(pixel_shifts_sort))
		max1 = pixel_shifts_sort[-1]
		max2 = pixel_shifts_sort[-2]
		max3 = pixel_shifts_sort[-3]
		m1index = pixel_shifts.index(max1)
		m2index = pixel_shifts.index(max2)
		m3index = pixel_shifts.index(max3)
		return [(max1,m1index),(max2,m2index),(max3,m3index)], median

	def saveAlignStats(self, rundata, trajdata=None):
		'''
		save appiondata ApDDAlignStatsData
		'''
		max_drifts, median = self.getFrameStats()
		q = appiondata.ApDDAlignStatsData(image=self.image, apix=self.apix)
		q['ddstackrun'] = rundata
		q['median_shift_value'] = median
		for i, drift_tuple in enumerate(max_drifts):
			key = 'top_shift%d' % (i+1,)
			q[key+'_index'] = drift_tuple[1]
			q[key+'_value'] = drift_tuple[0]
		q['trajectory'] = trajdata
		q.insert()
		return q

if __name__ == '__main__':
	imagedata = leginondata.AcquisitionImageData().direct_query(461)
	print(imagedata['filename'])
	dd = DDResults(imagedata)
	# shift for single aligned sum
	print(dd.getPixelShiftsBetweenFrames())
	cwd = os.getcwd()
	# shift for the whole run
	os.chdir(dd.rundir)
	print(dd.rundir)
	ddinfo.printDriftStats(imagedata['filename'][:-5]+'*',dd.apix)
	print(dd.getFrameStats())
	xydict = dd.getFrameTrajectoryFromLog()
	trajdata = dd.saveFrameTrajectory(dd.ddstackrun, xydict)
	if trajdata.dbid:
		dd.saveAlignStats(dd.ddstackrun, trajdata)
	os.chdir(cwd)
