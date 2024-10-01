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


#camdata0['energy filtered'] -- means: does the camera have a filter or not
#camdata0['energy filter'])  -- means: is the slit inserted or not


from leginon import leginondata
from leginon import event
from leginon import imagewatcher
import threading
from leginon import node
from leginon import calibrationclient
#import numpy  wjr
#import math   wjr
import pyami.quietscipy
#import scipy.ndimage wjr
from pyami import imagefun, arraystats  #wjr
import leginon.gui.wx.IcethicknessEF  #wjr
#from pyami import fftfun
from leginon import presets # wjr
import leginon.gui.wx.Presets #wjr`
from math import log # natural log
import copy
from leginon import instrument
import time
from leginon import appclient
from leginon import bestice


class IcethicknessEF(imagewatcher.ImageWatcher):
	eventinputs = imagewatcher.ImageWatcher.eventinputs + [event.AcquisitionImagePublishEvent]
	eventoutputs = imagewatcher.ImageWatcher.eventoutputs 

	panelclass = leginon.gui.wx.IcethicknessEF.Panel   #wjr
	settingsclass = leginondata.ZeroLossIceThicknessSettingsData   #wjr
	defaultsettings = {
		'process': False,
		'exposure time': 500.0, #ms
		'slit width': 15.0,  #eV
		'mean free path': 395.0,   #nm
		'decimate': 4,  #take measurement every N images
		'process_obj_thickness': False,
		'obj mean free path': 300.0, #nm
		'vacuum intensity': -1.0, #counts 
		'binning': 1,  # binning for image, will throw uncorrected warning if not match exposure binning, but can significantly speed up with no effect on result
		'use_best_quart_stats': False,
		'cfeg': False,  # is instrument a Cold FEG
		'cfeg_slope':  -0.04657619048,  # intensity drop of CFEG, per second
		'cfeg_intercept':  0,  # intercept of linear fit of cfeg drop
	}
	def __init__(self, id, session, managerlocation, **kwargs):
		imagewatcher.ImageWatcher.__init__(self, id, session, managerlocation, **kwargs)

		self.instrument = instrument.Proxy(self.objectservice,
																				self.session,
																				self.panel)
		self.calclient = calibrationclient.CalibrationClient(self)
		self.postprocess = threading.Event()
		self.presetsclient = presets.PresetsClient(self)
		self.zlpcounter = 0 #keep count of how many times it has been called in order to di it every N images
		self.start()

	def queryConditioningDone(self, crequest):
		'''
		Get the most recent conditioning request that fixing was completed, i.e., not bypassed.
		'''
		cdonequery = leginondata.ConditioningDoneData(session=self.session, request=crequest)
		done_conditions = cdonequery.query(results=1)
		if done_conditions:
			return done_conditions[0]
		else:
			return None

	def processImageData(self, imagedata, ):  #wjr
		'''
		collect two images: one with slit in, one without, and compare intensitites to get thickness
		'''
		self.zlpcounter += 1

		if (self.settings['decimate'] <1):
			self.settings['decimate'] =1
		modulus = self.zlpcounter % self.settings['decimate']
		if (modulus >0) :
			self.logger.info('skipping zlp measurement for this image; count = %i' %(self.zlpcounter))
		if self.settings['process'] and not modulus:
			exp_preset = imagedata['preset']
			acquirestr = 'Itot'
			noslitimagedata=  self._acquireSpecialImage(exp_preset, acquirestr, self.settings['exposure time'], False, self.settings['slit width'], self.settings['binning'])
			acquirestr = 'Izlp'
			zlpimagedata =  self._acquireSpecialImage(exp_preset, acquirestr, self.settings['exposure time'], True, self.settings['slit width'], self.settings['binning'])

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
			
			self.logger.info('no slit mean: %f counts' % (zlossth['no slit mean'],))
			self.logger.info('slit mean: %f counts' % (zlossth['slit mean'],))
			self.logger.info('calculated thickness: %f nm' % (zlossth['thickness'],))
			self.logger.info('Number of function calls: %i' %(self.zlpcounter))
			zlossth.insert()

		if self.settings['process_obj_thickness'] and self.settings['vacuum intensity'] >0 :
			
			objth = leginondata.ObjIceThicknessData()
			objth['vacuum intensity'] = self.settings['vacuum intensity']
			if self.settings['cfeg']:
			# adjust vacuum intensty for expected drop since last flash
				ctype = 'cfeg'
				#ctype = 'autofiller'
				#ctype = 'buffer_cycle'
				#Save timestamped conditioning request to database
				crequestdata = leginondata.ConditioningRequestData(session=self.session, type=ctype)
				crequestdata.insert()
				conditiondone = self.queryConditioningDone(crequestdata)
				if conditiondone is not None:
					donetime = conditiondone.timestamp
					diff = donetime.now() - donetime
					self.logger.info('since last  %s check, it has been %d seconds ' % (ctype,diff.seconds))
					#objth['vacuum intensity'] += objth['vacuum intensity'] * self.settings['cfeg_slope'] * diff.seconds  + self.settings['cfeg_intercept'] 	
					objth['vacuum intensity'] =  self.settings['cfeg_slope'] * diff.seconds  + self.settings['cfeg_intercept'] 	
					self.logger.info('Using adjusted vacuum intensity %f' %(objth['vacuum intensity']))
			objth['mfp'] = self.settings['obj mean free path']
			if self.settings['use_best_quart_stats'] :
				objth['intensity'] = bestice.getBestHoleMeanIntensity(imagedata['image'])
			else:
				objth['intensity'] = arraystats.mean(imagedata['image'])
			try:
				objth['thickness'] = objth['mfp'] * log (objth['vacuum intensity'] / objth['intensity']) 
			except: 
				self.logger.error('Math error! Negative or zero value for intensity?')
				objth['thickness'] = 0
			objth['image'] = imagedata;
