import acquisition
import node, data
import calibrationclient
import camerafuncs

class Focuser(acquisition.Acquisition):
	def __init__(self, id, nodelocations, **kwargs):
		self.cam = camerafuncs.CameraFuncs(self)

		self.btcalclient = calibrationclient.BeamTiltCalibrationClient(self)
		self.focus_methods = {
			'None': self.correctNone,
			'Stage Z': self.correctZ,
			'Defocus': self.correctDefocus
		}

		acquisition.Acquisition.__init__(self, id, nodelocations, **kwargs)

	def acquire(self, preset):
		'''
		this replaces Acquisition.acquire()
		Instead of acquiring and image, we do autofocus
		'''
		btilt = self.btilt.get()
		pub = self.publishimages.get()
		correction = self.btcalclient.measureDefocusStig(btilt, pub)
		print 'MEASURED DEFOCUS AND STIG', correction
		defoc = correction['defocus']
		stigx = correction['stigx']
		stigy = correction['stigy']
		min = correction['min']

		### validate defocus correction
		# possibly use min (value minimized during least square fit)
		#   mag: 50000, tilt: 0.02, defoc: 30e-6
		#     84230 was bad
		#   mag: 50000, tilt: 0.02, defoc: 25e-6
		#     5705 was bad
		#   mag: 50000, tilt: 0.02, defoc: 22e-6
		#     4928 was maybe
		#   mag: 50000, tilt: 0.02, defoc: 20e-6
		#     3135 was maybe
		#   mag: 50000, tilt: 0.02, defoc: 18e-6
		#     1955 was maybe
		#   mag: 50000, tilt: 0.02, defoc: 14e-6
		#      582 was good
		# for now, assum it is valid
		validdefocus = 1

		### validate stig correction
		# stig is only valid for large defocus
		if validdefocus and (abs(defoc) > 1e-6):
			validstig = 1
		
		if validstig and self.stigcorrection.get():
			print 'Stig correction'
			self.correctStig(stigx, stigy)

		if validdefocus:
			print 'Defocus correction'
			focustype = self.focustype.get()
			try:
				focusmethod = self.focus_methods[focustype]
			except KeyError:
				print 'no method selected for correcting defocus'
			else:
				focusmethod(defoc)

	def correctStig(self, deltax, deltay):
		#stig = self.researchByDataID('stigmator').content
		stig = self.researchByDataID('stigmator')
		stig['stigmator']['objective']['x'] += deltax
		stig['stigmator']['objective']['y'] += deltay
		#emdata = data.EMData('scope', em=stig)
		emdata = data.EMData('scope', stig)
		print 'correcting stig by %s,%s' % (deltax,deltay)
		self.publishRemote(emdata)

	def correctDefocus(self, delta):
		#defocus = self.researchByDataID('defocus').content
		defocus = self.researchByDataID('defocus')
		defocus['defocus'] += delta
		#emdata = data.EMData('scope', defocus)
		emdata = data.EMData('scope', em=defocus)
		print 'correcting defocus by %s' % (delta,)
		self.publishRemote(emdata)

	def correctZ(self, delta):
		#stage = self.researchByDataID('stage position').content
		stage = self.researchByDataID('stage position')
		newz = stage['stage position']['z'] + delta
		newstage = {'stage position': {'z': newz }}
		#emdata = data.EMData('scope', newstage)
		emdata = data.EMData('scope', em=newstage)
		print 'correcting stage Z by %s' % (delta,)
		self.publishRemote(emdata)

	def correctNone(self, delta):
		print 'not applying defocus correction'

	def uiTest(self):
		self.acquire(None)
		return ''

	def defineUserInterface(self):
		acqui = acquisition.Acquisition.defineUserInterface(self)

		self.btilt = self.registerUIData('Beam Tilt', 'float', default=0.02, permissions='rw')
		focustypes = self.registerUIData('focustypes', 'array', default=self.focus_methods.keys())
		self.focustype = self.registerUIData('Focus Correction Type', 'string', choices=focustypes, permissions='rw', default='None')
		self.stigcorrection = self.registerUIData('Stigmator Correction', 'boolean', permissions='rw')
		self.publishimages = self.registerUIData('Publish Images', 'boolean', default=1)

		test = self.registerUIMethod(self.uiTest, 'Test Autofocus', ())

		prefs = self.registerUIContainer('Focuser Setup', (self.btilt, self.focustype, self.stigcorrection, self.publishimages, test))

		myui = self.registerUISpec('Focuser', (prefs,))
		myui += acqui
		return myui

