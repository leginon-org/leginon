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
		self.instrument_state = self.tiltimagedata[0][0]['scope']

	def restoreInstrumentState(self):
		pass

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
		#self.tilt_series.save()

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
			if self.settings['pausegroup']:
				self.node.player.pause()
				self.node.setStatus('user input')
				self.node.logger.info('Click play button to continue tilt series')
				self.node.player.wait()
				self.node.logger.info('Continuing')
				self.node.setStatus('processing')
			try:
				self.node.initGoodPredictionInfo(tiltgroup=2)
				self.prediction.newTiltGroup()
				self.loop(self.tilts[1], self.exposures[1], True)
			except:
				return
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

		self.checkAbort()
		self.group=0
		if second_loop:
			self.group=1
			self.correlator.reset()

		self._loop(tilts, exposures)
		
		self.logger.info('Collection loop completed.')

	def getPredictionInfo(self,imagedata):
		q = leginondata.TomographyPredictionData(image=imagedata)
		results = q.query(results=1)
		if len(results) > 0:
			return results[0]

	def _loop(self, tilts, exposures):
		image_pixel_size = self.pixel_size*self.preset['binning']['x']

		tilt0 = tilts[0]
		imagedata = self.tiltimagedata[self.group][0]
		prediction0 = self.getPredictionInfo(imagedata)
		if prediction0 is None:
			self.logger.warning('no prediction information')
			return
		position0 = prediction0['position']
		defocus0 = imagedata['scope']['defocus']

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

		#	try:
		#		self.node.setPosition('image shift', predicted_position)
		#	except Exception, e:
		#		self.logger.error('Calibration error: %s' % e) 
		#		self.finalize()
		#		raise Fail

			m = 'Predicted position: %g, %g pixels, %g, %g meters.'
			self.logger.info(m % (predicted_position['x'],
								  predicted_position['y'],
								  predicted_position['x']*image_pixel_size,
								  predicted_position['y']*image_pixel_size))
			self.logger.info('Predicted defocus: %g meters.' % defocus)

			self.node.setDefocus(defocus)
			measured_defocus = None
			measured_fit = None

			self.checkAbort()

			exposure = exposures[i]
			m = 'Acquiring image (%g second exposure)...' % exposure
			self.logger.info(m)

			self.checkAbort()

			time.sleep(self.settings['tilt pause time'])

			# TODO: error checking
			try:
				image_data = self.tiltimagedata[self.group][i]
			except IndexError:
				#image not acquired
				break
			channel = image_data['correction channel']
			self.logger.info('Image acquired.')

			image_mean = image_data['image'].mean()
			image = image_data['image']

			tilt_series_image_data = image_data
			filename = tilt_series_image_data['filename']
			self.logger.info('Image loaded (filename: \'%s\').' % filename)

			self.checkAbort()

			self.viewer.addImage(image)

			self.checkAbort()

			try:
				next_tilt = tilts[i + 1]
				s = 'Tilting stage to next angle (%g degrees)...' % math.degrees(tilt)
				self.logger.info(s)
				stage_position = {'a': next_tilt}
			except IndexError:
				pass

			self.checkAbort()

			self.logger.info('Correlating image with previous tilt...')
			#self.correlator.setTiltAxis(predicted_position['phi'])
			while True:
				try:
					correlation_image = self.correlator.correlate(image_data, self.settings['use tilt'], channel=channel, wiener=self.settings['use wiener'],taper=self.settings['taper size'])
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

			saved_prediction = self.getPredictionInfo(image_data)
			if saved_prediction is None:
				self.logger.warning('No prediction information')
				abort_loop = True
			else:
				args = (
					saved_prediction['predicted position'],
					predicted_position,
					predicted_shift,
					position,
					correlation,
					saved_prediction['correlation'],
					image_pixel_size,
					image_data['filename'],
					measured_defocus,
					measured_fit,
				)
				self.showPredictionInfo(*args)

			self.checkAbort()

			if abort_loop:
				break

		self.viewer.clearImages()

	def showPredictionInfo(self,saved_predicted_position, predicted_position, predicted_shift, position, correlation, saved_correlation, image_pixel_size, image, measured_defocus=None, measured_fit=None):
		print "-----------PREDICTION-------------"
		keys = saved_predicted_position.keys()
		keys.sort()
		print "%14s  %8s %8s" % ('key','saved','current')
		for key in keys:
			try:
				print "%14s: %8.1f %8.1f" % (key, saved_predicted_position[key],predicted_position[key])
			except:
				pass
		print "----------CORRELATION-------------"
		keys = saved_correlation.keys()
		keys.sort()
		print "%14s  %8s %8s" % ('key','saved','current')
		for key in keys:
			print "%14s: %8.1f %8.1f" % (key, saved_correlation[key],correlation[key])
		initializer = {
			'predicted shift': predicted_shift,
			'position': position,
			'image': image,
		}
		for key in initializer.keys():
			print key,initializer[key]
		print '============================'


	def checkAbort(self):
		state = self.player.wait()
		if state in ('stop', 'stopqueue'):
			self.finalize()
			raise Abort

