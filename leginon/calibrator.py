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
		cameraconfig = self.cam.configUIData()

		container = uidata.LargeContainer('Calibrator')
		container.addObjects((self.ui_image, cameraconfig))
		self.uiserver.addObject(container)
