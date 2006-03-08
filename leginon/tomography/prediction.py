import math
#import numarray
#import numarray.linear_algebra
import numpy
import scipy.optimize

def RM(theta):
    sin = math.sin(theta)
    cos = math.cos(theta)
    return [[cos, -sin],
            [sin,  cos]]

class Prediction(object):
    def __init__(self):
        self.beam_position = {'x':0.0, 'y':0.0, 'z':0.0}
        #self.prediction = Position()
        self.prediction = LeastSquares()

    def reset(self):
        self.beam_position = {'x':0.0, 'y':0.0, 'z':0.0}

        #self.prediction.reset()

    def refineAll(self, tilt, shift):
        # tilt is in radians
        feature = {
            'x': self.beam_position['x'] + shift['x'],
            'y': self.beam_position['y'] + shift['y'],
        }

        self.prediction.addShift(tilt, feature)
        self.prediction.calculate()

    def predict(self, tilt):
        # tilt is in radians
        prediction = self.prediction.predict(tilt)

        shift = {}
        for axis in ['x', 'y', 'z']:
            shift[axis] = prediction[axis] - self.beam_position[axis]
            self.beam_position[axis] = prediction[axis]

        #n, t = self.prediction.calculateNT(shift['x'], shift['y'])
        #shift['n'], shift['t'] = n, t

        return prediction, shift

class LeastSquares(object):
    def __init__(self):
        self.a = None
        self.v_measured = None
        self.p = None

    def reset(self):
        self.a = None
        self.v_measured = None
        self.p = None

    def addShift(self, tilt, shift):
        if self.a is None:
            self.a = numpy.zeros(1, numpy.Float)
        else:
            self.a = numpy.resize(self.a, self.a.shape[0] + 1)
        self.a[-1] = tilt

        if self.v_measured is None:
            self.v_measured = numpy.zeros((1, 2), numpy.Float)
        else:
            self.v_measured = numpy.resize(self.v_measured,
                      (self.v_measured.shape[0] + 1, self.v_measured.shape[1]))
        self.v_measured[-1, 0] = shift['x']
        self.v_measured[-1, 1] = shift['y']

        n = self.a.shape[0]
        if n == 2:
            self.p = numpy.zeros(2, numpy.Float)
        elif n == 3:
            p = self.p
            self.p = numpy.zeros(3, numpy.Float)
            self.p[0] = p[0]
            self.p[1] = p[1]
        elif n == 16:
            p = self.p
            self.p = numpy.zeros(16, numpy.Float)
            cos_t = numpy.cos(p[2])
            sin_t = numpy.sin(p[2])
            self.p = [ cos_t, sin_t, 0.0,
                      -sin_t, cos_t, 0.0,
                         0.0,   0.0, 1.0,
                        p[0],   0.0, p[1]]

    def predict(self, tilt):
        x, y, z = self.model(numpy.array([tilt], numpy.Float))[0]
        x = float(x)
        y = float(y)
        z = float(z)
        return {'x': x, 'y': y, 'z': z, 'theta': 0.0}

    def calculate(self):
        if self.p is None:
            return
        result = scipy.optimize.leastsq(self.residuals,
                                        self.p, args=(self.a, self.v_measured))
        self.p = result[0]

    def parameters(self, p):
        affine = numpy.identity(3, numpy.Float)
        v_object = numpy.zeros(3, numpy.Float)
    
        if p is None:
            n = 0
        else:
            n = len(p)
        if n == 12:
            affine[0] = p[0:3]
            affine[1] = p[3:6]
            affine[2] = p[6:9]
            v_object = p[9:12]
        elif n == 3:
            t = p[2]
            cos_t = numpy.cos(t)
            sin_t = numpy.sin(t)
            affine[0, 0] = cos_t
            affine[0, 1] = sin_t
            affine[1, 0] = -sin_t
            affine[1, 1] = cos_t
            v_object[0] = p[0]
            v_object[2] = p[1]
        elif n == 2:
            v_object[0] = p[0]
            v_object[2] = p[1]
    
        return affine, v_object

    def residuals(self, p, a, v_measured):
        affine, v_object = self.parameters(p)
    
        cos_a = numpy.cos(a)
        sin_a = numpy.sin(a)
    
        rotation_a = numpy.identity(3, numpy.Float)
        result = numpy.zeros(v_measured.shape, numpy.Float)
        for i in range(v_measured.shape[0]):
            rotation_a[0, 0] = cos_a[i]
            rotation_a[0, 2] = -sin_a[i]
            rotation_a[2, 0] = sin_a[i]
            rotation_a[2, 2] = cos_a[i]
            transform = numpy.dot(affine, rotation_a)
            result[i] = numpy.dot(transform, v_object)[:result.shape[1]]
    
        error = v_measured - result
        return numpy.hypot(error[:, 0], error[:, 1])

    def model(self, a):
        result = numpy.zeros((a.shape[0], 3), numpy.Float)

        affine, v_object = self.parameters(self.p)
    
        cos_a = numpy.cos(a)
        sin_a = numpy.sin(a)
    
        rotation_a = numpy.identity(3, numpy.Float)
        for i in range(a.shape[0]):
            rotation_a[0, 0] = cos_a[i]
            rotation_a[0, 2] = -sin_a[i]
            rotation_a[2, 0] = sin_a[i]
            rotation_a[2, 2] = cos_a[i]
            transform = numpy.dot(affine, rotation_a)
            result[i] = numpy.dot(transform, v_object)
    
        return result

