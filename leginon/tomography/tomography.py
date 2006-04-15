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

        dose = 0.0
        exposure_time = 0.0
        try:
            name = self.settings['preset order'][-1]
            preset = self.presetsclient.getPresetFromDB(name)
        except (IndexError, ValueError):
            pass
        else:
            if preset['dose'] is not None:
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
        collect.instrument = self.instrument
        collect.settings = self.settings.copy()
        collect.preset = presetdata
        collect.target = target
        collect.emtarget = emtarget
        collect.viewer = self.panel.viewer
        collect.player = self.player
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
        # invert y and position
        return {'x': pixel_position['col'], 'y': -pixel_position['row']}

    def getParameterPosition(self, move_type, position=None):
        scope_data = self.instrument.getData(data.ScopeEMData)
        camera_data = self.instrument.getData(data.CameraEMData, image=False)
        if position is None:
            position = {'x': 0.0, 'y': 0.0}
        else:
            scope_data[move_type] = {'x': 0.0, 'y': 0.0}
        client = self.calclients[move_type]
        # invert y and position
        position = {'row': -position['y'], 'col': position['x']}
        try:
            scope_data = client.transform(position, scope_data, camera_data)
        except calibrationclient.NoMatrixCalibrationError, e:
            raise CalibrationError(e)
        return scope_data[move_type]

    def setPosition(self, move_type, position):
        position = self.getParameterPosition(move_type, position)
        initializer = {move_type: position}
        position = data.ScopeEMData(initializer=initializer)
        self.instrument.setData(position)
        return position[move_type]

    def getDefocus(self):
        return self.instrument.tem.Defocus

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

    def removeStageAlphaBacklash(self, tilts, preset_name, target, emtarget):
        if len(tilts) < 2:
            raise ValueError

        delta = math.radians(5.0)

        if tilts[1] - tilts[0] > 0:
            alpha = tilts[0] - delta
        else:
            alpha = tilts[0] + delta

        self.instrument.tem.StagePosition = {'a': alpha}

        self.instrument.tem.StagePosition = {'a': tilts[0]}

        #self.driftDetected(preset_name, emtarget, None)
        target = self.adjustTargetForDrift(target, force=True)
        emtarget = self.targetToEMTargetData(target)

        self.presetsclient.toScope(preset_name, emtarget)
        current_preset = self.presetsclient.getCurrentPreset()
        if current_preset['name'] != preset_name:
            raise RutimeError('error setting preset \'%s\'' % preset_name)

        return target, emtarget

