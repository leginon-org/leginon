
import targetwatcher


class Acquisition(targetwatcher.TargetWatcher):
	def __init__(self, id, nodelocations, **kwargs):
		targetwatcher.TargetWatcher.__init__(self, id, nodelocations, **kwargs)

		self.calclients = {
			'image shift': calibrationclient.ImageShiftCalibrationClient(self),
			'stage position': calibrationclient.StageCalibrationClient(self),
			'modeled stage position': calibrationclient.ModeledStageCalibrationClient(self)
		}

		self.defineUserInterface()
		self.start()

	def processTargetData(self, targetlist):
		'''this is called by TargetWatcher.processData when targets available'''
		print 'PROCESSING', targetlist
		detailedlist = self.detailedTargetList(self.presetlist, targetlist, self.targetmethod)
		for target in detailedlist:
			emdata = data.EMData('scope', target)
			self.publishRemote(emdata)
			## maybe some settling time here?

			self.acquire()

	def targetToState(self, targetdata, movetype):
		'''
		convert an ImageTargetData to a scope/camera dict
		using chosen move type
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
		mag = targetscope['magnification']

		## figure out shift
		calclient = self.calclients[movetype]
		newstate = calclient.transform(pixelshift, targetscope, targetcamera)

		emdat = data.EMData('scope', newstate)
		self.publishRemote(emdat)

		# wait for a while
		time.sleep(self.delaydata.get())

		## acquire image
		self.acquireImage()


	def detailedTargetList(self, presetlist, targetlist, targetmethod):
		'''
		create detailed target list
		'''
		## add some inteligence here to automatically figure out
		## with target method to use

		
