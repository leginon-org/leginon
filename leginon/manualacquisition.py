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
import uidata

class AcquireError(Exception):
	pass

class ManualAcquisition(node.Node):
	def __init__(self, id, session, nodelocations, **kwargs):
		self.loopstop = threading.Event()
		self.loopstop.set()
		self.camerafuncs = camerafuncs.CameraFuncs(self)
		self.gridmapping = {'None': None}
		self.lowdosemode = None
		node.Node.__init__(self, id, session, nodelocations, **kwargs)
		self.defineUserInterface()
		self.start()

	def getImageStats(self, image):
		mean = imagefun.mean(image)
		stdev = imagefun.stdev(image, known_mean=mean)
		min = imagefun.min(image)
		max = imagefun.max(image)
		return {'mean': mean, 'stdev': stdev, 'min': min, 'max': max}

	def displayImageStats(self, image):
		if image is None:
			self.mean.set(None)
			self.min.set(None)
			self.max.set(None)
			self.std.set(None)
		else:
			stats = self.getImageStats(image)
			self.mean.set(stats['mean'])
			self.min.set(stats['min'])
			self.max.set(stats['max'])
			self.std.set(stats['stdev'])

	def acquire(self):
		correct = self.correctimage.get()
		if correct:
			prefix = ''
		else:
			prefix = 'un'
		self.status.set('Acquiring %scorrected image...' % prefix)
		try:
			self.camerafuncs.uiApplyAsNeeded()
			imagedata = self.camerafuncs.acquireCameraImageData(correction=correct)
		except Exception, e:
			if isinstance(e, node.ResearchError):
				self.messagelog.error('Cannot access EM node to acquire image')
			elif isinstance(e, camerafuncs.NoCorrectorError):
				self.messagelog.error('Cannot access Corrector node to correct image')
			else:
				self.messagelog.error('Error acquiring image')
			self.status.set('Error acquiring image')
			raise AcquireError
		if imagedata is None:
			if correct:
				self.messagelog.error('Corrector failed to acquire corrected image')
			else:
				self.messagelog.error('EM failed to acquire image')
			self.status.set('Error acquiring image')
			raise AcquireError
		self.status.set('Displaying image...')
		self.image.set(imagedata['image'])
		self.displayImageStats(imagedata['image'])
		if self.usedatabase.get():
			self.status.set('Saving image to database...')
			try:
				self.publishImageData(imagedata)
			except node.PublishError, e:
				message = 'Error saving image to database'
				self.status.set(message)
				if str(e):
					message += ' (%s)' % str(e)
				self.messagelog.error(message)
				raise AcquireError
		self.status.set('Image acquisition complete')

	def setScope(self, value):
		value['id'] = ('scope',)
		scopedata = data.ScopeEMData(initializer=value)
		try:
			self.publishRemote(scopedata)
		except node.PublishError:
			self.messagelog.error('Cannot access EM node')
			self.status.set('Error setting instrument parameters')
			raise RuntimeError('Unable to set instrument parameters')

	def getScope(self, key):
		try:
			value = self.researchByDataID((key,))
		except node.ResearchError:
			raise
			self.messagelog.error('Cannot access EM node')
			self.status.set('Error getting instrument parameters')
			raise RuntimeError('Unable to get instrument parameters')
		return value[key]

	def preExposure(self):
		if self.up.get():
			self.setScope({'main screen position': 'up'})

		if self.lowdose.get():
			self.lowdosemode = self.getScope('low dose mode')
			self.setScope({'low dose mode': 'exposure'})
			time.sleep(self.pause.get())

	def postExposure(self):
		if self.lowdosemode is not None:
			self.setScope({'low dose mode': self.lowdosemode})
			self.lowdosemode = None
			time.sleep(self.pause.get())

		if self.down.get():
			self.setScope({'main screen position': 'down'})

	def publishImageData(self, imagedata):
		acquisitionimagedata = data.AcquisitionImageData(initializer=imagedata)
		acquisitionimagedata['id'] = self.ID()

		grid = self.gridselect.getSelectedValue()
		gridinfo = self.gridmapping[grid]
		if gridinfo is not None:
			griddata = data.GridData()
			griddata['grid ID'] = gridinfo['gridId']
			acquisitionimagedata['grid'] = griddata

		acquisitionimagedata['filename'] = \
			data.ImageData.filename(acquisitionimagedata)[:-4]

		try:
			self.publish(acquisitionimagedata, database=True)
		except RuntimeError:
			raise node.PublishError

	def acquireImage(self):
		self.acquiremethod.disable()
		self.startmethod.disable()
		self.status.set('Acquiring image...')

		try:
			self.preExposure()
		except RuntimeError:
			self.acquiremethod.enable()
			self.startmethod.enable()
			return

		try:
			self.acquire()
		except AcquireError:
			self.acquiremethod.enable()
			self.startmethod.enable()
			return

		try:
			self.postExposure()
		except RuntimeError:
			self.acquiremethod.enable()
			self.startmethod.enable()
			return

		self.status.set('Image acquired')
		self.acquiremethod.enable()
		self.startmethod.enable()

	def acquisitionLoop(self):
		self.status.set('Starting acquisition loop...')

		try:
			self.preExposure()
		except RuntimeError:
			self.acquiremethod.enable()
			self.startmethod.enable()
			self.stopmethod.disable()
			return

		self.loopstop.clear()
		self.status.set('Acquisition loop started')
		while True:
			if self.loopstop.isSet():
				break
			try:
				self.acquire()
			except AcquireError:
				self.loopstop.set()
				break
			pausetime = self.pausetime.get()
			if pausetime > 0:
				self.status.set('Pausing for ' + str(pausetime) + ' seconds...')
				time.sleep(pausetime)

		try:
			self.postExposure()
		except RuntimeError:
			self.acquiremethod.enable()
			self.startmethod.enable()
			self.stopmethod.disable()
			return

		self.acquiremethod.enable()
		self.startmethod.enable()
		self.stopmethod.disable()
		self.status.set('Acquisition loop stopped')

	def acquisitionLoopStart(self):
		if not self.loopstop.isSet():
			return
		self.status.set('Starting acquisition loop...')
		self.acquiremethod.disable()
		self.startmethod.disable()
		self.stopmethod.enable()
		loopthread = threading.Thread(target=self.acquisitionLoop)
		loopthread.setDaemon(1)
		loopthread.start()

	def acquisitionLoopStop(self):
		self.stopmethod.disable()
		self.status.set('Stopping acquisition loop...')
		self.loopstop.set()

	def onSetPauseTime(self, value):
		if value < 0:
			return 0
		return value

	def cmpGridLabel(self, x, y):
		return cmp(self.gridmapping[x]['location'], self.gridmapping[y]['location'])

	def onGridBoxSelect(self, value):
		projectdata = project.ProjectData()
		if not projectdata.isConnected():
			self.gridboxselect.set(['None'], 0)
			self.gridselect.setList(['None'])
			return 0

		label = self.gridboxselect.getSelectedValue(value)

		if label == 'None':
			self.gridselect.set(['None'], 0)
		else:
			gridboxes = projectdata.getGridBoxes()
			labelindex = gridboxes.Index(['label'])
			gridbox = labelindex[label].fetchone()
			gridboxid = gridbox['gridboxId']
			gridlocations = projectdata.getGridLocations()
			gridboxidindex = gridlocations.Index(['gridboxId'])
			gridlocations = gridboxidindex[gridboxid].fetchall()
			grids = projectdata.getGrids()
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
			self.gridselect.set(['None'] + keys, 0)
			self.gridmapping['None'] = None

		return value

	def updateGridBoxSelection(self):
		projectdata = project.ProjectData()
		if not projectdata.isConnected():
			self.gridboxselect.set(['None'], 0)
			return

		gridboxes = projectdata.getGridBoxes()
		labelindex = gridboxes.Index(['label'])
		gridboxlabels = map(lambda d: d['label'], gridboxes.getall())
		gridboxlabels.append('None')
		gridboxlabels.reverse()
		self.gridboxselect.set(gridboxlabels, 0)

	def defineUserInterface(self):
		node.Node.defineUserInterface(self)

		self.messagelog = uidata.MessageLog('Message Log')
		self.status = uidata.String('Status', '', 'r')

		self.mean = uidata.Float('Mean', None, 'r')
		self.min = uidata.Float('Min', None, 'r')
		self.max = uidata.Float('Max', None, 'r')
		self.std = uidata.Float('Std. Dev.', None, 'r')
		statisticscontainer = uidata.Container('Statistics')
		statisticscontainer.addObject(self.mean, position={'position': (0, 0),
																											'justify': ['center']})
		statisticscontainer.addObject(self.min, position={'position': (0, 1),
																											'justify': ['center']})
		statisticscontainer.addObject(self.max, position={'position': (0, 2),
																											'justify': ['center']})
		statisticscontainer.addObject(self.std, position={'position': (0, 3),
																											'justify': ['center']})

		statuscontainer = uidata.Container('Status')
		statuscontainer.addObject(self.status)

		self.image = uidata.Image('Image', None, 'rw')
		imagecontainer = uidata.Container('Image')
		imagecontainer.addObject(statisticscontainer,
															position={'justify': ['center'], 'expand': 'all'})
		imagecontainer.addObject(self.image)

		self.gridboxselect = uidata.SingleSelectFromList('Grid Box', None, None,
																											'rw')
		self.gridselect = uidata.SingleSelectFromList('Grid', None, None, 'rw')
		self.gridboxselect.setCallback(self.onGridBoxSelect)
		self.updateGridBoxSelection()
		refreshmethod = uidata.Method('Refresh', self.updateGridBoxSelection,
									tooltip='Refresh the grid listing from the project database')

		gridcontainer = uidata.Container('Current Grid')
		gridcontainer.addObjects((self.gridboxselect, self.gridselect))
		gridcontainer.addObject(refreshmethod, position={'justify': ['right']})

		self.lowdose = uidata.Boolean('Low dose', False, 'rw', persist=True,
							tooltip='Switch to low dose exposure mode before acquiring, and'
								+ ' switch back to previous mode when acquisition is completed')
		self.pause = uidata.Number('Low dose pause (seconds)', 5.0, 'rw',
																persist=True,
						tooltip='Number of seconds to pause after switching low dose modes')
		self.up = uidata.Boolean('Up before acquire', True, 'rw',
															persist=True,
						tooltip='Move the main viewing screen up before image acquisition')
		self.down = uidata.Boolean('Down after acquire', True,
																'rw', persist=True,
						tooltip='Move the main viewing screen down after image acquisition'
											+ ' has completed')
		mainscreencontainer = uidata.Container('Main Screen Control')
		mainscreencontainer.addObjects((self.up, self.down))

		self.correctimage = uidata.Boolean('Correct image', True, 'rw',
																				persist=True,
																			tooltip='Correct the acquired image data')
		camerafuncscontainer = self.camerafuncs.uiSetupContainer()
		self.pausetime = uidata.Number('Loop pause time (seconds)', 0.0, 'rw',
																		callback=self.onSetPauseTime, persist=True,
										tooltip='Time in seconds to pause between image acquistion'
														+ ' when continuously acquiring')
		self.usedatabase = uidata.Boolean('Save image to database', True, 'rw',
																			persist=True,
																	tooltip='Save each image and its information'
																						+ ' to the database when acquired')
		settingscontainer = uidata.Container('Settings')
		settingscontainer.addObjects((gridcontainer, mainscreencontainer,
																	self.correctimage, camerafuncscontainer,
																	self.pausetime, self.usedatabase,
																	self.lowdose, self.pause))

		self.acquiremethod = uidata.Method('Acquire', self.acquireImage,
													tooltip='Acquire an image with the current settings')
		self.startmethod = uidata.Method('Start', self.acquisitionLoopStart,
										tooltip='Start acquiring images on the specified interval')
		self.stopmethod = uidata.Method('Stop', self.acquisitionLoopStop,
																		tooltip='Stop acquiring images')
		self.stopmethod.disable()
		loopcontainer = uidata.Container('Continuous Acquisition')
		loopcontainer.addObject(self.startmethod, position={'position': (0, 0)}) 
		loopcontainer.addObject(self.stopmethod, position={'position': (1, 0)})
		controlcontainer = uidata.Container('Control')
		controlcontainer.addObject(self.acquiremethod,
																position={'justify': ['center']})
		controlcontainer.addObject(loopcontainer,
																position={'position': (0, 1),
																					'justify': ['center']})

		container = uidata.LargeContainer('Manual Acquisition')
		container.addObject(self.messagelog, position={'position': (0, 0),
																										'span': (1, 2),
																										'expand': 'all'})
		container.addObject(statuscontainer, position={'position': (1, 0),
																										'span': (1, 2),
																										'expand': 'all'})
		container.addObject(settingscontainer, position={'position': (2, 0),
																				'justify': ['bottom', 'left', 'right']})
		container.addObject(controlcontainer, position={'position': (3, 0),
																									'justify': ['left', 'right']})
		container.addObject(imagecontainer, position={'position': (2, 1),
																							'span': (2, 1)})
																							#'justify': ['center']})
		self.uicontainer.addObject(container)