#			self.logger.info('mean counts of current image: %f' %(objth['intensity']))
			self.logger.info('objective scattering thickness: %f nm' %(objth['thickness']))
			if objth['thickness'] < -10:
				objth['thickness'] = -10
				self.logger.info('objective scattering thickness truncated to -10 nm')
			if objth['thickness'] > 500:
				objth['thickness'] = 500
				self.logger.info('objective scattering thickness truncated to 500 nm')
			
			objth.insert()

	def _acquireSpecialImage(self, preset, acquirestr, exp_time, filtered, slit_width, binning):
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
		was_slit_offset = float(camdata0['energy filter offset']) 
		was_filtered = bool(camdata0['energy filter']) 
		was_time = float(camdata0['exposure time'])
		was_binning = camdata0['binning']
#		print(was_binning)
		## deactivate frame saving and align frame flags
		camdata0['save frames'] = False
		camdata0['align frames'] = False

		camdata1 = copy.copy(camdata0) #not a deep copy
		#set correct energy filter params
		camdata1['energy filter'] = filtered
		camdata1['energy filter width'] = slit_width
		camdata1['energy filter offset'] = 0
		camdata1['exposure time'] = exp_time
		for key in camdata1['binning']:
			camdata1['binning'][key] = int(binning)
#		print(camdata1['binning'])

		try:
			self.instrument.setCCDCamera(camdata1['ccdcamera']['name'])  #select the right camera!!!!
			has_filter = self.instrument.ccdcamera.getEnergyFiltered()
			if not has_filter:   # if camera does not have an EF, raise an error
				self.logger.error(errstr % 'Energy filter not present')
				return
			#self.instrument.ccdcamera.setEnergyFilter(filtered)
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
			camdata0['energy filter'] = was_filtered
			camdata0['energy filter width'] = was_slit_width
			camdata0['energy filter offset'] = was_slit_offset
			camdata0['exposure time'] = was_time
			camdata0['binning'] = was_binning
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

	def handleApplicationEvent(self,evt):
		'''
		Find the Acquisition class or its subclass instance bound
		to this node upon application loading.
		'''
		app = evt['application']
		self.last_acq_node = appclient.getLastNodeThruBinding(app,self.name,'AcquisitionImagePublishEvent','Acquisition')


	def checkSettings(self,settings):
		'''
		Check that exposure will wait for this node to finish
		'''
		if type(self.last_acq_node) == type({}) and self.last_acq_node['is_direct_bound'] == True:
			settingsclassname = self.last_acq_node['node']['class string']+'SettingsData'
			results= self.researchDBSettings(getattr(leginondata,settingsclassname),self.last_acq_node['node']['alias'])
			if not results:
				# default acquisition settings waiting is False. However, admin default
				# should be o.k.
				return []
			else:
				last_acq_wait = results[0]['wait for process']
			if settings['process'] and not last_acq_wait:
				return [('error','"%s" node "wait for process" setting must be True when EF ice thickness measurements are taken' % (self.last_acq_node['node']['alias'],))]
			if not (settings['process'] or settings['process_obj_thickness'])  and last_acq_wait:
				return [('error','"%s" node "wait for process" setting must be False when ice thickness measurements are not taken' % (self.last_acq_node['node']['alias'],))]
		return []

