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
import gui.wx.Calibrator
import instrument

class Calibrator(node.Node):
	'''
	Calibrator base class
	Contains basic functions useful for doing calibrations
	'''
	panelclass = gui.wx.Calibrator.Panel
	settingsclass = data.CalibratorSettingsData
	defaultsettings = {
		'use camera settings': False,
		'camera settings': None,
		'correlation type': 'cross',
	}
	def __init__(self, id, session, managerlocation, **kwargs):
		node.Node.__init__(self, id, session, managerlocation, **kwargs)
		self.cortypes = ['cross', 'phase']
		self.instrument = instrument.Proxy(self.objectservice, self.session,
																				self.panel)

	def getMagnification(self):
		try:
			mag = self.instrument.tem.Magnification
		except:
			mag = None
		try:
			mags = self.instrument.tem.Magnifications
		except:
			mags = None
		return mag, mags

	def getHighTension(self):
		try:
			ht = self.instrument.tem.HighTension
		except:
			return None
		return ht

	def currentState(self):
		try:
			dat = self.instrument.getData(data.ScopeEMData)
		except:
			return None
		return dat

	def acquireImage(self):
		try:
			if self.settings['use camera settings']:
				self.instrument.ccdcamera.Settings = self.settings['camera settings']
			imagedata = self.instrument.getData(data.CorrectedCameraImageData)
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

