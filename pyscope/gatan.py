#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import ccdcamera
import sys
import numpy
import time

try:
    import pythoncom
    import pywintypes
    import win32com.client
    import comarray
except ImportError:
    pass

class Gatan(ccdcamera.CCDCamera):
    name = 'Gatan'
    def __init__(self):
        ccdcamera.CCDCamera.__init__(self)
        self.unsupported = []

        self.cameraid = 0

        pythoncom.CoInitializeEx(pythoncom.COINIT_MULTITHREADED)
        try:
            self.camera = win32com.client.dynamic.Dispatch('TecnaiCCD.GatanCamera.2')
        except pywintypes.com_error, e:
            raise RuntimeError('unable to initialize Gatan interface')

        self.camerasize = self._getCameraSize()

        self.binning = {'x': self.camera.Binning, 'y': self.camera.Binning}
        self.offset = {'x': self.camera.CameraLeft, 'y': self.camera.CameraTop}
        self.dimension = {'x': self.camera.CameraRight - self.camera.CameraLeft,
                          'y': self.camera.CameraBottom - self.camera.CameraTop}
        self.exposuretype = 'normal'

        if not self.getRetractable():
            self.unsupported.append('getInserted')
            self.unsupported.append('setInserted')

        self.script_functions = [
            ('AFGetSlitState', 'getEnergyFilter'),
            ('AFSetSlitState', 'setEnergyFilter'),
            ('AFGetSlitWidth', 'getEnergyFilterWidth'),
            ('AFSetSlitWidth', 'setEnergyFilterWidth'),
            ('AFDoAlignZeroLoss', 'alignEnergyFilterZeroLossPeak'),
        ]

        for name, method_name in self.script_functions:
            if not self.hasScriptFunction(name):
                self.unsupported.append(method_name)

    def __getattribute__(self, attr_name):
        if attr_name in object.__getattribute__(self, 'unsupported'):
            raise AttributeError('attribute not supported')
        return object.__getattribute__(self, attr_name)

    def getOffset(self):
        return dict(self.offset)

    def setOffset(self, value):
        self.offset = dict(value)

    def getDimension(self):
        return dict(self.dimension)

    def setDimension(self, value):
        self.dimension = dict(value)

    def getBinning(self):
        return dict(self.binning)

    def setBinning(self, value):
        if value['x'] != value['y']:
            raise ValueError('multiple binning dimesions not supported')
        self.binning = dict(value)

    def getExposureTime(self):
        return int(self.camera.ExposureTime*1000)

    def setExposureTime(self, value):
        self.camera.ExposureTime = float(value)/1000.0

    def getExposureTypes(self):
        return ['normal', 'dark']

    def getExposureType(self):
        return self.exposuretype

    def setExposureType(self, value):
        if value not in ['normal', 'dark']:
            raise ValueError('invalid exposure type')
        self.exposuretype = value

    def _getImage(self):
        try:
            self.camera.Binning = self.binning['x']
            self.camera.CameraLeft = self.offset['x']
            self.camera.CameraTop = self.offset['y']
            self.camera.CameraRight = self.dimension['x'] + self.camera.CameraLeft
            self.camera.CameraBottom = self.dimension['y'] + self.camera.CameraTop
        except pywintypes.com_error, e:
            raise ValueError('invalid image dimensions')
        if self.getExposureType() == 'dark':
            if False:
            #if self.getRetractable():
                if self.getInserted():
                    self.setInserted(False)

                    image = comarray.call(self.camera, 'AcquireRawImage')

                    self.setInserted(True)
                    return image
            else:
                exposuretime = self.getExposureTime()
                self.setExposureTime(0)
                image = comarray.call(self.camera, 'AcquireRawImage')
                self.setExposureTime(exposuretime)
                return image
        try:
            image = comarray.call(self.camera, 'AcquireRawImage')
            return image
        except pywintypes.com_error, e:
            raise ValueError('invalid image dimensions')

    def getCameraSize(self):
        return self.camerasize

    def getPixelSize(self):
        x, y = self.camera.GetCCDPixelSize(self.cameraid)
        return {'x': x, 'y': y}

    def getAcquiring(self):
        if self.camera.IsAcquiring:
            return True
        else:
            return False

    def getSpeed(self):
        return self.camera.Speed

    def setSpeed(self, value):
        try:
            self.camera.Speed = value
        except pywintypes.com_error, e:
            raise ValueError('invalid speed')

    def getRetractable(self):
        if self.camera.IsRetractable:
            return True
        else:
            return False

    def setInserted(self, value):
        inserted = self.getInserted()
        if not inserted and value:
            self.camera.Insert()
        elif inserted and not value:
            self.camera.Retract()
        else:
            return
        time.sleep(5)

    def getInserted(self):
        if self.camera.IsInserted:
            return True
        else:
            return False

    def _getCameraSize(self):
        binning = self.camera.Binning
        left = self.camera.CameraLeft
        right = self.camera.CameraRight
        top = self.camera.CameraTop
        bottom = self.camera.CameraBottom

        self.camera.CameraLeft = 0
        self.camera.CameraTop = 0

        size = {}
        for i in ['CameraRight', 'CameraBottom']:
            for j in [4096, 2048, 1024]:
                try:
                    setattr(self.camera, i, j)
                except:
                    continue
                try:
                    setattr(self.camera, i, j + 1)
                except:
                    size[i] = j
                    break
            if i not in size:
                j = 0
                while True:
                    try:
                        setattr(self.camera, i, j)
                        j += 1
                    except:
                        break
                size[i] = j - 1
        self.camera.Binning = binning
        self.camera.CameraLeft = left
        self.camera.CameraRight = right
        self.camera.CameraTop = top
        self.camera.CameraBottom = bottom
        return {'x': size['CameraRight'], 'y': size['CameraBottom']}

    def hasScriptFunction(self, name):
        script = 'if(DoesFunctionExist("%s")) Exit(1.0) else Exit(-1.0)'
        script %= name
        result = self.camera.ExecuteScript(script)
        return result > 0.0

    def getEnergyFiltered(self):
        method_names = [
            'getEnergyFilter',
            'setEnergyFilter',
            'getEnergyFilterWidth',
            'setEnergyFilterWidth',
            'alignEnergyFilterZeroLossPeak',
        ]

        for method_name in method_names:
            if not hasattr(self, method_name):
                return False
        return True

    def getEnergyFilter(self):
        script = 'if(IFCGetSlitIn()) Exit(1.0) else Exit(-1.0)'
        result = self.camera.ExecuteScript(script)
        return result > 0.0

    def setEnergyFilter(self, value):
        script = 'IFCSetSlitIn(%d)'
        if value:
            script %= 1
        else:
            script %= 0
        self.camera.ExecuteScript(script)

    def getEnergyFilterWidth(self):
        script = 'Exit(AFGetSlitWidth())'
        result = self.camera.ExecuteScript(script)
        return result

    def setEnergyFilterWidth(self, value):
        script = 'if(AFSetSlitWidth(%f)) Exit(1.0) else Exit(-1.0)'
        script %= value
        result = self.camera.ExecuteScript(script)
        if result < 0.0:
            raise RuntimeError('unable to set energy filter width')

    def alignEnergyFilterZeroLossPeak(self):
        script = 'if(AFDoAlignZeroLoss()) Exit(1.0) else Exit(-1.0)'
        result = self.camera.ExecuteScript(script)
        if result < 0.0:
            raise RuntimeError('unable to align energy filter zero loss peak')

