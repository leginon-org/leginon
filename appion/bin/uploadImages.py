#!/usr/bin/env python

import os
import time
import glob
import numpy
import string
import shutil
import leginon.leginondata
import leginon.projectdata
from pyami import mrc
from appionlib import appionScript
from appionlib import apDisplay
from appionlib import apParam
from appionlib import apFile

#=====================
#=====================
class UploadImages(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.add_option("--mpix", "--pixel-size", dest="mpix", type="float",
			help="Pixel size of the images in meters", metavar="#.#")
		self.parser.add_option("--mag", dest="magnification", type="int", metavar="MAG",
			help="nominal magnification, e.g., --mag=50000 for 50kX")
		self.parser.add_option("--kv", dest="kv", type="int", metavar="INT",
			help="high tension (in kilovolts), e.g., --kv=120")

		self.parser.add_option("--image-dir", dest="imagedir",
			help="Directory that contains MRC files to upload", metavar="DIR")

		self.parser.add_option("--leginon-output-dir", dest="leginondir",
			help="Leginon output directory, e.g., --leginon-output-dir=/data/leginon",
			metavar="DIR")

		self.parser.add_option("--images-per-series", dest="seriessize", type="int", default=1,
			help="Number of images in tilt series", metavar="#")

		self.parser.add_option("--angle-list", dest="angleliststr",
			help="List of angles in radians to apply to tilt series", metavar="#,#,#")
		self.parser.add_option("--defocus-list", dest="defocusliststr",
			help="List of defoci in meters to apply to defocal series", metavar="#,#,#")
		self.parser.add_option("--defocus", dest="defocus", type="float",
			help="Defocus in meters to apply to all images", metavar="#.#e#")
		self.parser.add_option("--invert", dest="invert", default=False,
			action="store_true", help="Invert image density")

		self.uploadtypes = ('tiltseries', 'defocalseries', 'normal')
		self.parser.add_option("--type", dest="uploadtype", default="normal",
			type="choice", choices=self.uploadtypes,
			help="Type of upload to perform: "+str(self.uploadtypes), metavar="..")

	#=====================
	def checkConflicts(self):
		if self.params['description'] is None:
			apDisplay.printError("Please provide a description, e.g., --description='test'")
		if self.params['imagedir'] is None:
			apDisplay.printError("Please provide a image directory, e.g., --imagedir=/path/to/files/")
			if not os.path.isdir(self.params['imagedir']):
				apDisplay.printError("Image directory '%s' does not exist"%(self.params['imagedir']))
		if self.params['kv'] is None:
			apDisplay.printError("Please provide a high tension (in kV), e.g., --kv=120")
			if self.params['kv'] > 1000:
				apDisplay.printError("High tension must be in kilovolts (e.g., --kv=120)")
		if self.params['magnification'] is None:
			apDisplay.printError("Please provide a magnification, e.g., --mag=50000")		
		if self.params['mpix'] is None:
			apDisplay.printError("Please provide a pixel size (in meters), e.g., --pixelsize=1.3e-10")

		### series only valid with non-normal uplaods
		if self.params['seriessize'] is None and self.params['uploadtype'] != "normal":
			apDisplay.printError("If using tilt or defocal series, please provide --images-per-series")
		if self.params['seriessize'] > 1 and self.params['uploadtype'] == "normal":
			apDisplay.printError("If using normal mode, do NOT provide --images-per-series")

		### angleliststr only valid with tiltseries uplaods
		if self.params['angleliststr'] is None and self.params['uploadtype'] == "tiltseries":
			apDisplay.printError("If using tilt series, please provide --angle-list")
		if self.params['angleliststr'] is not None and self.params['uploadtype'] != "tiltseries":
			apDisplay.printError("If not using tilt series, do NOT provide --angle-list")
		if self.params['angleliststr'] is not None:
			self.anglelist = self.convertStringToList(self.params['angleliststr'])
			if len(self.anglelist) != self.params['seriessize']:
				apDisplay.printError("'images-per-tilt-series' and 'angle-list' have different lengths")

		### defocusliststr only valid with non-normal uplaods
		if self.params['defocus'] is not None and self.params['defocusliststr'] is not None:
			apDisplay.printError("Please provide only one of --defocus or --defocus-list")
		if self.params['defocus'] is None and self.params['defocusliststr'] is None:
			apDisplay.printError("Please provide either --defocus or --defocus-list")
		if self.params['defocusliststr'] is not None and self.params['uploadtype'] == "normal":
			apDisplay.printError("If using normal mode, do NOT provide --defocus-list")
		if self.params['defocusliststr'] is not None:
			self.defocuslist = self.convertStringToList(self.params['defocusliststr'])
			if len(self.defocuslist) != self.params['seriessize']:
				apDisplay.printError("'images-per-tilt-series' and 'defocus-list' have different lengths")

		### check for negative defoci
		if self.params['defocus'] is not None and self.params['defocus'] > 0:
			apDisplay.printWarning("defocus is being switched to negative, %.3f"
				%(self.params['defocus']))
			self.params['defocus'] *= -1.0
			if self.params['defocus'] > -0.1:
				apDisplay.printError("defocus must be in microns, %.3f"
					%(self.params['defocus']))
		elif self.params['defocus'] is None:
			newlist = []
			for defocus in self.defocuslist:
				if defocus > 0:
					apDisplay.printWarning("defocus is being switched to negative, %.3f"
						%(defocus))
					defocus *= -1.0
					if defocus > -0.1:
						apDisplay.printError("defocus must be in microns, %.3f"%(defocus))
				newlist.append(defocus)
			self.defocuslist = newlist

		### set session name if undefined
		if not 'sessionname' is self.params or self.params['sessionname'] is None:
			self.params['sessionname'] = self.getUnusedSessionName()

		### set leginon dir if undefined
		if self.params['leginondir'] is None:
			try:
				self.params['leginondir'] = leginon.leginonconfig.IMAGE_PATH
			except AttributeError:
				apDisplay.printError("Please provide a leginon output directory, "
					+"e.g., --leginon-output-dir=/data/leginon")
		self.leginonimagedir = os.path.join(self.params['leginondir'], self.params['sessionname'], 'rawdata')

	#=====================
	def convertStringToList(self, string):
		"""
		convert a string containing commas to a list
		"""
		if not "," in string:
			apDisplay.printError("Unable to parse string"%(string))
		stripped = string.strip()
		rawlist = stripped.split(",")
		parsedlist = []
		for item in rawlist:
			if not item:
				continue
			num = float(item)
			parsedlist.append(num)
		return parsedlist

	#=====================
	def getUserData(self):
		username = apParam.getUsername()
		userq = leginon.leginondata.UserData()
		userq['username'] = username
		userdatas = userq.query(results=1)
		if not userdatas:
			return None
		return userdatas[0]

	#=====================
	def getUnusedSessionName(self):
		### get standard appion time stamp, e.g., 10jun30
		sessionq = leginon.leginondata.SessionData()
		sessionq['name'] = self.timestamp
		sessiondatas = sessionq.query(results=1)
		if not sessiondatas:
			return self.timestamp

		for char in string.lowercase:
			sessionname = self.timestamp+char
			sessionq = leginon.leginondata.SessionData()
			sessionq['name'] = sessionname
			sessiondatas = sessionq.query(results=1)
			if not sessiondatas:
				break
		return sessionname

	#=====================
	def createNewSession(self):
		apDisplay.printColor("Creating a new session", "cyan")

		### get user data
		userdata = self.getUserData()

		sessionq = leginon.leginondata.SessionData()
		sessionq['name'] = self.params['sessionname']
		sessionq['image path'] = self.leginonimagedir
		sessionq['comment'] = self.params['description']
		sessionq['user'] = userdata

		projectdata = leginon.projectdata.projects.direct_query(self.params['projectid'])

		projectexpq = leginon.projectdata.projectexperiments()
		projectexpq['project'] = projectdata
		projectexpq['session'] = sessionq
		if self.params['commit'] is True:
			projectexpq.insert()

		self.sessiondata = sessionq
		apDisplay.printColor("Created new session %s"%(self.params['sessionname']), "cyan")
		return

	#=====================
	def setRunDir(self):
		"""
		This function is only run, if --rundir is not defined on the commandline
		"""
		### set the rundir to the leginon image directory
		self.params['rundir'] = self.leginonimagedir

	#=====================
	def getAppionInstruments(self):
		instrumentq = leginon.leginondata.InstrumentData()
		instrumentq['hostname'] = "appion"
		instrumentq['name'] = "AppionTEM"
		instrumentdatas = instrumentq.query(results=1)
		if not instrumentdatas:
			apDisplay.printError("Could not find the default Appion TEM in Leginon")
		self.temdata = instrumentdatas[0]
		
		instrumentq = leginon.leginondata.InstrumentData()
		instrumentq['hostname'] = "appion"
		instrumentq['name'] = "AppionCamera"
		instrumentdatas = instrumentq.query(results=1)
		if not instrumentdatas:
			apDisplay.printError("Could not find the default Appion Camera in Leginon")
		self.camdata = instrumentdatas[0]
		return

	#=====================
	def getImagesInDirectory(self, directory):
		searchstring = os.path.join(directory, "*.mrc")
		mrclist = glob.glob(searchstring)
		if len(mrclist) == 0:
			apDisplay.printError("Did not find any images to upload")
		mrclist.sort()
		return mrclist

	#=====================
	def setDefocalTargetData(self, seriescount):
		if self.params['uploadtype'] != "defocalseries":
			return None

		### setup preset data
		targetpresetdata = leginon.leginondata.PresetData()
		targetpresetdata['session'] = self.sessiondata
		targetpresetdata['tem'] = self.temdata
		targetpresetdata['ccdcamera'] = self.camdata
		targetpresetdata['magnification'] = self.params['magnification']
		targetpresetdata['name'] = 'target'

		### setup camera data
		targetcameradata = leginon.leginondata.CameraEMData()
		targetcameradata['session'] = self.sessiondata
		targetcameradata['ccdcamera'] = self.camdata
		targetcameradata['dimension'] = {'x': 1, 'y': 1}
		targetcameradata['binning'] = {'x': 1, 'y': 1}

		### setup scope data
		targetscopedata = leginon.leginondata.ScopeEMData()
		targetscopedata['session'] = self.sessiondata
		targetscopedata['tem'] = self.temdata
		targetscopedata['magnification'] = self.params['magnification']
		targetscopedata['high tension'] = self.params['kv']*1000
		targetscopedata['defocus'] = 0.0
		targetscopedata['stage position'] = { 'x': 0.0, 'y': 0.0, 'z': 0.0, 'a': 0.0, }

		### setup image data
		targetimgdata = leginon.leginondata.AcquisitionImageData()
		targetimgdata['session'] = self.sessiondata
		targetimgdata['scope'] = targetscopedata
		targetimgdata['camera'] = targetcameradata
		targetimgdata['preset'] = targetpresetdata
		targetimgdata['label'] = 'UploadTarget'
		targetimgdata['image'] = numpy.ones((1,1))

		### required
		targetimgdata['filename'] = "null"

		### setup target data
		targetdata = leginon.leginondata.AcquisitionImageTargetData()
		targetdata['session'] = self.sessiondata
		targetdata['image'] = targetimgdata
		targetdata['scope'] = targetscopedata
		targetdata['camera'] = targetcameradata
		targetdata['preset'] = targetpresetdata
		targetdata['type'] = "upload"
		targetdata['version'] = 0
		targetdata['number'] = seriescount
		targetdata['status'] = "done"

		return targetdata

	#=====================
	def getTiltSeries(self, seriescount):
		if self.params['uploadtype'] != "tiltseries":
			return None

		tiltq = leginon.leginondata.TiltSeriesData()
		tiltq['session'] = self.sessiondata
		tiltq['number'] = seriescount

		return tiltq

	#=====================
	def getTiltAngle(self, numinseries):
		"""
		get tilt angle from list, if no list return 0.0

		Note: numinseries starts at 1
		"""
		if self.params['angleliststr'] is not None:
			return self.anglelist[numinseries-1]
		return 0.0

	#=====================
	def getImageDefocus(self, numinseries):
		"""
		get defocus from list, if no list return 'defocus' variable

		Note: numinseries starts at 1
		"""
		if self.params['defocus'] is None:
			return self.defocuslist[numinseries-1]
		return self.params['defocus']

	#=====================
	def uploadImageInformation(self, newimagepath, dims, seriescount, numinseries):
		### setup scope data
		scopedata = leginon.leginondata.ScopeEMData()
		scopedata['session'] = self.sessiondata
		scopedata['tem'] = self.temdata
		scopedata['magnification'] = self.params['magnification']
		scopedata['high tension'] = self.params['kv']*1000

		### these are dynamic variables
		scopedata['defocus'] = self.getImageDefocus(numinseries)
		scopedata['stage position'] = {
			'x': 0.0,
			'y': 0.0,
			'z': 0.0,
			'a': self.getTiltAngle(numinseries),
		}

		### setup camera data
		cameradata = leginon.leginondata.CameraEMData()
		cameradata['session'] = self.sessiondata
		cameradata['ccdcamera'] = self.camdata
		cameradata['dimension'] = dims
		cameradata['binning'] = {'x': 1, 'y': 1}

		### setup camera data
		presetdata = leginon.leginondata.PresetData()
		presetdata['session'] = self.sessiondata
		presetdata['tem'] = self.temdata
		presetdata['ccdcamera'] = self.camdata
		presetdata['magnification'] = self.params['magnification']
		presetdata['name'] = 'upload%d'%(numinseries)

		### setup image data
		imgdata = leginon.leginondata.AcquisitionImageData()
		imgdata['session'] = self.sessiondata
		imgdata['scope'] = scopedata
		imgdata['camera'] = cameradata
		imgdata['preset'] = presetdata
		basename = os.path.basename(newimagepath)
		if basename.endswith(".mrc"):
			basename = os.path.splitext(basename)[0]
		imgdata['filename'] = basename
		imgdata['label'] = 'UploadImage'

		### fake small image array to avoid overloading memory
		imgdata['image'] = numpy.ones((1,1))

		### use this for defocal group data
		imgdata['target'] = self.setDefocalTargetData(seriescount)

		### use this for tilt series data
		imgdata['tilt series'] = self.getTiltSeries(seriescount)

		if self.params['commit'] is True:
			imgdata.insert()

	#=====================
	def updatePixelSizeCalibration(self):
		"""
		This updates the pixel size for the magnification on the
		instruments before the image is published.  Later query will look up the
		pixelsize calibration closest and before the published image 
		"""
		pixelcalibrationq = leginon.leginondata.PixelSizeCalibrationData()
		pixelcalibrationq['magnification'] = self.params['magnification']
		pixelcalibrationq['tem'] = self.temdata
		pixelcalibrationq['ccdcamera'] = self.camdata
		pixelcalibrationdatas = pixelcalibrationq.query(results=1)
		if pixelcalibrationdatas:
			lastpixelsize = pixelcalibrationdatas[0]['pixelsize']
			if self.params['mpix'] == lastpixelsize:
				if pixelcalibrationq['session'] is not None:
					lastsession = pixelcalibrationq['session']['name']
					if lastsession == self.params['sessionname']:
						### values have been set correctly already
						return False

		pixelcalibrationq['pixelsize'] = self.params['mpix']
		pixelcalibrationq['comment'] = 'based on uploaded pixel size'
		pixelcalibrationq['session'] = self.sessiondata

		if self.params['commit'] is True:
			pixelcalibrationq.insert()

	#=====================
	def newImagePath(self, mrcfile, numinseries):
		extension = os.path.splitext(mrcfile)[1]
		rootname = os.path.splitext(os.path.basename(mrcfile))[0]
		newname = self.params['sessionname']+"_"+rootname+"_"+str(numinseries)+extension
		newimagepath = os.path.join(self.leginonimagedir, newname)
		return newimagepath

	#=====================
	def copyfile(self, oldmrcfile, newmrcfile):
		# invert image density
		if self.params['invert'] is False:
			shutil.copy(oldmrcfile, newmrcfile)
		else:
			tmpimage = mrc.read(oldmrcfile)
			tmpimage *= -1.0
			mrc.write(tmpimage,newmrcfile)
		if apFile.fileSize(oldmrcfile) != apFile.fileSize(newmrcfile):
			apDisplay.printError("File sizes are different")

	#=====================
	def getImageDimensions(self, mrcfile):
		mrcheader = mrc.readHeaderFromFile(mrcfile)
		x = int(mrcheader['nx'].astype(numpy.uint16))
		y = int(mrcheader['ny'].astype(numpy.uint16))
		return {'x': x, 'y': y}

	#=====================
	def start(self):
		"""
		This is the core of your function.
		You decide what happens here!
		"""
		### try and get the appion instruments
		self.getAppionInstruments()

		### create new session, so we have a place to store the log file
		self.createNewSession()

		mrclist = self.getImagesInDirectory(self.params['imagedir'])

		for i in range(min(len(mrclist),6)):
			print mrclist[i]

		numinseries = 1
		seriescount = 1
		count = 1
		t0 = time.time()
		for mrcfile in mrclist:
			### rename image
			newimagepath = self.newImagePath(mrcfile, numinseries)

			### get image dimensions
			dims = self.getImageDimensions(mrcfile)

			### set pixel size in database
			self.updatePixelSizeCalibration()

			### upload image
			self.uploadImageInformation(newimagepath, dims, seriescount, numinseries)

			## copy the file
			self.copyfile(mrcfile, newimagepath)

			### counting
			numinseries += 1
			if numinseries % (self.params['seriessize']+1) == 0:
				### reset series counter
				seriescount += 1
				numinseries = 1

			#print count, seriescount, numinseries
			timeperimage = (time.time()-t0)/float(count)
			apDisplay.printMsg("time per image: %s"
				%(apDisplay.timeString(timeperimage)))
			esttime = timeperimage*(len(mrclist) - count)
			apDisplay.printMsg("estimated time remaining for %d of %d images: %s"
				%(len(mrclist)-count, len(mrclist), apDisplay.timeString(esttime)))
			### counting
			count += 1

#=====================
#=====================
if __name__ == '__main__':
	upimages = UploadImages()
	upimages.start()
	upimages.close()

