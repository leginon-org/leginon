#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#
import node, event, leginondata
import gui.wx.Calibrator
import instrument
import presets

class Calibrator(node.Node):
	'''
	Calibrator base class
	Contains basic functions useful for doing calibrations
	'''
	eventinputs = node.Node.eventinputs + presets.PresetsClient.eventinputs
	panelclass = gui.wx.Calibrator.Panel
	defaultsettings = {
		'instruments': {'tem': None, 'ccdcamera': None},
		'override preset': False,
		'camera settings': None,
		'correlation type': 'cross',
	}
	def __init__(self, id, session, managerlocation, **kwargs):
		node.Node.__init__(self, id, session, managerlocation, **kwargs)
		self.cortypes = ['cross', 'phase']
		self.instrument = instrument.Proxy(self.objectservice, self.session,
																				self.panel)
		self.presetsclient = presets.PresetsClient(self)

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
			dat = self.instrument.getData(leginondata.ScopeEMData)
		except:
			return None
		return dat

	def initInstruments(self):
		if self.settings['override preset']:
			instruments = self.settings['instruments']
			try:
				self.instrument.setTEM(instruments['tem'])
				self.instrument.setCCDCamera(instruments['ccdcamera'])
			except ValueError, e:
				self.logger.error('Cannot set instruments: %s' % (e,))
				return 1
			try:
				self.instrument.ccdcamera.Settings = self.settings['camera settings']
			except Exception, e:
				self.logger.error(e)
				return 1
		else:
			if self.presetsclient.getCurrentPreset() is None:
				self.logger.error('Preset is unknown and preset override is off')
				return 1
		return 0

	def acquireImage(self):
		try:
			status = self.initInstruments()
		except Exception, e:
			self.logger.exception('Acquisition failed: %s' % e)
			self.panel.acquisitionDone()
			return
		if status:
			self.panel.acquisitionDone()
			return
		try:
			imagedata = self.acquireCorrectedCameraImageData()
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

