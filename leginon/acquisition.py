
import targetwatcher
import time
import data, event
import calibrationclient
import camerafuncs
import presets
import copy


class Acquisition(targetwatcher.TargetWatcher):
	def __init__(self, id, nodelocations, **kwargs):
		targetwatcher.TargetWatcher.__init__(self, id, nodelocations, **kwargs)
		self.cam = camerafuncs.CameraFuncs(self)

		self.calclients = {
			'image shift': calibrationclient.ImageShiftCalibrationClient(self),
			'stage position': calibrationclient.StageCalibrationClient(self),
			'modeled stage position': calibrationclient.ModeledStageCalibrationClient(self)
		}
		self.presetsclient = presets.PresetsClient(self)

		self.defineUserInterface()
		self.start()

	def processTargetData(self, targetdata):
		'''this is called by TargetWatcher.processData when targets available'''
		print 'PROCESSING', targetdata
		#detailedlist = self.detailedTargetList(self.presetlist, targetlist, self.targetmethod)

		movetype = self.movetype.get()
		targetstate = self.targetToState(targetdata, movetype)

		### subtract the old preset from the target, so that
		### we can apply a new preset
		print 'targetdata keys', targetdata.content.keys()
		if 'preset' in targetdata.content:
			oldpreset = targetdata.content['preset']

			## right now, the only thing a target and preset
			## have in common is image shift
			targetstate['image shift']['x'] -= oldpreset['image shift']['x']
			targetstate['image shift']['y'] -= oldpreset['image shift']['y']
			print 'TARGETSTATE', targetstate

		### do each preset for this acquisition
		presetnames = self.presetnames.get()
		for presetname in presetnames:
			newpreset = self.presetsclient.getPreset(presetname)
			newtarget = copy.deepcopy(targetstate)
			## merge the preset and target
			## every item in preset overides corresponding item
			## in target, except image shift, which is added
			## so we can't just use newtarget.update(newpreset)
			## For the future, make specialized class that
			## can handle update(), with knowledge of how to 
			## update different keys
			for key in newtarget:
				if key in newpreset:
					### image shift is special
					if key == 'image shift':
						newtarget[key]['x'] += newpreset[key]['x']
						newtarget[key]['y'] += newpreset[key]['y']
					else:
						newtarget[key] = newpreset[key]

			print 'NEWTARGET', newtarget

			## set the scope/camera state
			emdata = data.EMData('scope', newtarget)
			self.publishRemote(emdata)

			print 'sleeping 2 sec'
			time.sleep(2)

			print 'acquire'
			self.acquire(newpreset)

	def acquire(self, preset):
		acqtype = self.acqtype.get()
		if acqtype == 'raw':
			imagedata = self.cam.acquireCameraImageData(None,0)
		elif acqtype == 'corrected':
			try:
				imagedata = self.cam.acquireCameraImageData(None,1)
			except:
				print 'image not acquired'
				imagedata = None

		if imagedata is None:
			return

		## attach preset to imagedata
		imagedata.content['preset'] = dict(preset)

		print 'publishing image'
		self.publish(imagedata, event.CameraImagePublishEvent)
		print 'image published'

	def targetToState(self, targetdata, movetype):
		'''
		convert an ImageTargetData to a scope/camera dict
		using chosen move type
		The result is scope state
		'''
		targetinfo = copy.deepcopy(targetdata.content)
		## get relavent info from target event
		targetrow = targetinfo['array row']
		targetcol = targetinfo['array column']
		targetshape = targetinfo['array shape']
		targetscope = targetinfo['scope']
		targetcamera = targetinfo['camera']

		## calculate delta from image center
		deltarow = targetrow - targetshape[0] / 2
		deltacol = targetcol - targetshape[1] / 2

		## to shift targeted point to center...
		deltarow = -deltarow
		deltacol = -deltacol

		pixelshift = {'row':deltarow, 'col':deltacol}

		## figure out scope state that gets to the target
		calclient = self.calclients[movetype]
		newscope = calclient.transform(pixelshift, targetscope, targetcamera)
		return newscope

	def detailedTargetList(self, presetlist, targetlist, targetmethod):
		'''
		create detailed target list
		'''
		## add some inteligence here to automatically figure out
		## with target method to use

		pass

	def defineUserInterface(self):
		super = targetwatcher.TargetWatcher.defineUserInterface(self)

		movetypes = self.calclients.keys()
		temparam = self.registerUIData('temparam', 'array', default=movetypes)
		self.movetype = self.registerUIData('TEM Parameter', 'string', choices=temparam, permissions='rw', default='stage position')

		self.delaydata = self.registerUIData('Delay (sec)', 'float', default=2.5, permissions='rw')

		acqtypes = self.registerUIData('acqtypes', 'array', default=('raw', 'corrected'))
		self.acqtype = self.registerUIData('Acquisition Type', 'string', default='raw', permissions='rw', choices=acqtypes)
		self.presetnames = self.registerUIData('Preset Names', 'array', default=('p550',), permissions='rw')

		prefs = self.registerUIContainer('Preferences', (self.movetype, self.delaydata, self.acqtype, self.presetnames))

		self.registerUISpec('Acquisition', (prefs, super))

