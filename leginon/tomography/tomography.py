import math
import numarray
import threading
import calibrationclient
import data
import event
import acquisition
import gui.wx.tomography.Tomography
import collection
import tilts
import exposure

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
        'xcf bin': 1,
        'registration preset order': [],
        'run buffer cycle': True,
        'align zero loss peak': True,
        'dose': 200.0,
        'min exposure': None,
        'max exposure': None,
    }

    def __init__(self, *args, **kwargs):
        acquisition.Acquisition.__init__(self, *args, **kwargs)
        self.calclients['pixel size'] = \
                calibrationclient.PixelSizeCalibrationClient(self)

        self.tilts = tilts.Tilts()
        self.exposure = exposure.Exposure()

        self.start()

    '''
    def onPresetPublished(self, evt):
        acquisition.Acquisition.onPresetPublished(self, evt)

        preset = evt['data']

        if preset is None or preset['name'] is None:
            return

        if preset['name'] not in self.settings['preset order']:
            return

        dose = preset['dose']
        exposure_time = preset['exposure time']/1000.0

        try:
            self.exposure.update(dose=dose, exposure=exposure_time)
        except exposure.LimitError, e:
            s = 'Exposure time limit exceeded for preset \'%s\': %s.'
            s %= (preset['name'], e)
            self.logger.warning(s)

    def setSettings(self, *args, **kwargs):
        acquisition.Acquisition.setSettings(self, *args, **kwargs)
        self.update()
    '''

    def update(self):
        try:
            self.tilts.update(min=math.radians(self.settings['tilt min']),
                              max=math.radians(self.settings['tilt max']),
                              start=math.radians(self.settings['tilt start']),
                              step=math.radians(self.settings['tilt step']))
        except ValueError, e:
            self.logger.warning('Tilt parameters invalid: %s.' % e)

        total_dose = self.settings['dose']
        exposure_min = self.settings['min exposure']
        exposure_max = self.settings['max exposure']

        tilts = self.tilts.getTilts()

        try:
            name = self.settings['preset order'][-1]
            preset = self.presetsclient.getPresetFromDB(name)
        except (IndexError, ValueError):
            dose = 0.0
            exposure_time = 0.0
        else:
            dose = preset['dose']*1e-20
            exposure_time = preset['exposure time']/1000.0

        try:
            self.exposure.update(total_dose=total_dose,
                                 tilts=tilts,
                                 dose=dose,
                                 exposure=exposure_time,
                                 exposure_min=exposure_min,
                                 exposure_max=exposure_max)
        except exposure.LimitError, e:
            self.logger.warning('Exposure time out of range: %s.' % e)
        except exposure.Default, e:
            self.logger.warning('Using preset exposure time: %s.' % e)
        else:
            try:
                exposure_range = self.exposure.getExposureRange()
            except ValueError:
                pass
            else:
                s = 'Exposure time range: %g to %g seconds.' % exposure_range
                self.logger.info(s)

    def checkDose(self):
        self.update()

    def acquireFilm(self, *args, **kwargs):
        self.logger.error('Film acquisition not currently supported.')
        return

    def acquire(self, presetdata, target=None, emtarget=None, attempt=None):
        try:
            calibrations = self.getCalibrations()
        except CalibrationError, e:
            self.logger.error('Calibration error: %s' % e) 
            return 'failed'
        high_tension, pixel_size = calibrations

        self.logger.info('Pixel size: %g meters.' % pixel_size)

        # TODO: error check
        self.update()
        tilts = self.tilts.getTilts()
        exposures = self.exposure.getExposures()

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
        collect.tilts = tilts
        collect.exposures = exposures

        try:
            collect.start()
        except collection.Abort:
            return 'aborted'
        except collection.Fail:
            return 'failed'

        # ignoring wait for process
        #self.publishDisplayWait(imagedata)

        return 'ok'

    def getPixelPosition(self, move_type, position=None):
        scope_data = self.instrument.getData(data.ScopeEMData)
        camera_data = self.instrument.getData(data.CameraEMData, image=False)
        if position is None:
            position = {'x': 0.0, 'y': 0.0}
        else:
            scope_data[move_type] = {'x': 0.0, 'y': 0.0}
        client = self.calclients[move_type]
        try:
            pixel_position = client.itransform(position, scope_data, camera_data)
        except calibrationclient.NoMatrixCalibrationError, e:
            raise CalibrationError(e)
        # invert y
        return {'x': pixel_position['col'], 'y': -pixel_position['row']}

    def getParameterPosition(self, move_type, position=None):
        scope_data = self.instrument.getData(data.ScopeEMData)
        camera_data = self.instrument.getData(data.CameraEMData, image=False)
        if position is None:
            position = {'x': 0.0, 'y': 0.0}
        else:
            scope_data[move_type] = {'x': 0.0, 'y': 0.0}
        client = self.calclients[move_type]
        # invert y
        position = {'row': -position['y'], 'col': position['x']}
        try:
            scope_data = client.transform(position, scope_data, camera_data)
        except calibrationclient.NoMatrixCalibrationError, e:
            raise CalibrationError(e)
        return scope_data[move_type]

    def move(self, position, move_type):
        position = self.getParameterPosition(position, move_type)
        initializer = {move_type: position}
        position = data.ScopeEMData(initializer=initializer)
        self.instrument.setData(position)
        return position[move_type]

    def setDefocus(self, defocus):
        self.instrument.tem.Defocus = defocus

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
        shift = self.getShift(shift, move_type)
        initializer = {move_type: shift}
        position = data.ScopeEMData(initializer=initializer)
        self.instrument.setData(position)

