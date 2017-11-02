#
# COPYRIGHT:
#       The Leginon software is Copyright under
#       Apache License, Version 2.0
#       For terms of the license agreement
#       see  http://leginon.org
#

# to get ice thickness from mean values of images with and without energy filter
# theory: Thickness/MFP = log (It/Izl)
# MFP = electron mean free path in ice
# Izl = zero-loss peak intensity
# It = total spectrum intensity
# APPROXIMATION: Use energy-filtered mean intensity as Izl
#                Use image intensity without slit as It
# mean free path estimate from paper: need to verify experimentally
# by comparing calculated values with geometrically detrmined values
# Geometry: by tomogram (Alex Noble) or Berriman +30 -30 image pairs


from leginon import leginondata
import event
import imagewatcher
import threading
import node
import calibrationclient
#import numpy  wjr
#import math   wjr
import pyami.quietscipy
#import scipy.ndimage wjr
from pyami import imagefun, arraystats  #wjr
import gui.wx.IcethicknessEF  #wjr
#from pyami import fftfun
from acquisition import Acquisition   #wjr
import presets # wjr
import gui.wx.Presets #wjr`
from math import log # natural log
import copy
import instrument



class IcethicknessEF(imagewatcher.ImageWatcher):
	eventinputs = imagewatcher.ImageWatcher.eventinputs + [event.AcquisitionImagePublishEvent]
	eventoutputs = imagewatcher.ImageWatcher.eventoutputs 

	panelclass = gui.wx.IcethicknessEF.Panel   #wjr
	settingsclass = leginondata.ZeroLossIceThicknessSettingsData   #wjr
	defaultsettings = {
		'process': False,
                'exposure time': 500.0,         #ms
		'slit width': 15.0,         #eV
		'mean free path': 340.0,   #nm
	}
	def __init__(self, id, session, managerlocation, **kwargs):
		imagewatcher.ImageWatcher.__init__(self, id, session, managerlocation, **kwargs)

		self.instrument = instrument.Proxy(self.objectservice,
																				self.session,
																				self.panel)
		self.calclient = calibrationclient.CalibrationClient(self)
		self.postprocess = threading.Event()
		self.presetsclient = presets.PresetsClient(self)
		self.start()

	def processImageData(self, imagedata, ):  #wjr
		'''
	        collect two images: one with slit in, one without, and compare intensitites to get thickness
		'''
		if self.settings['process']:
			exp_preset = imagedata['preset']
			acquirestr = 'Itot'
			noslitimagedata=  self._acquireSpecialImage(exp_preset, acquirestr, self.settings['exposure time'], False, self.settings['slit width'])
			acquirestr = 'Izlp'
			zlpimagedata =  self._acquireSpecialImage(exp_preset, acquirestr, self.settings['exposure time'], True, self.settings['slit width'])

			try: 
				imagearray_tot = noslitimagedata['image']
				imagearray_zlp = zlpimagedata['image']
			except:
				self.logger.error('no thickness images collected')
				return
			zlossth = leginondata.ZeroLossIceThicknessData()
		        zlossth['no slit mean'] = arraystats.mean(imagearray_tot)
                        zlossth['no slit sd'] = arraystats.std(imagearray_tot)

		        zlossth['slit mean'] = arraystats.mean(imagearray_zlp)
                        zlossth['slit sd'] = arraystats.std(imagearray_zlp)
			zlossth['image'] = imagedata

   			zlossth['thickness'] = self.settings['mean free path'] * log (zlossth['no slit mean']/(zlossth['slit mean']))
			
			self.logger.info('no slit mean: %f' % (zlossth['no slit mean'],))
			self.logger.info('slit mean: %f' % (zlossth['slit mean'],))
			self.logger.info('calculated thickness: %f' % (zlossth['thickness'],))
 
			zlossth.insert()
	def _acquireSpecialImage(self, preset, acquirestr, exp_time, filtered, slit_width):
		# acquire an image by only changing camera params, not microscope. 
						#leginon/leginondata.py: ('energy filtered', bool),
						#leginon/leginondata.py: ('energy filter', bool),
						#leginon/leginondata.py: ('energy filter width', float),
		errstr = 'Acquire %s image failed: ' %(acquirestr) +'%s'
		self.logger.info('Acquiring %s image' %(acquirestr))
		camdata0 = leginondata.CameraEMData()
#		if not camdata0['energy filter']:   # if camera does not have an EF, raise an error
#			self.logger.error(errstr % 'Energy filter not present')
#			return
		camdata0.friendly_update(preset)

		# These will be overwritten to acquire special image
		was_saving_frames = bool(camdata0['save frames'])
		was_aligning_frames = bool(camdata0['align frames'])
		was_slit_width = float(camdata0['energy filter width']) 
		was_filtered = bool(camdata0['energy filtered']) 
		was_time = float(camdata0['exposure time'])
		## deactivate frame saving and align frame flags
		camdata0['save frames'] = False
		camdata0['align frames'] = False

		camdata1 = copy.copy(camdata0) #not a deep copy
		#set correct energy filter params
		camdata1['energy filtered'] = filtered
		camdata1['energy filter width'] = slit_width
		camdata1['exposure time'] = exp_time

		try:
			self.instrument.setData(camdata1)
		except:
			self.logger.error(errstr % 'unable to set camera parameters')
			return
		try:
			imagedata = self.acquireCorrectedCameraImageData(force_no_frames=True)
		except:
			self.logger.error(errstr % 'unable to acquire corrected image data')
			return
		try:
			# restore preset parameters Bug #3614
			camdata0['save frames'] = was_saving_frames
			camdata0['align frames'] = was_aligning_frames
			camdata0['energy filtered'] = was_filtered
			camdata0['energy filter width'] = was_slit_width
			camdata0['exposure time'] = was_time
			self.instrument.setData(camdata0)
		except:
			estr = 'Return to orginial camera state failed: %s'
			self.logger.error(estr % 'unable to set camera parameters')
			return
		self.logger.info('Returned to original camera settings')
		if imagedata is None:
			self.logger.error(errstr % 'unable to get corrected image')
			return
		return imagedata





