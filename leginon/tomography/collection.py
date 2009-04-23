import math
import time
import leginondata
import tiltcorrelator
import tiltseries
import numpy

class Abort(Exception):
	pass

class Fail(Exception):
	pass

class Collection(object):
	def __init__(self):
		self.tilt_series = None
		self.correlator = None
		self.instrument_state = None
		self.theta = 0.0

	def saveInstrumentState(self):
		self.instrument_state = self.instrument.getData(leginondata.ScopeEMData)

	def restoreInstrumentState(self):
		keys = ['stage position', 'defocus', 'image shift', 'magnification']
		if self.instrument_state is None:
			return
		instrument_state = leginondata.ScopeEMData()
		for key in keys:
			instrument_state[key] = self.instrument_state[key]
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

		self.prediction.fitdata = self.settings['fit data points']
		self.tilt_series = tiltseries.TiltSeries(self.node, self.settings,
												 self.session, self.preset,
												 self.target, self.emtarget)
		self.tilt_series.save()

		if self.settings['use lpf']:
			lpf = 1.5
		else:
			lpf = None
		# bin down images for correlation
		imageshape = self.preset['dimension']
		maxsize = max((imageshape['x'],imageshape['y']))
		if maxsize > 512:
			correlation_bin = self.calcBinning(maxsize, 256, 512)
		else:
			correlation_bin = 1
		self.correlator = tiltcorrelator.Correlator(self.node, self.theta, correlation_bin, lpf)
		if self.settings['run buffer cycle']:
			self.runBufferCycle()

		return True

	def collect(self):
		n = len(self.tilts)

		# TODO: move to tomography
		if n != len(self.exposures):
			raise RuntimeError('tilt angles and exposure times do not match')

		for i in range(n):
			if len(self.tilts[i]) != len(self.exposures[i]):
				s = 'tilt angle group #%d and exposure time group do not match'
				s %= i + 1
				raise RuntimeError(s)

		if n == 0:
			return
		elif n == 1:
			self.prediction.newTiltSeries()
			self.prediction.newTiltGroup()
			self.loop(self.tilts[0], self.exposures[0], False)
		elif n == 2:
			self.prediction.newTiltSeries()
			self.prediction.newTiltGroup()
			self.loop(self.tilts[0], self.exposures[0], False)
			self.checkAbort()
			self.node.initGoodPredictionInfo(tiltgroup=2)
			self.prediction.newTiltGroup()
			self.loop(self.tilts[1], self.exposures[1], True)
		else:
			raise RuntimeError('too many tilt angle groups')

	def finalize(self):
		self.tilt_series = None

		self.correlator.reset()

		self.restoreInstrumentState()
		self.instrument_state = None

		self.logger.info('Data collection ended.')

		self.viewer.clearImages()

	def loop(self, tilts, exposures, second_loop):
		self.logger.info('Starting tilt collection (%d angles)...' % len(tilts))

		if second_loop:
			self.restoreInstrumentState()
			if self.settings['adjust for transform'] != "no":
				self.logger.info('Adjust target for the second tilt group...')
				try:
					self.emtarget, status = self.node.adjusttarget(self.preset['name'], self.target, self.emtarget)
				except Exception, e:
					self.logger.error('Failed to adjust target: %s.' % e)
					raise
				if status == 'error':
					self.finalize()
					return
		self.logger.info('Removing tilt backlash...')
		try:
			self.node.removeStageAlphaBacklash(tilts, self.preset['name'], self.target, self.emtarget)
		except Exception, e:
			self.logger.error('Failed to remove backlash: %s.' % e)
			self.finalize()
			raise

		self.checkAbort()

		if second_loop:
			self.correlator.reset()

		self._loop(tilts, exposures)
		
		self.logger.info('Collection loop completed.')

	def _loop(self, tilts, exposures):
		image_pixel_size = self.pixel_size*self.preset['binning']['x']

		tilt0 = tilts[0]
		position0 = self.node.getPixelPosition('image shift')
		defocus0 = self.node.getDefocus()

		m = 'Initial feature position: %g, %g pixels.'
		self.logger.info(m % (position0['x'], position0['y']))
		m = 'Initial defocus: %g meters.'
		self.logger.info(m % defocus0)

		self.prediction.addPosition(tilt0, position0)

		position = dict(position0)
		defocus = defocus0

		abort_loop = False
		for i, tilt in enumerate(tilts):
			self.checkAbort()

			self.logger.info('Current tilt angle: %g degrees.' % math.degrees(tilt))
			try:
				predicted_position = self.prediction.predict(tilt)
			except:
				raise
			self.checkAbort()

			predicted_shift = {}
			predicted_shift['x'] = predicted_position['x'] - position['x']
			predicted_shift['y'] = predicted_position['y'] - position['y']

			predicted_shift['z'] = -defocus
			defocus = defocus0 + predicted_position['z']*image_pixel_size
			self.logger.info('defocus0: %g meters,sintilt: %g' % (defocus0,math.sin(tilt)))
