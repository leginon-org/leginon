import math
import time
import data
import tiltcorrelator
import tiltseries
import registration
import prediction

class Abort(Exception):
    pass

class Fail(Exception):
    pass

class Collection(object):
    def __init__(self):
        self.tilt_series = None
        self.prediction = None
        self.correlator = None
        self.instrument_state = None
        self.theta = 0.0
        self.parameter_position = None
        self.defocus = None

    def saveInstrumentState(self):
        self.instrument_state = self.instrument.getData(data.ScopeEMData)

    def restoreInstrumentState(self):
        keys = ['stage position', 'defocus', 'image shift', 'magnification']
        if self.instrument_state is None:
            return
        instrument_state = data.ScopeEMData()
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

    def initialize(self):
        self.logger.info('Initializing...')

        self.prediction = prediction.Prediction()
        self.logger.info('Calibrations loaded.')

        self.saveInstrumentState()
        self.logger.info('Instrument state saved.')

        # HACK: fix me
        key = self.settings['move type']
        position = self.instrument_state[key]
        self.parameter_position = self.node.getPixelPosition(key, position)
        self.defocus = self.instrument_state['defocus']

        self.tilt_series = tiltseries.TiltSeries(self.node, self.settings,
                                                 self.session, self.preset,
                                                 self.target, self.emtarget)
        self.tilt_series.save()

        self.correlator = tiltcorrelator.Correlator(self.settings['xcf bin'],
                                                    self.theta)

        self.registration = registration.Registration(
                                          self.node,
                                          self.presets_client,
                                          self.calibration_clients,
                                          self.instrument,
                                          self.viewer,
                                          self.settings,
                                          self.theta,
                                          self.emtarget)

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
            self.loop(self.tilts[0], self.exposures[0], False)
        elif n == 2:
            self.loop(self.tilts[0], self.exposures[0], False)
            self.checkAbort()
            self.loop(self.tilts[1], self.exposures[1], True)
        else:
            raise RuntimeError('too many tilt angle groups')

    def alignZeroLossPeak(self):
        ccd_camera = self.instrument.ccdcamera
        if not ccd_camera.EnergyFiltered:
            self.logger.warning('No energy filter on this instrument.')
            return
        try:
            if not ccd_camera.EnergyFilter:
                self.logger.warning('Energy filtering is not enabled.')
                return
            ccd_camera.alignEnergyFilterZeroLossPeak()
            m = 'Energy filter zero loss peak aligned.'
            self.logger.info(m)
        except AttributeError:
            m = 'Energy filter methods are not available on this instrument.'
            self.logger.warning(m)
        except Exception, e:
            s = 'Energy filter align zero loss peak failed: %s.'
            self.logger.error(s % e)

    def finalize(self):
        self.tilt_series = None

        self.correlator.reset()

        self.registration = None

        self.defocus = None
        self.parameter_position = None

        self.restoreInstrumentState()
        self.instrument_state = None

        if self.settings['align zero loss peak']:
            self.alignZeroLossPeak()

        self.logger.info('Data collection ended.')

        self.viewer.clearImages()

    def loop(self, tilts, exposures, second_loop):
        self.logger.info('Starting tilt collection (%d angles)...' % len(tilts))

        if second_loop:
            self.restoreInstrumentState()

        self.logger.info('Removing tilt backlash...')
        try:
            shift = self.registration.removeBacklash(tilts)
        except Exception, e:
            self.logger.error('Failed to remove backlash: %s.' % e)
            self.finalize()
            raise Fail
        m = 'Tilt backlash removed (position shifted: %d, %d pixels).'
        self.logger.info(m % (shift['x'], shift['y']))

        self.checkAbort()

        self.prediction.reset()

        if second_loop:
            self.correlator.reset()

        self._loop(tilts, exposures)
        
        self.logger.info('Collection loop completed.')

    def _loop(self, tilts, exposures):
        pixel_size = self.pixel_size
        position = self.parameter_position
        defocus = self.defocus
        theta = self.theta
        for i, tilt in enumerate(tilts):
            self.checkAbort()

            self.logger.info('Current tilt angle: %g degrees.' % math.degrees(tilt))

            predicted_position = self.prediction.predict(tilt)
            if predicted_position is None:
                predicted_position = position
                predicted_position['z'] = defocus
                predicted_position['theta'] = theta

            predicted_shift = {}
            predicted_shift['x'] = predicted_position['x'] - position['x']
            predicted_shift['x'] = predicted_position['y'] - position['y']

            predicted_shift['z'] = -defocus
            defocus = self.defocus - predicted_position['z']*pixel_size
            predicted_shift['z'] += defocus

            try:
                self.node.setPosition(self.settings['move type'], predicted_position)
            except Exception, e:
                self.logger.error('Calibration error: %s' % e) 
                self.finalize()
                raise Fail

            self.node.setDefocus(defocus)

            m = 'Predicted position (from first image): %g, %g pixels, %g, %g meters.'
            self.logger.info(m % (predicted_position['x'],
                                  predicted_position['y'],
                                  predicted_position['x']*pixel_size,
                                  predicted_position['y']*pixel_size))
            self.logger.info('Predicted defocus: %g meters.' % (predicted_position['z']*pixel_size))

            self.checkAbort()

            exposure = exposures[i]
            m = 'Acquiring image (%g second exposure)...' % exposure
            self.logger.info(m)
            self.instrument.ccdcamera.ExposureTime = int(exposure*1000)

            self.checkAbort()

            time.sleep(1.0)

            # TODO: error checking
            image_data = self.instrument.getData(data.CorrectedCameraImageData)
            self.logger.info('Image acquired.')
            image = image_data['image']

            self.logger.info('Saving image...')
            while True:
                try:
                    tilt_series_image_data = self.tilt_series.saveImage(image_data)
                    break
                except Exception, e:
                    self.logger.warning('Retrying save image: %s.' % (e,))
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
                s = 'Tilting stage to next angle (%g degrees)...' % math.degrees(tilt)
                self.logger.info(s)
                stage_position = {'a': next_tilt}
                self.instrument.tem.StagePosition = stage_position
            except IndexError:
                pass

            self.checkAbort()

            self.logger.info('Correlating image with previous tilt...')
            self.correlator.setTiltAxis(predicted_position['theta'])
            while True:
                try:
                    correlation_image = self.correlator.correlate(image, tilt)
                    break
                except Exception, e:
                    self.logger.warning('Retrying correlate image: %s.' % (e,))
                for tick in range(15):
                    self.checkAbort()
                    time.sleep(1.0)

            correlation = self.correlator.getShift(False)

            position = {
                'x': predicted_position['x'] + correlation['x'],
                'y': predicted_position['y'] + correlation['y'],
            }

            m = 'Feature position: %g, %g pixels, %g, %g meters.'
            self.logger.info(m % (position['x'],
                                  position['y'],
                                  position['x']*pixel_size,
                                  position['y']*pixel_size))

            m = 'Correlated shift from feature: %g, %g pixels, %g, %g meters.'
            self.logger.info(m % (correlation['x'],
                                  correlation['y'],
                                  correlation['x']*pixel_size,
                                  correlation['y']*pixel_size))

            raw_correlation = self.correlator.getShift(True)
            s = (raw_correlation['x'], raw_correlation['y'])
            self.viewer.setXC(correlation_image, s)

            self.checkAbort()

            time.sleep(3.0)

            self.checkAbort()

            args = (
                predicted_position,
                predicted_shift,
                position,
                correlation,
                raw_correlation,
                self.pixel_size,
                tilt_series_image_data,
            )
            self.savePredictionInfo(*args)

            self.checkAbort()

            self.prediction.addShift(tilt, position)
            self.prediction.calculate()

            self.checkAbort()

        self.viewer.clearImages()

    def savePredictionInfo(self, predicted_position, predicted_shift, position, correlation, raw_correlation, pixel_size, image):
        initializer = {
            'predicted position': predicted_position,
            'predicted shift': predicted_shift,
            'position': position,
            'correlation': correlation,
            'raw correlation': raw_correlation,
            'pixel size': pixel_size,
            'image': image,
        }
        tomo_prediction_data = data.TomographyPredictionData(initializer=initializer)
                    
        self.node.publish(tomo_prediction_data, database=True, dbforce=True)

    def checkAbort(self):
        state = self.player.wait()
        if state in ('stop', 'stopqueue'):
            self.finalize()
            raise Abort

