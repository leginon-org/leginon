import math
from pyami import correlator, peakfinder
import numpy
import scipy.ndimage

def hanning(size):
    border = size >> 5
    def function(m, n):
        m = abs(m - (size - 1)/2.0) - ((size + 1)/2.0 - border)
        n = abs(n - (size - 1)/2.0) - ((size + 1)/2.0 - border)
        v = numpy.where(m > n, m, n)
        v = numpy.where(v > 0, v, 0)
        return 0.5*(1 - numpy.cos(numpy.pi*v/border - numpy.pi))
    return numpy.fromfunction(function, (size, size))

class Correlator(object):
    def __init__(self, tilt_axis, correlation_binning=2):
        self.correlation = correlator.Correlator()
        self.peakfinder = peakfinder.PeakFinder()
        self.reset()
        self.setCorrelationBinning(correlation_binning)
        self.hanning = None
        self.channel = None

    def getChannel(self):
        if self.channel is None or self.channel == 1:
            return 0
        else:
            return 1

    def getCorrelationBinning(self):
        return self.correlation_binning

    def setCorrelationBinning(self, correlation_binning):
        self.correlation_binning = correlation_binning

    def setTiltAxis(self, tilt_axis):
        pass

    def reset(self):
        self.shift = {'x':0.0, 'y':0.0}
        self.raw_shift = {'x':0.0, 'y':0.0}
        self.correlation.clearBuffer()

    def peak2shift(self, peak, shape):
        shift = list(peak)
        half = shape[0] / 2.0, shape[1] / 2.0
        if peak[0] > half[0]:
            shift[0] = peak[0] - shape[0]
        if peak[1] > half[1]:
            shift[1] = peak[1] - shape[1]
        return tuple(shift)

    def swapQuadrants(self, image):
        rows, columns = image.shape
        swap = image[:rows/2, :columns/2].copy()
        image[:rows/2, :columns/2] = image[rows/2:, columns/2:]
        image[rows/2:, columns/2:] = swap
        swap = image[rows/2:, :columns/2].copy()
        image[rows/2:, :columns/2] = image[:rows/2, columns/2:]
        image[:rows/2, columns/2:] = swap

    def correlate(self, image, tilt, channel=None):
        # pad for now (not enough time to not be lazy)
        if len(image.shape) != 2 or image.shape[0] != image.shape[1]:
            raise ValueError

        padded_image = numpy.zeros(image.shape, image.dtype)
        image = scipy.ndimage.zoom(image, 1.0/self.correlation_binning)

        mean = image.mean()
        image -= mean

        if self.hanning is None or image.shape[0] != self.hanning.shape[0]:
            self.hanning = hanning(image.shape[0])
        image *= self.hanning

        row = (padded_image.shape[0] - image.shape[0])/2
        column = (padded_image.shape[1] - image.shape[1])/2
        padded_image[row:row + image.shape[0],
                     column:column + image.shape[1]] = image
        self.correlation.insertImage(padded_image)
        self.channel = channel
        try:
            pc = self.correlation.phaseCorrelate()
        except correlator.MissingImageError:
            return

        #peak = self.peakfinder.subpixelPeak(newimage=pc)
        peak = self.peakfinder.pixelPeak(newimage=pc)
        rows, columns = self.peak2shift(peak, pc.shape)


        self.raw_shift = {'x': columns, 'y': rows}

        self.shift['x'] += self.raw_shift['x']*self.correlation_binning
        self.shift['y'] -= self.raw_shift['y']*self.correlation_binning

        self.swapQuadrants(pc)

        return pc

    def getShift(self, raw):
        if raw:
            shift = self.raw_shift.copy()
        else:
            shift = self.shift.copy()
        return shift

if __name__ == '__main__':
#    import numpy.random
#    _correlator = Correlator(None, None)
#
#    size = 16
#
#    offset = (400 + 64, 400 + 64)
#    image = numpy.random.random((512, 512))
#    image[offset[0]:offset[0] + size, offset[1]:offset[1] + size] += 16
#    _correlator.correlate(image, None)
#
#    offset = (50 + 64, 50 + 64)
#    image = numpy.random.random((512, 512))
#    image[offset[0]:offset[0] + size, offset[1]:offset[1] + size] += 16
#    _correlator.correlate(image, None)
#
#    print _correlator.getShift(True)

    from pyami import mrc

    window = hanning(1024)

    mrc.write(window, 'foo.mrc')

