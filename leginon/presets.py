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
import strictdict
import EM
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
	def __init__(self, node, uistatus=None):
		self.uistatus = uistatus
		self.node = node
		self.node.addEventInput(event.PresetChangedEvent, self.presetchanged)
		self.pchanged = {}
		self.currentpreset = None

	def getPresetsFromDB(self, session=None):
		'''
		get ordered list of presets for this session from DB
		'''
		if session is None:
			session = self.node.session

		## find presets that belong to this session
		pquery = data.PresetData(session=session, hold=False)
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
		namedict = strictdict.OrderedDict()
		for key in keys:
			p = pdict[key]
			namedict[p['name']] = p
		return namedict

	def toScope(self, presetname, emtarget=None):
		'''
		send the named preset to the scope
		optionally send a target to the scope as well
		'''
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

	eventinputs = node.Node.eventinputs + [event.ChangePresetEvent] + EM.EMClient.eventinputs
	eventoutputs = node.Node.eventoutputs + [event.PresetChangedEvent] + EM.EMClient.eventoutputs

	def __init__(self, name, session, managerlocation, **kwargs):
		self.initializeLogger(name)

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
		self.presets = strictdict.OrderedDict()
		self.selectedsessionpresets = None

		self.defineUserInterface()
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
			if emtarget is None:
				self.uistatus.set('Changing preset to "%s"' % pname)
				self.cycleToScope(pname)
			else:
				self.uistatus.set('Changing preset to "%s" and targeting' % pname)
				self.targetToScope(pname, emtarget)
		except PresetChangeError:
			self.uistatus.set('preset request to "%s" failed' % pname)
		else:
			self.uistatus.set('Preset changed to "%s"' % pname)
		## should we confirm if failure?
		self.confirmEvent(ievent)

	def getPresetsFromDB(self):
		'''
		get presets from current session out of database
		'''
		self.presets = self.presetsclient.getPresetsFromDB()
		## make sure we hold on to these
		for p in self.presets.values():
			p.addHold()
		self.setOrder()

	def importPresets(self, pdict):
		'''
		takes a set of presets from any session and generates 
		an identical set for this session
		'''
		## make new presets with this session
		self.presets = strictdict.OrderedDict()
		for name, preset in pdict.items():
			newp = data.PresetData(initializer=preset, session=self.session, hold=True)
			self.presetToDB(newp)
			self.presets[name] = newp
		self.setOrder()

	def presetToDB(self, presetdata):
		'''
		stores a preset in the DB under the current session name
		if no preset is specified, store all self.presets
		'''
		self.publish(presetdata, database=True, dbforce=True)
		## immediately replace it with a copy so we can do updates
		#pname = presetdata['name']

	def presetByName(self, name):
		if name in self.presets.keys():
			return self.presets[name]
		else:
			return None

	def setOrder(self, names=None, fromcallback=False):
		'''
		set order of self.presets, and set numbers
		if names given, use that to determine order
		otherwise, current order is ok, just update numbers
		'''
		if names is None:
			names = self.presets.keys()

		newdict = strictdict.OrderedDict()
		number = 0
		for name in names:
			p = self.presets[name]
			if p['number'] != number:
				newp = data.PresetData(initializer=p, number=number, hold=True)
				p.removeHold()

				self.presetToDB(newp)
			else:
				newp = p
			newdict[name] = newp
			number += 1
		self.presets = newdict

		## update the selector list but keep the same preset
		## selected
		if hasattr(self, 'uiselectpreset'):
			selectedindex = self.uiselectpreset.getSelected()
			try:
				selectedname = self.uiselectpreset.getSelectedValue()
				## may not be in presets anymore if removed
				## should cause exception
				selectedindex = self.presets.keys().index(selectedname)
			except:
				selectedindex = 0
			self.uiselectpreset.set(self.presets.keys(), selectedindex)

		## only set the UI if this was not from a callback
		if hasattr(self, 'orderlist') and not fromcallback:
			self.orderlist.set(self.presets.keys())

	def uiSetOrderCallback(self, namelist):
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
			self.setOrder(namelist, fromcallback=True)
		else:
			namelist = self.presets.keys()
		return namelist

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
		del self.presets[pname]
		pnew = data.PresetData(initializer=premove, removed=1, hold=False)
		self.presetToDB(pnew)
		premove.removeHold()

		## update order, selector list, etc.
		self.setOrder()

	def toScope(self, pname, magonly=False, outputevent=True):
		'''
		'''
		presetdata = self.presetByName(pname)
		if presetdata is None:
			message = 'No such preset %s' % (pname,)
			self.messagelog.error(message)
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

		self.uistatus.set(beginmessage)
		self.logger.info(beginmessage)

		self.emclient.setScope(scopedata)
		if cameradata is not None:
			self.emclient.setCamera(cameradata)

		pause = self.changepause.get()
		time.sleep(pause)
		if magonly:
			self.currentpreset = None
		else:
			self.currentpreset = presetdata
		self.uistatus.set(endmessage)
		self.logger.info(endmessage)
		if outputevent:
			self.outputEvent(event.PresetChangedEvent(name=name, preset=presetdata))

	def fromScope(self, name):
		'''
		create a new preset with name
		if a preset by this name already exists in my 
		list of managed presets, it will be replaced by the new one
		also returns the new preset object
		'''
		scopedata = self.emclient.getScope()
		cameradata = self.emclient.getCamera()
		newpreset = data.PresetData(hold=True)
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

		if name in self.presets:
			oldpreset = self.presets[name]
			oldpreset.removeHold()
		newpreset['number'] = number
		self.presets[name] = newpreset
		self.presetToDB(newpreset)

		## update UI
		self.uiselectpreset.set(self.presets.keys(), number)
		self.uistatus.set('Set preset "%s" values from instrument' % name)
		node.beep()
		return newpreset

	def presetNames(self):
		return self.presets.keys()

	def uiSessionSelectCallback(self, value):
		sname = self.othersession.getSelectedValue()
		self.importplist.set('Looking for presets...')
		sessiondata = self.sessiondict[sname]
		pdict = self.presetsclient.getPresetsFromDB(sessiondata)
		self.selectedsessionpresets = pdict
		## display the names
		names = pdict.keys()
		if names:
			namestr = ' '.join(names)
		else:
			namestr = 'None'
		self.importplist.set(namestr)
		return value

	def uiImport(self):
		if self.selectedsessionpresets is None:
			return
		self.importPresets(self.selectedsessionpresets)

	def uiToScope(self):
		new = self.uiselectpreset.getSelectedValue()
		try:
			self.cycleToScope(new)
		except PresetChangeError:
			self.logger.error('Preset change failed')
		node.beep()

	def cycleToScope(self, presetname, dofinal=True):
		'''
		prestename = target preset
		force = True:  cycle even if cycling to same preset
		magrepeat = True:  allow two or more consecutive presets
		   that have the same magnification
		magonly = True:  all presets in cycle (except for final) 
		   will only send magnification to TEM
		'''
		if not self.usecycle.get():
			if dofinal:
				self.toScope(presetname)
			return

		order = self.presets.keys()
		magonly = self.cyclemagonly.get()
		magshortcut = self.cyclemagshortcut.get()

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

	def uiSelectedFromScope(self):
		sel = self.uiselectpreset.getSelectedValue()
		newpreset = self.fromScope(sel)

	def uiSelectedRemove(self):
		sel = self.uiselectpreset.getSelectedValue()
		self.removePreset(sel)

	def uiNewFromScope(self):
		newname = self.enteredname.get()
		if newname:
			newpreset = self.fromScope(newname)
			self.setOrder()
			self.presetparams.set(newpreset)
			self.messagelog.information('created new preset: %s' % (newname,))
		else:
			self.messagelog.error('Invalid name for new preset')

	def uiSelectCallback(self, index):
		try:
			pname = self.presetNames()[index]
			self.currentselection = self.presetByName(pname)
		except IndexError:
			self.currentselection = None
		else:
			self.presetparams.set(self.currentselection)
			self.displayCalibrations(self.currentselection)
			self.displayDose(self.currentselection)
		return index

	def getHighTension(self):
		try:
			return self.emclient.getScope()['high tension']
		except EM.ScopeUnavailable:
			return None

	def displayCalibrations(self, preset):
		mag = preset['magnification']
		ht = self.getHighTension()

		## not dependent on HT
		pcaltime = self.calclients['pixel size'].time(mag)
		self.cal_pixelsize.set(str(pcaltime))
		modstagemodtimex = self.calclients['modeled stage'].timeModelCalibration('x')
		modstagemodtimey = self.calclients['modeled stage'].timeModelCalibration('y')
		tmpstr = 'x: %s, y: %s' % (modstagemodtimex,modstagemodtimey)
		self.cal_modeledstagemod.set(tmpstr)

		## dependent on HT
		if ht is None:
			message = 'unknown high tension'
			modmagstr = beamtime = imagetime = stagetime = message
		else:
			stagetime = self.calclients['stage'].time(ht, mag, 'stage position')
			imagetime = self.calclients['image'].time(ht, mag, 'image shift')
			beamtime = self.calclients['beam'].time(ht, mag, 'beam shift')
			modstagemagtimex = self.calclients['modeled stage'].timeMagCalibration(ht, mag, 'x')
			modstagemagtimey = self.calclients['modeled stage'].timeMagCalibration(ht, mag, 'y')
			modmagstr = 'x: %s, y: %s' % (modstagemagtimex,modstagemagtimey)

		self.cal_stage.set(str(stagetime))
		self.cal_imageshift.set(str(imagetime))
		self.cal_beam.set(str(beamtime))
		self.cal_modeledstagemag.set(modmagstr)

	def renewPreset(self, p):
		### this makes a copy of an existing preset
		### so that dbid is not set and we can 
		### edit the values
		if p.dbid is None:
			return p
		newpreset = data.PresetData(initializer=p, hold=True)
		p.removeHold()
		if p['name'] in self.presets:
			self.presets[p['name']].removeHold()
		self.presets[newpreset['name']] = newpreset
		if self.currentpreset is p:
			self.currentpreset = newpreset
		if self.currentselection is p:
			self.currentselection = newpreset
		return newpreset

	def uiCommitParams(self, value):
		newpreset = self.renewPreset(self.currentselection)
		presetdict = self.presetparams.get()
		newpreset.update(presetdict)
		self.presetToDB(newpreset)

	def getSessionList(self):
		'''
		get list of session names from this instrument
		'''
		myinstname = self.session['instrument']['name']
		querysession = data.SessionData()
		queryinst = data.InstrumentData()
		queryinst['name'] = myinstname
		querysession['instrument'] = self.session['instrument']
		limit = 100
		sessionlist = self.research(datainstance=querysession, results=limit)
		sessionnamelist = [x['name'] for x in sessionlist]
		self.sessiondict = dict(zip(sessionnamelist, sessionlist))
		self.othersession.setList(sessionnamelist)
		self.importplist.set('Select a session to see available presets')

	def defineUserInterface(self):
		self.initializeLoggerUserInterface()
		node.Node.defineUserInterface(self)

		self.messagelog = uidata.MessageLog('Message Log')

		self.uistatus = uidata.String('Status', '', 'r')
		self.uiprevious = uidata.String('Previous', '', 'r')
		self.uicurrent = uidata.String('Current', '', 'r')
		self.uinew = uidata.String('New', '', 'r')
		statuscontainer = uidata.Container('Status')
		statuscontainer.addObject(self.uistatus, position={'position':(0,0), 'span':(1,3)})
		statuscontainer.addObject(self.uiprevious, position={'position':(1,0)})
		statuscontainer.addObject(self.uicurrent, position={'position':(1,1)})
		statuscontainer.addObject(self.uinew, position={'position':(1,2)})

		# from other session
		self.othersession = uidata.SingleSelectFromList('Session', [], 0, usercallback=self.uiSessionSelectCallback)
		importmeth = uidata.Method('Import', self.uiImport)
		importcont = uidata.Container('Import')
		self.importplist = uidata.String('Presets', '', 'r')
		importcont.addObject(self.othersession, position={'position':(0,0)})
		importcont.addObject(importmeth, position={'position':(0,1)})
		importcont.addObject(self.importplist, position={'position':(1,0), 'span':(1,2)})

		# from scope
		newfromscopecont = uidata.Container('New')
		self.enteredname = uidata.String('Name', '', 'rw')
		newfromscopemethod = uidata.Method('New From Scope', self.uiNewFromScope)
		newfromscopecont.addObject(self.enteredname, position={'position':(0,0)})
		newfromscopecont.addObject(newfromscopemethod, position={'position':(0,1)})

		# calibrations status
		calcont = uidata.Container('Calibration Status')
		self.cal_pixelsize = uidata.String('Pixel Size', '', 'r')
		self.cal_imageshift = uidata.String('Image Shift Matrix', '', 'r')
		self.cal_stage = uidata.String('Stage Shift Matrix', '', 'r')
		self.cal_beam = uidata.String('Beam Shift Matrix', '', 'r')
		self.cal_modeledstagemod = uidata.String('Modeled Stage', '', 'r')
		self.cal_modeledstagemag = uidata.String('Modeled Stage Mag Only', '', 'r')
		calcont.addObjects((self.cal_pixelsize, self.cal_imageshift,
												self.cal_stage, self.cal_beam,
												self.cal_modeledstagemod, self.cal_modeledstagemag))


		## change parameters
		changecont = uidata.Container('Preset Change Parameters')
		self.xyonly = uidata.Boolean('Target stage x and y only', True, 'rw', persist=True)
		self.changepause = uidata.Float('Pause', 1.0, 'rw', persist=True)
		changecont.addObject(self.changepause, position={'position':(0,0)})
		changecont.addObject(self.xyonly, position={'position':(0,1)})

		# selection
		selectcont = uidata.Container('Selection')
		self.presetparams = PresetParameters(self, usercallback=self.uiCommitParams)
		controls = uidata.Container('')
		self.uiselectpreset = uidata.SingleSelectFromList('Preset', [], 0,
																								callback=self.uiSelectCallback)
		toscopemethod = uidata.Method('To Scope', self.uiToScope)
		fromscopemethod = uidata.Method('From Scope', self.uiSelectedFromScope)
		removemethod = uidata.Method('Remove', self.uiSelectedRemove)
		controls.addObject(self.uiselectpreset, position={'position':(0,0)})
		controls.addObject(toscopemethod, position={'position':(0,1)})
		controls.addObject(fromscopemethod, position={'position':(0,2)})
		controls.addObject(removemethod, position={'position':(0,3)})

		## Cycle
		cyclecont = uidata.Container('Cycle')
		self.usecycle = uidata.Boolean('On', True, 'rw', persist=True)
		self.cyclemagshortcut = uidata.Boolean('Mag Shortcut', True, 'rw', persist=True)
		self.cyclemagonly = uidata.Boolean('Mag Only', True, 'rw', persist=True)
		self.orderlist = uidata.Sequence('Order', [], 'rw', callback=self.uiSetOrderCallback)

		cyclecont.addObject(self.usecycle, position={'position':(0,0)})
		cyclecont.addObject(self.cyclemagshortcut, position={'position':(0,1)})
		cyclecont.addObject(self.cyclemagonly, position={'position':(0,2)})
		cyclecont.addObject(self.orderlist, position={'position':(1,0), 'span':(1,3)})

		selectcont.addObjects((controls, self.presetparams, calcont, cyclecont))

		# acquisition frame

		## goes with Acquire Reference Image and therefore is not
		## useful at the moment
		#cameraconfigure = self.cam.uiSetupContainer()
		acqdosemeth = uidata.Method('Acquire Dose Image (be sure specimen is not in the field of view)', self.uiAcquireDose)
		self.acqdosevalue = uidata.String('Dose', '', 'r')
		## not useful at the moment
		#acqrefmeth = uidata.Method('Acquire Preset Reference Image', self.uiAcquireRef)

		self.ui_image = uidata.Image('Image', None, 'r')

		imagecont = uidata.Container('Acquisition')
		imagecont.addObject(acqdosemeth, position={'position':(0,0)})
		imagecont.addObject(self.acqdosevalue, position={'position':(0,1)})
		imagecont.addObject(self.ui_image, position={'span':(1,2)})

		# main container
		container = uidata.LargeContainer('Presets Manager')
		container.addObject(self.messagelog, position={'expand': 'all'})
		container.addObjects((statuscontainer, changecont, importcont, newfromscopecont, selectcont, imagecont))
		self.uicontainer.addObject(container)
		return

	def XXXuiAcquireRef(self):
		self.uistatus.set('Acquiring reference image')
		self.cam.uiApplyAsNeeded()
		imagedata = self.cam.acquireCameraImageData(correction=True)
		if imagedata is None:
			return

		## store the CameraImageData as a PresetReferenceImageData
		ref = data.PresetReferenceImageData()
		ref.update(imagedata)
		if not self.currentpreset['hasref']:
			self.currentpreset['hasref'] = True
		ref['preset'] = self.currentpreset
		self.publish(ref, database=True)
		self.uistatus.set('Published new reference image for %s'
												% (self.currentpreset['name'],))

		## display
		self.ui_image.set(imagedata['image'].astype(Numeric.Float32))
		self.setStatus(self.currentpreset)

	def uiAcquireDose(self):
		if self.currentpreset is None:
			self.messagelog.error('You go to a preset before measuring dose')
			return
		self.uistatus.set('Acquiring dose image using preset config at 512x512')
		camdata0 = data.CameraEMData()
		camdata0.friendly_update(self.currentpreset)

		camdata1 = copy.deepcopy(camdata0)

		## figure out if we want to cut down to 512x512
		for axis in ('x','y'):
			change = camdata0['dimension'][axis] - 512
			if change > 0:
				camdata1['dimension'][axis] = 512
				camdata1['offset'][axis] += (change / 2)

		self.cam.setCameraEMData(camdata1)
		imagedata = self.cam.acquireCameraImageData(correction=True)
		self.uistatus.set('returning to original preset camera dimensions')
		self.cam.setCameraEMData(camdata0)
		if imagedata is None:
			return

		## display
		self.ui_image.set(imagedata['image'].astype(Numeric.Float32))
		dose = self.dosecal.dose_from_imagedata(imagedata)
		## store the dose in the current preset
		self.currentpreset = self.renewPreset(self.currentpreset)
		self.currentpreset['dose'] = dose
		self.presetToDB(self.currentpreset)
		self.presetparams.set(self.currentpreset)
		self.displayDose(self.currentpreset)

	def displayDose(self, preset):
		dose = preset['dose']
		if dose is None:
			displaydose = 'N/A'
		else:
			displaydose = dose / 1e20
			displaydose = '%.2f' % (displaydose,)
		self.acqdosevalue.set('%s: %s' % (preset['name'], displaydose))

	def XXXsetStatus(self, preset):
		## dose
		if preset['dose'] is None:
			status = 'N/A'
		else:
			fixed = preset['dose'] / 1e20
			status = '%.2f e/A^2' % (fixed,)
		self.dosestatus.set(status)

		## reference image
		if preset['hasref']:
			status = 'Done (would like a timestamp here)'
		else:
			status = 'N/A'
		self.refstatus.set(status)

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

		emdata = data.ScopeEMData(initializer=emtargetdata['scope'])

		if emdata['stage position'] and self.xyonly.get():
			## only set stage x and y
			for key in emdata['stage position'].keys():
				if key not in ('x','y'):
					del emdata['stage position'][key]

		## always ignore focus (only defocus should be used)
		try:
			emdata['focus'] = None
		except:
			pass

		scopedata = data.ScopeEMData(initializer=emdata)

		## figure out how to transform the target image shift
		## ???
		## for now, assume that image shift targets are not passed
		## across mag mode ranges, so newishift is straight from 
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

		newishift = {}
		if oldmag == newmag:
			self.uistatus.set('Using same magnification mode')
			newishift['x'] = scopedata['image shift']['x']
			newishift['x'] -= oldpreset['image shift']['x']
			newishift['x'] += newpreset['image shift']['x']

			newishift['y'] = scopedata['image shift']['y']
			newishift['y'] -= oldpreset['image shift']['y']
			newishift['y'] += newpreset['image shift']['y']
		else:
			self.uistatus.set('Using different magnification mode')
			newishift['x'] = newpreset['image shift']['x']
			newishift['y'] = newpreset['image shift']['y']

		## should use AllEMData, but that is not working yet
		scopedata.friendly_update(newpreset)
		scopedata['image shift'] = newishift
		cameradata = data.CameraEMData()
		cameradata.friendly_update(newpreset)

		try:
			self.emclient.setScope(scopedata)
			self.emclient.setCamera(cameradata)
		except:
			message = 'Cannot set instrument parameters'
			self.messagelog.error(message)
			raise PresetChangeError(message)

		pause = self.changepause.get()
		time.sleep(pause)
		name = newpreset['name']
		self.currentpreset = newpreset
		message = 'Preset (with target) changed to %s' % (name,)
		self.uistatus.set(message)
		self.logger.info(message)
		self.outputEvent(event.PresetChangedEvent(name=name, preset=newpreset))

