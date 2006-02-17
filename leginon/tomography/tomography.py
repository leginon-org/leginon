import math
import numarray
import threading
import calibrationclient
import data
import event
import acquisition
import gui.wx.tomography.Tomography
import collection

class CalibrationError(Exception):
    pass

class Tomography(acquisition.Acquisition):
    eventinputs = acquisition.Acquisition.eventinputs
    eventoutputs = acquisition.Acquisition.eventoutputs

    panelclass = gui.wx.tomography.Tomography.Panel
    settingsclass = data.TomographySettingsData

    defaultsettings = {
        'pause time': 2.5,
        'move type': 'image shift',
        'preset order': [],
        'correct image': True,
        'display image': True,
        'save image': True,
        'wait for process': False,
        'wait for rejects': False,
        'duplicate targets': False,
        'duplicate target type': 'focus',
        'iterations': 1,
        'wait time': 0,
        'adjust for drift': False,
        'tilt min': -60.0,
        'tilt max': 60.0,
        'tilt start': 0.0,
        'tilt step': 1.0,
        'cosine exposure': True,
        'thickness value': 100.0,
        'xcf bin': 1,
        'registration preset order': [],
        'run buffer cycle': True,
        'align zero loss peak': True,
    }

    def __init__(self, *args, **kwargs):
        acquisition.Acquisition.__init__(self, *args, **kwargs)
        self.calclients['pixel size'] = \
                calibrationclient.PixelSizeCalibrationClient(self)

        self.start()

    def acquireFilm(self, *args, **kwargs):
        self.logger.error('Film acquisition not currently supported.')
        return

    def acquire(self, presetdata, target=None, emtarget=None, attempt=None):
        try:
            calibrations = self.getCalibrations()
        except CalibrationError, e:
            self.logger.error('Calibration error: %s' % e) 
            return 'failed'
        #high_tension, pixel_size, tilt_axis, stage_angle, offset_n, offset_z = calibrations
        high_tension, pixel_size = calibrations

        #self.logger.info('Pixel size: %g meters, tilt axis: %g degrees, stage angle: %g degrees, offset n: %g meters.' % (pixel_size, math.degrees(tilt_axis), math.degrees(stage_angle), offset_n))
        self.logger.info('Pixel size: %g meters.' % pixel_size)

        collect = collection.Collection()
        collect.node = self
        collect.session = self.session
        collect.logger = self.logger
        collect.presets_client = self.presetsclient
        collect.calibration_clients = self.calclients
        collect.instrument = self.instrument
        collect.settings = self.settings.copy()
        collect.preset = presetdata
        collect.target = target
        collect.emtarget = emtarget
        collect.viewer = self.panel.viewer
        collect.player = self.player
        collect.high_tension = high_tension
        collect.pixel_size = pixel_size
        #collect.tilt_axis = tilt_axis
        #collect.stage_angle = stage_angle
        #collect.offset_n = offset_n
        #collect.offset_z = offset_z

        try:
            collect.start()
        except collection.Abort:
            return 'aborted'
        except collection.Fail:
            return 'failed'

        # ignoring wait for process
        #self.publishDisplayWait(imagedata)

        return 'ok'

    def getShift(self, shift, move_type):
        scope_data = self.instrument.getData(data.ScopeEMData)
        camera_data = self.instrument.getData(data.CameraEMData, image=False)
        client = self.calclients[move_type]
        # invert y
        shift = {'row': shift['y'], 'col': -shift['x']}
        try:
            scope_data = client.transform(shift, scope_data, camera_data)
        except calibrationclient.NoMatrixCalibrationError, e:
            raise CalibrationError(e)
        return scope_data[move_type]

    def correctShift(self, shift, move_type):
        position = self.getShift(shift, move_type)
        initializer = {move_type: position}
        position = data.ScopeEMData(initializer=initializer)
        self.instrument.setData(position)

    def correctDefocus(self, delta_defocus):
        defocus = self.instrument.tem.Defocus
        self.instrument.tem.Defocus = defocus - delta_defocus

    def getStageAngle(self, tem, ccd_camera, high_tension, magnification):
        parameter = 'stage position'
        client = self.calclients[parameter]
        args = (tem, ccd_camera, parameter, high_tension, magnification)
        try:
            theta_x, theta_y = client.getAngles(*args)
        except calibrationclient.NoMatrixCalibrationError, e:
            raise CalibrationError(e)
        return theta_y

    def getTiltAxis(self, stage_angle):
        raw_tilt_axis = stage_angle - math.pi/2
        tilt_axis = raw_tilt_axis - math.pi/2
        if tilt_axis > math.pi/2:
            tilt_axis -= math.pi
        elif tilt_axis < -math.pi/2:
            tilt_axis += math.pi
        return tilt_axis

    def getOpticalAxisCalibration(self, *args):
        tem, ccd_camera, high_tension, magnification = args
        initializer = {
            'tem': tem,
            'ccdcamera': ccd_camera,
            'high tension': high_tension,
            'magnification': magnification,
        }
        query_data = data.OpticalAxisCalibrationData(initializer=initializer)
        try:
            calibration_data = self.research(query_data, results=1)[0]
        except IndexError:
            s = 'no optical axis calibration for %s, %s, %seV, %sX'
            s %= (tem['name'], ccd_camera['name'], high_tension, magnification)
            raise CalibrationError(s)
        n0 = calibration_data['n0']
        z0 = calibration_data['z0']
        return n0, z0

    def getOffsetN(self, stage_angle, parameter, scope_data, camera_data,
                         pixel_size):
        shift = dict(scope_data[parameter])
        client = self.calclients[parameter]
        try:
            pixel_shift = client.itransform(shift, scope_data, camera_data)
        except calibrationclient.NoMatrixCalibrationError, e:
            raise CalibrationError(e)

        # inverting y
        offset = {
            'x': pixel_shift['col']*camera_data['binning']['x']*pixel_size,
            'y': -pixel_shift['row']*camera_data['binning']['y']*pixel_size,
        }

        n = offset['x']*math.cos(stage_angle) + offset['y']*math.sin(stage_angle)
        return n

    def getCalibrations(self):
        scope_data = self.instrument.getData(data.ScopeEMData)
        camera_data = self.instrument.getData(data.CameraEMData, image=False)

        tem = scope_data['tem']
        ccd_camera = camera_data['ccdcamera']
        high_tension = scope_data['high tension']
        magnification = scope_data['magnification']

        args = (magnification, tem, ccd_camera)
        pixel_size = self.calclients['pixel size'].getPixelSize(*args)

        if pixel_size is None:
            raise CalibrationError('no pixel size for %gx' % magnification)

        #args = (tem, ccd_camera, high_tension, magnification)
        #stage_angle = -self.getStageAngle(*args)
        #n0, z0 = self.getOpticalAxisCalibration(*args)

        #parameter = 'image shift'

        #args = (stage_angle, parameter, scope_data, camera_data, pixel_size)
        #n = self.getOffsetN(*args)
        #offset_n = n0 + n

        #tilt_axis = self.getTiltAxis(stage_angle)

        #offset_z = 0

        #return high_tension, pixel_size, tilt_axis, stage_angle, offset_n, offset_z
        return high_tension, pixel_size

    def XXXprocessTargetData(self, targetdata, attempt=None):
        try:
            preset_names = self.validatePresets()
        except InvalidPresetsSequence:
            s = 'Presets sequence is invalid, please correct it'
            if targetdata is None or targetdata['type'] == 'simulated':
                self.logger.error(s + ' and try again.')
                return 'aborted'
            else:
                self.player.pause()
                self.logger.error(s + ' and press continue.')
                self.beep()
                return 'repeat'

        result = 'ok'
        for preset_name in presetnames:
            if self.alreadyAcquired(targetdata, preset_name):
                continue

            self.correctBacklash()
            self.declareDrift('stage')

            if self.settings['adjust for drift']:
                targetdata = self.adjustTargetForDrift(targetdata)

            try:
                emtarget = self.targetToEMTargetData(targetdata)
            except InvalidStagePosition:
                return 'invalid'
            except NoMoveCalibration:
                self.player.pause()
                self.logger.error('Calibrate this move type, then continue')
                self.beep()
                return 'repeat'

            self.setStatus('waiting')
            self.presetsclient.toScope(preset_name, emtarget)
            self.setStatus('processing')
            self.logger.info('Determining current preset...')
            preset = self.presetsclient.getCurrentPreset()

            if preset is None or preset['name'] != preset_name:
                self.logger.error('Failed to set preset "%s".' % preset_name)
                continue

            if preset['film']:
                self.logger.error('Film currently unsupported for tomography.')
                return 'invalid'

            self.logger.info('Current preset is "%s".' % preset['name'])

            pause_time = self.settings['pause time']
            self.logger.info('Pausing for %s seconds...' % pause_time)
            time.sleep(pause_time)

            result = self.acquire(preset,
                                  target=targetdata,
                                  emtarget=emtarget,
                                  attempt=attempt)

            # in these cases, return immediately
            if result in ('aborted', 'repeat'):
                self.logger.info('Acquisition state is "%s"' % result)
                break

        self.logger.info('Processing completed.')

        return result

