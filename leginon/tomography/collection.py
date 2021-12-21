import math
import time
import numpy

import leginon.leginondata
import leginon.calibrationclient
import tiltcorrelator
import tiltseries
import traceback
import pyscope.simccdcamera2 #.SimCCDCamera as simcam


class Abort(Exception):
	pass

class Fail(Exception):
	pass

class Collection(object):
	def __init__(self):
		self.tilt_series = None
		# Use two correlators to track positive and negative tilts independently
		self.correlator = {}
		self.correlator[0] = None
		self.correlator[1] = None
		self.instrument_state = None
		self.theta = 0.0
		self.reset_tilt = 0.0

	def saveInstrumentState(self):
		self.instrument_state = self.instrument.getData(leginon.leginondata.ScopeEMData)
		a_state = self.instrument_state['stage position']['a']
		if abs(a_state - self.reset_tilt) > math.radians(1):
			self.logger.error('instrument state saved to %.1f degrees, not %.1f. The last tilt did not return properly.' % (math.degrees(a_state), math.degrees(self.reset_tilt)))

	def restoreInstrumentState(self):
		keys = ['stage position', 'defocus', 'image shift', 'magnification']
		if self.instrument_state is None:
			return
		instrument_state = leginon.leginondata.ScopeEMData()
		for key in keys:
			instrument_state[key] = self.instrument_state[key]
		self.logger.info('stage alpha reset to %.1f' % (instrument_state['stage position']['a']*180.0/3.14159,))
		self.instrument.setData(instrument_state)

	def start(self):

		result = self.initialize()
		if not result:
			self.finalize()
			return

		self.checkAbort()

		self.collect()

		self.finalize()

	def runBufferCycle(self):
		try:
			self.logger.info('Running buffer cycle...')
			self.instrument.tem.runBufferCycle()
		except AttributeError:
			self.logger.warning('No buffer cycle for this instrument')
		except Exception, e:
			self.logger.error('Run buffer cycle failed: %s' % e)

	def calcBinning(self, origsize, min_newsize, max_newsize):
		## new size can be bigger than origsize, no binning needed
		if max_newsize >= origsize:
			return 1
		## try to find binning that will make new image size <= newsize
		bin = origsize / max_newsize
		remain = origsize % max_newsize
		while remain:
			bin += 1
			remain = origsize % bin
			newsize = float(origsize) / bin
			if newsize < min_newsize:
				return None
		return bin

	def initialize(self):
		self.logger.info('Initializing...')

		self.logger.info('Calibrations loaded.')

		self.saveInstrumentState()
		self.logger.info('Instrument state saved.')

		self.prediction.fitdata = self.settings['fit data points'], self.settings['fit data points2']
		self.tilt_series = leginon.tomography.tiltseries.TiltSeries(self.node, self.settings,
												 self.session, self.preset,
												 self.target, self.emtarget)
		self.tilt_series.save()

		if self.settings['use lpf']:
			lpf = 1.5
		else:
			lpf = None
		# bin down images for correlation
		imageshape = self.preset['dimension']
		# use minsize since tiltcorrelator needs it square, will crop the image in there.
		minsize = min((imageshape['x'],imageshape['y']))
		if minsize > 512:
			correlation_bin = self.calcBinning(minsize, 256, 512)
		else:
			correlation_bin = 1
		if correlation_bin is None:
			# use a non-dividable number and crop in the correlator
			correlation_bin = int(math.ceil(minsize / 512.0))
		self.correlator[0] = leginon.tomography.tiltcorrelator.Correlator(self.node, self.theta, correlation_bin, lpf)
		self.correlator[1] = leginon.tomography.tiltcorrelator.Correlator(self.node, self.theta, correlation_bin, lpf)

		if self.settings['run buffer cycle']:
			self.runBufferCycle()

		return True

	def collect(self):
		n = len(self.tilts)
		self.node.logger.info('collect %d tilt groups' % n)

		# TODO: move to tomography
		if n != len(self.exposures):
			raise RuntimeError('tilt angles and exposure times do not match')

		for i in range(n):
			if len(self.tilts[i]) != len(self.exposures[i]):
				s = 'tilt angle group #%d and exposure time group do not match'
				s %= i + 1
				raise RuntimeError(s)

		# initialize prediction
		self.prediction.newTiltSeries()
		for g in range(n):
			self.prediction.newTiltGroup()

		# Collect according to tilt_index_sequence.
		if self.tilt_order == 'sequential' and len(self.tilts) == 2:
			self.sequentialLoop()
		else:			
			self.loop(self.tilts, self.exposures, self.tilt_index_sequence)

	def sequentialLoop(self):
		# The group in the first loop is already determined for self.tilt_index_sequence
		# we just get it from it.
		first_group = self.tilt_index_sequence[0][0]
		break1 = len(self.tilts[first_group])
		self.loop(self.tilts, self.exposures, self.tilt_index_sequence[:break1])
		if break1 < len(self.tilt_index_sequence):
			self.initLoop2()
			self.loop(self.tilts, self.exposures, self.tilt_index_sequence[break1:])
		self.finalize()

	def finalize(self):
		self.tilt_series = None

		self.correlator[0].reset()
		self.correlator[1].reset()

		self.restoreInstrumentState()
		self.instrument_state = None

		self.logger.info('Data collection ended.')
		self.setStatus('idle')

		self.viewer.clearImages()

	def initLoop2(self):
		self.restoreInstrumentState()
		self.correlator[1].reset()
		if True:
			self.logger.info('Adjust target for the second tilt group...')
			try:
				self.emtarget, status = self.node.adjusttarget(self.preset['name'], self.target, self.emtarget)
			except Exception, e:
				self.logger.error('Aborting because of target adjusting exception: %s.' % e)
				self.finalize()
				raise
			if status == 'error':
				raise RuntimeError('Target adjustment status is error. Aborting....')
				self.finalize()
		return

	def loop(self, tilts, exposures, sequence):
		self.logger.info('Starting tilt collection (%d angles)...' % len(sequence))
		try:
			self.node.removeStageAlphaBacklash(tilts, sequence, self.preset['name'], self.target, self.emtarget)
		except Exception, e:
			self.logger.error('Failed to remove backlash: %s.' % e)
			self.finalize()
			raise

		self.checkAbort()

		self._loop(tilts, exposures, sequence)
		
		self.logger.info('Collection loop completed.')

	def _loop(self, tilts, exposures, sequence):
		'''
		Loop through sequence
		'''
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

		if self.tilt_order in ('alternate','swing') and len(tilts) > 1:
			# duplicate the first tilt to the other tilt group
			other_group = int(not seq0[0])
			self.prediction.setCurrentTiltGroup(other_group)
			self.prediction.addPosition(tilt0, position0)
		
		self.prediction.setCurrentTiltGroup(seq0[0])
		self.prediction.addPosition(tilt0, position0)
		
		position = dict(position0)
		defocus = defocus0
		tem = self.instrument.getTEMData()

		abort_loop = False
		for seq_index in range(len(sequence)):
			self.checkAbort()
			seq = sequence[seq_index]
			tilt = tilts[seq[0]][seq[1]]

			self.logger.info('Current tilt angle: %g degrees.' % math.degrees(tilt))
			try:
				self.prediction.setCurrentTiltGroup(seq[0])
				predicted_position = self.prediction.predict(tilt)
			except:
				raise
			self.checkAbort()

			predicted_shift = {}
			predicted_shift['x'] = predicted_position['x'] - position['x']
			predicted_shift['y'] = predicted_position['y'] - position['y']

			# undo defocus from last tilt
			predicted_shift['z'] = -defocus

			#Use calibrated defocus delta
			cal_delta = self.prediction.getCalibratedDefocusDelta(tilt)
			self.logger.info('calibrated tilt defocus shift: %.2f um' % (cal_delta*1e6))
			defocus =  defocus0 + cal_delta
			z_prediction = defocus0 + predicted_position['z']*image_pixel_size
			self.logger.info('defocus0: %g meters,sintilt: %g' % (defocus0,math.sin(tilt)))
			self.logger.info('prediction defocus %.2f um' % (defocus*1e6))
			# record z prediction
			predicted_shift['z'] += z_prediction

			try:
				self.node.setPosition('image shift', predicted_position)
			except Exception, e:
				self.logger.error('Calibration error: %s' % e) 
				self.finalize()
				raise Fail

			m = 'Predicted position: %g, %g pixels, %g, %g meters.'
			self.logger.info(m % (predicted_position['x'],
								  predicted_position['y'],
								  predicted_position['x']*image_pixel_size,
								  predicted_position['y']*image_pixel_size))
			self.logger.info('Predicted defocus: %g meters.' % defocus)
			# set defocus based on the calibration
			self.node.setDefocus(defocus)

			if self.settings['measure defocus']:
				defocus_measurement = self.node.measureDefocus()
				measured_defocus = defocus0 - (defocus + defocus_measurement[0])
				measured_fit = defocus_measurement[1]
				self.logger.info('Measured defocus: %g meters.' % measured_defocus)
				self.logger.info('Predicted defocus: %g meters.' % defocus)
			else:
				measured_defocus = None
				measured_fit = None

			self.checkAbort()

			exposure = exposures[seq[0]][seq[1]]
			m = 'Acquiring image (%g second exposure)...' % exposure
			self.logger.info(m)
			self.instrument.ccdcamera.ExposureTime = int(exposure*1000)

			self.checkAbort()

			self.logger.info('Pausing for %.1f seconds before starting acquiring' % self.settings['tilt pause time']) 
			time.sleep(self.settings['tilt pause time'])

			# TODO: error checking
			channel = self.correlator[seq[0]].getChannel()
			image_data = self.node.acquireCorrectedCameraImageData(channel)
			if image_data is None:
				self.finalize()
				raise Fail
			self.logger.info('Image acquired.')

			image_mean = image_data['image'].mean()
			if self.settings['integer']:
				intscale = self.settings['intscale']
				image_data['image'] = numpy.around(image_data['image']*intscale).astype(numpy.int16)
				image_mean *= intscale

			image = image_data['image']

			if image_mean < self.settings['mean threshold']:
				if seq[1] < (self.settings['collection threshold']/100.0)*len(tilts):
					self.logger.error('Image counts below threshold (mean of %.1f, threshold %.1f), aborting series...' % (image_mean, self.settings['mean threshold']))
					self.finalize()
					raise Abort
				else:
					self.logger.warning('Image counts below threshold, aborting loop...')
					self.restoreInstrumentState()
					break

			self.logger.info('Saving image...')
			# notify manager on every image.
			self.node.notifyNodeBusy()
			while True:
				try:
					tilt_series_image_data = self.tilt_series.saveImage(image_data)
					break
				except Exception, e:
					self.logger.warning('Retrying save image: %s.' % (e,))
					raise
				for tick in range(60):
					self.checkAbort()
					time.sleep(1.0)
			filename = tilt_series_image_data['filename']
			self.logger.info('Image saved (filename: \'%s\').' % filename)

			self.checkAbort()

			self.viewer.addImage(image)

			self.checkAbort()

			# Move to next tilt while correlating to allow stage to settle
			try:
				next_tilt = tilts[sequence[seq_index+1][0]][sequence[seq_index+1][1]]
				s = 'Tilting stage to next angle (%g degrees)...' % math.degrees(next_tilt)
				self.logger.info(s)
				stage_position = {'a': next_tilt}
				self.instrument.tem.StagePosition = stage_position
			except IndexError:
				pass

			self.checkAbort()
			
			self.logger.info('Correlating image with previous tilt...')
			# TODO: This got uncommented out in 87f3dd8b. an index is added to fix
			# attribute error. However, tiltcorrelation is not doing anything really.
			self.correlator[seq[0]].setTiltAxis(predicted_position['phi'])
			while True:
				try:
					correlation_image = self.correlator[seq[0]].correlate(tilt_series_image_data, self.settings['use tilt'], channel=channel, wiener=False, taper=0)
					break
				except Exception, e:
					self.logger.warning('Retrying correlate image: %s.' % (e,))
				for tick in range(15):
					self.checkAbort()
					time.sleep(1.0)

			if seq_index == 0: 
				if self.tilt_order in ('alternate','swing'):
					other_group = int(not seq[0])
					fake_corr_image = self.correlator[other_group].correlate(tilt_series_image_data, self.settings['use tilt'], channel=channel, wiener=False, taper=0)
		
			phi, optical_axis, z0 = self.prediction.getCurrentParameters()
			phi,offset = self.prediction.convertparams(phi,optical_axis)
			correlation = self.correlator[seq[0]].getShift(False)

			if self.settings['use tilt']:
				correlation = self.correlator[seq[0]].tiltShift(tilt,correlation,phi)

			position = {
				'x': predicted_position['x'] - correlation['x'],
				'y': predicted_position['y'] - correlation['y'],
			}

			self.prediction.addPosition(tilt, position)

			m = 'Correlated shift from feature: %g, %g pixels, %g, %g meters.'
			self.logger.info(m % (correlation['x'],
								  correlation['y'],
								  correlation['x']*image_pixel_size,
								  correlation['y']*image_pixel_size))

			m = 'Feature position: %g, %g pixels, %g, %g meters.'
			self.logger.info(m % (position['x'],
								  position['y'],
								  position['x']*image_pixel_size,
								  position['y']*image_pixel_size))
			raw_correlation = self.correlator[seq[0]].getShift(True)
			s = (raw_correlation['x'], raw_correlation['y'])
			self.viewer.setXC(correlation_image, s)
			if self.settings['use tilt']:
				raw_correlation = self.correlator[seq[0]].tiltShift(tilt,raw_correlation,phi)

			self.checkAbort()

			time.sleep(3.0)

			self.checkAbort()

			args = (
				predicted_position,
				predicted_shift,
				position,
				correlation,
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

	def savePredictionInfo(self, predicted_position, predicted_shift, position, correlation, raw_correlation, image_pixel_size, image, prediction_tilt_group, measured_defocus=None, measured_fit=None):
		initializer = {
			'session': self.node.session,
			'predicted position': predicted_position,
			'predicted shift': predicted_shift,
			'position': position,
			'correlation': correlation,
			'raw correlation': raw_correlation,
			'pixel size': image_pixel_size,
			'image': image,
			'measured defocus': measured_defocus,
			'measured fit': measured_fit,
			'tilt group': prediction_tilt_group,
		}
		tomo_prediction_data = leginon.leginondata.TomographyPredictionData(initializer=initializer)
					
		self.node.publish(tomo_prediction_data, database=True, dbforce=True)

	def checkAbort(self):
		if self.player.state() == 'pause':
			self.setStatus('user input')
		state = self.player.wait()
		if state in ('stop', 'stopqueue', 'stoptarget'):
			self.finalize()
			raise Abort

	
