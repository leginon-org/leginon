import math
import time
import data
import tiltcorrelator
import tiltseries
import numarray

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

        self.logger.info('Calibrations loaded.')

        self.saveInstrumentState()
        self.logger.info('Instrument state saved.')

        self.tilt_series = tiltseries.TiltSeries(self.node, self.settings,
                                                 self.session, self.preset,
                                                 self.target, self.emtarget)
        self.tilt_series.save()

        self.correlator = tiltcorrelator.Correlator(self.settings['xcf bin'],
                                                    self.theta)

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

        self.logger.info('Removing tilt backlash...')
        try:
            target, emtarget = self.node.removeStageAlphaBacklash(tilts, self.preset['name'], self.target, self.emtarget)
        except Exception, e:
            self.logger.error('Failed to remove backlash: %s.' % e)
            self.finalize()
            raise Fail

        self.checkAbort()

        self.prediction.reset()

        if second_loop:
            self.correlator.reset()

        self._loop(tilts, exposures)
        
        self.logger.info('Collection loop completed.')

    def _loop(self, tilts, exposures):
        pixel_size = self.pixel_size

        tilt0 = tilts[0]
        position0 = self.node.getPixelPosition(self.settings['move type'])
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

            predicted_position = self.prediction.predict(tilt)

            self.checkAbort()

            predicted_shift = {}
            predicted_shift['x'] = predicted_position['x'] - position['x']
            predicted_shift['y'] = predicted_position['y'] - position['y']

            measured_defocus = defocus
            predicted_shift['z'] = -defocus
            defocus = defocus0 - predicted_position['z']*pixel_size
            predicted_shift['z'] += defocus

            if self.settings['measure defocus']:
                measured_defocus += self.node.measureDefocus()
                self.logger.info('Measured defocus: %g meters.' % measured_defocus)
                self.logger.info('Predicted defocus: %g meters.' % defocus)
            else:
                measured_defocus = None

            try:
                self.node.setPosition(self.settings['move type'], predicted_position)
            except Exception, e:
                self.logger.error('Calibration error: %s' % e) 
                self.finalize()
                raise Fail

            self.node.setDefocus(defocus)

            m = 'Predicted position: %g, %g pixels, %g, %g meters.'
            self.logger.info(m % (predicted_position['x'],
                                  predicted_position['y'],
                                  predicted_position['x']*pixel_size,
                                  predicted_position['y']*pixel_size))
            self.logger.info('Predicted defocus: %g meters.' % defocus)

            self.checkAbort()

            exposure = exposures[i]
            m = 'Acquiring image (%g second exposure)...' % exposure
            self.logger.info(m)
            self.instrument.ccdcamera.ExposureTime = int(exposure*1000)

            self.checkAbort()

            time.sleep(self.settings['tilt pause time'])

            # TODO: error checking
            channel = self.correlator.getChannel()
            self.instrument.setCorrectionChannel(channel)
            image_data = self.instrument.getData(data.CorrectedCameraImageData)
            self.logger.info('Image acquired.')

            # HACK: fix me
            image_data['image'] = numarray.around(image_data['image']*10).astype(numarray.Int16)

            image = image_data['image']

            if image.mean() < self.settings['mean threshold']:
                if i < (self.settings['collection threshold']/100.0)*len(tilts):
                    self.logger.error('Image counts below threshold, aborting series...')
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
                s = 'Tilting stage to next angle (%g degrees)...' % math.degrees(tilt)
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
                    correlation_image = self.correlator.correlate(image, tilt, channel=channel)
                    break
                except Exception, e:
                    self.logger.warning('Retrying correlate image: %s.' % (e,))
                for tick in range(15):
                    self.checkAbort()
                    time.sleep(1.0)

            correlation = self.correlator.getShift(False)

            position = {
                'x': predicted_position['x'] - correlation['x'],
                'y': predicted_position['y'] - correlation['y'],
            }

            if not self.prediction.addPosition(tilt, position):
                if i < (self.settings['collection threshold']/100.0)*len(tilts):
                    self.logger.error('Position out of range, aborting series...')
                    self.finalize()
                    raise Abort
                else:
                    self.logger.warning('Position out of range, aborting loop...')
                    abort_loop = True

            m = 'Correlated shift from feature: %g, %g pixels, %g, %g meters.'
            self.logger.info(m % (correlation['x'],
                                  correlation['y'],
                                  correlation['x']*pixel_size,
                                  correlation['y']*pixel_size))

            m = 'Feature position: %g, %g pixels, %g, %g meters.'
            self.logger.info(m % (position['x'],
                                  position['y'],
                                  position['x']*pixel_size,
                                  position['y']*pixel_size))

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
                measured_defocus,
            )
            self.savePredictionInfo(*args)

            self.checkAbort()

            if abort_loop:
                break

        self.viewer.clearImages()

    def savePredictionInfo(self, predicted_position, predicted_shift, position, correlation, raw_correlation, pixel_size, image, measured_defocus=None):
        initializer = {
            'session': self.node.session,
            'predicted position': predicted_position,
            'predicted shift': predicted_shift,
            'position': position,
            'correlation': correlation,
            'raw correlation': raw_correlation,
            'pixel size': pixel_size,
            'image': image,
            'measured defocus': measured_defocus,
        }
        tomo_prediction_data = data.TomographyPredictionData(initializer=initializer)
                    
        self.node.publish(tomo_prediction_data, database=True, dbforce=True)

    def checkAbort(self):
        state = self.player.wait()
        if state in ('stop', 'stopqueue'):
            self.finalize()
            raise Abort

