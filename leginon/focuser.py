import acquisition
import node, data
import calibrationclient
import camerafuncs
import uidata
import threading

class Focuser(acquisition.Acquisition):
	def __init__(self, id, sesison, nodelocations, **kwargs):
		self.cam = camerafuncs.CameraFuncs(self)

		self.btcalclient = calibrationclient.BeamTiltCalibrationClient(self)
		self.focus_methods = {
			'None': self.correctNone,
			'Stage Z': self.correctZ,
			'Defocus': self.correctDefocus
		}
		self.abortfail = threading.Event()

		acquisition.Acquisition.__init__(self, id, sesison, nodelocations, targetclass=data.FocusTargetData, **kwargs)

	def acquire(self, preset, trial=False):
		'''
		this replaces Acquisition.acquire()
		Instead of acquiring an image, we do autofocus
		'''
		info = {}
		self.abortfail.clear()
		btilt = self.btilt.get()
		pub = self.publishimages.get()
		checkdrift = self.drifton.get()
		drift_timeout = self.drifttimeout.get()
		try:
			correction = self.btcalclient.measureDefocusStig(btilt, pub, checkdrift, drift_timeout)
		except calibrationclient.Abort:
			print 'measureDefocusStig was aborted'
			return 1
		print 'MEASURED DEFOCUS AND STIG', correction
		defoc = correction['defocus']
		stigx = correction['stigx']
		stigy = correction['stigy']
		min = correction['min']

		info.update({'defocus':defoc, 'stigx':stigx, 'stigy':stigy, 'min':min})

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
		if validdefocus and (abs(defoc) > self.stigfocthresh.get()):
			validstig = True
		else:
			validstig = False
		
		if validstig and self.stigcorrection.get():
			print 'Stig correction'
			self.correctStig(stigx, stigy)
			info['corrected stig'] = 1
		else:
			info['corrected stig'] = 0

		if validdefocus:
			print 'Defocus correction'
			try:
				focustype = self.focustype.getSelectedValue()
				focusmethod = self.focus_methods[focustype]
			except (IndexError, KeyError):
				print 'no method selected for correcting defocus'
			else:
				info['defocus correction'] = focustype
				focusmethod(defoc)

		frd = data.FocuserResultData(initializer=info)
		self.publish(frd, database=True)

		return 0

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

	def uiAbortFailure(self):
		self.btcalclient.abortevent.set()

	def defineUserInterface(self):
		acquisition.Acquisition.defineUserInterface(self)
		self.btilt = uidata.Float('Beam Tilt', 0.02, 'rw')
		self.stigfocthresh = uidata.Float('Stig Threshold', 1e-6, 'rw')
		self.drifton = uidata.Boolean('Check Drift', True, 'rw')
		self.drifttimeout = uidata.Float('Drift Timeout (sec)', 300, 'rw')
		focustypes = self.focus_methods.keys()
		focustypes.sort()
		self.focustype = uidata.SingleSelectFromList('Focus Correction Type',
																							focustypes, 0)
		self.stigcorrection = uidata.Boolean('Stigmator Correction', False, 'rw')
		self.publishimages = uidata.Boolean('Publish Images', True, 'rw')
		abortfailmethod = uidata.Method('Abort With Failure', self.uiAbortFailure)
		testmethod = uidata.Method('Test Autofocus', self.uiTest)
		container = uidata.MediumContainer('Focuser')
		container.addObjects((self.btilt, self.stigfocthresh, self.drifton, self.drifttimeout, self.focustype, self.stigcorrection, self.publishimages, abortfailmethod, testmethod))
		self.uiserver.addObject(container)

