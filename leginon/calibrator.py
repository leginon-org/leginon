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
		self.cortypes = ['cross', 'phase']
		self.emclient = EM.EMClient(self)
		self.cam = camerafuncs.CameraFuncs(self)

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
		try:
			self.cam.setCameraDict(self.settings['camera settings'])
			imagedata = self.cam.acquireCameraImageData()
		except (EM.ScopeUnavailable, camerafuncs.CameraError), e:
			self.logger.error('Acquisition failed: %s' % e)
			self.panel.acquisitionDone()
			return
		except Exception, e:
			self.logger.exception('Acquisition failed: %s' % e)
			self.panel.acquisitionDone()
			return

		if imagedata is None:
			self.messagelog.error('Acquisition failed')
			self.panel.acquisitionDone()
			return

		self.setImage(imagedata['image'], 'Image')
		self.panel.acquisitionDone()
		return imagedata

