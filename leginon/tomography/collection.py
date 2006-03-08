import math
import time
import data
import exposure
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
        self.exposure = None
        self.prediction = None
        self.correlator = None
        self.instrument_state = None

        self.tilt_axis = 0.0

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

        self.tilt_series = tiltseries.TiltSeries(self.node, self.settings,
                                                 self.session, self.preset,
                                                 self.target, self.emtarget)
        self.tilt_series.save()

        self.exposure = exposure.Exposure(self.preset['exposure time']/1000.0,
                                     self.settings['cosine exposure'],
                                     self.high_tension,
                                     self.settings['thickness value'],
                                     math.radians(self.settings['tilt start']))

        self.correlator = tiltcorrelator.Correlator(self.settings['xcf bin'],
                                                    self.tilt_axis)

        self.registration = registration.Registration(
                                          self.node,
                                          self.presets_client,
                                          self.calibration_clients,
                                          self.instrument,
                                          self.viewer,
                                          self.settings,
                                          self.tilt_axis,
                                          self.emtarget)



        if self.settings['run buffer cycle']:
            self.runBufferCycle()

        return True

    def collect(self):
        tilts = self.getTilts()
        n_tilts = len(tilts)
        if n_tilts == 0:
            return
        elif n_tilts == 1:
            self.loop(tilts[0], False)
        elif n_tilts == 2:
            self.loop(tilts[0], False)
            self.checkAbort()
            self.loop(tilts[1], True)
        else:
            raise RuntimeError

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

        self.exposure = None

        self.correlator.reset()

        self.registration = None

        self.restoreInstrumentState()
        self.instrument_state = None

        if self.settings['align zero loss peak']:
            self.alignZeroLossPeak()

        self.logger.info('Data collection ended.')

        self.viewer.clearImages()

    def loop(self, tilts, second_loop):
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

        self._loop(tilts)
        
        self.logger.info('Collection loop completed.')

    def _loop(self, tilts):
        pixel_size = self.pixel_size
        pixel_position = {'x': 0.0, 'y': 0.0}
        for i, tilt in enumerate(tilts):
            self.checkAbort()

            self.logger.info('Current tilt angle: %g degrees.' % tilt)

            tilt = math.radians(tilt)

            position, shift = self.prediction.predict(tilt)

            pixel = {
                'predicted position': position,
                'predicted shift': shift,
            }

            try:
                s = {}
                for axis in ['x', 'y']:
                    s[axis] = pixel['predicted shift'][axis]
                    s[axis] /= self.preset['binning'][axis]

                self.node.correctShift(s, self.settings['move type'])
            except Exception, e:
                self.logger.error('Calibration error: %s' % e) 
                self.finalize()
                raise Fail

            for axis in ['x', 'y']:
                pixel_position[axis] += pixel['predicted shift'][axis]

            pixel['position'] = dict(pixel_position)

            self.node.correctDefocus(pixel['predicted shift']['z']*pixel_size)

            m = 'Predicted position (from first image): %g, %g pixels, %g, %g meters.'
            self.logger.info(m % (pixel['predicted position']['x'],
                                  pixel['predicted position']['y'],
                                  pixel['predicted position']['x']*pixel_size,
                                  pixel['predicted position']['y']*pixel_size))
            info = (pixel['predicted shift']['x'],
                    pixel['predicted shift']['y'],
                    pixel['predicted shift']['x']*pixel_size,
                    pixel['predicted shift']['y']*pixel_size)
            m = 'Compensating image shift: %g, %g pixels, %g, %g meters'
            self.logger.info(m % info)
            info = (pixel['predicted shift']['z']*pixel_size,)
            self.logger.info('Compensating defocus: %g meters.' % info)

            self.checkAbort()

            exposure = self.exposure.calculate(tilt)
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
                stage_position = {'a': math.radians(next_tilt)}
                self.instrument.tem.StagePosition = stage_position
            except IndexError:
                pass

            self.checkAbort()

            self.logger.info('Correlating image with previous tilt...')
            self.correlator.setTiltAxis(pixel['predicted position']['theta'])
            correlation_image = self.correlator.correlate(image, tilt)
            pixel['correlation'] = self.correlator.getShift(False)
            pixel['correlated position'] = {}
            for axis in ['x', 'y']:
                pixel['correlation'][axis] = float(pixel['correlation'][axis])
                pixel['correlated position'][axis] = pixel['position'][axis]
                pixel['correlated position'][axis] += pixel['correlation'][axis]

            info = (pixel['correlated position']['x'],
                    pixel['correlated position']['y'],
                    pixel['correlated position']['x']*pixel_size,
                    pixel['correlated position']['y']*pixel_size)
            m = 'Image correlation completed, feature position: %g, %g pixels, %g, %g meters.'
            self.logger.info(m % info)
            info = (pixel['correlation']['x'],
                    pixel['correlation']['y'],
                    pixel['correlation']['x']*pixel_size,
                    pixel['correlation']['y']*pixel_size)
            m = 'Correlated shift from feature: %g, %g pixels, %g, %g meters.'
            self.logger.info(m % info)

            self.checkAbort()

            pixel['raw correlation'] = self.correlator.getShift(True)
            s = (pixel['raw correlation']['x'], pixel['raw correlation']['y'])
            self.viewer.setXC(correlation_image, s)

            time.sleep(3.0)

            self.savePredictionInfo(pixel, self.pixel_size, tilt_series_image_data)

            self.checkAbort()

            self.prediction.refineAll(tilt, pixel['correlation'])

            self.checkAbort()

        self.viewer.clearImages()

    def savePredictionInfo(self, info, pixel_size, image):
        initializer = {
            'predicted position': info['predicted position'],
            'predicted shift': info['predicted shift'],
            'position': info['position'],
            'correlation': info['correlation'],
            'correlated position': info['correlated position'],
            'raw correlation': info['raw correlation'],
            'pixel size': pixel_size,
            'image': image,
        }
        tomo_prediction_data = data.TomographyPredictionData(initializer=initializer)
                    
        self.node.publish(tomo_prediction_data, database=True, dbforce=True)

    def getTilts(self):
        return getTilts(self.settings['tilt min'], self.settings['tilt max'],
                        self.settings['tilt start'], self.settings['tilt step'])

    def checkAbort(self):
        state = self.player.wait()
        if state in ('stop', 'stopqueue'):
            self.finalize()
            raise Abort

def getTilts(min_tilt, max_tilt, start_tilt, tilt_step):
    tilts = []
    t = _getTilts(min_tilt, max_tilt, start_tilt, tilt_step)
    if len(t) > 1:
        tilts.append(t)
    t = _getTilts(min_tilt, max_tilt, start_tilt, -tilt_step)
    if len(t) > 1:
        tilts.append(t)
    return tilts

def _getTilts(min_tilt, max_tilt, start_tilt, tilt_step):
    tilt = start_tilt
    tilts = []
    while tilt >= min_tilt and tilt <= max_tilt:
        tilts.append(tilt)
        tilt += tilt_step
    return tilts

