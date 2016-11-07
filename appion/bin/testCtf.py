#!/usr/bin/env python

#pythonlib
import os
import shutil
import random
import MySQLdb
#appion
import sinedon
import leginon.leginondata
from appionlib import apParam
from appionlib import apDisplay
from appionlib import apDatabase
from appionlib import appionScript
from appionlib import apInstrument
from appionlib.apCtf import ctfdb
from appionlib.apCtf import ctfinsert
from appionlib.apCtf import ctfdisplay

class CTFTest(appionScript.AppionScript):
	"""
	CTF Test function, finds random image and runs fake CTF data
	"""

	#======================
	def setProcessingDirName(self):
		self.processdirname = "ctf"

	#======================
	def onInit(self):
		self.powerspecdir = os.path.join(self.params['rundir'], "opimages")
		apParam.createDirectory(self.powerspecdir, warning=False)
		self.ctfrundata = None
		self.dbconf = sinedon.getConfig('leginondata')
		self.db     = MySQLdb.connect(**self.dbconf)
		self.db.autocommit(True)
		# create a cursor
		self.cursor = self.db.cursor()
		return

	#======================
	def getImages(self, limit=100):
		query = (
			"SELECT "
			+"	img.`DEF_id` "
			+"FROM `AcquisitionImageData` AS img "
			+"LEFT JOIN `PresetData` AS preset "
			+"  ON img.`REF|PresetData|preset` = preset.`DEF_id` "
			+"WHERE (preset.name = 'upload' "
			+"  OR preset.name LIKE 'en%') "
			+"  AND preset.magnification > 10000 "
			+"ORDER BY RAND() "
			+("LIMIT %d; "%(limit))
		)
		#print query
		self.cursor.execute(query)
		results = self.cursor.fetchall()
		return results

	#======================
	def selectImage(self):
		results = self.getImages()
		imgdata = None
		for result in results:
			#print result
			dbid = int(result[0])
			try:
				imgdata = leginon.leginondata.AcquisitionImageData.direct_query(dbid)
			except TypeError:
				apDisplay.printWarning("data not found")
				continue
			#print imgdata.keys()
			if imgdata is None or imgdata['session'] is None:
				apDisplay.printWarning("data not found")
				continue
			try:
				filename = os.path.join(imgdata['session']['image path'], imgdata['filename']+".mrc")
				if not os.path.exists(filename):
					apDisplay.printWarning("file not found: %s"%(filename))
					continue
			except TypeError:
				apDisplay.printWarning("data not found")
				continue
			imgarray = imgdata['image']
			if imgarray is None:
				apDisplay.printWarning("data not found")
				continue
			if min(imgarray.shape) < 3000:
				apDisplay.printWarning("image too small for CTF %d x %d"%(imgarray.shape[0], imgarray.shape[1]))
				continue
			apix = apDatabase.getPixelSize(imgdata)
			if apix > 5.0:
				apDisplay.printWarning("pixel size too large for CTF %.3f A"%(apix))
				continue
			apDisplay.printColor("Selected Image: %s (%d x %d)"
				%(apDisplay.short(imgdata['filename']), imgarray.shape[0], imgarray.shape[1]), "cyan")
			return imgdata
		apDisplay.printError("Could not find a valid image")

	#======================
	def randomDefocus(self, nominal=None):
		randRangeSelect = random.random()
		if randRangeSelect < 0.33:
			#close to focus, 0.2 - 1.0 microns
			microns = 0.2 + 0.8 * random.random()
		elif randRangeSelect < 0.67:
			#normal range, 1.0 - 3.0 microns
			microns = 1.0 + 2.0 * random.random()
		else:
			#far from focus, 3.0 - 25.0 microns
			microns = 3.0 + 22.0 * random.random()
		defocus = microns * 1e-6
		if nominal is None:
			return defocus
		print "%.3f - %.3f"%(defocus*1e6, nominal*1e6)
		return (defocus+nominal)/2.

	#======================
	def setCtfValues(self, imgdata, bestdef):
		if bestdef is None:
			bestdef = { 'defocus1': None, 'defocus2': None, }
		ctfvalues = {
			'cs': apInstrument.getCsValueFromSession(imgdata['session']),
			'volts': imgdata['scope']['high tension'],
			'defocus1': self.randomDefocus(bestdef['defocus1']),
			'defocus2': self.randomDefocus(bestdef['defocus2']),
			'angle_astigmatism': random.randint(1,180),
			'amplitude_contrast': 0.01*random.randint(1,30),
		}
		return ctfvalues

	#======================
	def setBestCtfValues(self, imgdata, bestdef):
		if bestdef is None:
			return self.setCtfValues(imgdata, bestdef)
		ctfvalues = {
			'cs': apInstrument.getCsValueFromSession(imgdata['session']),
			'volts': imgdata['scope']['high tension'],
			'defocus1': bestdef['defocus1'],
			'defocus2': bestdef['defocus2'],
			'angle_astigmatism': bestdef['angle_astigmatism'],
			'amplitude_contrast': bestdef['amplitude_contrast'],
		}
		return ctfvalues

	#======================
	def start(self):
		for imgrun in range(self.params['images']):
			imgdata = self.selectImage()
			bestdef = ctfdb.getBestCtfByResolution(imgdata, msg=True)
			if self.params['bestonly'] is True and bestdef is None:
				continue
			for run in range(self.params['runs']):
				### parse log file
				if self.params['bestonly'] is True:
					ctfvalues = self.setBestCtfValues(imgdata, bestdef)
				else:
					ctfvalues = self.setCtfValues(imgdata, bestdef)
				self.validateCTFData(imgdata, ctfvalues)
		return

	#======================
	def validateCTFData(self, imgdata, ctfvalues):
		"""
		function to insert CTF values in database
		"""
		apDisplay.printMsg("Testing ctf parameters for "
			+apDisplay.short(imgdata['filename']))

		### convert to common convention
		ctfvalues = ctfinsert.convertDefociToConvention(ctfvalues)

		### check to make sure parameters are valid
		isvalid = ctfinsert.checkParams(ctfvalues)
		if isvalid is False:
			apDisplay.printError("Bad CTF values")

		### run the main CTF display program
		opimagedir = os.path.join(self.params['rundir'], "opimages")

		### RUN CTF DISPLAY TOOLS
		ctfdisplaydict = ctfdisplay.makeCtfImages(imgdata, ctfvalues)
		if ctfdisplaydict is None:
			apDisplay.printError("Image creation failed")

		psfile = os.path.join(opimagedir, ctfdisplaydict['powerspecfile'])
		if not os.path.isfile(ctfdisplaydict['powerspecfile']):
			apDisplay.printError("Powerspec file not created")
		else:
			shutil.move(ctfdisplaydict['powerspecfile'], psfile)

		### new 1d plot file
		plotfile = os.path.join(opimagedir, ctfdisplaydict['plotsfile'])
		shutil.move(ctfdisplaydict['plotsfile'], plotfile)

		ctfvalues['confidence_30_10'] = ctfdisplaydict['conf3010']
		ctfvalues['confidence_5_peak'] = ctfdisplaydict['conf5peak']
		ctfvalues['resolution_80_percent'] = ctfdisplaydict['res80']
		ctfvalues['resolution_50_percent'] = ctfdisplaydict['res50']
		ctfdb.printCtfData(ctfvalues)

		return

	#======================
	def setupParserOptions(self):
		### values
		self.parser.add_option("--runs", dest="runs", type="int", default=1,
			help="Number of runs to perform for each image", metavar="#")
		self.parser.add_option("--images", dest="images", type="int", default=1,
			help="Number of images to test", metavar="#")
		self.parser.add_option("--best-only", dest="bestonly", default=False,
			action="store_true", help="Use only best CTF values not random")

		#self.parser.add_option("--mindefocus", dest="mindefocus", type="float", default=0.1e-6,
		#	help="Minimal acceptable defocus (in meters)", metavar="#")
		#self.parser.add_option("--maxdefocus", dest="maxdefocus", type="float", default=15e-6,
		#	help="Maximal acceptable defocus (in meters)", metavar="#")

	#======================
	def checkConflicts(self):
		#if (self.params['mindefocus'] is not None and
		#		(self.params['mindefocus'] > 1e-3 or self.params['mindefocus'] < 1e-9)):
		#	apDisplay.printError("min defocus is not in an acceptable range, e.g. mindefocus=1.5e-6")
		#if (self.params['maxdefocus'] is not None and
		#		(self.params['maxdefocus'] > 1e-3 or self.params['maxdefocus'] < 1e-9)):
		#	apDisplay.printError("max defocus is not in an acceptable range, e.g. maxdefocus=1.5e-6")
		### set cs value

		return


if __name__ == '__main__':
	imgLoop = CTFTest()
	imgLoop.start()


