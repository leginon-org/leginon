import acquisition
import node, data
import calibrationclient
import camerafuncs
import uidata

class Focuser(acquisition.Acquisition):
	def __init__(self, id, sesison, nodelocations, **kwargs):
		self.cam = camerafuncs.CameraFuncs(self)

		self.btcalclient = calibrationclient.BeamTiltCalibrationClient(self)
		self.focus_methods = {
			'None': self.correctNone,
			'Stage Z': self.correctZ,
			'Defocus': self.correctDefocus
		}

		acquisition.Acquisition.__init__(self, id, sesison, nodelocations, targetclass=data.FocusTargetData, **kwargs)

	def acquire(self, preset, trial=False):
		'''
		this replaces Acquisition.acquire()
		Instead of acquiring an image, we do autofocus
		'''
		btilt = self.btilt.get()
		pub = self.publishimages.get()
		drift_timeout = 300
		correction = self.btcalclient.measureDefocusStig(btilt, pub, drift_timeout)
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
		if validdefocus and (abs(defoc) > 2e-6):
			validstig = True
		else:
			validstig = False
		
		if validstig and self.stigcorrection.get():
			print 'Stig correction'
			self.correctStig(stigx, stigy)

		if validdefocus:
			print 'Defocus correction'
			try:
				focustype = self.focustype.getSelectedValue()
				focusmethod = self.focus_methods[focustype]
			except (IndexError, KeyError):
				print 'no method selected for correcting defocus'
			else:
				focusmethod(defoc)

	def correctStig(self, deltax, deltay):
		stig = self.researchByDataID(('stigmator',))
		stig['stigmator']['objective']['x'] += deltax
		stig['stigmator']['objective']['y'] += deltay
		emdata = data.ScopeEMData(id=('scope',), initializer=stig)
		print 'correcting stig by %s,%s' % (deltax,deltay)
		self.publishRemote(emdata)

	def correctDefocus(self, delta):
		defocus = self.researchByDataID(('defocus',))
		defocus['defocus'] += delta
		defocus['reset defocus'] = 1
		emdata = data.ScopeEMData(id=('scope',), initializer=defocus)
		print 'correcting defocus by %s' % (delta,)
		self.publishRemote(emdata)

	def correctZ(self, delta):
		stage = self.researchByDataID(('stage position',))
		newz = stage['stage position']['z'] + delta
		newstage = {'stage position': {'z': newz }}
		newstage['reset defocus'] = 1
		emdata = data.ScopeEMData(id=('scope',), initializer=newstage)
		print 'correcting stage Z by %s' % (delta,)
		self.publishRemote(emdata)

	def correctNone(self, delta):
		print 'not applying defocus correction'

	def uiTest(self):
		self.acquire(None)

	def defineUserInterface(self):
		acquisition.Acquisition.defineUserInterface(self)
		self.btilt = uidata.Float('Beam Tilt', 0.02, 'rw')
		focustypes = self.focus_methods.keys()
		focustypes.sort()
		self.focustype = uidata.SingleSelectFromList('Focus Correction Type',
																							focustypes, 0)
		self.stigcorrection = uidata.Boolean('Stigmator Correction', False, 'rw')
		self.publishimages = uidata.Boolean('Publish Images', True, 'rw')
		testmethod = uidata.Method('Test Autofocus', self.uiTest)
		container = uidata.MediumContainer('Focuser')
		container.addObjects((self.btilt, self.focustype, self.stigcorrection,
														self.publishimages, testmethod))
		self.uiserver.addObject(container)

