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
from appionlib import apScriptLog
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
			help="Name of Preset used for evaluation", metavar="NAME")

		self.parser.add_option("--sort", dest="sorttype",
			help="bestdb CTF sorting method, Default to use fit resolution from the software package", metavar="TYPE",
			type="choice", choices=self.sortoptions, default="resPkg" )

		### int
		self.parser.add_option("--iceradius", dest="ice_radius", type="int", default=396,
			help="Radius in pixels on ctffind4 2d graph where the ice crystal is found. Not needed if not a ctffind4 run.", metavar="#")
		self.parser.add_option("--ctfrunid", dest="ctfrunid", type="int",
			help="Specific Ctf run to be evaluated", metavar="#")

		### true / false
		self.parser.add_option("--testrun", dest="testrun", default=False,
			action="store_true", help="Print the results instead of hiding them")
		self.parser.add_option("--bestdb", dest="bestdb", default=False,
			action="store_true", help="transfer best ctf")
		self.parser.add_option("--hideall", dest="hideall", default=False,
			action="store_true", help="Hide all source and results of DD frame alignment related to this preset")

		### float
		self.parser.add_option("--resmin", dest="resmin", type="float", default=None,
			help="Hide images with sorting method below this resolution in Angstroms", metavar="#")
		self.parser.add_option("--driftmax", dest="driftmax", type="float", default=None,
			help="Hide images with largest drift per frame above this value in Angstroms", metavar="#")
		self.parser.add_option("--icemax", dest="icemax", type="float", default=None,
			help="Hide images with intensity in expected resolution this much times standard deviation of the backgound", metavar="#")


	#=====================
	def checkConflicts(self):
		### check for requirement
		if not self.params['preset']:
			apDisplay.printError('Must specify preset')
		if self.params['icemax'] is None and self.params['resmin'] is None and self.params['driftmax'] is None:
			apDisplay.printError('No rejection criteria set')
		if self.params['icemax'] is not None and self.params['resmin'] is None:
			apDisplay.printError('Must reject also by ctf fit resolution as well if request ice crystal to be rejected')
		if self.params['resmin'] and self.params['ctfrunid'] is None and self.params['bestdb'] is False:
			apDisplay.printError("Please provide either a ctfrun or use best ctf in db to evaluate")
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
		self.isCtffind4_dict = {}
		return

	#=====================
	def setProcessingDirName(self):
		self.processdirname = "reject"

	#=====================
	def start(self):
		# default ic radius in pixels
		self.ice_radius = self.params['ice_radius']
		# go through images
		images = apDatabase.getImagesFromDB(self.params['sessionname'], self.params['preset'])
		if images:
			self.apix = apDatabase.getPixelSize(images[0])
		for imgdata in images:
			apDisplay.printMsg('______________________')
			apDisplay.printMsg('Checking %s' % imgdata['filename'])
			if self.params['driftmax']:
				self.hideDriftImage(imgdata)
			if self.params['resmin'] is not None:
				is_hidden = self.hideBadCtfImage(imgdata)
				if not is_hidden and self.params['icemax']:
					self.hideIceCrystalImage(imgdata)

	def hideDriftImage(self, imgdata):
		ddresults = apDDResult.DDResults(imgdata)
		try:
			logfile = ddresults.getAlignLogPath()
			shifts = ddresults.getAngstromShiftsBetweenFrames()
		except:
			apDisplay.printWarning('No alignment log file %s found for thresholding drift' % logfile)
			return False
		if self.params['driftmax'] < max(shifts):
			apDisplay.printMsg('Maximal frame drift %.2f Angstroms is too much' % (max(shifts),))
			return self.hideImage(imgdata)

	def hideBadCtfImage(self, imgdata):
		ctfdata = self.getFromCtfData(imgdata)
		self.ctfdata = ctfdata
		if not ctfdata:
			apDisplay.printWarning('No CTF result for %s' % apDisplay.short(imgdata['filename']))
			return False
		try:
			if self.isOutsideCTFRes(ctfdata, self.params['sorttype'],self.params['resmin']):
				return self.hideImage(imgdata)
		except Exception, e:
			raise

	def hideIceCrystalImage(self, imgdata):
		ctfdata = self.ctfdata
		if not ctfdata or not ctfdata['acerun']:
			return False
		ctfrun = ctfdata['acerun']
		pow_graph_path = self.getPowerGraphPath(imgdata, ctfdata)
		if self.hasIceCrystal(pow_graph_path):
			apDisplay.printWarning('Found Ice Crystal Pattern')
			return self.hideImage(imgdata)

	def isCtfFind4Run(self, ctfrun):
		'''
		Check if the ctfrun is from ctffind4 through ScriptLog.
		'''
		# This is needed because ctffind4 and gctf uses the same
		# ApCtfFind4ParamsData
		if not ctfrun.dbid:
			return False
		if ctfrun.dbid in self.isCtffind4_dict.keys():
			return self.isCtffind4_dict[ctfrun.dbid]
		program_run = apScriptLog.getScriptProgramRunFromRunname(ctfrun['name'],ctfrun['path'])
		isCtffind4 = program_run and 'ctffind4' in program_run['progname']['name']
		self.isCtffind4_dict[ctfrun.dbid] = isCtffind4
		return isCtffind4

	def getPowerGraphPath(self, imgdata, ctfdata):
		ctfrun_msg = ''
		if ctfdata:
			ctfrun = ctfdata['acerun']
			is_ctffind4 = self.isCtfFind4Run(ctfrun)
			# Only ctffind4 graph is good enough for quick evaluation
			if is_ctffind4:
				if ctfdata['graph3']:
					pow_graph_path = os.path.join(ctfrun['path']['path'],'opimages',ctfdata['graph3'])
					try:
						fs=open(pow_graph_path)
						fs.close()
						self.graph_size = 1024
						self.ice_radius = self.params['ice_radius']
						return pow_graph_path
					except:
						ctfrun_msg = 'CTFFind4 graph not readable.'
				else:
					ctfrun_msg = 'CTFFind4 graph not ready.'
			else:
				ctfrun_msg = 'Not a CTFFind4 run. Graph not analyzable'
		else:
			ctfrun_msg = 'No CTF estimation graph.'
		apDisplay.printWarning(ctfrun_msg+' Making power spectrum image')
		return self.makePowerGraphFromImage(imgdata)

	def makePowerGraphFromImage(self, imgdata):
		pow_graph_path = './tmp_pow.jpg'
		a = imgdata['image']
		ashape_min = min(a.shape)
		pow_array = imagefun.power(a[:ashape_min,:ashape_min])
		# calculate ice radius on the graph
		self.ice_radius = self.calculateIceCrystalRadius(ashape_min)
		numpil.write(pow_array,pow_graph_path,'JPEG')
		self.graph_size = ashape_min
		return pow_graph_path

	def calculateIceCrystalRadius(self, size):
		rec_apix = self.apix * size
		ice_radius_rec_pix = (1/3.8)/(1/rec_apix)
		return ice_radius_rec_pix

	def hasIceCrystal(self,graph_path):
		'''
		Detemine if there is significant ice crystal diffraction
		ring in the power spectrum graph.
		'''
		imgarray = numpil.read(graph_path)

		ice_pixel_radius = self.ice_radius

		# 20 bins roughly isolate the ice ring
		rbin=20
		min_std = 1.0
		# polar average goes to the full diagonal length
		max_radius = math.sqrt(2)*self.graph_size/2.0
		icer = int(rbin*ice_pixel_radius/(max_radius))
		qr_bins = self.calculateQuarterRadialProfile(imgarray, rbin,icer)
		before = qr_bins[icer-2]
		before_std = qr_bins[icer-3:icer-1].std()
		at = qr_bins[icer]
		after = qr_bins[icer+2]
		after_std = qr_bins[icer+2:icer+4].std()
		apDisplay.printMsg('Std deviation intensity around ice crystal resolution are: %.3f and %.3f' % (before_std, after_std))
		apDisplay.printMsg('Ice crystal resolution mean intensity above background: %.3f' % (at-(before+after)/2))
		return at-(before+after)/2 > self.params['icemax']* max((before_std,after_std,min_std))

	def calculateQuarterRadialProfile(self, imgarray, nr, icer):
		# Use only one quarter for simplicity
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
			apDisplay.printMsg('CTF fitted resolution failed validation at %.2f' % (ctf_res,))
			return True
		return False

	def getAllDDAlignSiblings(self, imgdata):
		try:
			ddresults = apDDResult.DDResults(imgdata)
			return ddresults.getAlignSiblings()
		except:
			return [imgdata,]

	def hideImage(self, image):
		if self.params['hideall']:
			allimages = self.getAllDDAlignSiblings(image)
		else:
			allimages = [image,]
		all_true = True
		for img in allimages:
			is_hidden = self._hideImage(img)
			all_true = all_true and is_hidden
		return all_true

	def _hideImage(self, image):
		'''
		Hide if not hidden.  Returns True if it is now hidden so
		that further validation can be skipped.  no-commit flag will
		always return False so that everything is checked.
		'''
		if not self.params['commit']:
			print 'Will need to hide %s' % (image['filename'])
			return False
		else:
			return self.commitToDatabase(image)

	def commitToDatabase(self, image):
		status = apDatabase.getImgViewerStatus(image)
		if status is False:
			# already hidden or trashed
			apDisplay.printMsg('%s is already hidden' % (image['filename']))
			return True
		apDatabase.setImgViewerStatus(image, False)
		return True

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





