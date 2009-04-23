#
# COPYRIGHT:
#			 The Leginon software is Copyright 2003
#			 The Scripps Research Institute, La Jolla, CA
#			 For terms of the license agreement
#			 see	http://ami.scripps.edu/software/leginon-license
#

import leginondata
import event
import node
import project
import threading
import time
import manualacquisition
import gui.wx.ManualImageLoader
import player
import instrument
import os
import re
import calibrationclient
import copy
from pyami import arraystats, imagefun, mrc
import numpy
import version

default_batch = os.path.join(version.getInstalledLocation(),'upload_example.txt')
class AcquireError(Exception):
	pass

class ManualImageLoader(manualacquisition.ManualAcquisition):
	panelclass = gui.wx.ManualImageLoader.Panel
	settingsclass = leginondata.ManualImageLoaderSettingsData
	eventoutputs = node.Node.eventoutputs + [event.AcquisitionImagePublishEvent]
	defaultsettings = {
		'instruments': {'tem': None, 'ccdcamera': None},
		'save image': False,
		'batch script': default_batch,
		'tilt group': 1,
		'camera settings': None,
	}

	def __init__(self, id, session, managerlocation, **kwargs):
		self.loopstop = threading.Event()
		self.loopstop.set()
		node.Node.__init__(self, id, session, managerlocation, **kwargs)

		self.defocus = None
		self.instrument = instrument.Proxy(self.objectservice,
																				self.session,
																				self.panel)

		self.calclient = calibrationclient.PixelSizeCalibrationClient(self)

		self.manualplayer = player.Player(callback=self.onManualPlayer)
		self.comment = ''
		self.published_images = []
		self.viewstatus = None
		self.grid = None

		self.start()

	def acquire(self):
		#This replaces the function of the same name in ManualAcquisition
		#to pretend an image acquisition
		self.logger.info('Loading image as if acquired...')
		self.instrument.ccdcamera.Settings = self.uploadedInfo['camera settings']

		try:
			image = self.uploadedInfo['image']
			scope = self.instrument.getData(leginondata.ScopeEMData)
			camera = self.instrument.getData(leginondata.CameraEMData)
			imagedata = leginondata.CameraImageData(image=image, scope=scope, camera=camera)
			imagedata['session'] = self.session
		except Exception, e:
			self.logger.exception('Error loading image: %s' % e)
			raise AcquireError
		image = imagedata['image']


		self.logger.info('Displaying image...')
		self.getImageStats(image)
		self.setImage(image)

		self.settings['image label'] = 'uploaded'
		if self.settings['save image']:
			self.logger.info('Saving image to database...')
			try:
				filedir, filename = os.path.split(self.uploadedInfo['original filepath'])
				notes = 'uploaded from %s' % self.uploadedInfo['original filepath']
				self.comment = notes
				self.publishImageData(imagedata, save=True)
				self.published_images.append(self.getMostRecentImageData(self.session))
				self.viewstatus = 'normal'
				self.saveComment()
			except Exception, e:
				message = 'Error saving image to database'
				if str(e):
					message += ' (%s)' % str(e)
				self.logger.error(message)
				raise AcquireError
		else:
			self.publishImageData(imagedata, save=False)
		self.logger.info('Image acquisition complete')

	def acquireImage(self):
		#single image testing disabled in GUI
		self.published_images = []
		try:
			self.readUploadInfo()
			self.setInfoToInstrument()
			self.acquire()
		except:
			self.panel.acquisitionDone()
			return
		self.logger.info('Image uploaded.')
		self.panel.acquisitionDone()

	def acquisitionLoop(self):
		#batch loading
		self.logger.info('Starting uploading loop...')
		batchinfo = self.readBatchUploadInfo()
		self.loopstop.clear()
		self.logger.info('Image loading loop started')
		self.loopStarted()
		self.tilt = 0
		for info in batchinfo:
			if self.loopstop.isSet():
				break
			self.published_images = []
			try:
				self.readUploadInfo(info)
				self.setTiltSeries()
				self.setInfoToInstrument()
				self.acquire()
			except:
				self.loopstop.set()
				break
		self.loopstop.set()

		self.loopStopped()
		self.logger.info('Image loading loop stopped')

	def setImageFilename(self, imagedata):
		try:
			path = imagedata.mkpath()
		except Exception, e:
			raise node.PublishError(e)
		try:
			filedir, filename = os.path.split(self.uploadedInfo['original filepath'])
			filenamesplit = filename.split('.')
			if filenamesplit[-1] == 'mrc':
				filenamesplit.pop()
			filename = '.'.join(filenamesplit)
			if os.path.exists(os.path.join(path,filename+'.mrc')):
				e = '%s already exists in %s' % (filename+'.mrc',path)
				self.logger.error(e)
				raise node.PublishError()
		except:
			raise
		self.logger.info('save the image as %s.mrc' % filename)
		imagedata['filename'] = filename
		imagedata['tilt series'] = self.tiltseries

	def readBatchUploadInfo(self):
		# in this example, the batch script file should be separated by tab
		# see example in function readUploadInfo for format
		batchfilename = self.settings['batch script']
		if not os.path.exists(batchfilename):
			self.logger.error('Batch file %s not exist' % batchfilename)
			return []
		batchfile = open(batchfilename,'r')
		lines = batchfile.readlines()
		batchfile.close()
		batchinfo = []
		for line in lines:
			texts = line.split('\n')
			info = texts[0].split('\t')
			batchinfo.append(info)
		return batchinfo

	def readUploadInfo(self,info=None):
		if info is None:
			# example
			info = ['test.mrc','2e-10','1','1','50000','-2e-6','120000']
		self.logger.info('reading image info')
		try:
			self.uploadedInfo = {}
			self.uploadedInfo['original filepath'] = os.path.abspath(info[0])
			self.uploadedInfo['unbinned pixelsize'] = float(info[1])
			self.uploadedInfo['binning'] = {'x':int(info[2]),'y':int(info[3])}
			self.uploadedInfo['magnification'] = int(info[4])
			self.uploadedInfo['defocus'] = float(info[5])
			self.uploadedInfo['high tension'] = int(info[6])
			if len(info) > 7:
				self.uploadedInfo['stage a'] = float(info[7])*3.14159/180.0
			# add other items in the dictionary and set to instrument in the function
			# setInfoToInstrument if needed
		except:
			#self.logger.exception('Bad batch file parameters')
			raise
		try:
			self.uploadedInfo['image'] = mrc.read(self.uploadedInfo['original filepath'])
		except IOError, e:
			self.logger.exception('File %s not available for upload' % self.uploadedInfo['original filepath'])
			raise

	def setInfoToInstrument(self):
		self.logger.info('setting instrument parameters')
		try:
			self.instrument.setTEM(self.settings['instruments']['tem'])
			self.instrument.setCCDCamera(self.settings['instruments']['ccdcamera'])
		except Exception, e:
			msg = 'Instrument Set failed: %s' % (e,)
			self.logger.error(msg)
			raise AquireError(msg)
		# uploaded information is send to the instruments to simulate an acquisition
		self.instrument.tem.HighTension = self.uploadedInfo['high tension']
		self.instrument.tem.Defocus = self.uploadedInfo['defocus']
		self.instrument.tem.Magnification = self.uploadedInfo['magnification']
		try:
			self.instrument.tem.StagePosition = {'a':self.uploadedInfo['stage a']}
		except:
			pass
		cam_settings = self.settings['camera settings']
		shape = self.uploadedInfo['image'].shape
		cam_settings['exposure time'] = 1000
		cam_settings['dimension']['x'] = shape[1]
		cam_settings['dimension']['y'] = shape[0]
		cam_settings['binning']['x'] = self.uploadedInfo['binning']['x']
		cam_settings['binning']['y'] = self.uploadedInfo['binning']['y']
		cam_settings['offset']['x'] = 0
		cam_settings['offset']['y'] = 0
		self.uploadedInfo['camera settings'] = cam_settings
		self.instrument.ccdcamera.Settings = cam_settings
		self.logger.info('instrument parameters set')
		if self.settings['save image']:
			self.updatePixelSizeCalibration()
		self.logger.info('setting instrument parameters')
	
	def updatePixelSizeCalibration(self):
		# This updates the pixel size for the magnification on the
		# instruments before the image is published.  Later query will look up the
		# pixelsize calibration closest and before the published image 
		temdata = self.instrument.getTEMData()
		camdata = self.instrument.getCCDCameraData()
		mag = self.instrument.tem.Magnification
		current_pixelsize = self.calclient.getPixelSize(mag, temdata, camdata)
		if current_pixelsize != self.uploadedInfo['unbinned pixelsize']:
			self.logger.info('Updating pixel size at %d' % mag)
			caldata = leginondata.PixelSizeCalibrationData()
			caldata['magnification'] = mag
			caldata['pixelsize'] = self.uploadedInfo['unbinned pixelsize']
			caldata['comment'] = 'based on uploaded pixel size'
			caldata['session'] = self.session
			caldata['tem'] = temdata
			caldata['ccdcamera'] = camdata
			self.publish(caldata, database=True)
		time.sleep(1.0)

	def setTiltSeries(self):
		grouplimit = self.settings['tilt group']
		if grouplimit	== 1:
			self.tiltseries = None
			self.logger.info('setting tilt series to None')
		else:
			self.logger.info('setting tilt series')
			if self.tilt == 0:
				self.tiltseries = leginondata.TiltSeriesData()
				#self.tiltseries['session'] = self.session
				self.tiltseries['number'] = grouplimit
				self.publish(self.tiltseries, database=True, dbforce=True)
			if self.tilt >=	grouplimit - 1:
				self.tilt = 0
			else:
				self.tilt = self.tilt + 1
