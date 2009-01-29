#
# COPYRIGHT:
#			 The Leginon software is Copyright 2003
#			 The Scripps Research Institute, La Jolla, CA
#			 For terms of the license agreement
#			 see	http://ami.scripps.edu/software/leginon-license
#

import data
import event
import node
import project
import threading
import time
import gui.wx.ManualAcquisition
import player
import instrument
import os
import re
import calibrationclient
import copy
from pyami import arraystats, imagefun
import numpy
import corrector

class AcquireError(Exception):
	pass

class ManualAcquisition(node.Node):
	panelclass = gui.wx.ManualAcquisition.Panel
	settingsclass = data.ManualAcquisitionSettingsData
	eventoutputs = node.Node.eventoutputs + [event.AcquisitionImagePublishEvent]
	defaultsettings = {
		'camera settings': None,
		'screen up': False,
		'screen down': False,
		'beam blank': False,
		'correct image': False,
		'save image': False,
		'image label': '',
		'loop pause time': 0.0,
		'low dose': False,
		'low dose pause time': 5.0,
		'defocus1switch': False,
		'defocus1': 0.0,
		'defocus2switch': False,
		'defocus2': 0.0,
		'dark': False,
		'manual focus exposure time': 100.0,
		'force annotate': False,
		'reduced params': False,
	}
	def __init__(self, id, session, managerlocation, **kwargs):
		self.loopstop = threading.Event()
		self.loopstop.set()
		node.Node.__init__(self, id, session, managerlocation, **kwargs)

		self.lowdosemode = None
		self.defocus = None

		try:
			self.projectdata = project.ProjectData()
		except:
			self.projectdata = None
		self.gridmapping = {}
		self.gridbox = None
		self.grid = None

		self.instrument = instrument.Proxy(self.objectservice,
																				self.session,
																				self.panel)

		self.dosecal = calibrationclient.DoseCalibrationClient(self)

		self.manualchecklock = threading.Lock()
		self.maskradius = 1.0
		self.focexptime = 100.0
		self.man_power = None
		self.man_image = None
		self.powmin = 0
		self.powmax = 1e10
		self.manualplayer = player.Player(callback=self.onManualPlayer)
		self.comment = ''
		self.published_images = []
		self.viewstatus = None

		self.corclient = corrector.CorrectorClient(self)
		self.initSameCorrection()
		
		self.start()

	def getImageStats(self, image):
		if image is None:
			return {'mean': None, 'stdev': None, 'min': None, 'max': None}

		stats = arraystats.all(image)
		stats['stdev'] = stats['std']
		return stats

	def initSameCorrection(self):
		self.correctargs = None

	def acquireCorrectedImage(self):
		if not self.correctargs:
			## acquire image and scope/camera params
			imagedata = self.instrument.getData(data.CameraImageData)
			imarray = imagedata['image']
			self.correctargs = {}
			camdata = imagedata['camera']
			self.correctargs['ccdcamera'] = camdata['ccdcamera']
			corstate = data.CorrectorCamstateData()
			corstate['dimension'] = camdata['dimension']
			corstate['offset'] = camdata['offset']
			corstate['binning'] = camdata['binning']
			self.correctargs['camstate'] = corstate
			self.correctargs['scopedata'] = imagedata['scope']
		else:
			## acquire only raw image
			imarray = self.instrument.ccdcamera.Image

		corrected = self.corclient.correct(original=imarray, **self.correctargs)
		return corrected

	def acquire(self):
		correct = self.settings['correct image']
		if correct:
			prefix = ''
		else:
			prefix = 'un'
		self.logger.info('Acquiring %scorrected image...' % prefix)
		self.instrument.ccdcamera.Settings = self.settings['camera settings']
		if self.settings['dark']:
			self.instrument.ccdcamera.ExposureType = 'dark'
		else:
			self.instrument.ccdcamera.ExposureType = 'normal'


		'''
		if self.settings['save image']:
			try:
				if correct:
					dataclass = data.CorrectedCameraImageData
				else:
					dataclass = data.CameraImageData
				imagedata = self.instrument.getData(dataclass)
			except Exception, e:
				self.logger.exception('Error acquiring image: %s' % e)
				raise AcquireError
			image = imagedata['image']
		else:
			if correct:
				ccdcameraname = self.instrument.getCCDCameraName()
				imagedata = self.instrument.imagecorrection.getImageData(ccdcameraname=ccdcameraname)
				image = imagedata['image']
			else:
				image = self.instrument.ccdcamera.Image
		'''

		try:
			if correct:
				#dataclass = data.CorrectedCameraImageData
				image = self.acquireCorrectedImage()
			else:
				#dataclass = data.CameraImageData
				image = self.instrument.ccdcamera.Image
			#imagedata = self.instrument.getData(dataclass)
			if self.settings['reduced params']:
				scope = self.instrument.getData(data.ManualAcquisitionScopeEMData)
				scope = data.ScopeEMData(initializer=scope)
			else:
				scope = self.instrument.getData(data.ScopeEMData)
			camera = self.instrument.getData(data.CameraEMData, image=False)
			imagedata = data.CameraImageData(image=image, scope=scope, camera=camera)
			imagedata['session'] = self.session
		except Exception, e:
			self.logger.exception('Error acquiring image: %s' % e)
			raise AcquireError
		image = imagedata['image']


		self.logger.info('Displaying image...')
		self.getImageStats(image)
		self.setImage(image)

		if self.settings['save image']:
			self.logger.info('Saving image to database...')
			try:
				self.publishImageData(imagedata, save=True)
				self.published_images.append(self.getMostRecentImageData(self.session))
			except node.PublishError, e:
				raise
				message = 'Error saving image to database'
				self.logger.info(message)
				if str(e):
					message += ' (%s)' % str(e)
				self.logger.error(message)
				raise AcquireError
		else:
			self.publishImageData(imagedata, save=False)
		self.logger.info('Image acquisition complete')

	def preExposure(self):
		if self.settings['low dose']:
			self.lowdosemode = self.instrument.tem.LowDoseMode
			if self.lowdosemode is None:
				self.logger.warning('Failed to save previous low dose state')
			self.instrument.tem.BeamBlank = 'on'
			self.instrument.tem.LowDoseMode = 'exposure'
			time.sleep(self.settings['low dose pause time'])
		if self.settings['screen up']:
			self.instrument.tem.MainScreenPosition = 'up'
			time.sleep(self.settings['low dose pause time'])
		if self.settings['low dose']:
			self.instrument.tem.BeamBlank = 'off'

	def postExposure(self):
		if self.lowdosemode is not None:
			if self.settings['beam blank']:
				self.instrument.tem.BeamBlank = 'on'
			self.instrument.tem.LowDoseMode = self.lowdosemode
			self.lowdosemode = None
			time.sleep(self.settings['low dose pause time'])

		if self.settings['screen down']:
			self.instrument.tem.MainScreenPosition = 'down'

	def setImageFilename(self, imagedata):
		prefix = self.session['name']
		digits = 5
		suffix = 'ma'
		extension = 'mrc'
		if self.defocus is None:
			defindex = '_0'
		else:
			defindex = '_%d' % (self.defocus,)
		try:
			path = imagedata.mkpath()
		except Exception, e:
			raise
			raise node.PublishError(e)
		filenames = os.listdir(path)
		pattern = '^%s_[0-9]{%d}%s_[0-9].%s$' % (prefix, digits, suffix, extension)
		number = 0
		end = len('%s%s.%s' % (suffix, defindex, extension))
		for filename in filenames:
			if re.search(pattern, filename):
				n = int(filename[-digits - end:-end])
				if n > number:
					number = n
		if self.defocus != 2:
			number += 1
		if number >= 10**digits:
			raise node.PublishError('too many images, time to go home')
		filename = ('%s_%0' + str(digits) + 'd%s' + '%s') % (prefix, number, suffix, defindex)
		imagedata['filename'] = filename

	def publishImageData(self, imagedata, save):
		acquisitionimagedata = data.AcquisitionImageData(initializer=imagedata)
		if save:
			if self.grid is not None:
				gridinfo = self.gridmapping[self.grid]
				griddata = data.GridData()
				griddata['grid ID'] = gridinfo['gridId']
				acquisitionimagedata['grid'] = griddata
	
			acquisitionimagedata['label'] = self.settings['image label']
	
			self.setImageFilename(acquisitionimagedata)
			acquisitionimagedata.attachPixelSize()
	
			try:
				self.publish(imagedata['scope'], database=True)
				self.publish(imagedata['camera'], database=True)
				self.publish(acquisitionimagedata, database=True)
			except RuntimeError:
				raise node.PublishError
		
		## publish event even if no save
		self.publish(acquisitionimagedata, pubevent=True)

	def acquireImage(self, dose=False):
		self.published_images = []
		try:
			try:
				self.preExposure()
			except RuntimeError:
				self.panel.acquisitionDone()
				return

			try:
				if dose:
					self.measureDose()
				else:
					if self.settings['defocus1switch']:
						self.logger.info('Setting defocus 1: %s' % (self.settings['defocus1'],))
						self.instrument.tem.Defocus = self.settings['defocus1']
						self.defocus = 1
						self.acquire()
					if self.settings['defocus2switch']:
						self.logger.info('Setting defocus 2: %s' % (self.settings['defocus2'],))
						self.instrument.tem.Defocus = self.settings['defocus2']
						self.defocus = 2
						self.acquire()
					if not (self.settings['defocus1switch'] or self.settings['defocus2switch']):
						self.defocus = None
						self.acquire()
			except AcquireError:
				self.panel.acquisitionDone()
				return

			try:
				self.postExposure()
			except RuntimeError:
				self.panel.acquisitionDone()
				return
		except:
			self.panel.acquisitionDone()
			raise

		self.logger.info('Image acquired.')
		self.panel.acquisitionDone()

	def loopStarted(self):
		self.panel.loopStarted()

	def loopStopped(self):
		self.panel.loopStopped()

	def acquisitionLoop(self):
		self.logger.info('Starting acquisition loop...')

		try:
			self.preExposure()
		except RuntimeError:
			self.loopStopped()
			return

		self.loopstop.clear()
		self.logger.info('Acquisition loop started')
		self.loopStarted()
		while True:
			if self.loopstop.isSet():
				break
			self.published_images = []
			try:
				self.acquire()
			except AcquireError:
				self.loopstop.set()
				break
			pausetime = self.settings['loop pause time']
			if pausetime > 0:
				self.logger.info('Pausing for ' + str(pausetime) + ' seconds...')
				time.sleep(pausetime)

		try:
			self.postExposure()
		except RuntimeError:
			self.loopStopped()
			return

		self.loopStopped()
		self.logger.info('Acquisition loop stopped')

	def acquisitionLoopStart(self):
		if not self.loopstop.isSet():
			self.loopStopped()
			return
		self.logger.info('Starting acquisition loop...')
		loopthread = threading.Thread(target=self.acquisitionLoop)
		loopthread.setDaemon(1)
		loopthread.start()

	def acquisitionLoopStop(self):
		self.logger.info('Stopping acquisition loop...')
		self.loopstop.set()

	def onSetPauseTime(self, value):
		if value < 0:
			return 0
		return value

	def cmpGridLabel(self, x, y):
		return cmp(self.gridmapping[x]['location'], self.gridmapping[y]['location'])

	def getGrids(self, label):
		gridboxes = self.projectdata.getGridBoxes()
		labelindex = gridboxes.Index(['label'])
		gridbox = labelindex[label].fetchone()
		gridboxid = gridbox['gridboxId']
		gridlocations = self.projectdata.getGridLocations()
		gridboxidindex = gridlocations.Index(['gridboxId'])
		gridlocations = gridboxidindex[gridboxid].fetchall()
		grids = self.projectdata.getGrids()
		grididindex = grids.Index(['gridId'])
		self.gridmapping = {}
		for gridlocation in gridlocations:
			grid = grididindex[gridlocation['gridId']].fetchone()
			key = '%d - %s' % (gridlocation['location'], grid['label'])
			self.gridmapping[key] = {'gridId': gridlocation['gridId'],
																'location': gridlocation['location'],
																'label': grid['label']}
		keys = self.gridmapping.keys()
		keys.sort(self.cmpGridLabel)
		return keys

	def getGridBoxes(self):
		gridboxes = self.projectdata.getGridBoxes()
		labelindex = gridboxes.Index(['label'])
		gridboxlabels = map(lambda d: d['label'], gridboxes.getall())
		gridboxlabels.reverse()
		return gridboxlabels

	def measureDose(self):
		self.logger.info('acquiring dose image')
		# configure camera using settings, but only 512x512 to save time
		origcam = self.settings['camera settings']
		# deep copy so internal dicts don't get modified
		tmpcam = copy.deepcopy(origcam)

		## cut down to 512x512, adjust offset to keep same center
		cutsize = 1024
		for axis in ('x','y'):
			change = origcam['dimension'][axis] - cutsize
			if change > 0:
				tmpcam['dimension'][axis] = cutsize
				tmpcam['offset'][axis] += (change / 2)

		self.instrument.ccdcamera.Settings = tmpcam

		# acquire image
		imagedata = self.instrument.getData(data.CorrectedCameraImageData)

		# display
		self.logger.info('Displaying %dx%d dose image...' % (cutsize,cutsize))
		self.getImageStats(imagedata['image'])
		self.setImage(imagedata['image'])

		# calculate dose
		dose = self.dosecal.dose_from_imagedata(imagedata)

		dosedata = data.DoseMeasurementData()
		dosedata['dose'] = dose
		self.publish(dosedata, database=True, dbforce=True)
		self.instrument.ccdcamera.Settings = origcam
		self.logger.info('measured dose: %.3e e/A^2' % (dose/1e20,))
		

	def onManualPlayer(self, state):
		self.panel.playerEvent(state, self.panel.manualdialog)

	def manualNow(self):
		istr = 'Using current tem condition for manual focus check'
		self.logger.info(istr)
		### Warning:  no target is being used, you are exposing
		### whatever happens to be under the beam
		t = threading.Thread(target=self.manualCheckLoop, args=())
		t.setDaemon(1)
		t.start()

	def onManualCheck(self):
		evt = gui.wx.ManualAcquisition.ManualCheckEvent(self.panel)
		self.panel.GetEventHandler().AddPendingEvent(evt)

	def onManualCheckDone(self):
		try:
			self.instrument.ccdcamera.Settings = self.settings['camera settings']
		except:
			self.logger.error('unable to set camera parameters')
		evt = gui.wx.ManualAcquisition.ManualCheckDoneEvent(self.panel)
		self.panel.GetEventHandler().AddPendingEvent(evt)

	def manualCheckLoop(self, presetname=None, emtarget=None):
		## copied and simplified from focuser.py
		## go to preset and target
		self.logger.info('Starting manual focus loop, please confirm defocus...')
		self.beep()
		camdata1 = {}

		camdata1['exposure time']=self.focexptime
		cutsize = 1024
		camdata1['dimension'] = {'x':cutsize, 'y':cutsize}
		camdata1['binning'] = {'x':1, 'y':1}
		camsize = self.instrument.ccdcamera.getCameraSize()
		camdata1['offset'] = {'x': (camsize['x']-cutsize)/2, 'y':(camsize['y']-cutsize)/2}
		self.instrument.ccdcamera.Settings = camdata1
		self.manualplayer.play()
		self.onManualCheck()
		while True:
			t0 = time.time()
			state = self.manualplayer.state()
			if state == 'stop':
				break
			elif state == 'pause':
				if self.manualplayer.wait() == 'stop':
					break
			# acquire image, show image and power spectrum
			# allow user to adjust defocus and stig
			correction = self.settings['correct image']
			camdata1['exposure time'] = self.focexptime
			
			self.manualchecklock.acquire()
			self.instrument.ccdcamera.Settings = camdata1
			try:
				if correction:
					imagedata = self.instrument.getData(data.CorrectedCameraImageData)
				else:
					imagedata = self.instrument.getData(data.CameraImageData)
				imarray = imagedata['image']
			except:
				raise
				self.manualchecklock.release()
				self.manualplayer.pause()
				self.logger.error('Failed to acquire image, pausing...')
				continue
			
			self.manualchecklock.release()
			pow = imagefun.power(imarray, self.maskradius)
			man_power = pow.astype(numpy.float32)
			self.man_power = numpy.clip(man_power,self.powmin,self.powmax)
			self.man_image = imarray.astype(numpy.float32)
			self.panel.setManualImage(self.man_image, 'Image')
			self.panel.setManualImage(self.man_power, 'Power')

			#sleep if too fast in simulation
			t1 = time.time()
			if t1-t0 < 0.5:
				time.sleep(0.5-(t1-t0))
				
		self.onManualCheckDone()
		self.logger.info('Manual focus check completed')

	def saveComment(self):
		images = self.published_images
		viewstatus = self.viewstatus
		if not viewstatus:
			return

		if len(images) == 0:
			self.logger.error('No image to be annotated')
			return

		for image in images:
			filename = image['filename']
			namelist = filename.split('_')
			shortname = '_'.join(namelist[1:])
			
			if not self.comment:
				pass
			else:
				comment = data.ImageCommentData()
				comment['session'] = self.session
				comment['image'] = image
				comment['comment']=self.comment
				self.publish(comment, database=True, dbforce=False)
				self.logger.info('Annotated %s' % shortname)
			if not viewstatus or viewstatus == 'normal':
				pass
			else:
				status = data.ImageStatusData()
				status['session'] = self.session
				status['image'] = image
				status['status'] = viewstatus
				self.publish(status, database=True, dbforce=True)
				self.logger.info('Viewing status of %s set to %s' % (shortname, viewstatus))
				
	def checkExistingCommentStatus(self):
		images = self.published_images
		if not images:
			self.logger.warning('No saved image for annotation')
			return True
		
		for imagedata in images:
			commentq = data.ImageCommentData()
			commentq['image'] = imagedata
			commentresults = self.research(commentq, readimages=False)
			
			statusq = data.ImageStatusData()
			statusq['image'] = imagedata
			statusresults = self.research(statusq, readimages=False)
			
			if commentresults or statusresults:
				self.logger.warning('Image already annotated')
				return True
		return False
				
				
	def getMostRecentImageData(self,sessiondata):
		imageq = data.AcquisitionImageData()
		imageq['session'] = sessiondata
		images = self.research(imageq, readimages=False, results=1)
		return images[0]
	
				

			
			
		
