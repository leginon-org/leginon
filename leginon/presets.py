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

	def uiSinglePresetSelector(self, label='', default='', permissions='rw', persist=False):
		return SinglePresetSelector(self, label, default, permissions, persist)

	def getPresetNames(self):
		presetlist = self.getPresets()
		pnames = [p['name'] for p in presetlist]
		return pnames

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

class DataHandler(node.DataHandler):
	def query(self, id):
		if id == ('presets',):
			result = data.PresetSequenceData()
			result['sequence'] = self.node.presets.values()
		elif id == ('current preset',):
			result = self.node.currentpreset
		else:
			result = node.DataHandler.query(self, id)
		return result

class PresetChangeError(Exception):
	pass

class PresetsManager(node.Node):

	eventinputs = node.Node.eventinputs + [event.ChangePresetEvent]
	eventoutputs = node.Node.eventoutputs + [event.PresetChangedEvent, event.ListPublishEvent]

	def __init__(self, id, session, nodelocations, tcpport=None, **kwargs):
		self.initializeLogger(id[-1])
		self.datahandler = DataHandler(self, loggername=self.logger.name)
		self.server = datatransport.Server(self.datahandler, tcpport,
																				loggername=self.logger.name)
		kwargs['datahandler'] = None

		node.Node.__init__(self, id, session, nodelocations, **kwargs)

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
		self.presets = strictdict.OrderedDict()
		self.getPresetsFromDB()

		self.defineUserInterface()
		self.validateCycleOrder()
		self.start()

	def exit(self):
		node.Node.exit(self)
		self.server.exit()

	def location(self):
		location = node.Node.location(self)
		location['data transport'] = self.server.location()
		return location

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
		pdata = data.PresetData(session=session)
		presets = self.research(datainstance=pdata)

		### only want most recent of each name
		self.presets = strictdict.OrderedDict()
		for preset in presets:
			pname = preset['name']
			if pname not in self.presets.keys():
				if preset['removed'] != 1:
					if preset['session'] is not self.session:
						newpreset = data.PresetData(initializer=preset, session=self.session, hasref=False)
						self.presetToDB(newpreset)
					else:
						newpreset = preset
					self.presets[pname] = newpreset

		self.validateCycleOrder()

	def presetToDB(self, presetdata=None):
		'''
		stores a preset in the DB under the current session name
		if no preset is specified, store all self.presets
		'''
		if presetdata is None:
			tostore = self.presets.values()
		else:
			tostore = [presetdata]
		for p in tostore:
			self.publish(p, database=True, dbforce=True)

	def presetByName(self, name):
		if name in self.presets.keys():
			return self.presets[name]
		else:
			return None

	def removePreset(self, pname):
		'''
		remove a preset by name
		'''
		if pname in self.presets.keys():
			premove = self.presets[pname]
			del self.presets[pname]
			pnew = data.PresetData(initializer=premove, removed=1)
			self.presetToDB(pnew)
		pnames = self.presetNames()
		self.uiselectpreset.set(pnames, 0)
		self.validateCycleOrder()

	def toScope(self, pname, magonly=False):
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
			scopedata['id'] = ('scope',)
			cameradata = None
		else:
			scopedata.friendly_update(presetdata)
			cameradata.friendly_update(presetdata)
			scopedata['id'] = ('scope',)
			cameradata['id'] = ('camera',)

		self.uistatus.set(beginmessage)
		self.logger.info(beginmessage)

		## should switch to using AllEMData
		try:
			self.publishRemote(scopedata)
			if cameradata is not None:
				self.publishRemote(cameradata)
		except node.PublishError:
			message = 'Cannot set instrument parameters. Maybe EM node is not working'
			self.messagelog.error(message)
			raise PresetChangeError(message)

		pause = self.changepause.get()
		time.sleep(pause)
		if magonly:
			self.currentpreset = None
		else:
			self.currentpreset = presetdata
		self.uistatus.set(endmessage)
		self.logger.info(endmessage)
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

		# to put preset at end, remove it first
		if name in self.presets.keys():
			del self.presets[name]
		self.presets[name] = newpreset

		self.presetToDB(newpreset)
		pnames = self.presetNames()
		self.uiselectpreset.set(pnames, len(pnames)-1)
		self.uistatus.set('Set preset "%s" values from instrument' % name)
		node.beep()
		return newpreset

	def presetNames(self):
		return self.presets.keys()

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

		order = self.orderlist.get()
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
			self.toScope(presetname)
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
		order = self.orderlist.get()

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

	def uiSelectedRemove(self):
		sel = self.uiselectpreset.getSelectedValue()
		self.removePreset(sel)

	def uiNewFromScope(self):
		newname = self.enteredname.get()
		if newname:
			newpreset = self.fromScope(newname)
			self.presetparams.set(newpreset)
			self.messagelog.information('created new preset: %s' % (newname,))
			self.validateCycleOrder()
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

	def uiCommitParams(self, value):
		oldpreset = self.currentselection
		pname = oldpreset['name']
		presetdict = self.presetparams.get()
		newpreset = data.PresetData(initializer=presetdict, session=self.session, name=pname)

		# to put preset at end, remove it first
		del self.presets[pname]
		self.presets[pname] = newpreset

		### make sure other pointers go to this new preset
		if self.currentpreset is oldpreset:
			self.currentpreset = newpreset
		self.currentselection = newpreset

		self.presetToDB(newpreset)

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
		self.initializeLoggerUserInterface()
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
		self.presetparams = PresetParameters(self, postcallback=self.uiCommitParams)
		self.uiselectpreset = uidata.SingleSelectFromList('Preset', [], 0,
																								callback=self.uiSelectCallback)
		toscopemethod = uidata.Method('To Scope', self.uiToScope)
		self.changepause = uidata.Float('Pause', 1.0, 'rw', persist=True)
		cyclecont = uidata.Container('Cycle')
		self.usecycle = uidata.Boolean('Cycle On', True, 'rw', persist=True)
		self.cyclemagshortcut = uidata.Boolean('Cycle Magnification Shortcut', True, 'rw', persist=True)
		self.cyclemagonly = uidata.Boolean('Cycle Magnification Only', True, 'rw', persist=True)
		self.orderlist = uidata.Sequence('Cycle Order', [], 'rw', persist=True)
		cyclecont.addObjects((self.usecycle, self.cyclemagshortcut,
													self.cyclemagonly, self.orderlist))

		fromscopemethod = uidata.Method('From Scope', self.uiSelectedFromScope)
		removemethod = uidata.Method('Remove', self.uiSelectedRemove)

		selectcont = uidata.Container('Selection')
		selectcont.addObjects((self.uiselectpreset, toscopemethod, fromscopemethod, removemethod, self.changepause, self.presetparams, statuscont, calcont, cyclecont))

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
		self.uicontainer.addObject(container)

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
		if self.currentpreset is None or self.currentpreset['name'] != newpresetname:
			self.cycleToScope(newpresetname, dofinal=False)

		self.logger.info('Going to target and to preset %s' % (newpresetname,))

		oldpreset = emtargetdata['preset']
		newpreset = self.presetByName(newpresetname)

		emdata = copy.deepcopy(emtargetdata['scope'])

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
		self.outputEvent(event.PresetChangedEvent(name=name))

