#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#
import node
import calibrationclient
import data
import datatransport
import event
import dbdatakeeper
import copy
import uidata
import camerafuncs
import threading
import time
import unique
import newdict
import EM
import gui.wx.PresetsManager

try:
	import numarray as Numeric
except:
	import Numeric

class PresetChangeError(Exception):
	pass

class CurrentPresetData(data.Data):
	def typemap(cls):
		t = data.Data.typemap()
		t += [('preset', data.PresetData)]
		return t
	typemap = classmethod(typemap)

class CurrentPresetPublishEvent(event.PublishEvent):
	dataclass = CurrentPresetData

class PresetsClient(object):
	'''
	client functions for nodes to access PresetsManager
	'''
	eventinputs = [event.PresetChangedEvent, event.PresetPublishEvent]
	def __init__(self, node, uistatus=None):
		self.uistatus = uistatus
		self.node = node
		self.node.addEventInput(event.PresetChangedEvent, self.presetchanged)
		self.node.addEventInput(event.PresetPublishEvent, self.onPresetPublished)
		self.pchanged = {}
		self.currentpreset = None

	def getPresetsFromDB(self, session=None):
		'''
		get ordered list of presets for this session from DB
		'''
		if session is None:
			session = self.node.session

		## find presets that belong to this session
		pquery = data.PresetData(session=session)
		plist = self.node.research(datainstance=pquery)
		if not plist:
			return {}

		### only want most recent of each name, none that are removed
		## index by number so we can sort
		pdict = {}
		done = {}
		for p in plist:
			pname = p['name']
			if pname in done:
				continue
			done[pname] = None
			if p['removed']:
				continue
			pnumber = p['number']
			# to be backward compatible
			# if number was not in DB or number is not unique
			if pnumber is None or pnumber in pdict:
				pdict[pname] = p
			else:
				pdict[pnumber] = p

		## sort by number (maybe name if old, non-numbered data)
		keys = pdict.keys()
		keys.sort()
		namedict = newdict.OrderedDict()
		for key in keys:
			p = pdict[key]
			namedict[p['name']] = p
		return namedict

	def toScope(self, presetname, emtarget=None):
		'''
		send the named preset to the scope
		optionally send a target to the scope as well
		'''
		if not presetname:
			self.logger.error('Invalid preset name')
			return
		evt = event.ChangePresetEvent()
		evt['name'] = presetname
		evt['emtarget'] = emtarget
		if self.uistatus is not None:
			self.uistatus.set('Requesting preset change to %s' % (presetname,))
		self.pchanged[presetname] = threading.Event()
		self.node.outputEvent(evt)
		self.pchanged[presetname].wait()

		if self.uistatus is not None:
			self.uistatus.set('Preset change to %s completed' % (presetname,))

	def presetchanged(self, ievent):
		self.currentpreset = ievent['preset']
		name = self.currentpreset['name']
		# if waiting for this event, then set the threading event
		if name in self.pchanged:
			self.pchanged[name].set()
		self.node.confirmEvent(ievent)

	def onPresetPublished(self, evt):
		if hasattr(self.node, 'onPresetPublished'):
			self.node.onPresetPublished(evt)

	def getCurrentPreset(self):
		return self.currentpreset

	def getPresetByName(self, pname):
		ps = self.getPresetsFromDB()
		if pname in ps:
			return ps[pname]
		else:
			return None

	def uiSinglePresetSelector(self, label='', default='', permissions='rw', persist=False):
		return SinglePresetSelector(self, label, default, permissions, persist)

	def getPresetNames(self):
		presetlist = self.getPresetsFromDB()
		return presetlist.keys()


class SinglePresetSelector(uidata.Container):
	def __init__(self, presetsclient, label='', default='', permissions='rw', persist=False):
		uidata.Container.__init__(self, label)
		self.presetsclient = presetsclient
		showavailable = uidata.Method('Show Available Names', self.refreshPresetNames)
		self.available = uidata.String('Available', '', 'r')
		self.entry = uidata.String('Preset Name', default, permissions, persist=persist)
		self.addObjects((showavailable, self.available, self.entry))

	def get(self):
		return self.entry.get()

	def set(self, value):
		self.entry.set(value)

	def refreshPresetNames(self):
		names = self.presetsclient.getPresetNames()
		if names:
			availstr = '   '.join(names)
		else:
			availstr = 'No Presets Available'
		self.available.set(availstr)


