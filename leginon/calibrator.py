#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#
import node, event, data
import fftengine
import correlator
import peakfinder
import time
import camerafuncs
import uidata

class Calibrator(node.Node):
	'''
	Calibrator base class
	Contains basic functions useful for doing calibrations
	'''
	def __init__(self, id, session, nodelocations, **kwargs):
		node.Node.__init__(self, id, session, nodelocations, **kwargs)
		self.cam = camerafuncs.CameraFuncs(self)
		self.ui_image = None

	def getMagnification(self):
		magdata = self.researchByDataID(('magnification',))
		return magdata['magnification']

	def getHighTension(self):
		htdata = self.researchByDataID(('high tension',))
		return htdata['high tension']

	def currentState(self):
		dat = self.researchByDataID(('scope',))
		return dat

	def imageViewer(self):
		if self.ui_image is None:
			self.ui_image = uidata.Image('Calibrator Image', None, 'r')
		return self.ui_image

	def defineUserInterface(self):
		node.Node.defineUserInterface(self)
		
		self.ui_image = uidata.Image('Calibrator Image', None, 'r')
		camsetup = self.cam.uiSetupContainer()

		container = uidata.LargeContainer('Calibrator')
		container.addObjects((self.ui_image, camsetup))
		self.uiserver.addObject(container)
