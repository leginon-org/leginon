import node, event, data
import fftengine
import correlator
import peakfinder
import time
import camerafuncs

class Calibrator(node.Node):
	'''
	Calibrator base class
	Contains basic functions useful for doing calibrations
	'''
	def __init__(self, id, session, nodelocations, **kwargs):
		node.Node.__init__(self, id, session, nodelocations, **kwargs)
		self.cam = camerafuncs.CameraFuncs(self)

	def getMagnification(self):
		magdata = self.researchByDataID(('magnification',))
		return magdata['em']['magnification']

	def currentState(self):
		dat = self.researchByDataID(('scope',))
		return dat['em']