class PresetParameters(uidata.Container):
	def __init__(self, node, usercallback=None):
		uidata.Container.__init__(self, 'Preset Parameters')
		self.node = node
		self.usercallback = usercallback
		self.singles = ('magnification', 'spot size', 'defocus', 'intensity')
		self.doubles = ('image shift', 'beam shift')
		self.others = ('dose', 'film')

		self.build()

	def build(self):
		self.singlesdict = {}
		row = 0
		col = 0
		for single in self.singles:
			if col > 1:
				col = 0
				row += 1
			o = self.singlesdict[single] = uidata.Number(single, 0, 'rw', usercallback=self.usercallback)
			self.addObject(o, position={'position':(row,col)})
			col += 1
		row += 1
		self.othersdict = {}
		o = self.othersdict['dose'] = uidata.Number('dose', 0, 'r', usercallback=self.usercallback)
		self.addObject(o, position={'position':(row,0)})
		o = self.othersdict['film'] = uidata.Boolean('film', False, 'rw', usercallback=self.usercallback)
		self.addObject(o, position={'position':(row,1)})
		
		self.doublesdict = {}
		for double in self.doubles:
			row += 1
			self.doublesdict[double] = {}
			subcont = uidata.Container(double)
			for pos,axis in ((0,'x'), (1,'y')):
				o = self.doublesdict[double][axis] = uidata.Number(axis, 0, 'rw', usercallback=self.usercallback)
				subcont.addObject(o, position={'position':(0,pos)})
			self.addObject(subcont, position={'position':(row,0),'span':(1,3)})
		self.camera = camerafuncs.SmartCameraParameters(self.node, usercallback=self.usercallback)
		self.addObject(self.camera)
		self.dosestring = uidata.String('Dose', 'N/A', 'r')
		self.addObject(self.dosestring)

	def set(self, presetdata):
		presetdict = presetdata.toDict()
		self.camera.set(presetdict)
		for single in self.singles:
			self.singlesdict[single].set(presetdict[single], usercallback=False)
		for double in self.doubles:
			for axis in ('x','y'):
				self.doublesdict[double][axis].set(presetdict[double][axis], usercallback=False)
		for other in self.others:
			self.othersdict[other].set(presetdict[other], usercallback=False)
		dose = presetdata['dose']
		self.dose = dose
		if dose is None:
			displaydose = 'N/A'
		else:
			displaydose = '%.4f' % (dose/1e20,)
		self.dosestring.set(displaydose)

	def get(self):
		presetdict = {}

		camdict = self.camera.get()
		presetdict.update(camdict)

		for single in self.singles:
			presetdict[single] = self.singlesdict[single].get()
		for double in self.doubles:
			presetdict[double] = {}
			for axis in ('x','y'):
				presetdict[double][axis] = self.doublesdict[double][axis].get()
		for other in self.others:
			presetdict[other] = self.othersdict[other].get()
		presetdict['dose'] = self.dose
		return presetdict


