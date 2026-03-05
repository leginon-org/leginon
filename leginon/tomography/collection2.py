import math
import time
import numpy

import leginon.leginondata
import leginon.calibrationclient
from . import tiltcorrelator
from . import tiltseries
import traceback
import pyscope.simccdcamera2 #.SimCCDCamera as simcam
from leginon.tomography.collection import Collection

class Abort(Exception):
	pass

class AbortLoop(Exception):
	pass

class Fail(Exception):
	pass

class TrackingError(Exception):
	pass

class TrackingImgError(Exception):
	pass

from leginon.tomography.prediction import PredictionError

class Collection2(Collection):
	
	def __init__(self):
		super(Collection2,self).__init__()
		self.initTracking()

	def initTracking(self):
		self.doPredict = None
		self.trackingImg = None
		self.correlator[2] = None								# tracking correlator used in Collection2 in positive tilt
		self.correlator[3] = None								# negative tilt

		self.pix_shifts = {0:{'x':[],'y':[]},1:{'x':[],'y':[]}} 		# a list of pixel shift at tomo relative to a fake image at preset value.
		self.ntrack = {0:0,1:0}									# number of iterations last tracking image was taken
		self.ntrackmax = 4										# maximum number of iterations before we have to take another tracking image
		self.offset = None
		self.trackpreset = None
		self.fulltrack = False
		self.save_track_images = False
		self.correlation_bin = []	# 4 total, 2 for tomo 2 for track
		
	def initialize(self):
		self.logger.info('Initializing...')
		self.logger.info('Calibrations loaded.')
		self.saveInstrumentState()
		self.logger.info('Instrument state saved.')

		self.prediction.fitdata = self.settings['fit data points'], self.settings['fit data points2']
		self.tilt_series = leginon.tomography.tiltseries.TiltSeries(self.node, self.settings,
									self.session, self.preset, self.target,
									self.emtarget, self.save_track_images)
		self.tilt_series.save()

		if self.settings['use lpf']:
			lpf = 1.5
		else:
			lpf = None
		# Set up 4 correlators with 0,1 for tomo preset, 2,3 for track preset
		for i,p in enumerate((self.preset,self.trackpreset)):
			for j in range(2):
				k = i*2+j
				corr_bin = self.calcCorrelatorBinning(p)
				self.correlation_bin.append(corr_bin)
				self.correlator[k] = leginon.tomography.tiltcorrelator.Correlator(self.node, self.theta, corr_bin, lpf)
		self.trackoffset = None
		if self.settings['run buffer cycle']:
			self.runBufferCycle()
		return True

	def calcCorrelatorBinning(self, preset):
		# bin down images for correlation
		imageshape = preset['dimension']
		# use minsize since tiltcorrelator needs it square, will crop the image in there.
		minsize = min((imageshape['x'],imageshape['y']))
		if minsize > 512*2:
			correlation_bin = self.calcBinning(minsize, 256*2, 512*2)
		else:
			correlation_bin = 1
		if correlation_bin is None:
			# use a non-dividable number and crop in the correlator
			correlation_bin = int(math.ceil(minsize / (512.0*2)))
		return correlation_bin

	def get_pix_shifts(self,seq):
		self.logger.debug('all pix_shifts of group %d %s' % (seq[0], self.pix_shifts[seq[0]]))
		self.logger.debug('sum pix_shifts of group (x,y)= %.3f, %.3f' % (sum(self.pix_shifts[seq[0]]['x']), sum(self.pix_shifts[seq[0]]['y'])))
		return self.pix_shifts[seq[0]]
	
	def update_pix_shifts(self,seq,shift,append=True):
		if append:
			self.pix_shifts[seq[0]]['x'].append(shift['x'])
			self.pix_shifts[seq[0]]['y'].append(shift['y'])
		else:
			# so far this is not used.
			self.pix_shifts[seq[0]]['x'][-1] += shift['x']
			self.pix_shifts[seq[0]]['y'][-1] += shift['y']
		
	def reset_pix_shifts(self,seq):
		self.pix_shifts[seq[0]]['x'] = []
		self.pix_shifts[seq[0]]['y'] = []
		self.reset_ntrack(seq)
	
	def reset_ntrack(self,seq):
		self.ntrack[seq[0]] = 0
	
	def increment_ntrack(self,seq):
		self.ntrack[seq[0]] += 1
	
	def dotrackimg(self,seq):
		if self.ntrack[seq[0]] < self.ntrackmax:
			return False
		else:
			return True
	
	def finalize(self):
		self.tilt_series = None

		self.correlator[0].reset()
		self.correlator[1].reset()
		self.correlator[2].reset()
		self.correlator[3].reset()
		self.reset_pix_shifts((0,))
		self.reset_pix_shifts((1,))
		
		self.restoreInstrumentState()
		self.instrument_state = None

		self.logger.info('Data collection ended.')
		self.setStatus('idle')

		self.viewer.clearImages()
		self.viewer.clearTrackImages()

	def adjust4Swing(self):
		self.restoreInstrumentState()
		if True:
			self.logger.info('Adjust target for the other tilt group...')
			try:
				self.emtarget, status = self.node.adjusttarget(self.preset['name'], self.target, self.emtarget)
			except Exception as e:
				self.logger.error('Failed to adjust target: %s.' % e)
				self.finalize()
				raise
			if status == 'error':
				raise RuntimeError('Target adjustment status is error. Aborting....')
				self.finalize()

		status = self.node.moveAndPreset(self.preset, self.emtarget)
		
		if status == 'error':
			self.logger.warning('Move failed.')
			
		return
	
	def loop(self, tilts, exposures, sequence):
		self.logger.info('Starting tilt collection (%d angles)...' % len(sequence))
		self.logger.info('Removing tilt backlash...')
		try:
			self.node.removeStageAlphaBacklash(tilts, sequence, self.preset['name'], self.target, self.emtarget)
		except Exception as e:
			self.logger.error('Failed to remove backlash: %s.' % e)
			self.finalize()
			raise

		# setup predictor and limits
		dim = min(self.preset['dimension'].values())		# get dimension of image at exposure preset. 
		tolerance = min(self.settings['tolerance'],0.2)		
		self.prediction.setcutoff(dim*tolerance)			# set prediction threshold at % of image size
		self.prediction.set_maxfitpoints(self.settings['maxfitpoints'] )
		self.checkAbort()

		self._loop(tilts, exposures, sequence)
		self.logger.info('Collection loop completed.')

		
	def _loop(self, tilts, exposures, sequence):
		'''
		Loop through sequence
		'''		
		img0 = None
		# tilts and exposures are grouped
		# sequence is the 2 element tuple used to choose the tilt and the exposure
		image_pixel_size = self.pixel_size*self.preset['binning']['x']

		seq0 = sequence[0]
		tilt0 = tilts[seq0[0]][seq0[1]]
		position0 = self.node.getPixelPosition('image shift')
		defocus0 = self.node.getDefocus()

		m = 'Initial feature position: %g, %g pixels.'
		self.logger.info(m % (position0['x'], position0['y']))
		m = 'Initial defocus: %g meters.'
		self.logger.info(m % defocus0)

		# TODO: figure out the next block of code. 
		#if self.tilt_order in ('alternate','swing') and len(tilts) > 1:		
			# duplicate the first tilt to the other tilt group
		#	other_group = int(not seq0[0])
		#	self.prediction.setCurrentTiltGroup(other_group)
		#	self.prediction.addPosition(tilt0, position0)
		
		self.prediction.setCurrentTiltGroup(seq0[0])		
		position = dict(position0)
		position0 = dict(position0)
		defocus = defocus0
		
		abort_loop = False
		m = 'sequence------- %s' % sequence
		self.logger.debug(m)
		for seq_index in range(len(sequence)):
			self.checkAbort()
			seq = sequence[seq_index]
			tilt = tilts[seq[0]][seq[1]]
			#import rpdb2; rpdb2.start_embedded_debugger("asdf")

			try:
				channel = self.correlator[seq[0]].getChannel()
				self.prediction.setCurrentTiltGroup(seq[0])
				ispredict = self.prediction.ispredict()							# can we rely on prediction? 

				has_new_trackingImg = False
				if seq_index == 0:	
					m = 'Starting tilt angle: %g degrees.' % math.degrees(tilt)
					self.logger.info(m)
					predicted_position = position0								# first position
					predicted_position['z'] = self.preset['defocus']/image_pixel_size # assumes that eucentric error z0 is 0.  
					self.update_pix_shifts(seq0,position0)
					self.trackingImg = self.getTrackingImg(seq0)			# get first tracking image
					has_new_trackingImg = True
					self.reset_ntrack(seq)			
					self.correlator[seq[0]+2].reset()							# clear buffer
					# The next line adds the first tracking image to the correlator and returns None. 
					firstcorrelation_image = self.correlator[seq[0]+2].correlate(self.trackingImg,\
								self.settings['use tilt'], channel=channel, wiener=False, taper=0,corrtype='phase')	

					if self.tilt_order in ('alternate','swing'):
						other_group = int(not seq[0])
						fake_corr_image = self.correlator[other_group+2].correlate(self.trackingImg,\
							self.settings['use tilt'], channel=channel, wiener=False, taper=0,corrtype='phase')	
						self.reset_ntrack((other_group,0))
						
				elif self.fulltrack or not ispredict:	
						
					self.logger.debug("****TRACKING****")
					pix_shifts = self.get_pix_shifts(seq)		# history of previous shifts
															 
					# tilt to current tilt angle. 
					self.tilt(tilt)
					self.logger.debug('tilted to %.2f degrees' % math.degrees(tilt))
					# acquire tracking image, correlate with previous tracking image.
					# IMPORTANT DRAWBACK: measured position in tomo is not taken into account
					tracked_shift = self.track(tilt,seq)						# this is in binned pixels for exposure mag.
					has_new_trackingImg = True
					#position = {'x':sum(pix_shifts['x']),'y':sum(pix_shifts['x'])}

					predicted_position = {}
					# tracked_shift has to be corrected by total pixel shifts applied up to now
					predicted_position['x'] = tracked_shift['x'] + sum(pix_shifts['x'])
					predicted_position['y'] = tracked_shift['y'] + sum(pix_shifts['y'])
					# TODO: actually implement something for z heights in unit of image pixel
					defocus, predicted_z = self.predictDefocusZByCalibration(defocus0, tilt)
					predicted_position['z'] = predicted_z
					self.logger.debug('previous x: %.3f, y: %.3f' %(position['x'],position['y']))
					self.logger.debug('tracked shift x: %.3f, y: %.3f' %(tracked_shift['x'],tracked_shift['y']))
					self.logger.debug('set to binned pixel from track x: %.3f, y: %.3f' %(predicted_position['x'],predicted_position['y']))
					self.logger.debug('')
				else:
					# tilt to current tilt angle. 
					self.logger.debug("****PREDICTING****")
					pix_shifts = self.get_pix_shifts(seq)									# history of previous shifts
					
					self.tilt(tilt)
					predicted_shift = self.prediction.predict(tilt,seq)
					
					predicted_position = {}
					# tracked_shift has to be corrected by total image shifts applied up to now
					predicted_position['x'] = predicted_shift['x'] + sum(pix_shifts['x'])
					predicted_position['y'] = predicted_shift['y'] + sum(pix_shifts['y'])
					# use calibrated defocus change  for z heights
					predicted_position['z'] = predicted_shift['z'] + self.preset['defocus']/image_pixel_size

					# determine if we need to take a tracking image
					if self.dotrackimg(seq):
						self.trackingImg = self.getTrackingImg(seq)
						has_new_trackingImg = True
						trackingcorrelation_image = self.correlator[seq[0]+2].correlate(self.trackingImg,\
							self.settings['use tilt'], channel=channel, wiener=False, taper=0)	
						self.reset_ntrack(seq)
						
					#self.logger.debug('previous x: %.3f, y: %.3f' %(position['x'],position['y']))
					#self.logger.debug('predicted x: %.3f, y: %.3f' %(predicted_position['x'],predicted_position['y']))
					#self.logger.debug('predicted shift x: %.3f, y: %.3f' %(predicted_shift['x'], predicted_shift['y']))
					#self.logger.debug()
					
			except TrackingError as e:
				traceback.print_exc()
				self.logger.error('Failed to track. Aborting tilt series: %s' % e)
				raise Abort
			except PredictionError as e:
				self.logger.error('Failed to predict. Aborting tilt series: %s' % e)
				raise Abort
			except Exception as e:
				traceback.print_exc()
				self.finalize()
				raise Abort

			self.checkAbort()
			# predicted_shift HERE for tracked case is just track_shift correlation
			predicted_shift = {}
			predicted_shift['x'] = predicted_position['x'] - position['x']
			predicted_shift['y'] = predicted_position['y'] - position['y']
			predicted_shift['z'] = predicted_position['z'] - self.preset['defocus']/image_pixel_size
			
			# append to shift list
			self.update_pix_shifts(seq,predicted_shift)
			
			"""
			# TODO: implement something below for z. 
			# undo defocus from last tilt
			predicted_shift['z'] = -defocus
			defocus = defocus0 + predicted_position['z']*image_pixel_size		# currently, predicted z is set to initial z0, which is assumed to be 0
			self.logger.info('defocus0: %g meters,sintilt: %g' % (defocus0,math.sin(tilt)))
			# apply new defocus
			predicted_shift['z'] += defocus
			"""
			try:
				self.node.setPosition('image shift', predicted_position)
				self.logger.debug('set Image shift in %s with pixel shift %.2f, %.2f' % (self.preset['name'],predicted_position['x'], predicted_position['y']))
			except Exception as e:
				self.logger.error('Calibration error: %s' % e) 
				self.finalize()
				raise Fail
			
			self.node.setDefocus(predicted_position['z']*image_pixel_size)
			
			"""
			#TODO: implement defocus measurement 
			if self.settings['measure defocus']:
				defocus_measurement = self.node.measureDefocus()
				measured_defocus = defocus0 - (defocus + defocus_measurement[0])
				measured_fit = defocus_measurement[1]
				self.logger.info('Measured defocus: %g meters.' % measured_defocus)
				self.logger.info('Predicted defocus: %g meters.' % defocus)
			else:
				measured_defocus = None
				measured_fit = None
			"""
			#TODO: implement something for this!!
			measured_defocus = None
			measured_fit = None
			self.checkAbort()
			
			exposure = exposures[seq[0]][seq[1]]

			is_early_tilts = seq[1] < (self.settings['collection threshold']/100.0)*len(tilts)
			try:
				image_data = self.getTomoImg(exposure, channel, is_early_tilts)
			except AbortLoop:
				break
			except Exception:
				raise

			self.logger.info('Saving image...')
			need_save_trackimg = self.save_track_images and has_new_trackingImg
			tilt_series_image_data, tilt_series_track_image_data = self.saveImages(image_data, need_save_trackimg)

			image = image_data['image']
			self.viewer.addImage(image)
			self.checkAbort()

			self.logger.info('Correlating image with previous tilt...')	
			self.logger.debug('****Correlating tomo image with previous tilt...')	
			while True:
				try:
					correlation_image = self.correlator[seq[0]].correlate(tilt_series_image_data, self.settings['use tilt'], channel=channel, wiener=False, taper=0)
					break
				except Exception as e:
					self.logger.warning('Retrying correlate image: %s.' % (e,))
				for tick in range(15):
					self.checkAbort()
					time.sleep(1.0)

			if seq_index == 0: 
				if self.tilt_order in ('alternate','swing'):
					other_group = int(not seq[0])
					fake_corr_image = self.correlator[other_group].correlate(tilt_series_image_data, self.settings['use tilt'], channel=channel, wiener=False, taper=0)

			#These are measured in tomo condition
			#raw_correlation is at the same scale as correlation_image
			#include correlation_binning
			raw_correlation = self.correlator[seq[0]].getShift(True)
			corr_bin = self.correlation_bin[seq[0]]
			shift_from_last = {'x':raw_correlation['x'] * corr_bin,'y':raw_correlation['y'] * corr_bin}
			pid_d_constant = 0.1
			pid_p_constant = 1
			#tomo_correlation is at the tomo image pixel scale and relative to the first image
			tomo_correlation = self.correlator[seq[0]].getShift(False)
			s = (raw_correlation['x'], raw_correlation['y'])
			self.viewer.setXC(correlation_image, s)
			
			# TODO: look into making the next 2 lines do something
			#if self.settings['use tilt']:
			#	correlation = self.correlator[seq[0]].tiltShift(tilt,correlation,phi)
			#

			# measured position is used in the next tilt where it runs update_pix_shift
			tomo_corr_bin = self.correlator[seq[0]].correlation_binning
			damping = 1
			feedback_correction = {
				'x': pid_p_constant * tomo_correlation['x'] - pid_d_constant * shift_from_last['x'],
				'y': pid_p_constant * tomo_correlation['y'] - pid_d_constant * shift_from_last['y']
			}
			position = {
				'x': predicted_position['x'] + feedback_correction['x'],
				'y': predicted_position['y'] + feedback_correction['y']
			}
			
			self.logger.debug("****AFTER IMAGE CORRELATION****")
			if ispredict:
				self.logger.debug('predicted x: %.3f, y: %.3f' %(predicted_position['x'],predicted_position['y']))
			else:
				self.logger.debug('tracked x: %.3f, y: %.3f' %(predicted_position['x'],predicted_position['y']))
			self.logger.debug('raw correlation x: %.3f, y: %.3f' %((raw_correlation['x']),(raw_correlation['y'])))
			self.logger.debug('correlation x: %.3f, y: %.3f' %((tomo_correlation['x']),(tomo_correlation['y'])))
			self.logger.debug('damping by %.3f with raw_correlation as feedback correction. Why needed ???' % damping)
			self.logger.debug('feedback correction x: %.3f y:%.3f' % (feedback_correction['x'], feedback_correction['y']))
			self.logger.debug('measured position including feedback x: %.3f, y: %.3f' %(position['x'],position['y']))
			self.logger.debug('')

			if not ispredict:
				predicted_shift = self.prediction.predict(tilt,seq)						# still predict position, just don't rely on it. 				
				self.prediction.addPosition(tilt, position, tomo_correlation) 		# Add measured and predicted position.
				# send image shift to position instead of predicted_position for next tilt
				#print('send measured position x: %f, y: %f' %(position['x'],position['y']))
				#self.sendImageShift(position)
			else:
				self.prediction.addPosition(tilt, position, tomo_correlation)
				# figure out if we need to take a tracking image before tilting
				ispredict = self.prediction.ispredict()								
				if not ispredict:
					self.trackingImg = self.getTrackingImg(seq)
					trackingcorrelation_image = self.correlator[seq[0]+2].correlate(self.trackingImg,\
						self.settings['use tilt'], channel=channel, wiener=False, taper=0)	
					self.reset_ntrack(seq)			

			m = 'Correlated shift from feature: %.3f, %.3f pixels, %.3f, %.3f um.'
			self.logger.info(m % (tomo_correlation['x'],
								  tomo_correlation['y'],
								  tomo_correlation['x']*image_pixel_size*1e6,
								  tomo_correlation['y']*image_pixel_size*1e6))
			m = 'Feature position: %.3f, %.3f pixels, %.3f, %.3f um.'
			self.logger.info(m % (position['x'],
								  position['y'],
								  position['x']*image_pixel_size*1e6,
								  position['y']*image_pixel_size*1e6))
			#if self.settings['use tilt']:
			#	raw_correlation = self.correlator[seq[0]].tiltShift(tilt,raw_correlation,phi)

			self.checkAbort()
			time.sleep(3.0)
			self.checkAbort()

			args = (
				predicted_position,
				predicted_shift,
				position,
				tomo_correlation,
				raw_correlation,
				image_pixel_size,
				tilt_series_image_data,
				seq[0],
				measured_defocus,
				measured_fit,
			)
			self.savePredictionInfo(*args)

			self.checkAbort()

			if abort_loop:
				self.restoreInstrumentState()
				break
		self.viewer.clearImages()
		self.viewer.clearTrackImages()
		self.reset_pix_shifts(seq)

	def saveImages(self, image_data, need_save_trackimg):
		"""
		Save tomo and optional track image with the tilt series.
		"""
		# notify manager on every image.
		self.node.notifyNodeBusy()
		tilt_series_track_image_data = None
		while True:
			try:
				tilt_series_image_data = self.tilt_series.saveImage(image_data)
				if need_save_trackimg:
					tilt_series_track_image_data = self.tilt_series.saveTrackingImage(self.trackingImg, self.trackpreset)
				break
			except Exception as e:
				self.logger.warning('Retrying save image: %s.' % (e,))
				raise
			for tick in range(60):
				self.checkAbort()
				time.sleep(1.0)
		filename = tilt_series_image_data['filename']
		self.logger.info('Image saved (filename: \'%s\').' % filename)
		self.checkAbort()
		return tilt_series_image_data, tilt_series_track_image_data

	def getTomoImg(self, exposure, channel, is_early_tilts):
		"""
		Return tomo image with current scope state.
		"""
		m = 'Acquiring image (%g second exposure)...' % exposure
		self.logger.info(m)
		self.instrument.ccdcamera.ExposureTime = int(exposure*1000)
		self.checkAbort()

		self.logger.info('Pausing for %.1f seconds before starting acquiring' % self.settings['tilt pause time'])
		time.sleep(self.settings['tilt pause time'])

		image_data = self.node.acquireCorrectedCameraImageData(channel)
		if image_data is None:
			self.logger.info('Image not acquired, aborting series...')
			self.finalize()
			raise RuntimeError('Failed to acquire image')
		else:
			self.logger.info('Image acquired.')

		image_mean = image_data['image'].mean()
		if self.settings['integer']:
			intscale = self.settings['intscale']
			image_data['image'] = numpy.around(image_data['image']*intscale).astype(numpy.int16)
			image_mean *= intscale

		if image_mean < self.settings['mean threshold']:
			if is_early_tilts:
				self.logger.error('Image counts below threshold (mean of %.1f, threshold %.1f), aborting series...' % (image_mean, self.settings['mean threshold']))
				self.finalize()
				raise Abort
			else:
				self.logger.warning('Image counts below threshold, aborting loop...')
				self.restoreInstrumentState()
				raise AbortLoop
		return image_data

	def getTrackingImg(self,seq,maxtries=5):
		# (1) Change to tracking preset, taking into acount current position and offset.
		# (2) Take an image.
		isoffset = self.node.getImageShiftOffset()
			
		try:
			self.logger.info('Acquiring tracking image.')
			self.change2Track()												# (1) 
			imagedata = self.node.acquireCorrectedCameraImageData(0)		# (2)
			myimage = self.node.instrument.tem.ImageShift
			self.logger.debug('image shift in track image (um): x: %8.2f y: %8.2f' % (myimage['x']*1e6, myimage['y']*1e6)) 	# (1)
			self.viewer.addTrackingImage(imagedata['image'])
			self.return2Tomo(isoffset)
		except:
			raise TrackingImgError
		return imagedata
	
	def change2Track(self):
		# This function follows the procedure in presets.PresetManager.targetToScope
		# (1) Get current image shift at tomo preset.
		# (2) Convert to track preset pixels.
		# (3) Convert track offset from parent preset .
		# (4) Combine both is.
		# (5) Send to scope. 
		
		mypreset = self.preset
		parentpreset = self.parentpreset
		trackpreset = self.trackpreset
		# myimage comes from tomo
		myimage = self.node.instrument.tem.ImageShift	# (1)
		self.logger.debug('current image shift in tomo (um): x: %8.2f y: %8.2f' % (myimage['x']*1e6, myimage['y']*1e6)) 	# (1)
		#myscope/mycam are from tomo preset
		myscope = leginon.leginondata.ScopeEMData()		
		myscope.friendly_update(mypreset)
		mycam = leginon.leginondata.CameraEMData()
		mycam.friendly_update(mypreset)
		trackscope = leginon.leginondata.ScopeEMData()
		trackscope.friendly_update(trackpreset)
		trackcam = leginon.leginondata.CameraEMData()
		trackcam.friendly_update(trackpreset)

		ht = self.node.instrument.tem.HighTension
		# x,y dict input of binned col, row, dict output, binned and include rotation and scale change
		p1_shift = self.node.calclients['image shift'].itransform(myimage, myscope, mycam)		# binned
		p2_shift = self.node.calclients['image shift'].presetImagePixelToPixel(ht, mypreset, trackpreset, p1_shift)
		# (3) track preset pixel shift from preset of its emtarget
		p3_shift = self.getTrackOffset()
		# offset in binned pixels to be applied once we change to track preset
		pixel_offset_shift = {'row':p2_shift['row'] - p3_shift['row'],
							'col':p2_shift['col'] - p3_shift['col']}				# (4)

		track_is = self.node.calclients['image shift'].transform(pixel_offset_shift, trackscope, trackcam)['image shift']

		self.node.presetsclient.toScope(self.trackpreset['name'])
		myimage = self.node.instrument.tem.ImageShift	# (1)
		#
		self.node.instrument.tem.setImageShift(track_is)							# (5)
		# For logging
		isoffset = {'x': track_is['x']-myimage['x'],'y':track_is['y']-myimage['y']}
		self.logger.debug('moved image shift by (um): x: %8.2f y: %8.2f' % (isoffset['x']*1e6, isoffset['y']*1e6))
	
	def getTrackOffset(self):
		# Get binned pixel offset dict of keys row, col to be applied once the scope has been sent to track preset.
		# This is in addition to is offset going from tomo to track. 

		if self.trackoffset:
			return self.trackoffset
		else:
			parentpreset = self.target['preset']
			trackpreset = self.trackpreset
			
			ht = self.node.instrument.tem.HighTension
			# (r,c) binned pixels relative to parent preset
			trackoffset = self.offset['trackoffset']
			# magnification and camera (if camera is different)
			# Transform trackoffset at parent preset to track in binned pixel
			p1_shift = {'row':trackoffset[0],'col':trackoffset[1]}
			p2_shift = self.node.calclients['image shift'].presetImagePixelToPixel(ht, parentpreset, trackpreset, p1_shift)
			# set self.trackoffset with this
			self.trackoffset = p2_shift
			return p2_shift

	def getTomoOffset(self, track_shift):
		# Get pixel shift be applied once the scope has been sent back to tomo preset
		# after tracking. 
		mypreset = self.preset
		trackpreset = self.trackpreset
		ht = self.node.instrument.tem.HighTension
		p2_shift = self.node.calclients['image shift'].presetImagePixelToPixel(ht, trackpreset, mypreset, p1_shift)
		return p2_shift
	
	def track(self,tilt,seq):
		try:
			channel = self.correlator[seq[0]].getChannel()
			# getTrackingImg and return to tomo preset at original image shift
			trackingImg = self.getTrackingImg(seq)
			# Cross correlate with previous tracking image. 
			self.logger.info('Correlating with previous tracking image in correlator %d' % (seq[0]+2))
			assert self.trackingImg is not None		# make sure we have a previous tracking image to compare to. 
			assert self.correlator[seq[0]+2].correlation.buffer[1]['image'] is not None
			
			correlation_image = self.correlator[seq[0]+2].correlate(trackingImg, \
								self.settings['use tilt'], channel=channel, wiener=False, taper=0,corrtype='phase')
			# get raw correlation, i.e. not accumulated
			raw_correlation = self.correlator[seq[0]+2].getShift(True)
			# get correlation shift sum, i.e, shift relative to the first track.
			correlation = self.correlator[seq[0]+2].getShift(False)
			self.logger.debug('track correlation pixel shift sum (x,y)= %.3f, %.3f' % (correlation['x'], correlation['y']))


			s = (raw_correlation['x'], raw_correlation['y'])
			self.viewer.setXC_track(correlation_image, s)
			
			# TODO: look into making the next 2 lines do something
			#if self.settings['use tilt']:													# This does not do anything. 
			#	correlation = self.correlator[seq[0]+2].tiltShift(tilt,correlation,phi)		# TODO: unstretch image. 
			self.trackingImg = trackingImg			
			
			# need to convert from tracking coordinates to exposure coordinates. 
			# This should be track to tomo pixelToPixel
			mypreset = self.preset
			trackpreset = self.trackpreset	
			ht = self.node.instrument.tem.HighTension
			
			# x,y dict input col, row, dict output, binned
			p1_row = correlation['y']
			p1_col = correlation['x']
			# row, col dictionary
			p1_shift = {'row':p1_row,'col':p1_col}
			p2_shift = self.node.calclients['image shift'].presetImagePixelToPixel(ht, trackpreset, mypreset, p1_shift)
			
			self.logger.debug("CORRELATION after pixelToPixel from track to tomo x: %.3f y: %.3f" %(p2_shift['col'], p2_shift['row']))
			
			result = {
				'x': -p2_shift['col'],			# This is in exposure pixels. 
				'y': -p2_shift['row'],
				'z': 0,		#TODO: need to predict z from eucentric error and optical axis offset and shift during tilt? 
			}
			self.reset_ntrack(seq)
		except Exception as e :
			if e.__class__.__name__ == 'TrackingImageError':
				raise TrackingImageError
			else:
				raise TrackingError
		return result		
	
	def tilt(self, ang):
		# Tilt to next angle
		try:
			s = 'Tilting stage to next angle (%g degrees)...' % math.degrees(ang)
			self.logger.info(s)
			stage_position = {'a': ang}
			self.instrument.tem.StagePosition = stage_position
		except IndexError:
			pass

		self.checkAbort()
					
	def return2Tomo(self,isoffset):
		# return to tomography preset
		self.node.presetsclient.toScope(self.preset['name'])
		self.node.setImageShiftOffset(isoffset)				# apply image shift to instrument. 
	
	def sendImageShift(self, position):
		try:
			self.node.setPosition('image shift', position)
		except Exception as e:
			self.logger.error('Calibration error: %s' % e) 
			self.finalize()
			raise Fail
	
	
	
	
