
import acquisition
import node, data, event

class Focuser(acquisition.Acquisition):
	def __init__(self, id, nodelocations, **kwargs):

		self.btcalclient = calibrationclient.BeamTiltCalibrationClient(self)

		acquisition.Acquisition.__init__(self, id, nodelocations, **kwargs)

	def acquire(self, preset):
		'''
		this replaces Acquisition.acquire()
		Instead of acquiring and image, we do autofocus
		'''
		correction = self.btcalclient.measureDefocusStig(btilt)
		defoc = correction['defocus']
		stigx = correction['stigx']
		stigy = correction['stigy']
		self.correctStig(stigx, stigy)
		self.correctZ(defoc)

	def correctStig(self, deltax, deltay):
		stig = self.researchByDataID('stigmator').content
		stig['stigmator']['objective']['x'] += deltax
		stig['stigmator']['objective']['y'] += deltay
		emdata = data.EMData('scope', stig)
		print 'correcting stig by %s,%s', % (deltax,deltay)
		self.publishRemote(emdata)

	def correctZ(self, delta):
		stage = self.researchByDataID('stage position').content
		newz = state['x'] + delta
		newstage = {'stage position': {'z': newz }}
		emdata = data.EMData('scope', newstage)
		print 'moving stage Z by %s', % (delta,)
		self.publishRemote(emdata)
