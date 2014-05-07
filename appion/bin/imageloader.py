#!/usr/bin/env python

#pythonlib
import os
import shutil
import time
import numpy
import math
import glob
#appion
from appionlib import appionLoop2
from appionlib import apDatabase
from appionlib import apDisplay
from appionlib import apProject
from appionlib import apEMAN
#leginon
import leginon.leginondata
import leginon.projectdata
import leginon.leginonconfig
#pyami
from pyami import mrc

class ImageLoader(appionLoop2.AppionLoop):
	#=====================
	def __init__(self):
		"""
		appionScript OVERRIDE
		"""
		self.processcount = 0
		appionLoop2.AppionLoop.__init__(self)

	#=====================
	def setupParserOptions(self):
		"""
		standard appionScript
		"""
		### id info
		self.parser.add_option("--userid", dest="userid", type="int",
			help="Leginon User database ID", metavar="INT")

		self.parser.add_option("--dir", dest="imgdir", type="string", metavar="DIR",
			help="directory containing MRC files for upload")
		self.filetypes = ("mrc","dm3","dm2","tif")
		self.parser.add_option("--filetype", dest="filetype", metavar="TYPE",
			help="input image filetype",
			type="choice", choices=self.filetypes, default="mrc")

		self.parser.add_option("--append-session", dest="appendsession", default=True,
			action="store_true", help="Append session to image names")
		self.parser.add_option("--no-append-session", dest="appendsession", default=True,
			action="store_false", help="Do not append session to image names")

		self.parser.add_option("--invert", dest="invert", default=False,
			action="store_true", help="Invert image density")

		### mode 1: command line params
		self.parser.add_option("--tiltgroup", dest="tiltgroup", type="int", default=1,
			help="Number of image per tilt series, default=1", metavar="INT")
		self.parser.add_option("--apix", dest="apix", type="float", metavar="FLOAT",
			help="angstroms per pixel")
		self.parser.add_option("--df", dest="df", type="float", metavar="DEFOCUS",
			help="nominal defocus (negative, in microns)")
		self.parser.add_option("--mag", dest="mag", type="int", metavar="MAG",
			help="nominal magnification")
		self.parser.add_option("--kv", dest="kv", type="int", metavar="INT",
			help="high tension (in kilovolts)")
		self.parser.add_option("--cs", dest="cs", type="float", metavar="#.#",
			default=2.0, help="spherical aberration constant (in mm), e.g., --cs=2.0")
		self.parser.add_option("--binx", dest="binx", type="int", metavar="INT",
			default=1, help="binning in x (default=1)")
		self.parser.add_option("--biny", dest="biny", type="int", metavar="INT",
			default=1, help="binning in y (default=1)")
		### mode 2: batch script
		self.parser.add_option("--batch", "--batchparams", dest="batchscript", type="str",
			help="File containing image parameters", metavar="FILE")



	#=====================
	def checkConflicts(self):
		"""
		standard appionScript
		"""
		if self.params['batchscript'] is None:
			#mode 1: command line params
			if self.params['apix'] is None:
				apDisplay.printError("If not specifying a parameter file, supply apix")
			if self.params['df'] is None:
				apDisplay.printError("If not specifying a parameter file, supply defocus of the images")
			if self.params['df'] > 0:
				apDisplay.printWarning("defocus is being switched to negative")
				self.params['df']*=-1
			if self.params['df'] > -0.1:
				apDisplay.printError("defocus must be in microns")
			if self.params['mag'] is None:
				apDisplay.printError("If not specifying a parameter file, supply magnification")
			if self.params['kv'] is None:
				apDisplay.printError("If not specifying a parameter file, supply a high tension")
			if self.params['kv'] > 1000:
				apDisplay.printError("High tension must be in kilovolts (e.g., 120)")
			if self.params['cs'] < 0.0:
				apDisplay.printError("Cs value must be in mm (e.g., 2.0)")
			if self.params['imgdir'] is None:
				apDisplay.printError("If not specifying a parameter file, specify directory containing images")
			if not os.path.exists(self.params['imgdir']):
				apDisplay.printError("specified path '%s' does not exist\n"%self.params['imgdir'])
		elif not os.path.isfile(self.params["batchscript"]):
			#mode 2: batch script
			apDisplay.printError("Could not find Batch parameter file: %s"%(self.params["batchscript"]))

		if self.params['sessionname'] is None:
			apDisplay.printError("Please provide a Session name, e.g., --session=09feb12b")
		if self.params['projectid'] is None:
			apDisplay.printError("Please provide a Project database ID, e.g., --projectid=42")
		if self.params['description'] is None:
			apDisplay.printError("Please provide a Description, e.g., --description='awesome data'")
		if self.params['userid'] is None:
			self.params['userid'] = self.getLeginonUserId()

		#This really is not conflict checking but to set up new session.
		#There is no place in Appion script for this special case

		sessionq = leginon.leginondata.SessionData(name=self.params['sessionname'])
		sessiondatas = sessionq.query()
		if len(sessiondatas) > 0:
			### METHOD 1 : session already exists
			apDisplay.printColor("Add images to an existing session", "cyan")
			sessiondata = sessiondatas[0]
			### what about linking an existing session with project id to a new project id
			oldprojectid = apProject.getProjectIdFromSessionName(self.params['sessionname'])
			if oldprojectid != self.params['projectid']:
				apDisplay.printError("You cannot assign an existing session (PID %d) to a different project (PID %d)"%
					(oldprojectid, self.params['projectid']))
			if self.params['rundir'] is not None and self.params['rundir'] != sessiondata['image path']:
				apDisplay.printError("Specified Rundir is different from current session path\n%s\n%s"
					%( self.params['rundir'], sessiondata['image path']))
			### only allows uploading more images if all images are uploaded through appion host.
			instrumentq = leginon.leginondata.InstrumentData(hostname='appion',name='AppionTEM')
			appiontems = instrumentq.query()
			allappionscopeems = []
			for appiontem in appiontems:
				scopeemq = leginon.leginondata.ScopeEMData(session=sessiondatas[0],tem=appiontem)
				appionscopeems = scopeemq.query()
				if appionscopeems:
					allappionscopeems.extend(appionscopeems)
			scopeemq = leginon.leginondata.ScopeEMData(session=sessiondatas[0])
			allscopeems = scopeemq.query()
			if len(allscopeems) > len(allappionscopeems):

				apDisplay.printError("You can only add more images to an existing session that contains only appion uploads")
		else:
			### METHOD 2 : create new session
			apDisplay.printColor("Creating a new session", "cyan")
			try:
				directory = leginon.leginonconfig.mapPath(leginon.leginonconfig.IMAGE_PATH)
			except AttributeError:
				apDisplay.printWarning("Could not set directory")
				directory = ''
			if self.params['userid'] is not None:
				userdata = leginon.leginondata.UserData.direct_query(self.params['userid'])
			else:
				userdata = None
			sessiondata = self.createSession(userdata, self.params['sessionname'], self.params['description'], directory)

		self.linkSessionProject(sessiondata, self.params['projectid']) 
		self.session = sessiondata
		return

	#=====================
	def commitToDatabase(self,imagedata):
		"""
		standard appionScript
		"""
		return

	#=====================
	def setRunDir(self):
		"""
		standard appionScript
		"""	
		self.params['rundir'] = self.session['image path']

	#=====================
	#===================== Appion Loop Hacks
	#=====================

	#=====================
	def getLeginonUserId(self):
		"""
		standard appionScript
		"""
		try:
			### sometimes this crashes
			username = os.getlogin()
		except:
			return None

		userq = leginon.leginondata.UserData()
		userq['username'] = username
		userdatas = userq.query(results=1)
		if not userdatas or len(userdatas) == 0:
			return None
		return userdatas[0].dbid

	#=====================
	def preLoopFunctions(self):
		"""
		standard appionLoop
		"""	
		self.getAppionInstruments()

	#=====================
	def run(self):
		"""
		appionLoop OVERRIDE
		processes all images
		"""
		self.pixelsizes = {}
		### get images from upload image parameters file
		self.getAllImages()
		os.chdir(self.params['rundir'])
		self.preLoopFunctions()
		### start the loop
		self.badprocess = False
		self.stats['startloop'] = time.time()
		apDisplay.printColor("\nBeginning Main Loop", "green")
		imgnum = 0
		while imgnum < len(self.batchinfo):
			self.stats['startimage'] = time.time()
			info = self.readUploadInfo(self.batchinfo[imgnum])
			imgnum += 1
			### CHECK IF IT IS OKAY TO START PROCESSING IMAGE
			if not self._startLoop(info):
				continue

			### START any custom functions HERE:
			imgdata, results = self.loopProcessImage(info)
			### WRITE db data
			if self.badprocess is False:
				if self.params['commit'] is True:
					apDisplay.printColor(" ==== Committing data to database ==== ", "blue")
					self.loopCommitToDatabase(imgdata)
					self.commitResultsToDatabase(imgdata, results)
				else:
					apDisplay.printWarning("not committing results to database, all data will be lost")
					apDisplay.printMsg("to preserve data start script over and add 'commit' flag")
					self.writeResultsToFiles(imgdata, results)
			else:
				apDisplay.printWarning("IMAGE FAILED; nothing inserted into database")
				self.badprocess = False

			### FINISH with custom functions

			self._writeDoneDict(imgdata['filename'])

			load = os.getloadavg()[0]
			if load > 2.0:
				apDisplay.printMsg("Load average is high %.2f"%(load))
				sleeptime = min(load, 60)
				time.sleep(load)

			self._printSummary()
		self.postLoopFunctions()
		self.close()

	#=====================
	def getAllImages(self):
		"""
		appionLoop OVERRIDE
		"""
		if self.params['batchscript']:
			self.batchinfo = self.readBatchUploadInfo()
		else:
			self.batchinfo = self.setBatchUploadInfo()
		self.stats['imagecount'] = len(self.batchinfo)

	#=====================
	def _startLoop(self, info):
		"""
		appionLoop OVERRIDE
		initilizes several parameters for a new image
		and checks if it is okay to start processing image
		"""
		if info is None:
			self.stats['lastimageskipped'] = True
			self.stats['skipcount'] += 1
			return False
		name = info['filename']
		# check to see if image of the same name is already in leginon
		imgq = leginon.leginondata.AcquisitionImageData(session=self.session, filename=name)
		results = imgq.query(readimages=False)
		if results:
			apDisplay.printWarning("File %s.mrc exists at the destination" % name)
			apDisplay.printWarning("Skip Uploading")
			self.stats['lastimageskipped'] = True
			self.stats['skipcount'] += 1
			return False
		#calc images left
		self.stats['imagesleft'] = self.stats['imagecount'] - self.stats['count']
		#only if an image was processed last
		if(self.stats['lastcount'] != self.stats['count']):
			apDisplay.printColor( "\nStarting image "+str(self.stats['count'])\
				+" ( skip:"+str(self.stats['skipcount'])+", remain:"\
				+str(self.stats['imagesleft'])+" ) file: "\
				+apDisplay.short(name), "green")
			self.stats['lastcount'] = self.stats['count']
			self._checkMemLeak()
		# check to see if image has already been processed
		if self._alreadyProcessed(info):
			return False
		self.stats['waittime'] = 0
		return True

	#=====================
	def processImage(self, imginfo):
		"""
		standard appionLoop
		"""	
		self.updatePixelSizeCalibration(imginfo)
		origimgfilepath = imginfo['original filepath']
		newimgfilepath = os.path.join(self.params['rundir'], imginfo['filename']+".mrc")
		apDisplay.printMsg("Reading original image: "+origimgfilepath)
		### In order to obey the rule of first save image then insert 
		### database record, image need to be read as numpy array, not copied
		### single image should not overload memory
		imagearray = mrc.read(origimgfilepath)
		imgdata = self.makeImageData(imagearray,imginfo)
		pixeldata = None
		return imgdata, pixeldata

	#=====================
	#===================== custom functions
	#=====================

	#=====================
	def publish(self,data,dbforce=False):
		"""
		sinedon already does this check, but since we want
		the results back whether commit or not, we need to do it here.
		"""
		results = data.query(readimages=False)
		if not results or dbforce:
			if self.params['commit'] is True:
				data.insert(force=dbforce)
			return data
		return results[0]

	#=====================
	def createSession(self, user, name, description, directory):
		imagedirectory = os.path.join(leginon.leginonconfig.unmapPath(directory), name, 'rawdata').replace('\\', '/')
		initializer = {
			'name': name,
			'comment': description,
			'user': user,
			'image path': imagedirectory,
		}
		sessionq = leginon.leginondata.SessionData(initializer=initializer)
		sessiondata = self.publish(sessionq)
		# session become unreserved if is committed
		reservationq = leginon.leginondata.SessionReservationData(name=sessiondata['name'],reserved=False)
		self.publish(reservationq,True)
		return sessiondata
		

	#=====================
	def linkSessionProject(self, sessiondata, projectid):
		projectexpq = leginon.projectdata.projectexperiments()
		projectexpq['project'] = leginon.projectdata.projects.direct_query(projectid)
		projectexpq['session'] = sessiondata
		if self.params['commit'] is True:
			projectexpq.insert()

	#=====================
	def readBatchUploadInfo(self):
		# in this example, the batch script file should be separated by tab
		# see example in function readUploadInfo for format
		batchfilename = self.params['batchscript']
		if not os.path.exists(batchfilename):
			apDisplay.printError('Batch file %s not exist' % batchfilename)
			return []
		batchfile = open(batchfilename,'r')
		lines = batchfile.readlines()
		batchfile.close()
		batchinfo = []
		count = 0
		for line in lines:
			count += 1
			#remove white space at ends
			sline = line.strip()
			if ' ' in sline:
				apDisplay.printWarning("There is a space in the batch file on line %d"%(count))
			#remove white space at ends
			cols = sline.split('\t')
			if len(cols) > 1:
				batchinfo.append(cols)
			else:
				apDisplay.printWarning("Skipping line %d"%(count))
		return batchinfo

	#=====================
	def setBatchUploadInfo(self):
		# instead of specifying a batch script file, the same values
		# are applied to all images for upload
		batchinfo = []
		imgdir = os.path.join(self.params['imgdir'],"*."+self.params['filetype'])
		upfiles = glob.glob(imgdir)
		if not upfiles:
			apDisplay.printError("No images for upload in '%s'"%self.params['imgdir'])
		upfiles.sort()
		for upfile in upfiles:
			fname = os.path.abspath(upfile)
			apix = "%.4e"%(self.params['apix']*1e-10)
			binx = "%d"%(self.params['binx'])
			biny = "%d"%(self.params['biny'])
			mag =  "%d"%(self.params['mag'])
			df =   "%.4e"%(self.params['df']*1e-6)
			ht =   "%d"%(self.params['kv']*1000)
			cols = [fname, apix, binx, biny, mag, df, ht]
			batchinfo.append(cols)
		return batchinfo

	#=====================
	def readUploadInfo(self,info=None):
		if info is None:
			# example
			info = ['test.mrc','2e-10','1','1','50000','-2e-6','120000']
		apDisplay.printMsg('reading image info')
		try:
			uploadedInfo = {}
			uploadedInfo['original filepath'] = os.path.abspath(info[0])
			uploadedInfo['unbinned pixelsize'] = float(info[1])
			if uploadedInfo['unbinned pixelsize'] > 1e-6:
				apDisplay.printError("pixel size is bigger than a micron, that is ridiculous")
			uploadedInfo['binning'] = {'x':int(info[2]),'y':int(info[3])}
			uploadedInfo['magnification'] = int(info[4])
			uploadedInfo['defocus'] = float(info[5])
			uploadedInfo['high tension'] = int(info[6])
			if len(info) > 7:
				uploadedInfo['stage a'] = float(info[7])*math.pi/180.0
			# add other items in the dictionary and set to instrument in the function
			# setInfoToInstrument if needed
		except:
			apDisplay.printError("Bad batch file parameters")

		if not os.path.isfile(uploadedInfo['original filepath']):
			apDisplay.printWarning("Original File %s does not exist" % uploadedInfo['original filepath'])
			apDisplay.printWarning("Skip Uploading")
			return None

		uploadedInfo['filename'] = self.setNewFilename(uploadedInfo['original filepath'])
		newimgfilepath = os.path.join(self.params['rundir'],uploadedInfo['filename']+".tmp.mrc")
		### convert to mrc in new session directory if not mrc:
		if self.params['filetype'] != "mrc":
			if not os.path.isfile(newimgfilepath):
				emancmd = "proc2d %s %s edgenorm flip mrc"%(uploadedInfo['original filepath'], newimgfilepath)
				apEMAN.executeEmanCmd(emancmd)
				if not os.path.exists(newimgfilepath):
					apDisplay.printError("image conversion to mrc did not execute properly")
			uploadedInfo['original filepath'] = newimgfilepath
		tmpimage = mrc.read(uploadedInfo['original filepath'])
		# invert image density
		if self.params['invert'] is True:
			tmpimage *= -1.0
			mrc.write(tmpimage,uploadedInfo['original filepath'])
		shape = tmpimage.shape
		uploadedInfo['dimension'] = {'x':shape[1],'y':shape[0]}
		uploadedInfo['session'] = self.session
		uploadedInfo['pixel size'] = uploadedInfo['unbinned pixelsize']*uploadedInfo['binning']['x']
		return uploadedInfo

	#=====================
	def setNewFilename(self, original_filepath):
		keep_old_name = True
		if keep_old_name:
			fullname = os.path.basename(original_filepath)
			found = fullname.rfind('.'+self.params['filetype'])
			if found > 0:
				name = fullname[:found]
			else:
				name = fullname
		else:
			imgq = leginon.leginondata.AcquisitionImageData(session=self.session)
			results = imgq.query(readimages=False)
			if results:
				imgcount = len(results)
			else:
				imgcount = 0
			name =  self.params['sessionname']+'_%05dupload' % (imgcount+1)
		if self.params['appendsession'] is True:
			name = self.params['sessionname']+"_"+name
		return name

	#=====================
	def getTiltSeries(self):
		if self.params['tiltgroup'] is None or self.params['tiltgroup']==1:
			return None
		else:
			divide = float(self.processcount)/self.params['tiltgroup']
			self.processcount += 1
			residual = divide - math.floor(divide)
			tiltq = leginon.leginondata.TiltSeriesData(session=self.session)
			results = tiltq.query(results=1,readimages=False)
			if residual > 0:
				return results[0]
			else:
				if results:
					series = results[0]['number']+1
				else:
					series = 1
				tiltq = leginon.leginondata.TiltSeriesData(session=self.session,number=series)
				return self.publish(tiltq)

	#=====================
	def getAppionInstruments(self):
		instrumentq = leginon.leginondata.InstrumentData()
		instrumentq['hostname'] = "appion"
		instrumentq['name'] = "AppionTEM"
		instrumentq['cs'] = self.params['cs'] * 1e-3
		self.temdata = instrumentq
		
		instrumentq = leginon.leginondata.InstrumentData()
		instrumentq['hostname'] = "appion"
		instrumentq['name'] = "AppionCamera"
		self.camdata = instrumentq
		return

	#=====================
	def makeImageData(self,imagearray,info):
		scopedata = leginon.leginondata.ScopeEMData(session=self.session,tem =self.temdata)
		scopedata['defocus'] = info['defocus']
		scopedata['magnification'] = info['magnification']
		scopedata['high tension'] = info['high tension']
		if 'stage a' in info.keys():
			tiltseriesdata = leginon.leginondata.TiltSeriesData(session=self.session)
			scopedata['stage position'] = {'x':0.0,'y':0.0,'z':0.0,'a':info['stage a']}
		else:
			scopedata['stage position'] = {'x':0.0,'y':0.0,'z':0.0,'a':0.0}
		cameradata = leginon.leginondata.CameraEMData(session=self.session,ccdcamera=self.camdata)
		cameradata['dimension'] = info['dimension']
		cameradata['binning'] = info['binning']
		presetdata = leginon.leginondata.PresetData(session=self.session,tem=self.temdata,ccdcamera= self.camdata)
		presetdata['name'] = 'upload'
		presetdata['magnification'] = info['magnification']
		imgdata = leginon.leginondata.AcquisitionImageData(session=self.session,scope=scopedata,camera=cameradata,preset=presetdata)
		imgdata['tilt series'] = self.getTiltSeries()
		imgdata['filename'] = info['filename']
		imgdata['label'] = 'upload'
		# single image should not overload memory
		imgdata['image'] = imagearray
		self.publish(imgdata)
		return imgdata

	#=====================
	def updatePixelSizeCalibration(self,info):
		# This updates the pixel size for the magnification on the
		# instruments before the image is published.  Later query will look up the
		# pixelsize calibration closest and before the published image 
		mag = info['magnification']
		pixelsize = info['unbinned pixelsize']
		caldata = leginon.leginondata.PixelSizeCalibrationData()
		caldata['magnification'] = mag
		caldata['pixelsize'] = pixelsize
		caldata['comment'] = 'based on uploaded pixel size'
		caldata['session'] = self.session
		caldata['tem'] = self.temdata
		caldata['ccdcamera'] = self.camdata
		# If this pixel size is not what last entered in this upload,
		# force db insert even if the same values exists because someone might 
		# have changed the calibration earlier and now you need to change it back
		if mag in self.pixelsizes.keys() and pixelsize == self.pixelsizes[mag]:
			return
		else:
			self.publish(caldata, dbforce=True)
			self.pixelsizes[mag] = pixelsize
			time.sleep(1.0)

#=====================
#=====================
#=====================
if __name__ == '__main__':
	imgLoop = ImageLoader()
	imgLoop.run()

