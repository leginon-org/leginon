# The Leginon software is Copyright 2003
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see  http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/presets.py,v $
# $Revision: 1.248 $
# $Name: not supported by cvs2svn $
# $Date: 2007-05-17 21:46:13 $
# $Author: pulokas $
# $State: Exp $
# $Locker:  $

import node
import calibrationclient
import data
import datatransport
import event
import dbdatakeeper
import copy
import threading
import time
import unique
from pyami import ordereddict
import gui.wx.PresetsManager
import instrument
import random

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
	eventinputs = [event.PresetChangedEvent, event.PresetPublishEvent, event.DoseMeasuredEvent]
	eventoutputs = [event.ChangePresetEvent, event.MeasureDoseEvent]
	def __init__(self, node):
		self.node = node
		self.node.addEventInput(event.PresetChangedEvent, self.presetchanged)
		self.node.addEventInput(event.PresetPublishEvent, self.onPresetPublished)
		self.node.addEventInput(event.DoseMeasuredEvent, self.doseMeasured)
		self.pchanged = {}
		self.dose_measured = {}
		self.currentpreset = None
		self.havelock = False

	def getPresetFromDB(self, name):
		session = self.node.session
		query = data.PresetData(session=session, name=name)
		try:
			return self.node.research(datainstance=query, results=1)[0]
		except IndexError:
			raise ValueError('no preset \'%s\' in the database' % name)

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
			if not pname or pname in done:
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
		namedict = ordereddict.OrderedDict()
		for key in keys:
			p = pdict[key]
			namedict[p['name']] = p
		return namedict

	def lock(self):
		'try to acquire lock on presets manager, block until I have it'
		if self.havelock:
			return
		lockevent = event.PresetLockEvent()
		self.node.logger.info('Acquiring preset lock...')
		self.node.outputEvent(lockevent, wait=True)
		self.node.logger.info('Have preset lock')
		self.havelock = True

	def unlock(self):
		'release the previously acquiring lock'
		if not self.havelock:
			return
		unlockevent = event.PresetUnlockEvent()
		self.node.logger.info('Releasing preset lock...')
		self.node.outputEvent(unlockevent, wait=True)
		self.havelock = False

	def toScope(self, presetname, emtarget=None):
		'''
		send the named preset to the scope
		optionally send a target to the scope as well
		'''
		if not presetname:
			self.node.logger.error('Invalid preset name')
			return
		evt = event.ChangePresetEvent()
		evt['name'] = presetname
		evt['emtarget'] = emtarget
		self.node.logger.info('Requesting preset change to \'%s\'...' % presetname)
		self.pchanged[presetname] = threading.Event()
		self.node.startTimer('preset toScope')
		self.node.outputEvent(evt)
		self.pchanged[presetname].wait()
		self.node.stopTimer('preset toScope')
		self.node.logger.info('Preset change to \'%s\' completed.' % presetname)

	def presetchanged(self, ievent):
		self.currentpreset = ievent['preset']
		name = self.currentpreset['name']

		# if waiting for this event, then set the threading event
		if name in self.pchanged:
			self.pchanged[name].set()

		# update node's instruments to match new preset
		self.node.instrument.setTEM(self.currentpreset['tem']['name'])
		self.node.instrument.setCCDCamera(self.currentpreset['ccdcamera']['name'])

		self.node.confirmEvent(ievent)

	def measureDose(self, preset_name, em_target=None):
		if not preset_name:
			raise ValueError('invalid preset name')
		request_event = event.MeasureDoseEvent()
		request_event['name'] = preset_name
		request_event['emtarget'] = em_target
		self.dose_measured[preset_name] = threading.Event()
		self.node.outputEvent(request_event)
		self.dose_measured[preset_name].wait()

	def doseMeasured(self, status_event):
		self.currentpreset = status_event['preset']
		name = self.currentpreset['name']
		if name in self.dose_measured:
			self.dose_measured[name].set()
		self.node.confirmEvent(status_event)

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

