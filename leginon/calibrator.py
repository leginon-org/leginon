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
import gui.wx.Calibrator

class Calibrator(node.Node):
	'''
	Calibrator base class
	Contains basic functions useful for doing calibrations
	'''
	panelclass = gui.wx.Calibrator.Panel
	settingsclass = data.CalibratorSettingsData
	defaultsettings = {
		'camera settings': None,
		'correlation type': 'cross',
	}
	eventinputs = node.Node.eventinputs + EM.EMClient.eventinputs
	eventoutputs = node.Node.eventoutputs + EM.EMClient.eventoutputs
	def __init__(self, id, session, managerlocation, **kwargs):
		node.Node.__init__(self, id, session, managerlocation, **kwargs)
		self.images = {
			'Image': None,
			'Correlation': None,
		}
		self.imagetargets = {
			'Image': {},
			'Correlation': {},
		}
		self.cortypes = ['cross', 'phase']
		self.emclient = EM.EMClient(self)
		self.cam = camerafuncs.CameraFuncs(self)

		self.typenames = ['Peak']
		self.panel.addTargetTypes(self.typenames)

	def updateImage(self, name, image, targets={}):
		self.images[name] = image
		self.imagetargets[name] = targets
		self.panel.imageUpdated(name, image, targets)

	def getMagnification(self):
		mag = self.emclient.getScope()['magnification']
		return mag

	def getHighTension(self):
		ht = self.emclient.getScope()['high tension']
		return ht

	def currentState(self):
		dat = self.emclient.getScope()
		return dat

	def acquireImage(self):
		self.cam.setCameraDict(self.settings['camera settings'].toDict())
		try:
			imagedata = self.cam.acquireCameraImageData()
		except camerafuncs.NoCorrectorError:
			self.messagelog.error('No Corrector node, acquisition failed')
			return

		if imagedata is None:
			self.messagelog.error('acquisition failed')
			return

		self.updateImage('Image', newimage)
		return imagedata