class PresetsManager(node.Node):
	panelclass = gui.wx.PresetsManager.Panel
	settingsclass = data.PresetsManagerSettingsData
	defaultsettings = {
		'pause time': 1.0,
		'xy only': True,
		'stage always': False,
		'cycle': True,
		'optimize cycle': True,
		'mag only': True,
	}
	eventinputs = node.Node.eventinputs + [event.ChangePresetEvent] + EM.EMClient.eventinputs
	eventoutputs = node.Node.eventoutputs + [event.PresetChangedEvent, event.PresetPublishEvent] + EM.EMClient.eventoutputs

	def __init__(self, name, session, managerlocation, **kwargs):
		node.Node.__init__(self, name, session, managerlocation, **kwargs)

		self.addEventInput(event.ChangePresetEvent, self.changePreset)

		self.emclient = EM.EMClient(self)
		self.cam = camerafuncs.CameraFuncs(self)
		self.calclients = {
			'pixel size':calibrationclient.PixelSizeCalibrationClient(self),
			'image':calibrationclient.ImageShiftCalibrationClient(self),
			'stage':calibrationclient.StageCalibrationClient(self),
			'beam':calibrationclient.BeamShiftCalibrationClient(self),
			'modeled stage':calibrationclient.ModeledStageCalibrationClient(self),
		}
		self.dosecal = calibrationclient.DoseCalibrationClient(self)

		self.presetsclient = PresetsClient(self)

		self.currentselection = None
		self.currentpreset = None
		self.presets = newdict.OrderedDict()
		self.selectedsessionpresets = None

		## this will fill in UI with current session presets
		self.getPresetsFromDB()
		self.getSessionList()
		self.start()

	def changePreset(self, ievent):
		'''
		callback for received PresetChangeEvent from client
		'''
		pname = ievent['name']
		emtarget = ievent['emtarget']
		try:
			if emtarget is None or emtarget['movetype'] is None:
				self.logger.info('Changing preset to "%s"' % pname)
				self.cycleToScope(pname)
			else:
				self.logger.info('Changing preset to "%s" and targeting' % pname)
				self.targetToScope(pname, emtarget)
		except PresetChangeError:
			self.logger.info('preset request to "%s" failed' % pname)
			pass
		else:
			self.logger.info('Preset changed to "%s"' % pname)
			pass
		## should we confirm if failure?
		self.confirmEvent(ievent)

	def getPresetsFromDB(self):
		'''
		get presets from current session out of database
		'''
		self.presets = self.presetsclient.getPresetsFromDB()
		self.setOrder()

	def importPresets(self, pdict):
		'''
		takes a set of presets from any session and generates 
		an identical set for this session
		'''
		## make new presets with this session
		#self.presets = newdict.OrderedDict()
		for name, preset in pdict.items():
			newp = data.PresetData(initializer=preset, session=self.session)
			self.presetToDB(newp)
			self.presets[name] = newp
		self.setOrder()

	def presetToDB(self, presetdata):
		'''
		stores a preset in the DB under the current session name
		'''
		self.publish(presetdata, database=True, dbforce=True, pubevent=True)

	def presetByName(self, name):
		if name in self.presets.keys():
			return self.presets[name]
		else:
			return None

	def setOrder(self, names=None, setorder=True):
		'''
		set order of self.presets, and set numbers
		if names given, use that to determine order
		otherwise, current order is ok, just update numbers
		'''
		if names is None:
			names = self.presets.keys()

		d = newdict.OrderedDict()
		number = 0
		for name in names:
			p = self.presets[name]
			if p['number'] != number:
				newp = data.PresetData(initializer=p, number=number)
				self.presetToDB(newp)
			else:
				newp = p
			d[name] = newp
			number += 1
		self.presets = d

		self.panel.onSetOrder(self.presets.keys(), setorder=setorder)

	def setCycleOrder(self, namelist):
		## make sure nothing is added or removed from the list
		## only order changes are allowed
		if namelist is None:
			test1 = None
		else:
			test1 = list(namelist)
			test1.sort()
		test2 = list(self.presets.keys())
		test2.sort()
		if test1 == test2:
			self.setOrder(namelist, setorder=False)
		else:
			namelist = self.presets.keys()

	def getOrder(self):
		return self.presets.keys()

	def removePreset(self, pname):
		'''
		remove a preset by name
		'''
		if pname not in self.presets.keys():
			return 

		## remove from self.presets, store in DB
		premove = self.presets[pname]
		if premove is self.currentpreset:
			message = 'You may not remove the currently set preset, send another preset to scope first'
			self.logger.info(message)
			return

		del self.presets[pname]
		pnew = data.PresetData(initializer=premove, removed=1)
		self.presetToDB(pnew)

		## update order, selector list, etc.
		self.setOrder()

	def toScope(self, pname, magonly=False, outputevent=True):
		'''
		'''
		presetdata = self.presetByName(pname)
		if presetdata is None:
			message = 'No such preset %s' % (pname,)
			self.logger.error(message)
			raise PresetChangeError(message)

		scopedata = data.ScopeEMData()
		cameradata = data.CameraEMData()

		name = presetdata['name']
		beginmessage = 'Changing preset to "%s"' % (name,)
		endmessage = '     Preset changed to "%s"' % (name,)

		if magonly:
			mag = presetdata['magnification']
			beginmessage = beginmessage + ' (mag only: %s)' % (mag,)
			endmessage = endmessage + ' (mag only: %s)' % (mag,)
			scopedata['magnification'] = mag
			cameradata = None
		else:
			scopedata.friendly_update(presetdata)
			cameradata.friendly_update(presetdata)

		self.logger.info(beginmessage)

		self.emclient.setScope(scopedata)
		if cameradata is not None:
			self.emclient.setCamera(cameradata)

		time.sleep(self.settings['pause time'])
		if magonly:
			self.currentpreset = None
		else:
			self.currentpreset = presetdata
		self.logger.info(endmessage)
		if outputevent:
			self.outputEvent(event.PresetChangedEvent(name=name, preset=presetdata))

	def _fromScope(self, name):
		'''
		create a new preset with name
		if a preset by this name already exists in my 
		list of managed presets, it will be replaced by the new one
		also returns the new preset object
		'''

		if not name:
			self.logger.error('Invalid preset name')
			return
		scopedata = self.emclient.getScope()
		cameradata = self.emclient.getCamera()
		newpreset = data.PresetData()
		newpreset.friendly_update(scopedata)
		newpreset.friendly_update(cameradata)
		newpreset['session'] = self.session
		newpreset['name'] = name

		# existing preset keeps same number
		# new preset is put at the end
		if name in self.presets.keys():
			number = self.presets[name]['number']
		else:
			## this is len before new one is added
			number = len(self.presets)

		newpreset['number'] = number
		self.presets[name] = newpreset
		self.presetToDB(newpreset)
		self.currentpreset = newpreset

		## update UI
		# ???
		self.panel.onSetOrder(self.presets.keys())
		self.logger.info('Set preset "%s" values from instrument' % name)
		self.beep()
		return newpreset

	def presetNames(self):
		return self.presets.keys()

	def getSessionPresets(self, name):
		sessiondata = self.sessiondict[name]
		return self.presetsclient.getPresetsFromDB(sessiondata)

	def cycleToScope(self, presetname, dofinal=True):
		'''
		prestename = target preset
		force = True:  cycle even if cycling to same preset
		magrepeat = True:  allow two or more consecutive presets
		   that have the same magnification
		magonly = True:  all presets in cycle (except for final) 
		   will only send magnification to TEM
		'''
		if not self.settings['cycle']:
			if dofinal:
				self.toScope(presetname)
			self.beep()
			return

		order = self.presets.keys()
		magonly = self.settings['mag only']
		magshortcut = self.settings['optimize cycle']

		if presetname not in order:
			raise RuntimeError('final preset %s not in cycle order list' % (presetname,))

		### check if this is the first time a preset
		### has been set for this PresetManager instance
		### In that case, immediately go to the requested preset
		### and force a cycle anyway.
		if self.currentpreset is None:
			self.logger.info('First preset change, changing preset and forcing cycle')
			self.toScope(presetname, outputevent=False)
			force = True
		else:
			force = False

		currentname = self.currentpreset['name']
		if currentname not in order:
			raise RuntimeError('current preset %s not in cycle order list' % (currentname,))

		thiscycle = self.createCycleList(currentname, presetname, magshortcut)
		
		### We can make one more possible shortcut if we are going
		### to a preset such that there are no mag changes between
		### the current preset and the final preset (even in the
		### reverse cycle)  In such case, we can go direct.
		### If len(thiscycle) == 1 already, then there is no advantage,
		### but if len(thiscycle) > 1 and len(reversecycle) == 1 and
		### the final preset has the same mag as the current one,
		### then we can go direct
		if magshortcut and len(thiscycle) > 1:
			reversecycle = self.createCycleList(currentname, presetname, magshortcut, reverse=True)
			if len(reversecycle) == 1:
				p = self.presetByName(reversecycle[0])
				if p['magnification'] == self.currentpreset['magnification']:
					thiscycle = reversecycle
					self.logger.info(
						'Magnification adjacency detected, going directly to final preset')

		## go to every preset in thiscycle except the last
		for pname in thiscycle[:-1]:
			self.toScope(pname, magonly)

		## final preset change
		if dofinal:
			self.toScope(thiscycle[-1])
			self.logger.info('Cycle completed')
		self.beep()

	def createCycleList(self, current, final, magshortcut, reverse=False):
		order = self.presets.keys()

		# start with only final in the reduced list
		reduced = [final]

		## propose adding previous/next presets one by one
		name2 = final
		preset2 = self.presetByName(name2)
		while 1:
			if reverse:
				name1 = self.nextNameInCycle(name2, order)
			else:
				name1 = self.previousNameInCycle(name2, order)
			if name1 == current:
				break
			preset1 = self.presetByName(name1)

			if preset1['magnification'] != preset2['magnification'] or not magshortcut:
				reduced.insert(0,name1)
			name2 = name1
			preset2 = preset1

		if magshortcut and len(reduced) > 1:
			currentmag = self.currentpreset['magnification']
			firstp = self.presetByName(reduced[0])
			firstmag = firstp['magnification']
			if firstmag == currentmag:
				del reduced[0]

		return reduced

	def nextNameInCycle(self, currentname, order):
		index = order.index(currentname)
		nextindex = index + 1
		if nextindex == len(order):
			nextindex = 0
		return order[nextindex]

	def previousNameInCycle(self, currentname, order):
		index = order.index(currentname)
		previndex = index - 1
		return order[previndex]

	def fromScope(self, newname):
		newpreset = self._fromScope(newname)
		self.setOrder()
		self.panel.setParameters(newpreset)
		self.logger.info('created new preset: %s' % (newname,))

	def selectPreset(self, pname):
		self.currentselection = self.presetByName(pname)
		self.panel.setParameters(self.currentselection)
		self.displayCalibrations(self.currentselection)
		self.displayDose(self.currentselection)

	def getHighTension(self):
		try:
			return self.emclient.getScope()['high tension']
		except EM.ScopeUnavailable:
			return None

	def displayCalibrations(self, preset):
		mag = preset['magnification']
		ht = self.getHighTension()

		## not dependent on HT
		ptime = str(self.calclients['pixel size'].time(mag))
		modtimex = self.calclients['modeled stage'].timeModelCalibration('x')
		modtimey = self.calclients['modeled stage'].timeModelCalibration('y')
		modtime = 'x: %s, y: %s' % (modtimex, modtimey)

		# dependent on HT
		if ht is None:
			message = 'Cannot get current high tension.'
			modmagtime = beamtime = imagetime = stagetime = message
		else:
			stagetime = self.calclients['stage'].time(ht, mag, 'stage position')
			imagetime = self.calclients['image'].time(ht, mag, 'image shift')
			beamtime = self.calclients['beam'].time(ht, mag, 'beam shift')
			modmagtimex = self.calclients['modeled stage'].timeMagCalibration(ht,
																																			mag, 'x')
			modmagtimey = self.calclients['modeled stage'].timeMagCalibration(ht,
																																			mag, 'y')
			modmagtime = 'x: %s, y: %s' % (modmagtimex, modmagtimey)

		times = {
			'pixel size': ptime,
			'image shift': imagetime,
			'stage': stagetime,
			'beam': beamtime,
			'modeled stage': modtime,
			'modeled stage mag only': modmagtime,
		}

		self.panel.setCalibrations(times)

	def renewPreset(self, p):
		### this makes a copy of an existing preset
		### so that dbid is not set and we can 
		### edit the values
		if p.dbid is None:
			return p
		newpreset = data.PresetData(initializer=p)
		self.presets[newpreset['name']] = newpreset
		if self.currentpreset is p:
			self.currentpreset = newpreset
		if self.currentselection is p:
			self.currentselection = newpreset
		return newpreset

	def updateParams(self, parameters):
		newpreset = self.renewPreset(self.currentselection)
		newpreset.update(parameters)
		self.presetToDB(newpreset)

	def getSessionList(self):
		'''
		get list of session names from this instrument
		'''
		if self.session['instrument'] is None:
			return
		myinstname = self.session['instrument']['name']
		querysession = data.SessionData()
		queryinst = data.InstrumentData()
		queryinst['name'] = myinstname
		querysession['instrument'] = queryinst
		limit = 100
		sessionlist = self.research(datainstance=querysession, results=limit)
		sessionnamelist = [x['name'] for x in sessionlist]
		self.sessiondict = dict(zip(sessionnamelist, sessionlist))

	def acquireDoseImage(self):
		if self.currentpreset is None:
			self.logger.error('Please go to a preset before measuring dose')
			return
		self.logger.info('Acquiring dose image using preset config at 512x512')
		camdata0 = data.CameraEMData()
		camdata0.friendly_update(self.currentpreset)

		camdata1 = copy.copy(camdata0)

		## figure out if we want to cut down to 512x512
		for axis in ('x','y'):
			change = camdata0['dimension'][axis] - 512
			if change > 0:
				camdata1['dimension'][axis] = 512
				camdata1['offset'][axis] += (change / 2)

		self.cam.setCameraEMData(camdata1)
		imagedata = self.cam.acquireCameraImageData(correction=True)
		self.logger.info('returning to original preset camera dimensions')
		self.cam.setCameraEMData(camdata0)
		if imagedata is None:
			return

		## display
		self.setImage(imagedata['image'].astype(Numeric.Float32))
		dose = self.dosecal.dose_from_imagedata(imagedata)
		## store the dose in the current preset
		self.currentpreset = self.renewPreset(self.currentpreset)
		self.currentpreset['dose'] = dose
		self.presetToDB(self.currentpreset)
		self.panel.setParameters(self.currentpreset)
		self.displayDose(self.currentpreset)

	def displayDose(self, preset):
		dose = preset['dose']
		if dose is None:
			displaydose = 'N/A'
		else:
			displaydose = dose / 1e20
			displaydose = '%.2f' % (displaydose,)
		self.panel.setDoseValue('%s: %s' % (preset['name'], displaydose))

	def targetToScope(self, newpresetname, emtargetdata):
		'''
		This is like toScope, but this one is mainly called
		by client nodes which request that presets and targets
		be tightly coupled.
		'''
		## first cycle through presets before sending the final one
		if self.currentpreset is None or self.currentpreset['name'] != newpresetname:
			self.cycleToScope(newpresetname, dofinal=False)

		self.logger.info('Going to target and to preset %s' % (newpresetname,))

		oldpreset = emtargetdata['preset']
		newpreset = self.presetByName(newpresetname)
		## make copy of target stage and image shift
		mystage = dict(emtargetdata['stage position'])
		myimage = dict(emtargetdata['image shift'])
		mybeam = dict(emtargetdata['beam shift'])

		## decide if moving stage or not, and which axes to move
		movetype = emtargetdata['movetype']
		if movetype in ('image shift', 'image beam shift'):
			if not self.settings['stage always']:
				mystage = None

		if mystage and self.settings['xy only']:
			## only set stage x and y
			for key in mystage.keys():
				if key not in ('x','y'):
					del mystage[key]

		## figure out how to transform the target image shift
		## ???
		## for now, assume that image shift targets are not passed
		## across mag mode ranges, so newimage is straight from 
		## newpreset
		## Within the same mag mode, use target - oldpreset + newpreset

		if oldpreset['magnification'] < 1500:
			oldmag = 'LM'
		else:
			oldmag = 'SA'
		if newpreset['magnification'] < 1500:
			newmag = 'LM'
		else:
			newmag = 'SA'

		if oldmag == newmag:
			self.logger.info('Using same magnification mode')
			myimage['x'] -= oldpreset['image shift']['x']
			myimage['x'] += newpreset['image shift']['x']
			myimage['y'] -= oldpreset['image shift']['y']
			myimage['y'] += newpreset['image shift']['y']

			mybeam['x'] -= oldpreset['beam shift']['x']
			mybeam['x'] += newpreset['beam shift']['x']
			mybeam['y'] -= oldpreset['beam shift']['y']
			mybeam['y'] += newpreset['beam shift']['y']
		else:
			self.logger.info('Using different magnification mode')
			myimage['x'] = newpreset['image shift']['x']
			myimage['y'] = newpreset['image shift']['y']

			mybeam['x'] = newpreset['beam shift']['x']
			mybeam['y'] = newpreset['beam shift']['y']

		### create ScopeEMData with preset and target shift
		scopedata = data.ScopeEMData()
		scopedata.friendly_update(newpreset)
		scopedata['image shift'] = myimage
		scopedata['beam shift'] = mybeam
		scopedata['stage position'] = mystage
		### createCameraEMData with preset
		cameradata = data.CameraEMData()
		cameradata.friendly_update(newpreset)

		try:
			self.emclient.setScope(scopedata)
			self.emclient.setCamera(cameradata)
		except:
			message = 'Cannot set instrument parameters'
			self.logger.error(message)
			raise PresetChangeError(message)

		time.sleep(self.settings['pause time'])
		name = newpreset['name']
		self.currentpreset = newpreset
		message = 'Preset (with target) changed to %s' % (name,)
		self.logger.info(message)
		self.outputEvent(event.PresetChangedEvent(name=name, preset=newpreset))

