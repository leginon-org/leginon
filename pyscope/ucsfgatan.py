#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import ccdcamera
import numarray
import re
import sys

try:
    import pythoncom
    import pywintypes
    import win32com.client
    try:
        import NumSafeArray
    except ImportError:
        from pyScope import NumSafeArray
except ImportError:
    pass

class UCSFGatan(ccdcamera.CCDCamera):
    name = 'UCSF Gatan'
    def __init__(self):
        ccdcamera.CCDCamera.__init__(self)

        pythoncom.CoInitializeEx(pythoncom.COINIT_MULTITHREADED)
        try:
            self.camera = win32com.client.dynamic.Dispatch('UcsfCCD.GatanCamera')
        except pywintypes.com_error, e:
            raise RuntimeError('unable to initialize UCSF Gatan interface')

        self.cameratypes = ('CCD', 'GIF')
        self.cameratype = self.cameratypes[0]

        try:
            self.loadConfigFile()
        except IOError:
            pass

        self.binning = {'x': self.camera.BinningX, 'y': self.camera.BinningY}
        self.offset = {'x': self.camera.ImageLeft, 'y': self.camera.ImageTop}
        self.dimension = {'x': self.camera.ImageRight - self.camera.ImageLeft,
                          'y': self.camera.ImageBottom - self.camera.ImageTop}
        self.exposuretype = 'normal'

    def loadConfigFile(self, filename='C:\\UCSF\\Tomo\\ConfigTomo.dat'):
        options = parseConfigTomo(filename)
        camerasize = {}
        for axis in ['x', 'y']:
            key = 'CCDReadout' + axis.upper()
            if key in options and isinstance(options[key], int):
                camerasize[axis] = options[key]
        if 'x' in camerasize and 'y' in camerasize:
            self.camerasize = camerasize

        self.pixelsizes = {}
        for camera in ('CCD', 'GIF'):
            try:
                mag = options[camera + 'PixelMag']
                pixelsize = options[camera + 'PixelSize']
                self.pixelsizes[camera] = float(mag)*float(pixelsize)*1e-10
            except KeyError:
                pass

    def getCameraType(self):
        return self.cameratype

    def setCameraType(self, cameratype):
        if cameratype not in self.cameratypes:
            raise ValueError('invalid camera \'%s\'' % cameratype)
        self.cameratype = cameratype

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
        self.binning = dict(value)

    def getExposureTime(self):
        return int(self.camera.Exposure*1000)

    def setExposureTime(self, value):
        self.camera.Exposure = float(value)/1000.0

    def getExposureTypes(self):
        return ['normal', 'dark']

    def getExposureType(self):
        return self.exposuretype

    def setExposureType(self, value):
        if value not in ['normal', 'dark']:
            raise ValueError('invalid exposure type')
        self.exposuretype = value

    def getImage(self):
        try:
            self.camera.BinningX = self.binning['x']
            self.camera.BinningY = self.binning['y']
            self.camera.ImageLeft = self.offset['x']
            self.camera.ImageTop = self.offset['y']
            self.camera.ImageRight = self.dimension['x'] + self.camera.ImageLeft
            self.camera.ImageBottom = self.dimension['y'] + self.camera.ImageTop
        except pywintypes.com_error, e:
            raise ValueError('invalid image dimensions')
        try:
            if self.getExposureType() == 'dark':
                return NumSafeArray.call(self.camera, 'AcquireDarkImage')
            else:
                return NumSafeArray.call(self.camera, 'AcquireRawImage')
        except pywintypes.com_error, e:
            raise ValueError('invalid image dimensions')

    def getCameraSize(self):
        if hasattr(self, 'camerasize'):
            return self.camerasize
        else:
            raise NotImplementedError

    def getPixelSize(self):
        try:
            pixelsize = self.pixelsizes[self.cameratype]
        except KeyError:
            raise ValueError('no pixel size for camera type')
        return {'x': pixelsize, 'y': pixelsize}

    def _getCameraSize(self):
        binningx = self.camera.BinningX
        binningy = self.camera.BinningY
        left = self.camera.ImageLeft
        right = self.camera.ImageRight
        top = self.camera.ImageTop
        bottom = self.camera.ImageBottom

        self.camera.BinningX = 1
        self.camera.BinningY = 1
        self.camera.ImageLeft = 0
        self.camera.ImageTop = 0

        size = {}
        for i in ['ImageRight', 'ImageBottom']:
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
        self.camera.BinningX = binningx
        self.camera.BinningX = binningy
        self.camera.ImageLeft = left
        self.camera.ImageRight = right
        self.camera.ImageTop = top
        self.camera.ImageBottom = bottom
        return {'x': size['ImageRight'], 'y': size['ImageBottom']}

    def getSlitWidth(self):
        return self.camera.SlitWidth

    def setSlitWidth(self, width):
        self.camera.SlitWidth = width

def parseConfigTomo(filename):
    fp = open(filename)

    commentre = re.compile('(?P<line>.*)#')
    valuere = re.compile(
        r'(?P<name>[^:=\s][^:=]*)'
        r'\s*([:=])\s*'
        r'(?P<value>.*)$'
    )

    options = {}
    while True:
        line = fp.readline()
        if not line:
            break
        mo = commentre.match(line)
        if mo:
            line = mo.group('line')
        mo = valuere.match(line)
        if mo:
            name, value = mo.group('name', 'value')
            name = name.strip()
            value = value.strip()
            for i in [int, float, strToBool]:
                try:
                    value = i(value)
                except ValueError:
                    pass
                else:
                    break
            options[name] = value
    fp.close()

    return options

def strToBool(s):
    if s.lower() == 'true':
        return True
    elif s.lower() == 'false':
        return False
    else:
        raise ValueError

