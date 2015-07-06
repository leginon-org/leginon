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
import os
import re
import cameraclient

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
		'camera settings': cameraclient.default_settings,
		'correlation type': 'phase',
		'lpf sigma': 1.5,
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

	def currentState(self,dataclass=leginondata.ScopeEMData):
		try:
			dat = self.instrument.getData(dataclass)
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

	def setImageFilename(self, imagedata):
		prefix = self.session['name']
		digits = 5
		suffix = self.name.replace(' ','')
		extension = 'mrc'
		try:
			path = imagedata.mkpath()
		except Exception, e:
			raise
			raise node.PublishError(e)
		filenames = os.listdir(path)
		pattern = '^%s_[0-9]{%d}%s*.%s$' % (prefix, digits, suffix, extension)
		number = 0
		end = len('%s.%s' % (suffix, extension))
		for filename in filenames:
			if re.search(pattern, filename):
				n = int(filename[-digits - end:-end])
				if n > number:
					number = n
		number += 1
		if number >= 10**digits:
			raise node.PublishError('too many images, time to go home')
		filename = ('%s_%0' + str(digits) + 'd%s') % (prefix, number, suffix)
		imagedata['filename'] = filename

	def insertAcquisitionImageData(self, imagedata):
		acquisitionimagedata = leginondata.AcquisitionImageData(initializer=imagedata,version=0)
		self.setImageFilename(acquisitionimagedata)
		acquisitionimagedata.attachPixelSize()
		acquisitionimagedata.insert(force=True)
		return acquisitionimagedata
