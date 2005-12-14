import copy
import ccdcamera
import numarray

class SimCCDCamera(ccdcamera.CCDCamera):
    name = 'SimCCDCamera'
    def __init__(self):
        ccdcamera.CCDCamera.__init__(self)
        self.camera_size = {'x': 2048, 'y': 2048}
        self.binning_values = {'x': [1, 2, 4, 8], 'y': [1, 2, 4, 8]}
        self.pixel_size = 2.5e-5
        self.exposure_types = ['normal', 'dark']

        self.binning = {'x': 1, 'y': 1}
        self.offset = {'x': 0, 'y': 0}
        self.dimension = copy.copy(self.camera_size)
        self.exposure_time = 0.0
        self.exposure_type = 'normal'

    def getBinning(self):
        return copy.copy(self.binning)

    def setBinning(self, value):
        for axis in self.binning.keys():
            try:
                if value[axis] not in self.binning_values[axis]:
                    raise ValueError('invalid binning')
            except KeyError:
                pass

        for axis in self.binning.keys():
            try:
                self.binning[axis] = value[axis]
            except KeyError:
                pass

    def getOffset(self):
        return copy.copy(self.offset)

    def setOffset(self, value):
        for axis in self.offset.keys():
            try:
                if value[axis] < 0 or value[axis] >= self.camera_size[axis]:
                    raise ValueError('invalid offset')
            except KeyError:
                pass

        for axis in self.offset.keys():
            try:
                self.offset[axis] = value[axis]
            except KeyError:
                pass

    def getDimension(self):
        return copy.copy(self.dimension)

    def setDimension(self, value):
        for axis in self.dimension.keys():
            try:
                if value[axis] < 1 or value[axis] > self.camera_size[axis]:
                    raise ValueError('invalid dimension')
            except KeyError:
                pass

        for axis in self.dimension.keys():
            try:
                self.dimension[axis] = value[axis]
            except KeyError:
                pass

    def getExposureTime(self):
        return int(self.exposure_time*1000)

    def setExposureTime(self, value):
        if value < 0:
            raise ValueError('invalid exposure time')
        self.exposure_time = float(value)/1000.0

    def getExposureTypes(self):
        return self.exposure_types

    def getExposureType(self):
        return self.exposure_type

    def setExposureType(self, value):
        if value not in self.exposure_types:
            raise ValueError('invalid exposure type')
        self.exposure_type = value

    def getCameraSize(self):
        return copy.copy(self.camera_size)

    def getImage(self):
        if not self.validateGeometry():
            raise ValueError('invalid image geometry')

        for axis in ['x', 'y']:
            if self.dimension[axis] % self.binning[axis] != 0:
                raise ValueError('invalid dimension/binning combination')

        columns = self.dimension['x']/self.binning['y']
        rows = self.dimension['y']/self.binning['y']

        shape = (rows, columns)

        if self.exposure_type == 'dark' or self.exposure_time == 0:
            return numarray.zeros(shape, numarray.Float)
        else:
            return numarray.ones(shape, numarray.Float)

