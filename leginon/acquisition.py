
import targetwatcher
import time
import data, event
import calibrationclient
import camerafuncs


class Acquisition(targetwatcher.TargetWatcher):
	def __init__(self, id, nodelocations, **kwargs):
		targetwatcher.TargetWatcher.__init__(self, id, nodelocations, **kwargs)

		self.calclients = {
			'image shift': calibrationclient.ImageShiftCalibrationClient(self),
			'stage position': calibrationclient.StageCalibrationClient(self),
			'modeled stage position': calibrationclient.ModeledStageCalibrationClient(self)
		}
		self.cam = camerafuncs.CameraFuncs(self)

		self.defineUserInterface()
		self.start()

	def processTargetData(self, targetdata):
		'''this is called by TargetWatcher.processData when targets available'''
		print 'PROCESSING', targetdata
		#detailedlist = self.detailedTargetList(self.presetlist, targetlist, self.targetmethod)

		#for target in detailedlist:
		movetype = self.movetype.get()
		scopestate = self.targetToState(targetdata, movetype)

		# for now camera state will be same as target origin
		camerastate = targetdata.content['camera']
		scopestate.update(camerastate)

		## set the scope/camera state
		emdata = data.EMData('scope', scopestate)
		self.publishRemote(emdata)
		## maybe some settling time here?

		print 'sleeping 2 sec'
		time.sleep(2)

		print 'acquire'
		self.acquire()

	def acquire(self):
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
		print 'publishing image'
		self.publish(imagedata, event.CameraImagePublishEvent)
		print 'image published'

	def targetToState(self, targetdata, movetype):
		'''
		convert an ImageTargetData to a scope/camera dict
		using chosen move type
		The result is scope state
		'''
		targetinfo = targetdata.content
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

		prefs = self.registerUIContainer('Preferences', (self.movetype, self.delaydata, self.acqtype))

		self.registerUISpec('Acquisition', (prefs, super))

