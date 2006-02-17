import math
import numarray
import numarray.linear_algebra

def RM(theta):
    sin = math.sin(theta)
    cos = math.cos(theta)
    return [[cos, -sin],
            [sin,  cos]]

class Prediction(object):
    def __init__(self):
        self.beam_position = {'x':0.0, 'y':0.0, 'z':0.0}
        self.prediction = Position()

    def reset(self):
        self.beam_position = {'x':0.0, 'y':0.0, 'z':0.0}

        self.prediction.reset()

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

        n, t = self.prediction.calculateNT(shift['x'], shift['y'])
        shift['n'], shift['t'] = n, t

        return prediction, shift

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

        a = numarray.zeros((rows, 1), numarray.Float)
        b = numarray.zeros((rows, 1), numarray.Float)
        for i, (tilt, shift) in enumerate(shifts):
            a[i, 0] = 1.0
            b[i, 0] = math.atan2(shift['y'], shift['x'])
            b[i, 0] += math.pi/2
            b[i, 0] %= math.pi
            b[i, 0] -= math.pi/2

        solution = numarray.linear_algebra.linear_least_squares(a, b)
        theta = solution[0][0, 0]
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

    p.calculate()
    print p.predict(math.radians(0))

    for i in range(8):
        p.addShift(math.radians(i), {'x': i, 'y': i})

    p.calculate()
    print p.predict(math.radians(-25))

