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
import EM

class Calibrator(node.Node):
	'''
	Calibrator base class
	Contains basic functions useful for doing calibrations
	'''
	eventinputs = node.Node.eventinputs + EM.EMClient.eventinputs
	eventoutputs = node.Node.eventoutputs + EM.EMClient.eventoutputs
	def __init__(self, id, session, managerlocation, **kwargs):
		node.Node.__init__(self, id, session, managerlocation, **kwargs)
		self.emclient = EM.EMClient(self)
		self.cam = camerafuncs.CameraFuncs(self)
		self.ui_image = None

	def getMagnification(self):
		mag = self.emclient.getScope()['magnification']
		return mag

	def getHighTension(self):
		ht = self.emclient.getScope()['high tention']
		return ht

	def currentState(self):
		dat = self.emclient.getScope()
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
		self.uicontainer.addObject(container)