class PresetsManager(node.Node):
	panelclass = gui.wx.PresetsManager.Panel
	settingsclass = data.PresetsManagerSettingsData
	defaultsettings = {
		'pause time': 1.0,
		'xy only': True,
		'stage always': True,
		'cycle': True,
		'optimize cycle': True,
		'mag only': True,
		'apply offset': False,
	}
	eventinputs = node.Node.eventinputs + [event.ChangePresetEvent, event.PresetLockEvent, event.PresetUnlockEvent, event.MeasureDoseEvent]
	eventoutputs = node.Node.eventoutputs + [event.PresetChangedEvent, event.PresetPublishEvent, event.DoseMeasuredEvent]

	def __init__(self, name, session, managerlocation, **kwargs):
		node.Node.__init__(self, name, session, managerlocation, **kwargs)

		self.instrument = instrument.Proxy(self.objectservice,
																				self.session,
																				self.panel)
		self.calclients = {
			'pixel size':calibrationclient.PixelSizeCalibrationClient(self),
			'image':calibrationclient.ImageShiftCalibrationClient(self),
			'stage':calibrationclient.StageCalibrationClient(self),
			'beam':calibrationclient.BeamShiftCalibrationClient(self),
			'modeled stage':calibrationclient.ModeledStageCalibrationClient(self),
		}
		self.dosecal = calibrationclient.DoseCalibrationClient(self)

		self.presetsclient = PresetsClient(self)
		self.locknode = None
		self._lock = threading.Lock()

		self.currentselection = None
		self.currentpreset = None
		self.presets = ordereddict.OrderedDict()
		self.selectedsessionpresets = None

		# HACK: fix me
		self.last_value = None

		self.addEventInput(event.ChangePresetEvent, self.changePreset)
		self.addEventInput(event.MeasureDoseEvent, self.measureDose)
		self.addEventInput(event.PresetLockEvent, self.handleLock)
		self.addEventInput(event.PresetUnlockEvent, self.handleUnlock)

		## this will fill in UI with current session presets
		self.getPresetsFromDB()
		self.start()

	def handleLock(self, ievent):
		requesting = ievent['node']
		self.lock(requesting)
		self.confirmEvent(ievent)

	def handleUnlock(self, ievent):
		n = ievent['node']
		self.unlock(n)
		self.confirmEvent(ievent)

	def lock(self, n):
		'''many nodes could be waiting for a lock.  It is undefined which
		one will get it first'''
		self.logger.info('%s requesting lock...' % n)
		self._lock.acquire()
		self.locknode = n
		self.logger.info('%s acquired lock' % self.locknode)

	def unlock(self, n):
		if n == self.locknode:
			self.logger.info('%s unlocking' % n)
			self.locknode = None
			self._lock.release()

	def changePreset(self, ievent):
		'''
		callback for received PresetChangeEvent from client
		'''
		### limit access to this function if lock is in place
		tmplock = False
		if self.locknode is None:
			self.lock(ievent['node'])
			tmplock = True
		if self.locknode is not None:
			## only locking node, or node with proper key can proceed
			if self.locknode not in (ievent['node'], ievent['key']):
				self.lock(ievent['node'])
				tmplock = True

		self.setStatus('processing')
		pname = ievent['name']
		emtarget = ievent['emtarget']
		failwait = 60
		failtries = 3
		succeed = False
		for i in range(failtries):
			try:
				if emtarget is None or emtarget['movetype'] is None:
					self.logger.info('Changing preset to "%s"' % pname)
					self._cycleToScope(pname)
				else:
					self.logger.info('Changing preset to "%s" and targeting' % pname)
					self.targetToScope(pname, emtarget)
			except PresetChangeError:
				if i < failtries-1:
					self.logger.warning('preset request to "%s" failed, waiting %d seconds to try again' % (pname,failwait))
					time.sleep(failwait)
				else:
					self.logger.error('preset request to "%s" failed %d times' % (pname,failtries))
			else:
				self.logger.info('Preset changed to "%s"' % pname)
				succeed = True
				break

		if not succeed:
			self.logger.error('preset request to "%s" failed %d times' % (pname,failtries))

		if tmplock:
						self.unlock(ievent['node'])
		## should we confirm if failure?
		self.confirmEvent(ievent)
		self.setStatus('idle')

	def measureDose(self, request_event):
		self.changePreset(request_event)
		preset_name = request_event['name']
		self.acquireDoseImage(preset_name, display=False)

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
		#self.presets = ordereddict.OrderedDict()
		for name, preset in pdict.items():
			if not name:
				continue
			newp = data.PresetData(initializer=preset, session=self.session)
			## for safety, disable random defocus range
			newp['defocus range min'] = newp['defocus range max'] = None
			self.presetToDB(newp)
			self.presets[name] = newp
		self.setOrder()
		self.panel.presetsEvent()

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

		d = ordereddict.OrderedDict()
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

		self.panel.setOrder(self.presets.keys(), setorder=setorder)

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
		self.panel.presetsEvent()

	def getOrder(self):
		return self.presets.keys()

	def removePreset(self, pname):
		'''
		remove a preset by name
		'''
		if pname not in self.presets.keys():
			self.panel.presetsEvent()
			return 

		## remove from self.presets, store in DB
		premove = self.presets[pname]
		if premove is self.currentpreset:
			message = 'You may not remove the currently set preset, send another preset to scope first'
			self.logger.info(message)
			self.panel.presetsEvent()
			return

		del self.presets[pname]
		pnew = data.PresetData(initializer=premove, removed=1)
		self.presetToDB(pnew)

		## update order, selector list, etc.
		self.setOrder()
		self.panel.presetsEvent()

	def getOffsetImageShift(self, presetdata):
		q = data.StageTiltAxisOffsetData(tem=presetdata['tem'],ccdcamera=presetdata['ccdcamera'])
		offsets = self.research(q, results=1)

		if not offsets:
			self.logger.warning('No stage axis offset has been saved, not applying offset')
			return presetdata['image shift']

		## convert stage offset to pixel offset
		stagey = offsets[0]['offset']

		fakescope = data.ScopeEMData()
		fakescope.friendly_update(presetdata)
		fakecam = data.CameraEMData()
		fakecam.friendly_update(presetdata)

		fakescope['stage position'] = {'x':0, 'y':0}
		fakescope['high tension'] = self.instrument.tem.HighTension

		position = {'x':0, 'y':-stagey}
		pixelshift = self.calclients['stage'].itransform(position, fakescope, fakecam)

		## convert pixel shift to image shift
		newscope = self.calclients['image'].transform(pixelshift, fakescope, fakecam)
		ishift = newscope['image shift']
		self.logger.info('calculated image shift to center tilt axis: %s' % (ishift,))
		return ishift

	def toScope(self, pname, magonly=False, outputevent=True, final=False):
		'''
		'''
		presetdata = self.presetByName(pname)
		if presetdata is None:
			message = 'Preset change failed: no such preset %s' % (pname,)
			self.logger.error(message)
			raise PresetChangeError(message)

		mymin = presetdata['defocus range min']
		mymax = presetdata['defocus range max']
		if None in (mymin, mymax):
			mydefocus = presetdata['defocus']
		else:
			# min <= defocus < max
			mydefocus = random.uniform(mymin, mymax)
			self.logger.info('Random defocus for preset %s:  %s' % (presetdata['name'], mydefocus))

		scopedata = data.ScopeEMData()
		cameradata = data.CameraEMData()

		name = presetdata['name']
		beginmessage = 'Changing preset to "%s"' % (name,)
		endmessage = 'Preset changed to "%s"' % (name,)

		if magonly:
			mag = presetdata['magnification']
			beginmessage = beginmessage + ' (mag only: %s)' % (mag,)
			endmessage = endmessage + ' (mag only: %s)' % (mag,)
			scopedata['magnification'] = mag
			cameradata = None
		else:
			scopedata.friendly_update(presetdata)
			if self.settings['apply offset']:
				scopedata['image shift'] = self.getOffsetImageShift(presetdata)
			cameradata.friendly_update(presetdata)
			if not final:
				cameradata['energy filter'] = None
				cameradata['energy filter width'] = None
			scopedata['defocus'] = mydefocus

		self.logger.info(beginmessage)

		if presetdata['tem'] is None:
			message = 'Preset change failed: no TEM selected for this preset'
			self.logger.error(message)
			raise PresetChangeError(message)
		if presetdata['ccdcamera'] is None:
			message = 'Preset change failed: no CCD camera selection for this preset'
			self.logger.error(message)
			raise PresetChangeError(message)
		
		if presetdata['tem']['name'] in self.instrument.getTEMNames():
			try:
				self.instrument.setTEM(presetdata['tem']['name'])
			except Exception, e:
				msg = 'Preset change failed: %s' % (e,)
				self.logger.error(msg)
				raise PresetChangeError(msg)
		else:
			if presetdata['tem']['name']:
				msg = 'Preset change failed: cannot set TEM to %s' % presetdata['tem']['name']
			else:
				msg = 'Preset change failed: no TEM selection for this preset'
			self.logger.error(msg)
			raise PresetChangeError(msg)

		if presetdata['ccdcamera']['name'] in self.instrument.getCCDCameraNames():
			try:
				self.instrument.setCCDCamera(presetdata['ccdcamera']['name'])
			except Exception, e:
				self.logger.error(e)
				msg = 'Preset change failed: %s' % (e,)
				self.logger.error(msg)
				raise PresetChangeError(msg)
		else:
			if presetdata['ccdcamera']['name']:
				msg = 'Preset change failed: cannot set CCD camera to %s' \
								% presetdata['ccdcamera']['name']
			else:
				msg = 'Preset change failed: no CCD camera selection for this preset'
			self.logger.error(msg)
			raise PresetChangeError(msg)

		try:
			self.instrument.setData(scopedata)
			if cameradata is not None:
				self.instrument.setData(cameradata)
		except Exception, e:
			self.logger.error(e)
			message = 'Preset change failed: unable to set instrument'
			self.logger.error(message)
			raise PresetChangeError(message)

		self.startTimer('preset pause')
		time.sleep(self.settings['pause time'])
		self.stopTimer('preset pause')
		if magonly:
			self.currentpreset = None
		else:
			self.currentpreset = presetdata
		self.logger.info(endmessage)
		if outputevent:
			self.outputEvent(event.PresetChangedEvent(name=name, preset=presetdata))

	def _fromScope(self, name, temname=None, camname=None, parameters=None):
		'''
		create a new preset with name
		if a preset by this name already exists in my 
		list of managed presets, it will be replaced by the new one
		also returns the new preset object
		'''

		if not name:
			self.logger.error('Invalid preset name')
			return

		## figure out tem and ccdcamera

		if temname is None and name in self.presets:
			tem = self.presets[name]['tem']
			if tem is not None and 'name' in tem:
				temname = tem['name']

		if camname is None and name in self.presets:
			cam = self.presets[name]['ccdcamera']
			if cam is not None and 'name' in cam:
				camname = cam['name']

		try:
			self.instrument.setCCDCamera(camname)
		except ValueError:
			self.logger.error('Cannot access CCD camera selected for this preset')
			return
		try:
			self.instrument.setTEM(temname)
		except ValueError:
			self.logger.error('Cannot access TEM selected for this preset')
			return

		if temname is None:
			self.logger.error('No TEM selected for this preset')
			return
		if camname is None:
			self.logger.error('No CCD camera selected for this preset')
			return

		self.logger.info('Preset from %s, %s' % (temname, camname))
		try:
			scopedata = self.instrument.getData(data.ScopeEMData)
		except Exception, e:
			self.logger.error('Preset from instrument failed, unable to get TEM parameters: %s' % e)
			return

		try:
			cameradata = self.instrument.getData(data.CameraEMData, image=False)
		except Exception, e:
			self.logger.error('Preset from instrument failed, unable to get CCD camera parameters: %s' % e)
			return

		newparams = {}
		newparams.update(scopedata)
		newparams.update(cameradata)

		if parameters is not None:
			for parameter in newparams.keys():
				if parameter not in parameters:
					del newparams[parameter]

		# update old preset or create new one
		if name in self.presets.keys():
			if self.settings['apply offset']: 
				self.logger.info('removing tilt axis offset from image shift before saving to preset')
				oldpreset = self.presets[name]
				oldimageshift = oldpreset['image shift']
				oldiswithoffset = self.getOffsetImageShift(oldpreset)
				newparams['image shift']['x'] -= (oldiswithoffset['x']-oldimageshift['x'])
				newparams['image shift']['y'] -= (oldiswithoffset['y']-oldimageshift['y'])
			newpreset = self.updatePreset(name, newparams)
		elif parameters is not None:
			raise ValueError
		else:
			newpreset = self.newPreset(name, newparams)

		self.logger.info('Set preset "%s" values from instrument' % name)
		self.beep()
		return newpreset

	def presetNames(self):
		return self.presets.keys()

	def getSessionPresets(self, sessiondata):
		return self.presetsclient.getPresetsFromDB(sessiondata)

	def cycleToScope(self, presetname):
		self._cycleToScope(presetname)
		self.panel.presetsEvent()

	def _cycleToScope(self, presetname, dofinal=True):
		'''
		prestename = target preset
		force = True:  cycle even if cycling to same preset
		magrepeat = True:  allow two or more consecutive presets
		   that have the same magnification
		magonly = True:  all presets in cycle (except for final) 
		   will only send magnification to TEM
		'''
		errstr = 'Preset cycle failed: %s'
		if not self.settings['cycle']:
			if dofinal:
				try:
					self.toScope(presetname, final=True)
				except PresetChangeError:
					pass
			self.beep()
			return

		order = self.presets.keys()
		magonly = self.settings['mag only']
		magshortcut = self.settings['optimize cycle']

		if presetname not in order:
			estr = 'final preset %s not in cycle order list' % (presetname,)
			self.logger.error(errstr % estr)
			return

		### check if this is the first time a preset
		### has been set for this PresetManager instance
		### In that case, immediately go to the requested preset
		### and force a cycle anyway.
		if self.currentpreset is None:
			self.logger.info('First preset change, changing preset and forcing cycle')
			try:
				self.toScope(presetname, outputevent=False)
			except PresetChangeError:
				return
			force = True
		else:
			force = False

		currentname = self.currentpreset['name']
		if currentname not in order:
			estr = 'current preset %s not in cycle order list' % (currentname,)
			self.logger.error(errstr % estr)
			return

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
			try:
				self.toScope(pname, magonly)
			except PresetChangeError:
				return

		## final preset change
		if dofinal:
			try:
				self.toScope(thiscycle[-1], final=True)
			except PresetChangeError:
				return
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

			if not preset1['skip']:
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

	def fromScope(self, newname, temname=None, camname=None):
		newpreset = self._fromScope(newname, temname, camname)
		if newpreset is None:
			self.panel.presetsEvent()
			return
		self.setOrder()
		self.panel.setParameters(newpreset)
		self.logger.info('Preset from instrument: %s' % (newname,))
		self.panel.presetsEvent()

	def selectPreset(self, pname):
		self.currentselection = self.presetByName(pname)
		self.panel.setParameters(self.currentselection)
		self.displayCalibrations(self.currentselection)

	def getHighTension(self):
		try:
			return self.instrument.tem.HighTension
		except:
			return None

	def displayCalibrations(self, preset):
		mag = preset['magnification']
		ht = self.getHighTension()
		tem = preset['tem']
		cam = preset['ccdcamera']

		## not dependent on HT
		ptime = str(self.calclients['pixel size'].time(tem, cam, mag))
		modtimex = self.calclients['modeled stage'].timeModelCalibration(tem, cam, 'x')
		modtimey = self.calclients['modeled stage'].timeModelCalibration(tem, cam, 'y')
		modtime = 'x: %s, y: %s' % (modtimex, modtimey)

		# dependent on HT
		if ht is None:
			message = 'Unknown (cannot get current high tension)'
			modmagtime = beamtime = imagetime = stagetime = message
		else:
			stagetime = self.calclients['stage'].time(tem, cam, ht, mag, 'stage position')
			imagetime = self.calclients['image'].time(tem, cam, ht, mag, 'image shift')
			beamtime = self.calclients['beam'].time(tem, cam, ht, mag, 'beam shift')
			modmagtimex = self.calclients['modeled stage'].timeMagCalibration(tem, cam, ht,
																																			mag, 'x')
			modmagtimey = self.calclients['modeled stage'].timeMagCalibration(tem, cam, ht,
																																			mag, 'y')
			modmagtime = 'x: %s, y: %s' % (modmagtimex, modmagtimey)

		times = {
			'pixel size': str(ptime),
			'image shift': str(imagetime),
			'stage': str(stagetime),
			'beam': str(beamtime),
			'modeled stage': str(modtime),
			'modeled stage mag only': str(modmagtime),
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

	def newPreset(self, presetname, newparams):
			newpreset = data.PresetData()
			newpreset['session'] = self.session
			newpreset['name'] = presetname
			newpreset['number'] = len(self.presets)
			newpreset['removed'] = False
			newpreset['film'] = False
			newpreset['hasref'] = False
			newpreset['pre exposure'] = 0.0
			newpreset['skip'] = False
			newpreset.friendly_update(newparams)
			self.presets[presetname] = newpreset
			self.presetToDB(newpreset)
			self.currentpreset = newpreset
			self.currentselection = newpreset
			self.panel.setOrder(self.presets.keys())
			self.panel.setParameters(newpreset)
			return newpreset

	def updatePreset(self, presetname, newparams, updatedose=True):
		'''
		called to change some parameters of an existing preset
		'''
		oldpreset = self.presetByName(presetname)
		newpreset = self.renewPreset(oldpreset)
		if 'tem' in newparams:
			if isinstance(newparams['tem'], basestring):
				try:
					newparams['tem'] = self.instrument.getTEMData(newparams['tem'])
				except:
					newparams['tem'] = oldpreset['tem']
		if 'ccdcamera' in newparams:
			if isinstance(newparams['ccdcamera'], basestring):
				try:
					newparams['ccdcamera'] = self.instrument.getCCDCameraData(newparams['ccdcamera'])
				except:
					newparams['ccdcamera'] = oldpreset['ccdcamera']
		newpreset.friendly_update(newparams)

		### change dose if neccessary
		if updatedose:
			self.updateDose(oldpreset, newpreset)

		if self.currentselection is newpreset:
			self.panel.setParameters(newpreset)
		self.presetToDB(newpreset)
		return newpreset

	def acquireDoseImage(self, presetname, display=True):
		errstr = 'Acquire dose image failed: %s'

		if not presetname:
			e = 'invalid preset \'%s\'' % presetname
			self.logger.error(errstr % e)
			self.panel.presetsEvent()
			return

		if self.currentpreset is None or self.currentpreset['name'] != presetname:
			self._cycleToScope(presetname)

		if self.currentpreset is None or self.currentpreset['name'] != presetname:
			e = 'cannot go to preset \'%s\'' % presetname
			self.logger.error(errstr % e)
			self.panel.presetsEvent()
			return

		self._acquireDoseImage(display=display)

		self.panel.presetsEvent()

		self.outputEvent(event.DoseMeasuredEvent(name=presetname, preset=self.currentpreset))

	def _acquireDoseImage(self, display=True):
		errstr = 'Acquire dose image failed: %s'
		self.logger.info('Acquiring dose image at 512x512')
		camdata0 = data.CameraEMData()
		camdata0.friendly_update(self.currentpreset)

		camdata1 = copy.copy(camdata0)

		## figure out if we want to cut down to 512x512
		for axis in ('x','y'):
			change = camdata0['dimension'][axis] - 512
			if change > 0:
				camdata1['dimension'][axis] = 512
				camdata1['offset'][axis] += (change / 2)

		try:
			self.instrument.setData(camdata1)
		except:
			self.logger.error(errstr % 'unable to set camera parameters')
			return
		try:
			imagedata = self.instrument.getData(data.CorrectedCameraImageData)
		except:
			self.logger.error(errstr % 'unable to acquire corrected image data')
			return
		try:
			self.instrument.setData(camdata0)
		except:
			estr = 'Return to orginial preset camera dimemsion failed: %s'
			self.logger.error(estr % 'unable to set camera parameters')
			return

		self.logger.info('Returned to original preset camera dimensions')

		if imagedata is None:
			self.logger.error(errstr % 'unable to get corrected image')
			return

		## display
		try:
			dose = self.dosecal.dose_from_imagedata(imagedata)
		except calibrationclient.NoPixelSizeError:
			self.logger.error('No pixel size for this magnification')
			return
		except calibrationclient.NoSensitivityError:
			self.logger.error('No sensitivity data for this magnification')
			return
			
		if dose is None:
			self.logger.error('Invalid dose measurement result')
		else:
			if display:
				self.panel.setDoseValue(dose)
				self.setImage(imagedata['image'])
			else:
				self.saveDose(dose, self.currentpreset['name'])

	def saveDose(self, dose, presetname):
		## store the dose in the current preset
		params = {'dose': dose}
		self.updatePreset(presetname, params)

	def updateDose(self, oldpreset, newpreset):
		'''
		call this when preset params changed so that dose can 
		be scaled, mirrored, or reset as neccessary
		This means:
			If no existing dose:
				do nothing
			If mag, spot size, or intensity changed:
				reset dose = None
			If exposure time changed:
				scale dose based on new exposure time
		'''
		## update dose when certain things change
		if oldpreset['dose']:
			dosekillers = []
			for param in ('magnification', 'spot size', 'intensity'):
				if oldpreset[param] != newpreset[param]:
					dosekillers.append(param)
			if dosekillers:
				newpreset['dose'] = None
				paramstr = ', '.join(dosekillers)
				s = 'Dose of preset "%s" reset due to change in %s' % (newpreset['name'], paramstr)
				self.logger.info(s)
			elif newpreset['exposure time'] != oldpreset['exposure time']:
				try:
					scale = float(newpreset['exposure time']) / float(oldpreset['exposure time'])
				except ZeroDivisionError:
					scale = 0.0
				newpreset['dose'] = scale * oldpreset['dose']
				self.logger.info('Scaling dose of preset "%s" x%.3f due to change in exposure time' % (newpreset['name'], scale,))

		## create list of similar presets
		similarpresets = []
		for pname, p in self.presets.items():
			if pname == newpreset['name']:
				continue
			similar = True
			for param in ('magnification', 'spot size', 'intensity'):
				if p[param] != newpreset[param]:
					similar = False
			if similar:
				similarpresets.append(p)

		if similarpresets:
			if not newpreset['dose']:
				## set my dose from a similar preset
				sim = similarpresets[0]
				try:
					scale = float(newpreset['exposure time']) / float(sim['exposure time'])
				except ZeroDivisionError:
					scale = 0.0
				if sim['dose'] is None:
					newpreset['dose'] = None
				else:
					newpreset['dose'] = scale * sim['dose']
				self.logger.info('Copying and scaling dose from similar preset "%s" to preset "%s"' % (sim['name'], newpreset['name']))
			elif oldpreset['dose'] != newpreset['dose']:
				## my dose changed, now update dose in other similar presets
				for sim in similarpresets:
					try:
						scale = float(sim['exposure time']) / float(newpreset['exposure time'])
					except ZeroDivisionError:
						scale = 0.0
					self.logger.info('Copying and scaling dose from preset "%s" to similar preset "%s"' % (newpreset['name'], sim['name']))
					simdose = scale * newpreset['dose']
					self.updatePreset(sim['name'], {'dose': simdose}, updatedose=False)

	def targetToScope(self, newpresetname, emtargetdata):
		'''
		This is like toScope, but this one is mainly called
		by client nodes which request that presets and targets
		be tightly coupled.
		'''
		## first cycle through presets before sending the final one
		if self.currentpreset is None or self.currentpreset['name'] != newpresetname:
			self._cycleToScope(newpresetname, dofinal=False)

		self.logger.info('Going to target and to preset %s' % (newpresetname,))

		newpreset = self.presetByName(newpresetname)
		if newpreset is None:
			msg = 'Preset change/target move failed: invalid preset name "%s"'
			msg %= newpresetname
			self.logger.error(msg)
			raise PresetChangeError(msg)

		## this is a hack to make this work with simulated targets which
		## have no "old preset"
		if emtargetdata['preset'] is None:
			oldpreset = newpreset
		else:
			oldpreset = emtargetdata['preset']

		## make copy of target stage and image shift
		mystage = dict(emtargetdata['stage position'])
		myimage = dict(emtargetdata['image shift'])
		mybeam = dict(emtargetdata['beam shift'])

## This should be unnecessary if we have a check for minimum stage movement
## (currently in pyScope).  It was a way to prevent moving the stage between
## targets which only require an image shift, but with queuing, we have to 
## assume that stage should always be moved.  If stage truly does not need to
## move, then the minimum stage movement threshold should take effect.
		## decide if moving stage or not, and which axes to move
#		movetype = emtargetdata['movetype']
#		if movetype in ('image shift', 'image beam shift'):
#			if not self.settings['stage always']:
#				mystage = None

		if mystage and self.settings['xy only']:
			## only set stage x and y
			for key in mystage.keys():
				if key not in ('x','y'):
					del mystage[key]

		## offset image shift to center stage tilt axis
		if self.settings['apply offset']:
			newimageshift = self.getOffsetImageShift(newpreset)
			oldimageshift = self.getOffsetImageShift(oldpreset)
		else:
			newimageshift = newpreset['image shift']
			oldimageshift = oldpreset['image shift']

		## this assumes that image shift is preserved through a mag change
		## although this may not always be true.  In particular, I think
		## that LM and M/SA mag ranges have different image shift coord systems
		myimage['x'] -= oldimageshift['x']
		myimage['x'] += newimageshift['x']
		myimage['y'] -= oldimageshift['y']
		myimage['y'] += newimageshift['y']

		mybeam['x'] -= oldpreset['beam shift']['x']
		mybeam['x'] += newpreset['beam shift']['x']
		mybeam['y'] -= oldpreset['beam shift']['y']
		mybeam['y'] += newpreset['beam shift']['y']

		mymin = newpreset['defocus range min']
		mymax = newpreset['defocus range max']
		if None in (mymin, mymax):
			mydefocus = newpreset['defocus']
		else:
			# min <= defocus < max
			mydefocus = random.uniform(mymin, mymax)
			self.logger.info('Random defocus for preset %s:  %s' % (newpreset['name'], mydefocus))


		### create ScopeEMData with preset and target shift
		scopedata = data.ScopeEMData()
		scopedata.friendly_update(newpreset)
		scopedata['image shift'] = myimage
		scopedata['beam shift'] = mybeam
		scopedata['stage position'] = mystage
		scopedata['defocus'] = mydefocus

		### correct defocus for tilted stage
		deltaz = emtargetdata['delta z']
		if deltaz:
			self.logger.info('Correcting defocus by %.2e for target on tilt' % (deltaz,))
			scopedata['defocus'] += deltaz

		### createCameraEMData with preset
		cameradata = data.CameraEMData()
		cameradata.friendly_update(newpreset)

		## set up instruments for this preset
		try:
			self.instrument.setTEM(newpreset['tem']['name'])
			self.instrument.setCCDCamera(newpreset['ccdcamera']['name'])
		except Exception, e:
			msg = 'Preset change/target move failed: %s' % (e,)
			self.logger.error(msg)
			raise PresetChangeError(msg)

		## send data to instruments
		try:
			self.instrument.setData(scopedata)
			self.instrument.setData(cameradata)
		except Exception, e:
			self.logger.error(e)
			message = 'Move to target failed: unable to set instrument'
			self.logger.error(message)
			raise PresetChangeError(message)

		self.startTimer('preset pause')
		time.sleep(self.settings['pause time'])
		self.stopTimer('preset pause')
		name = newpreset['name']
		self.currentpreset = newpreset
		message = 'Preset (with target) changed to %s' % (name,)
		self.logger.info(message)
		self.outputEvent(event.PresetChangedEvent(name=name, preset=newpreset))

	def getValue(self, instrument_type, instrument_name, parameter, event):
		# HACK: fix me
		try:
			value = self._getValue(instrument_type, instrument_name, parameter)
			self.last_value = value
		finally:
			event.set()

	def _getValue(self, instrument_type, instrument_name, parameter):
		try:
			if instrument_type == 'tem':
				return self.instrument.getTEMParameter(instrument_name, parameter)
			elif instrument_type == 'ccdcamera':
				if parameter == 'camera parameters':
					return self.instrument.getData(data.CameraEMData, image=False, ccdcameraname=instrument_name).toDict()
				else:
					return self.instrument.getCCDCameraParameter(instrument_name, parameter)
			else:
				raise ValueError('no instrument type \'%s\'' % instrument_type)
		except Exception, e:
			self.logger.error('Get value failed: %s' % (e,))
			raise e

