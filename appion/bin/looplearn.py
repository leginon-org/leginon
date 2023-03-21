#!/usr/bin/env python

#pythonlib
import os
import numpy
import time
#appion
from appionlib import appionLoop2
from appionlib import apDisplay
from appionlib import apDDResult
from appionlib.apCtf import ctfdb
from leginon import leginondata
from leginon import ptolemyhandler as ph
from leginon import updatetargetorder

class LoopLearner(appionLoop2.AppionLoop):
	'''
	This simple script just print the image filename. It can
	be used to test appionLoop and or simply propogate donedict.
	'''

	#=====================
	def setProcessingDirName(self):
		self.processdirname = "learn"

	def preLoopFunctions(self):
		self.grid_mosaic_targetlist = None
		self.learned_square_ids = []
		self.order_updater = updatetargetorder.SquareTargetOrderUpdater(self.sessiondata, apDisplay.LeginonLogger())

	#======================
	def processImage(self, imgdata):
		if not imgdata['target']['ptolemy_hole']:
			apDisplay.printWarning('Not ptolemy active learning image')
			self.icedata = None
			self.ctfvalue = None
			return
		if imgdata['camera']['align frames']:
			dd = apDDResult.DDResults(imgdata)
			self.unaligned = dd.getAlignImagePairData()['source']
		else:
			self.unaligned = imgdata
		apDisplay.printMsg('processing %s' % (imgdata['filename']))
		self.icedata = self.getIceThicknessData(self.unaligned)
		ctfvalue, conf = ctfdb.getBestCtfValueForImage(imgdata)
		if ctfvalue is None:
			apDisplay.printWarning('No ctf estimation, yet.  Wait until it exists')
			time.sleep(30)
			return self.processImage(imgdata)
		self.ctfvalue = ctfvalue

	def getIceThicknessData(self, imgdata):
		return leginondata.ObjIceThicknessData(image=imgdata).query(results=1)

	#======================
	def setupParserOptions(self):
		self.parser.add_option("--interval", dest="update_interval", type="int", default=1,
			help="Update square target order every  <update_interval> number of squares learned")
		return

	#======================
	def checkConflicts(self):
		return

	def updateLearnedSquare(self, imgdata):
		is_from_mosaic = False
		inspect_image = imgdata
		child_image = None
		while True:
			is_from_mosaic = inspect_image['target']['list']['mosaic']
			if is_from_mosaic:
				break
			child_image = inspect_image
			inspect_image = inspect_image['target']['image']
		if child_image is None:
			apDisplay.printError('image %s can not be used to update square targeting order' % inspect_image['filename'])
		my_grid_mosaic_targetlist = inspect_image['target']['list']
		if self.grid_mosaic_targetlist is None or self.grid_mosaic_targetlist.dbid != my_grid_mosaic_targetlist.dbid:
			self.grid_mosaic_targetlist = my_grid_mosaic_targetlist
			# reset counting
			self.learned_square_ids = []
		my_square_id = child_image.dbid
		if my_square_id not in self.learned_square_ids:
			self.learned_square_ids.append(my_square_id)
		apDisplay.printMsg('current mosaic label is "%s" and square image ides with learning since last order update are %s'  % (self.grid_mosaic_targetlist['label'],self.learned_square_ids))
		if len(self.learned_square_ids) > self.params['update_interval']:
			apDisplay.printMsg('updating square target order....')
			self.order_updater.updateOrder(is_first=False, mosaic_name=self.grid_mosaic_targetlist['label'])
			# reset count
			self.learned_square_ids = []
			apDisplay.printMsg('done square target order update')

	#======================
	def commitToDatabase(self, imgdata):
		if not self.unaligned['target']['ptolemy_hole']:
			# Not valid to learn
			return
		# post ctf resolution and ice thickness to ptolemy
		ctf_res = min(self.ctfvalue['resolution_50_percent'], self.ctfvalue['ctffind4_resolution']) #Angstrom
		if not self.icedata:
			apDisplay.printError('need ice thickness from Objective Aperture measurement')
		thickness = self.icedata[0]['thickness']*1e9 #??? nm
		hole_ids = [self.unaligned['target']['ptolemy_hole']['hole_id'],]
		ctfs = [ctf_res,]
		ice_thicknesses = [thickness,]
		ph.visit_holes(hole_ids, ctfs, ice_thicknesses)
		apDisplay.printMsg('inserted %d visited holes in session %s' % (len(hole_ids), self.unaligned['session']['name']))
		# TODO: redo target ordering on square targets
		self.updateLearnedSquare(imgdata)
		return

if __name__ == '__main__':
	testLoop = LoopLearner()
	testLoop.run()

