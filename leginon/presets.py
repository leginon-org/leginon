#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#
import node
import data
import event
import dbdatakeeper
import cPickle
import copy
import uidata
import camerafuncs
import strictdict
import threading
import time
import unique
import calibrationclient

class PresetsClient(object):
	'''
	client functions for nodes to access PresetsManager
	'''
	def __init__(self, node, uistatus=None):
		self.uistatus = uistatus
		self.node = node
		self.node.addEventInput(event.PresetChangedEvent, self.presetchanged)
		self.pchanged = {}

	def toScope(self, presetname, emtarget=None):
		'''
		send the named preset to the scope
		optionally send a target to the scope as well
		'''
		self.pchanged[presetname] = threading.Event()
		evt = event.ChangePresetEvent()
		evt['name'] = presetname
		evt['emtarget'] = emtarget
		try:
			if self.uistatus is not None:
				self.uistatus.set('Requesting preset change to %s' % (presetname,))
			self.node.outputEvent(evt, wait=True)
			if self.uistatus is not None:
				self.uistatus.set('Preset change to %s completed' % (presetname,))
		except node.ConfirmationTimeout:
			if self.uistatus is not None:
				self.uistatus.set('Preset change request timed out')

	def presetchanged(self, ievent):
		name = ievent['name']
		if name in self.pchanged:
			self.pchanged[name].set()
		self.node.confirmEvent(ievent)

	def getPresets(self):
		try:
			seqdata = self.node.researchByDataID(('presets',))
		except node.ResearchError:
			return []
		if seqdata is None:
			return []
		else:
			return seqdata['sequence']

	def getCurrentPreset(self):
		pdata = self.node.researchByDataID(('current preset',))
		return pdata

	def getPresetByName(self, pname):
		ps = self.getPresets()
		for p in ps:
			if p['name'] == pname:
				return p

	def uiPresetSelector(self):
		getpresets = uidata.Method('Get Names', self.uiGetPresetNames)
		self.uiselectpreset = uidata.SingleSelectFromList('Select Preset', [], 0, persist=True)
		container = uidata.Container('Preset Selection')
		container.addObjects((getpresets, self.uiselectpreset))
		return container

	def uiGetPresetNames(self):
		presetlist = self.getPresets()
		pnames = [p['name'] for p in presetlist]
		self.uiselectpreset.set(pnames, 0) 

	def uiGetSelectedName(self):
		presetname = self.uiselectpreset.getSelectedValue()
		return presetname

class DataHandler(node.DataHandler):
	def query(self, id):
		if id == ('presets',):
			result = data.PresetSequenceData()
			result['sequence'] = self.node.presets
		elif id == ('current preset',):
			result = self.node.currentpreset
		else:
			result = node.DataHandler.query(self, id)
		return result


