#!/usr/bin/env python

#pythonlib
import os
import math
#appion
from appionlib import appionScript
from appionlib import apDisplay
from appionlib import apDatabase
from appionlib import appiondata
from appionlib import apDBImage
from appionlib import apFile
from appionlib import apDDResult
from appionlib.apCtf import ctfdb
#pyami
from pyami import fileutil
from pyami import numpil, imagefun

class ImageRejector2(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		"""
		standard appionScript
		"""
		self.sortoptions = ('res80', 'res50', 'resPkg')
		### strings
		self.parser.add_option("--session", "--sessionname", dest="sessionname",
			help="Session name", metavar="NAME")

		self.parser.add_option("--preset", "--presetname", dest="preset",
			help="Name of Preset to check", metavar="NAME")

		self.parser.add_option("--sort", dest="sorttype",
			help="bestdb CTF sorting method", metavar="TYPE",
			type="choice", choices=self.sortoptions, default="res80" )

		### int
		self.parser.add_option("--ctfrunid", dest="ctfrunid", type="int",
			help="Ctf run to be transferred", metavar="#")

		### true / false
		self.parser.add_option("--bestdb", dest="bestdb", default=False,
			action="store_true", help="transfer best ctf")

		### float
		self.parser.add_option("--resmin", dest="resmin", type="float", default=None,
			help="Hide images with sorting method below this resolution in Angstroms", metavar="#")
		self.parser.add_option("--driftmax", dest="driftmax", type="float", default=None,
			help="Hide images with largest drift per frame above this value in Angstroms", metavar="#")


	#=====================
	def checkConflicts(self):
		### check for requirement
		if self.params['ctfrunid'] is None and self.params['bestdb'] is False:
			apDisplay.printError("Please provide either a ctfrun or use best ctf in db to transfer")
		if self.params['sessionname'] is None:
			if self.params['expid']:
				# onInit has not been run yet. There is no self.sessiondata to use here
				sessiondata = apDatabase.getSessionDataFromSessionId(self.params['expid'])
				self.params['sessionname'] = sessiondata['name']
			else:
				apDisplay.printError("Please provide a Session name, e.g., --session=09feb12b")
		if self.params['projectid'] is None:
			apDisplay.printError("Please provide a Project database ID, e.g., --projectid=42")

	#=====================
	def onInit(self):
		"""
		standard appionScript
		"""
		self.sessiondata = self.getSessionData()
		self.rundata = None
		return

	#=====================
	def setProcessingDirName(self):
		self.processdirname = "reject"

	#=====================
	def start(self):
		# go through images
		images = apDatabase.getImagesFromDB(self.params['sessionname'], self.params['preset'])
		for imgdata in images[-2:]:
			apDisplay.printMsg('Checking %s' % imgdata['filename'])
			if self.params['driftmax']:
				self.hideDriftImage(imgdata)
			if 'resmin' in self.params.keys():
				self.hideBadCtfImage(imgdata)

	def hideDriftImage(self, imgdata):
		ddresults = apDDResult.DDResults(imgdata)
		try:
			logfile = ddresults.getAlignLogPath()
			shifts = ddresults.getAngstromShiftsBetweenFrames()
		except:
			apDisplay.printWarning('No alignment log file %s found for thresholding drift' % logfile)
			return False
		if self.params['driftmax'] < max(shifts):
			self.hideImage(imgdata)

	def hideBadCtfImage(self, imgdata):
		ctfdata = self.getFromCtfData(imgdata)
		if not ctfdata:
			apDisplay.printWarning('No CTF result for %s' % apDisplay.short(imgdata['filename']))
			return
		try:
			if self.isOutsideCTFRes(ctfdata, self.params['sorttype'],self.params['resmin']):
				return self.hideImage(imgdata)
		except Exception, e:
			raise
		ctfrun = ctfdata['acerun']
		pow_graph_path = os.path.join(ctfrun['path']['path'],'opimages',ctfdata['graph3'])
		if self.hasIceCrystal(pow_graph_path):
			apDisplay.printWarning('Found Ice Crystal Pattern')
			return self.hideImage(imgdata)
		
	def hasIceCrystal(self,graph_path, ice_pixel_radius=394):
		print graph_path
		imgarray = numpil.read(graph_path)

		# 20 bins roughly isolate the ice ring
		rbin=20
		nr = int(math.sqrt(2)*256//rbin)
		icer = int(ice_pixel_radius//(rbin*2))
		qr_bins = self.calculateQuarterRadialProfile(imgarray, nr,icer)
		before = qr_bins[icer-2]
		before_std = qr_bins[icer-3:icer-1].std()
		at = qr_bins[icer]
		after = qr_bins[icer+2]
		after_std = qr_bins[icer+1:icer+3].std()
		print before_std, at, after_std
		return at-(before+after)/2 > 5* max((before_std,after_std))

	def calculateQuarterRadialProfile(self, imgarray, nr, icer):
		nt = 4
		rt_bins, r_centers, t_centers = imagefun.polarBin(imgarray,nr,nt)
		return rt_bins[:,2]

	def isOutsideCTFRes(self, ctfdata, sorttype, resmin=None):
		if sorttype ==  'resPkg':
			ctf_res = ctfdata['ctffind4_resolution']
		elif sorttype == 'res50':
			ctf_res = ctfdata['resolution_50_percent']
		elif sorttype == 'res80':
			ctf_res = ctfdata['resolution_80_percent']
		else:
			raise ValueError('handling method for sort type %s not defined' % (sorttype,))
		if resmin and resmin < ctf_res:
			return True
		return False

	def hideImage(self, image):
		print 'Will need to hide %s' % (image['filename'])
		return
		status = apDatabase.getImgViewerStatus(image)
		if status is False:
			# already hidden or trashed
			return
		apDatabase.setImgViewerStatus(image, False)

	def commitToDatabase(self,old_ctfdata, to_imgdata):
		pass

	def selectImageAtPreset(self, presetname, images):
		for imgdata in images:
			if presetname == 'manual':
				if imgdata['preset'] is None:
					return imgdata
			else:
				if imgdata['preset'] is not None and imgdata['preset']['name']==presetname:
					return imgdata

	def getFromCtfData(self,imgdata):
		### get all CTF parameters,
		if self.params['bestdb']:
			return self.getBestCtfValue(imgdata, False)
		elif self.params['ctfrunid'] is not None:
			return ctfdb.getCtfValueForCtfRunId(imgdata, self.params['ctfrunid'], msg=False)
		else:
			return None

	def getBestCtfValue(self, imgdata, msg=False):
		return ctfdb.getBestCtfValue(imgdata, sortType=self.params['sorttype'], method=None, msg=msg)

#=====================
#=====================
#=====================
if __name__ == '__main__':
	app = ImageRejector2()
	app.start()
	app.close()