#			defocus = defocus0 + predicted_shift['x']*0.5*math.sin(tilt)*image_pixel_size
			predicted_shift['z'] += defocus

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

			exposure = exposures[i]
			m = 'Acquiring image (%g second exposure)...' % exposure
			self.logger.info(m)
			self.instrument.ccdcamera.ExposureTime = int(exposure*1000)

			self.checkAbort()

			time.sleep(self.settings['tilt pause time'])

			# TODO: error checking
			channel = self.correlator.getChannel()
			image_data = self.acquireCorrectedCameraImageData(channel)
			self.logger.info('Image acquired.')

			image_mean = image_data['image'].mean()
			if self.settings['integer']:
				intscale = self.settings['intscale']
				image_data['image'] = numpy.around(image_data['image']*intscale).astype(numpy.int16)
				image_mean *= intscale

			image = image_data['image']

			if image_mean < self.settings['mean threshold']:
				if i < (self.settings['collection threshold']/100.0)*len(tilts):
					self.logger.error('Image counts below threshold (mean of %.1f, threshold %.1f), aborting series...' % (image_mean, self.settings['mean threshold']))
					self.finalize()
					raise Abort
				else:
					self.logger.warning('Image counts below threshold, aborting loop...')
					break

			self.logger.info('Saving image...')
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

			try:
				next_tilt = tilts[i + 1]
				s = 'Tilting stage to next angle (%g degrees)...' % math.degrees(next_tilt)
				self.logger.info(s)
				stage_position = {'a': next_tilt}
				self.instrument.tem.StagePosition = stage_position
			except IndexError:
				pass

			self.checkAbort()

			self.logger.info('Correlating image with previous tilt...')
			#self.correlator.setTiltAxis(predicted_position['phi'])
			while True:
				try:
					correlation_image = self.correlator.correlate(tilt_series_image_data, self.settings['use tilt'], channel=channel, wiener=False, taper=0)
					break
				except Exception, e:
					self.logger.warning('Retrying correlate image: %s.' % (e,))
				for tick in range(15):
					self.checkAbort()
					time.sleep(1.0)

			correlation = self.correlator.getShift(False)
			if self.settings['use tilt']:
				correlation = self.correlator.tiltShift(tilts[i],correlation)

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

			raw_correlation = self.correlator.getShift(True)
			s = (raw_correlation['x'], raw_correlation['y'])
			self.viewer.setXC(correlation_image, s)
			if self.settings['use tilt']:
				raw_correlation = self.correlator.tiltShift(tilts[i],raw_correlation)

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
				measured_defocus,
				measured_fit,
			)
			self.savePredictionInfo(*args)

			self.checkAbort()

			if abort_loop:
				break

		self.viewer.clearImages()

	def savePredictionInfo(self, predicted_position, predicted_shift, position, correlation, raw_correlation, image_pixel_size, image, measured_defocus=None, measured_fit=None):
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
		}
		tomo_prediction_data = leginondata.TomographyPredictionData(initializer=initializer)
					
		self.node.publish(tomo_prediction_data, database=True, dbforce=True)

	def checkAbort(self):
		state = self.player.wait()
		if state in ('stop', 'stopqueue'):
			self.finalize()
			raise Abort

