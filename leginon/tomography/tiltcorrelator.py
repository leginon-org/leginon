import math
import correlator
import peakfinder
import numarray
import scipy.ndimage

class TiltCorrelator(object):
    def __init__(self, binning, tilt_axis):
        self.reset()
        from UCSFTomo import ccf2d
        self.correlation = ccf2d.Correlation()
        self.setBinning(binning)
        self.setTiltAxis(tilt_axis)

    def setBinning(self, binning):
        self.binning = binning
        self.correlation.setBinning(self.binning)

    def setTiltAxis(self, tilt_axis):
        self.tilt_axis = tilt_axis
        self.correlation.setTiltAxis(math.degrees(self.tilt_axis))

    def reset(self):
        self.shift = {'x':0, 'y':0}
        self.image = None
        self.tilt = None

    def correlate(self, image, tilt):
        if self.image is None and self.tilt is None:
            self.image = image
            self.tilt = tilt
            return
        self.correlation.setAngles(math.degrees(self.tilt), math.degrees(tilt))
        correlation_image = self.correlation.doIt(self.image, image)
        shift = {}
        shift['x'] = self.shift['x'] + self.correlation.fShiftX
        shift['y'] = self.shift['y'] - self.correlation.fShiftY
        self.shift = self.unstretch(self.tilt, tilt, shift)

        return correlation_image

    def getShift(self, raw):
        if raw:
            shift = {}
            shift['y'] = self.correlation.fShiftY
            shift['x'] = self.correlation.fShiftX
        else:
            shift = self.shift.copy()
        return shift

    def unstretch(self, tilt1, tilt2, shift):
        cos_tilt1 = math.cos(tilt1)
        cos_tilt2 = math.cos(tilt2)
        stretch = abs(cos_tilt2/cos_tilt1)
        if stretch > 1.0:
            stretch = 1.0/stretch

        cos_tilt_axis = math.cos(self.tilt_axis)
        sin_tilt_axis = math.sin(self.tilt_axis)

        # TOOD: make matrix
        a11 = 1 + (stretch - 1)*cos_tilt_axis*cos_tilt_axis
        a22 = stretch + (1 - stretch)*cos_tilt_axis*cos_tilt_axis
        a12 = (1 - stretch)*sin_tilt_axis*cos_tilt_axis
        a21 = a12

        result = {}
        result['x'] = a11*shift['x'] + a12*shift['y']
        result['y'] = a21*shift['x'] + a22*shift['y']

        return result

class Correlator(object):
    def __init__(self, binning, tilt_axis):
        self.correlation = correlator.Correlator()
        self.peakfinder = peakfinder.PeakFinder()
        self.reset()
        self.setBinning(binning)

    def setBinning(self, binning):
        pass

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

    def correlate(self, image, tilt):
        # pad for now (not enough time to not be lazy)
        padded_image = numarray.zeros(image.shape, image.type())
        image = scipy.ndimage.zoom(image, 0.5)
        row = (padded_image.shape[0] - image.shape[0])/2
        column = (padded_image.shape[1] - image.shape[1])/2
        padded_image[row:row + image.shape[0], column:column + image.shape[1]] = image
        self.correlation.insertImage(padded_image)
        try:
            pc = self.correlation.phaseCorrelate()
        except correlator.MissingImageError:
            return

        #peak = self.peakfinder.subpixelPeak(newimage=pc)
        peak = self.peakfinder.pixelPeak(newimage=pc)
        rows, columns = self.peak2shift(peak, pc.shape)

        rows *= 2
        columns *= 2

        self.raw_shift = {'x': columns, 'y': rows}

        self.shift['x'] += self.raw_shift['x']
        self.shift['y'] -= self.raw_shift['y']

        self.swapQuadrants(pc)

        return pc

    def getShift(self, raw):
        if raw:
            shift = self.raw_shift.copy()
        else:
            shift = self.shift.copy()
        return shift

if __name__ == '__main__':
    import numarray.random_array
    _correlator = Correlator(None, None)

    size = 16

    offset = (512 - 64, 512 - 64)
    image = numarray.random_array.random((512, 512))
    image[offset[0]:offset[0] + size, offset[1]:offset[1] + size] += 1
    _correlator.correlate(image, None)

    offset = (64, 64)
    image = numarray.random_array.random((512, 512))
    image[offset[0]:offset[0] + size, offset[1]:offset[1] + size] += 1
    _correlator.correlate(image, None)

    print _correlator.getShift(True)