class PresetsManager(node.Node):

	eventinputs = node.Node.eventinputs + [event.ChangePresetEvent]
	eventoutputs = node.Node.eventoutputs + [event.PresetChangedEvent, event.ListPublishEvent]

	def __init__(self, id, session, nodelocations, **kwargs):
		node.Node.__init__(self, id, session, nodelocations, datahandler=DataHandler, **kwargs)

		self.addEventInput(event.ChangePresetEvent, self.changePreset)

		ids = [('presets',), ('current preset',)]
		e = event.ListPublishEvent(idlist=ids)
		self.outputEvent(e)

		self.cam = camerafuncs.CameraFuncs(self)
		self.calclients = {
			'pixel size':calibrationclient.PixelSizeCalibrationClient(self),
			'image':calibrationclient.ImageShiftCalibrationClient(self),
			'stage':calibrationclient.StageCalibrationClient(self),
			'beam':calibrationclient.BeamShiftCalibrationClient(self),
			'modeled stage':calibrationclient.ModeledStageCalibrationClient(self),
		}
		self.dosecal = calibrationclient.DoseCalibrationClient(self)

		self.currentselection = None
		self.currentpreset = None
		self.presets = []
		self.getPresetsFromDB()

		self.defineUserInterface()
		self.validateCycleOrder()
		self.start()

	def changePreset(self, ievent):
		'''
		callback for received PresetChangeEvent from client
		'''
		pname = ievent['name']
		emtarget = ievent['emtarget']
		if emtarget is None:
			self.uistatus.set('Changing preset to "%s"' % pname)
			self.toScopeFollowCycle(pname)
		else:
			self.uistatus.set('Changing preset to "%s" and targeting' % pname)
			self.targetToScope(pname, emtarget)
		self.confirmEvent(ievent)
		self.uistatus.set('Preset changed to "%s"' % pname)

	def getPresetsFromDB(self, session=None):
		'''
		get list of presets for this session from DB
		and use them to create self.presets list
		'''
		if session is None:
			session = self.session
			diffsession = False
		else:
			## importing another sessions presets
			diffsession = True

		### get presets from database
		newsession = data.SessionData(initializer=session)
		newsession['image path'] = None
		pdata = data.PresetData(session=newsession)
		presets = self.research(datainstance=pdata)

		### only want most recent of each name
		mostrecent = []
		names = []
		for preset in presets:
			if preset['name'] not in names:
				names.append(preset['name'])
				if preset['removed'] != 1:
					if preset['session'] is not self.session:
						preset['session'] = self.session
					mostrecent.append(preset)
		self.presets[:] = mostrecent

		### if using another session's presets, now save them
		### as this sessions presets
		if diffsession:
			## since this is a new session, we don't trust
			## previously acquired references (plus they won't
			## be linked to these new presets anyway)
			for p in self.presets:
				p['hasref'] = False
			self.presetToDB()

		self.validateCycleOrder()

	def presetToDB(self, presetdata=None):
		'''
		stores a preset in the DB under the current session name
		if no preset is specified, store all self.presets
		'''
		if presetdata is None:
			tostore = self.presets
		else:
			tostore = [presetdata]
		for p in tostore:
			pdata = copy.copy(p)
			pdata['session'] = self.session
			self.publish(pdata, database=True, dbforce=True)

	def presetByName(self, name):
		for p in self.presets:
			if p['name'] == name:
				return p
		return None

	def indexByName(self, name):
		i = 0
		for p in self.presets:
			if p['name'] == name:
				return i
			i += 1
		return None

	def indexByPreset(self, preset):
		return self.presets.index(preset)

	def insertPreset(self, p, newpreset):
		'''
		insert new preset into my set of managed presets
		p is either the index or item to insert at
		'''
		if type(p) is int:
			i = p
		else:
			i = self.index(p)
		self.presets.insert(i, newpreset)

	def removePreset(self, p):
		'''
		remove a preset by index or reference
		p is either a preset, or index of the preset
		'''
		premove = None
		if type(p) is int:
			premove = self.presets[p]
			del self.presets[p]
		elif type(p) is str:
			pcopy = list(self.presets)
			for preset in pcopy:
				if preset['name'] == p:
					premove = preset
					self.presets.remove(preset)
		else:
			premove = p
			self.presets.remove(p)
		if premove is not None:
			premove['removed'] = 1
			self.presetToDB(premove)
		pnames = self.presetNames()
		self.uiselectpreset.set(pnames, 0)
		self.validateCycleOrder()

	def presetFromName(self, pname):
		presetdata = None
		for preset in self.presets:
			if pname == preset['name']:
				presetdata = preset
				break
		return presetdata

	def toScope(self, p):
		'''
		p is either index, preset, or name
		'''
		presetdata = None
		if type(p) is int:
			presetdata = self.presets[p]
		elif type(p) is str:
			presetdata = self.presetFromName(p)
		elif isinstance(p, data.PresetData):
			presetdata = p
		else:
			self.messagelog.error('Invalid argument to set scope')
			return

		if presetdata is None:
			self.messagelog.error('No such preset')
			return

		name = presetdata['name']
		self.uistatus.set('Changing preset to "%s"' % name)

		## should switch to using AllEMData
		scopedata = data.ScopeEMData()
		cameradata = data.CameraEMData()
		scopedata.friendly_update(presetdata)
		cameradata.friendly_update(presetdata)
		scopedata['id'] = ('scope',)
		cameradata['id'] = ('camera',)
		try:
			self.publishRemote(scopedata)
			self.publishRemote(cameradata)
		except node.PublishError:
			self.printException()
			self.messagelog.error('Cannot set instrument parameters')
		else:
			pause = self.changepause.get()
			time.sleep(pause)
			self.currentpreset = presetdata
			self.uistatus.set('Preset changed to %s' % (name,))
			self.outputEvent(event.PresetChangedEvent(name=name))

	def fromScope(self, name):
		'''
		create a new preset with name
		if a preset by this name already exists in my 
		list of managed presets, it will be replaced by the new one
		also returns the new preset object
		'''
		scopedata = self.researchByDataID(('scope',))
		cameradata = self.researchByDataID(('camera no image data',))
		newpreset = data.PresetData()
		newpreset.friendly_update(scopedata)
		newpreset.friendly_update(cameradata)
		newpreset['id'] = None
		newpreset['session'] = self.session
		newpreset['name'] = name

		for p in self.presets:
			if p['name'] == name:
				self.presets.remove(p)
				break
		self.presets.append(newpreset)

		self.presetToDB(newpreset)
		pnames = self.presetNames()
		self.uiselectpreset.set(pnames, len(pnames)-1)
		self.uistatus.set('Set preset "%s" values from instrument' % name)
		node.beep()
		return newpreset

	def eucToScope(self, pname):
		'''
		p is either index, preset, or name
		'''
		eucfoc = None
		for preset in self.presets:
			if pname == preset['name']:
				eucfoc = preset['eucentric focus']
				break
		if eucfoc is None:
			self.messagelog.error('No such preset "%s"' % pname)
			return

		self.uistatus.set('Setting eucentric focus for preset %s' % (pname,))

		scopedata = data.ScopeEMData()
		scopedata['id'] = ('scope',)
		scopedata['focus'] = eucfoc
		try:
			self.publishRemote(scopedata)
		except node.PublishError:
			self.printException()
			self.messagelog.error('Cannot set instrument parameters')

	def eucFromScope(self, name):
		'''
		create a new copy of an existing preset and replace the 
		value of eucentric focus
		'''

		## get current value of focus
		scope = self.researchByDataID(('focus',))
		focusvalue = scope['focus']

		for p in self.presets:
			if p['name'] == name:
				p['eucentric focus'] = focusvalue
				self.presetToDB(p)
				self.uistatus.set('Eucentric focus for %s: %s' % (name, focusvalue))

		node.beep()

	def presetNames(self):
		names = [p['name'] for p in self.presets]
		return names

	def uiGetPresetsFromDB(self):
		othersessionname = self.othersession.getSelectedValue()
		initializer = {'name': othersessionname}
		othersessiondata = data.SessionData(initializer=initializer)
		sessions = self.research(datainstance=othersessiondata)
		try:
			othersession = sessions[0]
		except (TypeError, IndexError):
			self.messagelog.error('Cannot location session: %s', othersessionname)
			return
		self.getPresetsFromDB(othersession)
		names = self.presetNames()
		self.uiselectpreset.set(names, 0)

	def uiToScope(self):
		new = self.uiselectpreset.getSelectedValue()
		self.toScopeFollowCycle(new)
		node.beep()

	def toScopeFollowCycle(self, new):
		usecycle = self.usecycle.get()
		if usecycle:
			order = self.orderlist.get()
			self.uinew.set(new)
			if self.currentpreset is None:
				# first time, we don't know where where
				# are, so go directly to requested preset
				# then recursive toScopeFollowCylce
				self.uistatus.set('First preset change, automatically cycling...')
				self.toScope(new)
				self.toScopeFollowCycle(new)
				return
			current = self.currentpreset['name']
			self.uicurrent.set(current)

			## if cycle creation works, then 
			try:
				cycle = self.createCycleList(current, new)
			except RuntimeError:
				cycle = []
			self.uistatus.set('Cycle: %s' % str(cycle)[1:-1])

			if cycle:
				self.uistatus.set('Cycling to %s' % (new,))
				# remove first and last from list
				try:
					del cycle[0]
					del cycle[-1]
				except IndexError:
					pass
				currentmag = self.currentpreset['magnification']
				newpresetdata = self.presetFromName(new)
				if currentmag == newpresetdata['magnification']:
					samemag = True
				else:
					samemag = False

				if samemag:
					if self.cyclemagchanged.get():
						self.uistatus.set('Cycling, but magnification will not change')
					else:
						self.uistatus.set('Not cycling, magnification will not change')
						cycle = []

				for p in cycle:
					if self.cyclemagonly.get():
						presetdata = self.presetFromName(p)
						mag = presetdata['magnification']
						if currentmag == mag:
							continue
						self.uistatus.set('Magnification is %sx' % (mag,))
						scopedata = data.ScopeEMData()
						scopedata['magnification'] = mag
						scopedata['id'] = ('scope',)
						try:
							self.publishRemote(scopedata)
						except node.PublishError:
							self.printException()
							self.messagelog.error('Cannot set instrument parameters')
						currentmag = mag
						pause = self.changepause.get()
						time.sleep(pause)
					else:
						self.uistatus.set('Preset "%s" to instrument' % (p,))
						self.toScope(p)

		self.uistatus.set('Preset "%s" to instrument' % (new,))
		self.toScope(new)

	def createCycleList(self, first, last, order=None):
		if order is None:
			order = self.orderlist.get()
		if not order:
			#print 'no order list specified'
			raise RuntimeError('no order list specified')
		self.uistatus.set('Order: %s' % str(order)[1:-1])
		if last not in order:
			#print 'last not in order list'
			raise RuntimeError('last not in order')
		if first not in order:
			first = last
		cycle = []
		on = False
		done = False
		while True:
			for pname in order:
				if on:
					if pname == last:
						done = True
					cycle.append(pname)
				else:
					if pname == first:
						on = True
						cycle.append(pname)
				if done:
					break
			if done:
				break
		return cycle

	def validateCycleOrder(self):
		'''
		checks for missing presets or extra presets in the cycle list
		'''
		## this may be called before the user interface is done
		## so we return in that case
		if not hasattr(self, 'orderlist'):
			return
		cyclepresets = self.orderlist.get()
		allpresets = self.presetNames()

		missing_in_cycle = []
		for presetname in allpresets:
			if presetname not in cyclepresets:
				missing_in_cycle.append(presetname)
		extra_in_cycle = []
		for presetname in cyclepresets:
			if presetname not in allpresets:
				extra_in_cycle.append(presetname)

		missing_str = ', '.join(missing_in_cycle)
		extra_str = ', '.join(extra_in_cycle)
		problems = []
		if missing_str:
			missing_str = 'Presets Missing from cycle:  ' + missing_str
			problems.append(missing_str)
		if extra_str:
			extra_str = 'In Cycle, but no such preset:  ' + extra_str
			problems.append(extra_str)

		message = ', '.join(problems)
		if message:
			self.messagelog.warning(message)

	def uiSelectedFromScope(self):
		sel = self.uiselectpreset.getSelectedValue()
		newpreset = self.fromScope(sel)

	def uiSelectedEucFromScope(self):
		sel = self.uiselectpreset.getSelectedValue()
		self.eucFromScope(sel)

	def uiSelectedEucToScope(self):
		sel = self.uiselectpreset.getSelectedValue()
		self.eucToScope(sel)

	def uiSelectedRemove(self):
		sel = self.uiselectpreset.getSelectedValue()
		self.removePreset(sel)

	def uiNewFromScope(self):
		newname = self.enteredname.get()
		if newname:
			newpreset = self.fromScope(newname)
			d = newpreset.toDict(noNone=True)
			del d['session']
			self.presetparams.set(d, callback=False)
			self.messagelog.info('created new preset: %s' % (newname,))
			self.validateCycleOrder()
		else:
			self.messagelog.error('Invalid name for new preset')

	def uiSelectCallback(self, index):
		try:
			self.currentselection = self.presets[index]
		except IndexError:
			self.currentselection = None
		else:
			d = self.currentselection.toDict(noNone=True)
			try:
				del d['session']
			except KeyError:
				pass
			self.presetparams.set(d, callback=False)
			self.displayCalibrations(self.currentselection)
			self.setStatus(self.currentselection)
		return index

	def getHighTension(self):
		htdata = self.researchByDataID(('high tension',))
		return htdata['high tension']

	def displayCalibrations(self, preset):
		mag = preset['magnification']
		try:
			ht = self.getHighTension()
		except:
			self.messagelog.error('Cannot get high tension value, calibration display failed')
			return
		pcaltime = self.calclients['pixel size'].time(mag)
		self.cal_pixelsize.set(str(pcaltime))
		stagetime = self.calclients['stage'].time(ht, mag, 'stage position')
		self.cal_stage.set(str(stagetime))

		imagetime = self.calclients['image'].time(ht, mag, 'image shift')
		self.cal_imageshift.set(str(imagetime))
		beamtime = self.calclients['beam'].time(ht, mag, 'beam shift')
		self.cal_beam.set(str(beamtime))
		modstagemodtimex = self.calclients['modeled stage'].timeModelCalibration('x')
		modstagemodtimey = self.calclients['modeled stage'].timeModelCalibration('y')
		tmpstr = 'x: %s, y: %s' % (modstagemodtimex,modstagemodtimey)
		self.cal_modeledstagemod.set(tmpstr)
		modstagemagtimex = self.calclients['modeled stage'].timeMagCalibration(ht, mag, 'x')
		modstagemagtimey = self.calclients['modeled stage'].timeMagCalibration(ht, mag, 'y')
		tmpstr = 'x: %s, y: %s' % (modstagemagtimex,modstagemagtimey)
		self.cal_modeledstagemag.set(tmpstr)

	def uiParamsCallback(self, value):
		if (self.currentselection is None) or (not value):
			d = {}
		else:
			if self.autosquare.get():
				for autokey in ('dimension','binning','offset'):
					self.square(value[autokey])
			for key in value:
				self.currentselection[key] = value[key]
			self.presetToDB(self.currentselection)
			d = self.currentselection.toDict(noNone=True)
			del d['session']
		return d

	def square(self, xydict):
		xydict['y'] = xydict['x']

	def getSessionNameList(self):
		'''
		get list of session names from this instrument
		'''
		myinstname = self.session['instrument']['name']
		querysession = data.SessionData()
		queryinst = data.InstrumentData()
		queryinst['name'] = myinstname
		querysession['instrument'] = queryinst
		sessionlist = self.research(datainstance=querysession, fill=False)
		sessionnamelist = [x['name'] for x in sessionlist]
		return sessionnamelist

	def defineUserInterface(self):
		node.Node.defineUserInterface(self)

		self.messagelog = uidata.MessageLog('Message Log')

		self.uistatus = uidata.String('Status', '', 'r')
		self.uiprevious = uidata.String('Previous', '', 'r')
		self.uicurrent = uidata.String('Current', '', 'r')
		self.uinew = uidata.String('New', '', 'r')
		statuscontainer = uidata.Container('Status')
		statuscontainer.addObjects((self.uistatus, self.uiprevious,
																self.uicurrent, self.uinew))

		self.xyonly = uidata.Boolean('Target stage x and y only', True, 'rw',
																	persist=True)

		sessionnamelist = self.getSessionNameList()
		self.othersession = uidata.SingleSelectFromList('Session', sessionnamelist,
																										0)
		fromdb = uidata.Method('Import', self.uiGetPresetsFromDB)
		importcont = uidata.Container('Import')
		importcont.addObjects((self.othersession, fromdb))

		# create preset
		self.enteredname = uidata.String('New Name', '', 'rw')
		newfromscopemethod = uidata.Method('New From Scope', self.uiNewFromScope)
		createcont = uidata.Container('Preset Creation')
		createcont.addObjects((self.enteredname, newfromscopemethod))

		# preset status
		statuscont = uidata.Container('Preset Status')
		self.dosestatus = uidata.String('Dose', '', 'r')
		self.refstatus = uidata.String('Reference Image', '', 'r')
		statuscont.addObjects((self.dosestatus, self.refstatus))

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

		# selection
		self.autosquare = uidata.Boolean('Auto Square', True, 'rw')
		self.presetparams = uidata.Struct('Parameters', {}, 'rw',
																			self.uiParamsCallback)
		self.uiselectpreset = uidata.SingleSelectFromList('Preset', [], 0,
																								callback=self.uiSelectCallback)
		toscopemethod = uidata.Method('To Scope', self.uiToScope)
		self.changepause = uidata.Float('Pause', 1.0, 'rw', persist=True)
		cyclecont = uidata.Container('Cycle')
		self.usecycle = uidata.Boolean('Follow cycle', True, 'rw', persist=True)
		self.cyclemagchanged = uidata.Boolean('Cycle same magnification', True,
																					'rw', persist=True)
		self.cyclemagonly = uidata.Boolean('Cycle magnification only', False, 'rw',
																				persist=True)
		self.orderlist = uidata.Sequence('Cycle Order', [], 'rw', persist=True)
		cyclecont.addObjects((self.usecycle, self.cyclemagchanged,
													self.cyclemagonly, self.orderlist))

		fromscopemethod = uidata.Method('From Scope', self.uiSelectedFromScope)
		eucfromscopemethod = uidata.Method('Eucentric Focus From Scope',
																				self.uiSelectedEucFromScope)
		euctoscopemethod = uidata.Method('Eucentric Focus To Scope',
																			self.uiSelectedEucToScope)
		removemethod = uidata.Method('Remove', self.uiSelectedRemove)


		selectcont = uidata.Container('Selection')
		selectcont.addObjects((self.uiselectpreset, toscopemethod, fromscopemethod,
														eucfromscopemethod, euctoscopemethod, removemethod,
														self.changepause, cyclecont, self.autosquare,
														self.presetparams, statuscont, calcont))

		pnames = self.presetNames()
		self.uiselectpreset.set(pnames, 0)
		self.orderlist.set(pnames)

		# acquisition
		cameraconfigure = self.cam.uiSetupContainer()
		acqdosemeth = uidata.Method('Acquire Dose Image (be sure specimen is not in the field of view)', self.uiAcquireDose)
		acqrefmeth = uidata.Method('Acquire Preset Reference Image',
																self.uiAcquireRef)

		#self.statrows = uidata.Sequence('Stats Row Range', [], 'rw', persist=True)
		#self.statcols = uidata.Sequence('Stats Column Range', [], 'rw',
		#																	persist=True)
		#statsmeth = uidata.Method('Get Stats', self.uiGetStats)

		self.ui_image = uidata.Image('Image', None, 'r')


		imagecont = uidata.Container('Acquisition')
		imagecont.addObjects((cameraconfigure, acqdosemeth, acqrefmeth,
													self.ui_image,))

		# main container
		container = uidata.LargeContainer('Presets Manager')
		container.addObjects((self.messagelog, statuscontainer, self.xyonly,
													importcont, createcont, selectcont, imagecont))
		self.uiserver.addObject(container)

		return

	def uiAcquireRef(self):
		self.uistatus.set('Acquiring reference image')
		self.cam.uiApplyAsNeeded()
		imagedata = self.cam.acquireCameraImageData(correction=True)
		if imagedata is None:
			return

		## store the CameraImageData as a PresetReferenceImageData
		ref = data.PresetReferenceImageData(id=self.ID())
		ref.update(imagedata)
		if not self.currentpreset['hasref']:
			self.currentpreset['hasref'] = True
		ref['preset'] = self.currentpreset
		self.publish(ref, database=True)
		self.uistatus.set('Published new reference image for %s'
												% (self.currentpreset['name'],))

		## display
		self.ui_image.set(imagedata['image'])
		self.setStatus(self.currentpreset)

	def uiAcquireDose(self):
		if self.currentpreset is None:
			self.messagelog.error('You go to a preset before measuring dose')
			return
		self.uistatus.set('Acquiring dose image using preset config at 512x512')
		camdata0 = data.CameraEMData()
		camdata0.friendly_update(self.currentpreset)

		camdata1 = copy.deepcopy(camdata0)
		camdata1['dimension'] = {'x':512,'y':512}
		camdata1['offset'] = self.cam.autoOffset(camdata1['dimension'], camdata1['binning'])
		self.cam.setCameraEMData(camdata1)
		imagedata = self.cam.acquireCameraImageData(correction=True)
		self.uistatus.set('returning to original preset camera dimensions')
		self.cam.setCameraEMData(camdata0)
		if imagedata is None:
			return

		## display
		self.ui_image.set(imagedata['image'])
		dose = self.dosecal.dose_from_imagedata(imagedata)
		## store the dose in the current preset
		self.currentpreset['dose'] = dose
		self.presetToDB(self.currentpreset)
		self.setStatus(self.currentpreset)

	def setStatus(self, preset):
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
		if self.usecycle.get():
			order = self.orderlist.get()
			if self.currentpreset is None:
				currentname = order[0]
			else:
				currentname = self.currentpreset['name']
			previousname = order[order.index(newpresetname)-1]
			self.uiprevious.set(previousname)
			self.uicurrent.set(currentname)
			self.uinew.set(newpresetname)
			if currentname not in (newpresetname, previousname):
				self.uistatus.set('Now cycling to %s' % (previousname,))
				self.toScopeFollowCycle(previousname)

		oldpreset = emtargetdata['preset']
		newpreset = self.presetByName(newpresetname)

		emdata = copy.deepcopy(emtargetdata['scope'])

		## only set stage x and y
		if self.xyonly.get():
			for key in emdata['stage position'].keys():
				if key not in ('x','y'):
					del emdata['stage position'][key]

		## always ignore focus (only defocus should be used)
		try:
			emdata['focus'] = None
		except:
			pass

		scopedata = data.ScopeEMData(id=('scope',), initializer=emdata)

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

		cameradata['id'] = ('camera',)
		scopedata['id'] = ('scope',)

		try:
			self.publishRemote(scopedata)
			self.publishRemote(cameradata)
		except node.PublishError:
			self.printException()
			self.messagelog.error('Cannot set instrument parameters')
		except:
			self.printException()
		else:
			pause = self.changepause.get()
			time.sleep(pause)
			name = newpreset['name']
			self.currentpreset = newpreset
			self.uistatus.set('Preset changed to %s' % (name,))
			self.outputEvent(event.PresetChangedEvent(name=name))
