import copy
import ccdcamera
import numpy
import random
random.seed()

class FilmScanner(ccdcamera.CCDCamera):
    name = 'FilmScanner'
    def __init__(self):
        ccdcamera.CCDCamera.__init__(self)
        self.binning_values = {'x': [1, 2, 4, 8,16], 'y': [1, 2, 4, 8,16]}
        self.pixel_size = {'x': 7e-6, 'y': 7e-6}
        self.exposure_types = ['normal', 'dark']

        self.binning = {'x': 1, 'y': 1}
        self.offset = {'x': 0, 'y': 0}
        self.dimension = copy.copy(self.getCameraSize())
        self.exposure_time = 0.0
        self.exposure_type = 'normal'

        self.energy_filter = False
        self.energy_filter_width = 0.0

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
                if value[axis] < 0 or value[axis] >= self.getCameraSize()[axis]:
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
                if value[axis] < 1 or value[axis] > self.getCameraSize()[axis]:
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

    def _getImage(self):
        if not self.validateGeometry():
            raise ValueError('invalid image geometry')

        for axis in ['x', 'y']:
            if self.dimension[axis] % self.binning[axis] != 0:
                raise ValueError('invalid dimension/binning combination')

        columns = self.dimension['x']
        rows = self.dimension['y']
        #fake acquisition
        shape = (4, 4)
        mean = 10
        sigma = 2
        image = numpy.random.normal(mean, sigma, shape)
        return image

    def getEnergyFiltered(self):
        return True

    def getEnergyFilter(self):
        return self.energy_filter

    def setEnergyFilter(self, value):
        self.energy_filter = bool(value)

    def getEnergyFilterWidth(self):
        return self.energy_filter_width

    def setEnergyFilterWidth(self, value):
        self.energy_filter_width = float(value)

    def alignEnergyFilterZeroLossPeak(self):
        pass

    def getPixelSize(self):
        return dict(self.pixel_size)
