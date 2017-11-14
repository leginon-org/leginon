#!/usr/bin/env python
import os
import time
import glob
import shutil
import numpy
from pyami import mrc
import leginon.leginondata
import leginon.projectdata
from appionlib import appionScript
from appionlib import apDisplay
from appionlib import apParam
from appionlib import apFile
from appionlib.appiondata import ApSEMData
from PIL import Image
import re
from math import pi,cos
import subprocess
cmd = os.popen("csh -c 'modulecmd python load imod'")
exec(cmd)

#this part was takes from  William Rice's semheader.py code - http://emg.nysbc.org/redmine/issues/4973

fei_tag=34682 # this tag ID contains all the FEI header information in ascii format
keys=(
	  ("Date",""),("HV","V"),("Beam",""),("HFW","m"),("ApertureDiameter","m"),("BeamCurrent","A"),
	  ("DynamicFocusIsOn",""),("StageTa","radians"),("TiltCorrectionAngle","radians"),("Dwelltime","s"),
	  ("PixelWidth","m"),("FrameTime","s"),("Integrate",""),("WorkingDistance","m"),("ResolutionX","pixels"),
	  ("ResolutionY","pixels"))

#these numbers were taken from SEMC Helios by Ed Emg on 8/15/2017
e_beam_mag=[4973, 5000, 9947, 10000, 29840, 30000, 100000, 149200, 600000] #x mag
HFW	   =[30,   29.8, 15,   14.9,  5,	 4.97,  1.49,   1,	  0.249 ]  #Horizontal Field of View in microns
class UploadSEMImages(appionScript.AppionScript):
	def setupParserOptions(self):	
		self.parser.add_option("--image-dir", dest="imagedir",
			help="Directory that contains TIF files to upload", metavar="DIR")
		self.parser.add_option("--leginon-output-dir", dest="leginondir",
			help="Leginon output directory, e.g., --leginon-output-dir=/data/leginon",
			metavar="DIR")
		self.parser.add_option("--session-name", dest="sessionname",
			help="Session name, e.g., 17aug06a. If provided append images to this session.")
		self.parser.add_option("--z-slice", dest="z_slice",
			help="Section slice width (z width) in nm")
		
	def checkConflicts(self):
		if self.params['imagedir'] is None:
			apDisplay.printError("Please provide a image directory, e.g., --imagedir=/path/to/files/")
			if not os.path.isdir(self.params['imagedir']):
				apDisplay.printError("Image directory '%s' does not exist"%(self.params['imagedir']))


		### set session name if undefined
		if not 'sessionname' in self.params or self.params['sessionname'] is None:
			self.params['sessionname'] = self.getUnusedSessionName()
			if self.params['description'] is None:
				apDisplay.printError("Please provide a description, e.g., --description='test'")

		### set leginon dir if undefined
		if self.params['leginondir'] is None:
			try:
				self.params['leginondir'] = leginon.leginonconfig.unmapPath(leginon.leginonconfig.IMAGE_PATH).replace('\\','/')
			except AttributeError:
				apDisplay.printError("Please provide a leginon output directory, "
					+"e.g., --leginon-output-dir=/data/leginon")
		self.leginonimagedir = os.path.join(self.params['leginondir'], self.params['sessionname'], 'rawdata')
		if self.params['z_slice'] is None:
			self.params['z_slice'] = ""

	def getUserData(self):
		username = apParam.getUsername()
		userq = leginon.leginondata.UserData()
		userq['username'] = username
		userdatas = userq.query(results=1)
		if not userdatas:
			return None
		return userdatas[0]

	def getUnusedSessionName(self):
		### get standard appion time stamp, e.g., 10jun30
			
		sessionq = leginon.leginondata.SessionData()
		sessionq['name'] = self.params['runname']
		sessiondatas = sessionq.query(results=1)
		if not sessiondatas:
			return self.params['runname']

		apDisplay.printColor("Found session name with runname %s, creating new name"%(self.params['runname']), "blue")
		print sessiondatas[0]

		for char in string.lowercase:
			sessionname = self.timestamp+char
			sessionq = leginon.leginondata.SessionData()
			sessionq['name'] = sessionname
			sessiondatas = sessionq.query(results=1)
			if not sessiondatas:
				break
		return sessionname

	#=====================
	def getSession(self):
		
		userdata = self.getUserData()
		sessionq = None
		if self.params['sessionname']:
			session = leginon.leginondata.SessionData(name=self.params['sessionname'])
			sessionq = session.query() 
			if sessionq:
				apDisplay.printColor("Found session" + self.params['sessionname'], "cyan")
				sessionq = sessionq[0]
				
		if not sessionq:
			apDisplay.printColor("Creating a new session", "cyan")
			sessionq = leginon.leginondata.SessionData()
			sessionq['name'] = self.params['sessionname']
			sessionq['image path'] = self.leginonimagedir
			sessionq['comment'] = self.params['description']
			sessionq['user'] = userdata
			sessionq['hidden'] = False
			apDisplay.printColor("Created new session %s" % (self.params['sessionname']), "cyan")
			
		projectdata = leginon.projectdata.projects.direct_query(self.params['projectid'])
		
		projectexpq = leginon.projectdata.projectexperiments()
		projectexpq['project'] = projectdata
		projectexpq['session'] = sessionq
		if self.params['commit'] is True:
			projectexpq.insert()
		
		self.sessiondata = sessionq
		
		return

	#=====================
	def getAppionInstruments(self):
		instrumentq = leginon.leginondata.InstrumentData()
		instrumentq['hostname'] = "appion"
		instrumentq['name'] = "AppionSEM"
		self.temdata = instrumentq
		
		instrumentq = leginon.leginondata.InstrumentData()
		instrumentq['hostname'] = "appion"
		instrumentq['name'] = "AppionCamera"
		self.camdata = instrumentq
		return
	
	def setRunDir(self):
		self.params['rundir'] = self.leginonimagedir

	def getImagesInDirectory(self, directory):
		searchstring = os.path.join(directory, "*.tif")
		tif_list = glob.glob(searchstring)
		if len(tif_list) == 0:
			apDisplay.printError("Did not find any images to upload")
		tif_list.sort()
		return tif_list

	def getImageDimensions(self, mrcfile):
		mrcheader = mrc.readHeaderFromFile(mrcfile)
		x = int(mrcheader['nx'].astype(numpy.uint16))
		y = int(mrcheader['ny'].astype(numpy.uint16))
		return {'x': x, 'y': y}

	#=====================
	def uploadImageInformation(self, imagearray, newimagepath, dims):
		### setup scope data
		scopedata = leginon.leginondata.ScopeEMData()
		scopedata['session'] = self.sessiondata
		scopedata['magnification'] = numpy.interp(self.SEM_Data['HFW'],HFW, e_beam_mag)
		scopedata['high tension'] = self.SEM_Data['HV']
		
		### setup camera data
		presetdata = leginon.leginondata.PresetData()
		presetdata['session'] = self.sessiondata
		presetname = 'upload'

		presetdata['name'] = presetname

		### setup camera data
		cameradata = leginon.leginondata.CameraEMData()
		cameradata['session'] = self.sessiondata
		cameradata['ccdcamera'] = self.camdata
		cameradata['dimension'] = dims
		cameradata['binning'] = {'x': 1, 'y': 1}
		cameradata['pixel size'] = {'x':float(self.SEM_Data['PixelWidth'])*10e-9,
								'y':float(self.SEM_Data['PixelWidth'])*10e-9}
		### setup image data
		imgdata = leginon.leginondata.AcquisitionImageData()
		imgdata['session'] = self.sessiondata
		imgdata['preset'] = presetdata
		basename = os.path.basename(newimagepath)
		if basename.endswith(".mrc"):
			basename = os.path.splitext(basename)[0]
		imgdata['filename'] = basename
		imgdata['label'] = 'UploadImage'

		### use real imagearray to ensure that file is saved before database insert
		imgdata['image'] = imagearray

		if self.params['commit'] is True:
			imgdata.insert()
		return imgdata
	
	def prepareImageForUpload(self,origfilepath):	
		### In order to obey the rule of first save image then insert 
		### database record, image need to be read as numpy array, not copied
		### single image should not overload memory
		apDisplay.printMsg("Reading original image: "+origfilepath)
		im=Image.open(origfilepath)
		self.SEM_Data = {}
		header=im.tag[fei_tag]

		if isinstance(header,tuple):#sd added this since header type is tuple in the sample images from https://catalog.data.gov/dataset/fib-sem-image-data-set-of-caenorhabditis-elegans-exposed-to-60-nm-au-nanoparticles
			header=header[0] 
		 
		for key in keys:
		   match=re.search(re.escape(key[0]) + r"=(.*)\r\n",header)
		   if key[1] != 'radians' :
			  #import pdb;pdb.set_trace()
			  scientific=re.search(r'(\d+\.?\d*)e-(\d+)',match.group(1))
			  if scientific: #outputs 'engineering' notation rather than scientific: assumes exponents negative and numbers positive
				 mantissa=float(scientific.group(1))
				 ordinate=int(scientific.group(2))
				 toeven3 = (3- (ordinate %3)) %3
				 ordinate += toeven3
				 mantissa *= 10**toeven3
				 ordinate /= 3
				 self.SEM_Data[key[0]] = mantissa
			  else: #decimals: no conversion needed
				 self.SEM_Data[key[0]] = match.group(1)
		   elif match.group(1): #angle measurement: output in degrees if there is an angle listed
			  degrees = 180.0 * float(match.group(1)) / pi
			  self.SEM_Data[key[0]]  = degrees
		
		# output corrected y pixel size if image was taken using defocus gradient
		df=re.search(r"DynamicFocusIsOn=yes\r\n",header)
		if df:
		   tang=re.search(r"TiltCorrectionAngle=(.*)\r\n",header)
		   pixwidth=re.search(r"PixelWidth=(.*)\r\n",header)
		   tang=abs(float(tang.group(1)))
		   corr_ypix= float(pixwidth.group(1))/cos(tang) *1E9   # convert to nm
		   self.SEM_Data['corr_ypix'] =  corr_ypix


	def startInit(self):
		"""
		Initialization of variables
		"""
		self.getAppionInstruments()
		self.getSession()

	def newImagePath(self, mrcfile):
		extension = os.path.splitext(mrcfile)[1]
		rootname = os.path.splitext(os.path.basename(mrcfile))[0]
		newroot = rootname
		if not newroot.startswith(self.params['sessionname']):
			newroot = self.params['sessionname']+"_"+newroot
		newroot = newroot.replace(' ', '')
		newname = newroot+".mrc"
		newimagepath = os.path.join(self.leginonimagedir, newname)
		return newimagepath
	
	def uploadSEMData(self, image_data):
		SEMData = ApSEMData()
		SEMData['image'] = image_data
		SEMData['date'] = self.SEM_Data['Date']
		SEMData['hv'] = float(self.SEM_Data['HV'])
		SEMData['beam'] = self.SEM_Data['Beam']
		SEMData['hfw'] = float(self.SEM_Data['HFW'])
		SEMData['aperture_diameter'] = float(self.SEM_Data['ApertureDiameter'])
		SEMData['beam_current'] = float(self.SEM_Data['BeamCurrent'])
		SEMData['dynamic_focus_is_on'] = self.SEM_Data['DynamicFocusIsOn']
		SEMData['stage_ta'] = float(self.SEM_Data['StageTa'])
		SEMData['tilt_correction_angle'] = float(self.SEM_Data['TiltCorrectionAngle'])
		SEMData['dwell_time'] = float(self.SEM_Data['Dwelltime'])
		SEMData['pixel_width'] = float(self.SEM_Data['PixelWidth'])
		SEMData['integrate'] = float(self.SEM_Data['Integrate'])
		SEMData['working_distance'] = float(self.SEM_Data['WorkingDistance'])
		SEMData['resolution_x'] = int(self.SEM_Data['ResolutionX'])
		SEMData['resolution_y'] = int(self.SEM_Data['ResolutionY'])
		SEMData['z_slice'] = self.params['z_slice']
		
		if self.params['commit'] is True:
			SEMData.insert()
			
	def start(self):
		"""
		This is the core of your function.
		You decide what happens here!
		"""
		self.startInit()
		tif_list = self.getImagesInDirectory(self.params['imagedir'])
		count = 1
		t0 = time.time()
		for tif_file in tif_list:
			if not os.path.isfile(tif_file):
				continue
			newimagepath = self.newImagePath(tif_file)
			if os.path.exists(newimagepath):
				apDisplay.printMsg("Path exists: skipping "+newimagepath)
				continue
			imagearray = self.prepareImageForUpload(tif_file)
			cmd = ['tif2mrc','-s',tif_file, newimagepath]
			
			p = subprocess.Popen(cmd)
			p.communicate()

			imagearray = mrc.read(newimagepath)
			### get image dimensions
			dims = self.getImageDimensions(newimagepath)
			### upload image
			image_data = self.uploadImageInformation(imagearray, newimagepath, dims)
			self.uploadSEMData(image_data)
			timeperimage = (time.time()-t0)/float(count)
			apDisplay.printMsg("time per image: %s"
				%(apDisplay.timeString(timeperimage)))
			esttime = timeperimage*(len(tif_list) - count)
			apDisplay.printMsg("estimated time remaining for %d of %d images: %s"
				%(len(tif_list)-count, len(tif_list), apDisplay.timeString(esttime)))
			### counting
			count += 1

#=====================
#=====================
if __name__ == '__main__':
	upimages = UploadSEMImages()
	upimages.start()
	upimages.close()
