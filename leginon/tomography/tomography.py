import math
import threading
import calibrationclient
import data
import event
import acquisition
import gui.wx.tomography.Tomography
import collection
import tilts
import exposure
import prediction
import time

class CalibrationError(Exception):
    pass

class Tomography(acquisition.Acquisition):
    eventinputs = acquisition.Acquisition.eventinputs
    eventoutputs = acquisition.Acquisition.eventoutputs + \
                    [event.AlignZeroLossPeakPublishEvent,
                        event.MeasureDosePublishEvent]

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
        'equally sloped': False,
        'equally sloped n': 8,
        'xcf bin': 1,
        'run buffer cycle': True,
        'align zero loss peak': True,
        'measure dose': True,
        'dose': 200.0,
        'min exposure': None,
        'max exposure': None,
        'mean threshold': 100.0,
        'collection threshold': 90.0,
        'tilt pause time': 1.0,
        'measure defocus': False,
        'integer': False,
        'intscale': 10,
        'pausegroup': False,
    }

    def __init__(self, *args, **kwargs):
        acquisition.Acquisition.__init__(self, *args, **kwargs)
        self.calclients['pixel size'] = \
                calibrationclient.PixelSizeCalibrationClient(self)
        self.calclients['beam tilt'] = \
                calibrationclient.BeamTiltCalibrationClient(self)
        self.btcalclient = self.calclients['beam tilt'] 

        self.tilts = tilts.Tilts()
        self.exposure = exposure.Exposure()
        self.prediction = prediction.Prediction()
        self.loadPredictionInfo()

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
            self.tilts.update(equally_sloped=self.settings['equally sloped'],
                              min=math.radians(self.settings['tilt min']),
                              max=math.radians(self.settings['tilt max']),
                              start=math.radians(self.settings['tilt start']),
                              step=math.radians(self.settings['tilt step']),
                              n=self.settings['equally sloped n'])
        except ValueError, e:
            self.logger.warning('Tilt parameters invalid: %s.' % e)
        else:
            n = sum([len(tilts) for tilts in self.tilts.getTilts()])
            self.logger.info('%d tilt angle(s) for series.' % n)

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

    def acquire(self, presetdata, emtarget=None, attempt=None, target=None):
        self.moveAndPreset(presetdata, emtarget)

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
        collect.prediction = self.prediction

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
        position = {'row': position['y'], 'col': -position['x']}
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
    '''
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
    '''
    def removeStageAlphaBacklash(self, tilts, preset_name, target, emtarget):
        if len(tilts) < 2:
            raise ValueError

        delta = math.radians(5.0)
        n = 5
        increment = delta/n

        if tilts[1] - tilts[0] > 0:
            sign = -1
        else:
            sign = 1

        alpha = tilts[0] + sign*delta

        self.instrument.tem.StagePosition = {'a': alpha}

        time.sleep(1.0)

        for i in range(n):
            alpha -= sign*increment
            self.instrument.tem.StagePosition = {'a': alpha}
            time.sleep(1.0)

        #self.driftDetected(preset_name, emtarget, None)
        target = self.adjustTargetForDrift(target, drifted=True)
        emtarget = self.targetToEMTargetData(target)

        self.presetsclient.toScope(preset_name, emtarget)
        current_preset = self.presetsclient.getCurrentPreset()
        if current_preset['name'] != preset_name:
            raise RutimeError('error setting preset \'%s\'' % preset_name)

        return target, emtarget

    def loadPredictionInfo(self):
        initializer = {
            'session': self.session,
        }
        query_data = data.TiltSeriesData(initializer=initializer)
        results = self.research(query_data)
        results.reverse()

        keys = []
        settings = {}
        positions = {}
        for result in results:
            key = result.dbid
            keys.append(key)
            settings[key] = result
            positions[key] = []

        initializer = {
            'session': self.session,
        }
        query_data = data.TomographyPredictionData(initializer=initializer)
        results = self.research(query_data)
        results.reverse()

        for result in results:
            image = result.special_getitem('image', True, readimages=False)
            tilt_series = image['tilt series']
            tilt = image['scope']['stage position']['a']
            position = result['position']
            positions[tilt_series.dbid].append((tilt, position))

        for key in keys:
            start = settings[key]['tilt start']
            self.prediction.newTiltSeries()
            for tilt, position in positions[key]:
                if round(tilt, 3) == round(start, 3):
                    self.prediction.newTiltGroup()
                self.prediction.addPosition(tilt, position)

        n_groups = len(self.prediction.tilt_series_list)
        n_points = 0
        for tilt_series in self.prediction.tilt_series_list:
            for tilt_group in tilt_series.tilt_groups:
                n_points += len(tilt_group)
        m = 'Loaded %d points from %d previous series' % (n_points, n_groups)
        self.logger.info(m)

    def alignZeroLossPeak(self, preset_name):
        request_data = data.AlignZeroLossPeakData()
        request_data['session'] = self.session
        request_data['preset'] = preset_name
        self.publish(request_data, database=True, pubevent=True, wait=True)

    def measureDose(self, preset_name):
        request_data = data.MeasureDoseData()
        request_data['session'] = self.session
        request_data['preset'] = preset_name
        self.publish(request_data, database=True, pubevent=True, wait=True)

    def processTargetData(self, *args, **kwargs):
        preset_name = self.settings['preset order'][-1]
        if self.settings['align zero loss peak']:
            self.alignZeroLossPeak(preset_name)
        if self.settings['measure dose']:
            self.measureDose(preset_name)
        acquisition.Acquisition.processTargetData(self, *args, **kwargs)

    def measureDefocus(self):
        beam_tilt = 0.01
        stig = False
        correct_tilt = True
        correlation_type = 'phase'
        settle = 0.5
        image0 = None

        args = (beam_tilt, stig, correct_tilt, correlation_type, settle, image0)
        try:
            result = self.calclients['beam tilt'].measureDefocusStig(*args)
        except calibrationclient.NoMatrixCalibrationError, e:
            self.logger.error('Measurement failed without calibration: %s' % e)
            return None
        delta_defocus = result['defocus']
        fit = result['min']
        return delta_defocus, fit

