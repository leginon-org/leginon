#
# COPYRIGHT:
#			 The Leginon software is Copyright 2003
#			 The Scripps Research Institute, La Jolla, CA
#			 For terms of the license agreement
#			 see	http://ami.scripps.edu/software/leginon-license
#

import camerafuncs
import data
import imagefun
import node
import project
import threading
import time
import EM
import gui.wx.ManualAcquisition

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
	eventinputs = node.Node.eventinputs + EM.EMClient.eventinputs
	eventoutputs = node.Node.eventoutputs + EM.EMClient.eventoutputs
	def __init__(self, id, session, managerlocation, **kwargs):
		self.loopstop = threading.Event()
		self.loopstop.set()
		node.Node.__init__(self, id, session, managerlocation, **kwargs)
		self.emclient = EM.EMClient(self)
		self.camerafuncs = camerafuncs.CameraFuncs(self)

		self.lowdosemode = None

		self.projectdata = project.ProjectData()
		self.gridmapping = {}
		self.gridbox = None
		self.grid = None

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
		try:
			self.camerafuncs.setCameraDict(self.settings['camera settings'])
			imagedata = self.camerafuncs.acquireCameraImageData(correction=correct)
		except camerafuncs.CameraError, e:
			self.logger.error('Error acquiring image: %s' % e)
			raise AcquireError
		except camerafuncs.NoCorrectorError:
			self.logger.error('Cannot access Corrector node to correct image')
			raise AcquireError
		except Exception, e:
			self.logger.exception('Error acquiring image: %s' % e)
			raise AcquireError
		if imagedata is None:
			if correct:
				self.logger.error('Corrector failed to acquire corrected image')
			else:
				self.logger.error('Instrument failed to acquire image')
			raise AcquireError

		# store EMData to DB
		self.publish(imagedata['scope'], database=True)
		self.publish(imagedata['camera'], database=True)

		self.logger.info('Displaying image...')
		stats = self.getImageStats(imagedata['image'])
		self.setImage(imagedata['image'], stats=stats)
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

	def setScope(self, value):
		scopedata = data.ScopeEMData(initializer=value)
		try:
			self.emclient.setScope(scopedata)
		except node.PublishError:
			self.logger.error('Cannot access EM node')
			self.logger.info('Error setting instrument parameters')
			raise RuntimeError('unable to set instrument parameters')

	def getScope(self, key=None):
		try:
			value = self.emclient.getScope(key)
		except (node.ResearchError, EM.ScopeUnavailable):
			self.logger.error('Cannot access EM node')
			self.logger.info('Error getting instrument parameters')
			raise RuntimeError('unable to get instrument parameters')
		return value

	def preExposure(self):
		if self.settings['screen up']:
			self.setScope({'main screen position': 'up'})

		if self.settings['low dose']:
			self.lowdosemode = self.getScope('low dose mode')
			if self.lowdosemode is None:
				self.logger.warning('Failed to save previous low dose state')
			self.setScope({'low dose mode': 'exposure'})
			time.sleep(self.settings['low dose pause time'])

	def postExposure(self):
		if self.lowdosemode is not None:
			self.setScope({'low dose mode': self.lowdosemode})
			self.lowdosemode = None
			time.sleep(self.settings['low dose pause time'])

		if self.settings['screen down']:
			self.setScope({'main screen position': 'down'})

	def setImageFilename(self, imagedata):
		if imagedata['filename']:
			return
		rootname = self.getRootName(imagedata)
		listlabel = ''

		## use either data id or target number
		if imagedata['target'] is None or imagedata['target']['number'] is None:
			print 'This image does not have a target number, it would be nice to have an alternative to target number, like an image number.  for now we will use dmid'
			numberstr = '%05d' % (imagedata.dmid[-1],)
		else:
			numberstr = '%05d' % (imagedata['target']['number'],)
			if imagedata['target']['list'] is not None:
				listlabel = imagedata['target']['list']['label']
		if imagedata['preset'] is None:
			presetstr = ''
		else:
			presetstr = imagedata['preset']['name']
		mystr = numberstr + presetstr
		sep = '_'
		if listlabel:
			parts = (rootname, listlabel, mystr)
		else:
			parts = (rootname, mystr)
		filename = sep.join(parts)
		imagedata['filename'] = filename

	def getRootName(self, imagedata):
		'''
		get the root name of an image from its parent
		'''
		parent_target = imagedata['target']
		if parent_target is None:
			## there is no parent target
			## create my own root name
			return self.newRootName()

		parent_image = parent_target['image']
		if parent_image is None:
			## there is no parent image
			return self.newRootName()

		## use root name from parent image
		parent_root = parent_image['filename']
		if parent_root:
			return parent_root
		else:
			return self.newRootName()

	def newRootName(self):
		name = self.session['name']
		return name

	def publishImageData(self, imagedata):
		acquisitionimagedata = data.AcquisitionImageData(initializer=imagedata)
		if self.grid is not None:
			gridinfo = self.gridmapping[self.grid]
			griddata = data.GridData()
			griddata['grid ID'] = gridinfo['gridId']
			acquisitionimagedata['grid'] = griddata

		acquisitionimagedata['label'] = self.settings['image label']

		self.setImageFilename(acquisitionimagedata)
		#acquisitionimagedata['filename'] = \
		#	data.ImageData.filename(acquisitionimagedata)[:-4]

		try:
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