class PresetParameters(uidata.Container):
	def __init__(self, node, postcallback=None):
		uidata.Container.__init__(self, 'Preset Parameters')
		self.node = node
		self.postcallback = postcallback
		self.singles = ('magnification', 'spot size', 'defocus', 'intensity')
		self.doubles = ('image shift', 'beam shift')

		self.build()

	def build(self):
		self.singlesdict = {}
		for single in self.singles:
			self.singlesdict[single] = uidata.Number(single, 0, 'rw', postcallback=self.postcallback)
		self.doublesdict = {}
		for double in self.doubles:
			self.doublesdict[double] = {}
			for axis in ('x', 'y'):
				label = double + ' ' + axis
				self.doublesdict[double][axis] = uidata.Number(label, 0, 'rw', postcallback=self.postcallback)

		self.camera = camerafuncs.SmartCameraParameters(self.node, postcallback=self.postcallback)

		components = []
		for single in self.singles:
			components.append(self.singlesdict[single])
		for double in self.doubles:
			for axis in ('x', 'y'):
				components.append(self.doublesdict[double][axis])
		components.append(self.camera)
		self.addObjects(components)

	def set(self, presetdata):
		presetdict = presetdata.toDict()
		self.camera.set(presetdict)
		for single in self.singles:
			self.singlesdict[single].set(presetdict[single], postcallback=False)
		for double in self.doubles:
			for axis in ('x','y'):
				self.doublesdict[double][axis].set(presetdict[double][axis], postcallback=False)

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

		return presetdict