class Position(object):
    def __init__(self):
        self.fit_points = 5
        self.shifts = []
        self.theta = 0.0
        self.n_solution = 0.0

    def reset(self):
        self.shifts.reverse()

    def addShift(self, tilt, shift):
        # tilt in radians
        self.shifts.append((tilt, shift))

    def calculateNT(self, x, y):
        m = RM(-self.theta)
        n, t = numarray.matrixmultiply(m, [x, y])
        return n, t

    def calculateXY(self, n, t):
        m = RM(self.theta)
        x, y = numarray.matrixmultiply(m, [n, t])
        return x, y

    def calculateZ(self, tilt, n):
        z = n*math.tan(-tilt)
        return z

    def getN(self, tilt):
        n = self.n_solution*tilt
        return n

    def getT(self):
        if self.shifts:
            tilt, position = self.shifts[-1]
            n, t = self.calculateNT(position['x'], position['y'])
        else:
            t = 0.0
        return t

    def predict(self, tilt):
        n = self.getN(tilt)
        t = self.getT()
        x, y = self.calculateXY(n, t)
        z = self.calculateZ(tilt, n)
        return {'x': x, 'y': y, 'z': z, 'n': n, 't': t, 'theta': self.theta}

    def calculate(self):
        self.theta = self.calculateTheta()
        self.n_solution = self.calculateN()

    def calculateTheta(self):
        if len(self.shifts) > self.fit_points:
            start = -self.fit_points
        else:
            start = 0
        shifts = self.shifts[start:]

        if len(shifts) < 2:
            return self.theta

        rows = len(shifts)

        a = numarray.zeros((rows, 2), numarray.Float)
        b = numarray.zeros((rows, 1), numarray.Float)
        for i, (tilt, shift) in enumerate(shifts):
            a[i, 0] = shift['x']
            a[i, 1] = 1.0
            b[i, 0] = shift['y']

        solution = numarray.linear_algebra.linear_least_squares(a, b)
        theta = solution[0][0, 0]
        theta = math.atan2(1.0, solution[0][0, 0])
        theta += math.pi/2
        theta %= math.pi
        theta -= math.pi/2

        return theta

    def calculateN(self):
        if len(self.shifts) > self.fit_points:
            start = -self.fit_points
        else:
            start = 0
        shifts = self.shifts[start:]

        if len(shifts) < 2:
            return self.n_solution

        rows = len(shifts)

        a = numarray.zeros((rows, 1), numarray.Float)
        b = numarray.zeros((rows, 1), numarray.Float)
        for i, (tilt, shift) in enumerate(shifts):
            a[i, 0] = tilt
            n, t = self.calculateNT(shift['x'], shift['y'])
            b[i, 0] = n

        solution = numarray.linear_algebra.linear_least_squares(a, b)
        slope = solution[0][0, 0]

        return slope

if __name__ == '__main__':
    p = Position()
    p = LeastSquares()

    p.calculate()
    print p.predict(math.radians(0))

    for i in range(8):
        p.addShift(math.radians(i), {'x': i, 'y': i + 0.1234})

    p.calculate()
    print p.predict(math.radians(-25))
    print p.predict(math.radians(25))

