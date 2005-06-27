#
# COPYRIGHT:
#			 The Leginon software is Copyright 2003
#			 The Scripps Research Institute, La Jolla, CA
#			 For terms of the license agreement
#			 see	http://ami.scripps.edu/software/leginon-license
#

import data
import imagefun
import node
import project
import threading
import time
import gui.wx.ManualAcquisition
import instrument
import os
import re

class AcquireError(Exception):
	pass

class ManualAcquisition(node.Node):
	panelclass = gui.wx.ManualAcquisition.Panel
	settingsclass = data.ManualAcquisitionSettingsData
	defaultsettings = {
		'camera settings': None,
		'screen up': False,
		'screen down': False,
		'correct image': False,
		'save image': False,
		'image label': '',
		'loop pause time': 0.0,
		'low dose': False,
		'low dose pause time': 4.0,
	}
	def __init__(self, id, session, managerlocation, **kwargs):
		self.loopstop = threading.Event()
		self.loopstop.set()
		node.Node.__init__(self, id, session, managerlocation, **kwargs)

		self.lowdosemode = None

		try:
			self.projectdata = project.ProjectData()
		except project.NotConnectedError:
			self.projectdata = None
		self.gridmapping = {}
		self.gridbox = None
		self.grid = None

		self.instrument = instrument.Proxy(self.objectservice,
																				self.session,
																				self.panel)

		self.start()

	def getImageStats(self, image):
		if image is None:
			return {'mean': None, 'stdev': None, 'min': None, 'max': None}
		mean = imagefun.mean(image)
		stdev = imagefun.stdev(image, known_mean=mean)
		min = imagefun.min(image)
		max = imagefun.max(image)
		return {'mean': mean, 'stdev': stdev, 'min': min, 'max': max}

	def acquire(self):
		correct = self.settings['correct image']
		if correct:
			prefix = ''
		else:
			prefix = 'un'
		self.logger.info('Acquiring %scorrected image...' % prefix)
		self.instrument.ccdcamera.Settings = self.settings['camera settings']
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
				image = self.instrument.imagecorrection.getImage(ccdcameraname=ccdcameraname)
			else:
				image = self.instrument.ccdcamera.Image

		self.logger.info('Displaying image...')
		stats = self.getImageStats(image)
		self.setImage(image, stats=stats)

		if self.settings['save image']:
			self.logger.info('Saving image to database...')
			try:
				self.publishImageData(imagedata)
			except node.PublishError, e:
				message = 'Error saving image to database'
				self.logger.info(message)
				if str(e):
					message += ' (%s)' % str(e)
				self.logger.error(message)
				raise AcquireError
		self.logger.info('Image acquisition complete')

	def preExposure(self):
		if self.settings['screen up']:
			self.instrument.tem.MainScreenPosition = 'up'

		if self.settings['low dose']:
			self.lowdosemode = self.instrument.tem.LowDoseMode
			if self.lowdosemode is None:
				self.logger.warning('Failed to save previous low dose state')
			self.instrument.tem.LowDoseMode = 'exposure'
			time.sleep(self.settings['low dose pause time'])

	def postExposure(self):
		if self.lowdosemode is not None:
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
		try:
			path = imagedata.path()
		except Exception, e:
			raise node.PublishError(e)
		filenames = os.listdir(path)
		pattern = '^%s_[0-9]{%d}%s.%s$' % (prefix, digits, suffix, extension)
		number = 0
		end = len('%s.%s' % (suffix, extension))
		for filename in filenames:
			if re.search(pattern, filename):
				n = int(filename[-digits - end:-end])
				if n > number:
					number = n
		number += 1
		if number >= 10**digits:
			raise node.PublishError('too many images, time to go home')
		filename = ('%s_%0' + str(digits) + 'd%s') % (prefix, number, suffix)
		imagedata['filename'] = filename

	def publishImageData(self, imagedata):
		acquisitionimagedata = data.AcquisitionImageData(initializer=imagedata)
		if self.grid is not None:
			gridinfo = self.gridmapping[self.grid]
			griddata = data.GridData()
			griddata['grid ID'] = gridinfo['gridId']
			acquisitionimagedata['grid'] = griddata

		acquisitionimagedata['label'] = self.settings['image label']

		self.setImageFilename(acquisitionimagedata)

		try:
			self.publish(imagedata['scope'], database=True)
			self.publish(imagedata['camera'], database=True)
			self.publish(acquisitionimagedata, database=True)
		except RuntimeError:
			raise node.PublishError

	def acquireImage(self):
		try:
			try:
				self.preExposure()
			except RuntimeError:
				self.panel.acquisitionDone()
				return

			try:
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

