import math
import scipy
import scipy.optimize

class Prediction(object):
    def __init__(self):
        self.beam_position = {'x':0.0, 'y':0.0, 'z':0.0}
        self.prediction = LeastSquares()

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
            self.a = scipy.zeros(1, scipy.Float)
        else:
            self.a = scipy.resize(self.a, (self.a.shape[0] + 1,))
        self.a[-1] = tilt

        if self.v_measured is None:
            self.v_measured = scipy.zeros((1, 2), scipy.Float)
        else:
            self.v_measured = scipy.resize(self.v_measured,
                      (self.v_measured.shape[0] + 1, self.v_measured.shape[1]))
        self.v_measured[-1, 0] = shift['x']
        self.v_measured[-1, 1] = shift['y']

        n = self.a.shape[0]
        '''
        if n >= 16:
            p = self.p
            self.p = scipy.zeros(16, scipy.Float)
            cos_t = scipy.cos(p[2])
            sin_t = scipy.sin(p[2])
            self.p = [ cos_t, sin_t, 0.0,
                      -sin_t, cos_t, 0.0,
                         0.0,   0.0, 1.0,
                        p[0],   0.0, p[1]]
        elif n >= 3:
            p = self.p
            self.p = scipy.zeros(3, scipy.Float)
            self.p[1] = p[0]
            self.p[2] = p[1]
        elif n >= 2:
        '''
        if n >= 2:
            self.p = scipy.zeros(2, scipy.Float)

    def predict(self, tilt):
        x, y, z = self.model(scipy.array([tilt], scipy.Float))[0]
        x = float(x)
        y = float(y)
        z = float(z)
        return {'x': x, 'y': y, 'z': z, 'theta': 0.0}

    def calculate(self):
        if self.p is None:
            return
        result = scipy.optimize.leastsq(self.residuals,
                                        self.p, args=(self.a, self.v_measured),
                                        full_output=1)#, maxfev=1200)
        if result[3]:
            self.p = result[0]
            if self.p.shape[0] == 3:
                args = (self.p[0], self.p[1], math.degrees(self.p[1]))
                #print 'n0 = %g, z0 = %g, theta = %g' % args
            elif self.p.shape[0] == 2:
                args = (self.p[0], math.degrees(self.p[1]))
                #print 'z0 = %g, theta = %g' % args
        else:
            #print result[4]
            pass

    def parameters(self, p):
        affine = scipy.identity(3, scipy.Float)
        v_object = scipy.zeros(3, scipy.Float)
    
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
            v_object[0] = p[0]
            v_object[2] = p[1]
            t = p[2]
            #if t > math.pi:
            #    t = math.pi
            #elif t < -math.pi:
            #    t = -math.pi
            cos_t = scipy.cos(t)
            sin_t = scipy.sin(t)
            affine[0, 0] = cos_t
            affine[0, 1] = sin_t
            affine[1, 0] = -sin_t
            affine[1, 1] = cos_t
        elif n == 2:
            v_object[2] = p[0]
            t = p[1]
            if t > math.pi:
                t = math.pi
            elif t < -math.pi:
                t = -math.pi
            cos_t = scipy.cos(t)
            sin_t = scipy.sin(t)
            affine[0, 0] = cos_t
            affine[0, 1] = sin_t
            affine[1, 0] = -sin_t
            affine[1, 1] = cos_t
        elif n == 0:
            pass
        else:
            raise ValueError
    
        return affine, v_object

    def residuals(self, p, a, v_measured):
        affine, v_object = self.parameters(p)
    
        cos_a = scipy.cos(a)
        sin_a = scipy.sin(a)
    
        rotation_a = scipy.identity(3, scipy.Float)
        result = scipy.zeros(v_measured.shape, scipy.Float)
        for i in range(v_measured.shape[0]):
            rotation_a[0, 0] = cos_a[i]
            rotation_a[0, 2] = -sin_a[i]
            rotation_a[2, 0] = sin_a[i]
            rotation_a[2, 2] = cos_a[i]
            transform = scipy.dot(affine, rotation_a)
            result[i] = scipy.dot(transform, v_object)[:result.shape[1]]
    
        error = v_measured - result
        return scipy.hypot(error[:, 0], error[:, 1])

    def model(self, a):
        result = scipy.zeros((a.shape[0], 3), scipy.Float)

        affine, v_object = self.parameters(self.p)
    
        cos_a = scipy.cos(a)
        sin_a = scipy.sin(a)
    
        rotation_a = scipy.identity(3, scipy.Float)
        for i in range(a.shape[0]):
            rotation_a[0, 0] = cos_a[i]
            rotation_a[0, 2] = -sin_a[i]
            rotation_a[2, 0] = sin_a[i]
            rotation_a[2, 2] = cos_a[i]
            transform = scipy.dot(affine, rotation_a)
            result[i] = scipy.dot(transform, v_object)
    
        return result

if __name__ == '__main__':
    p = LeastSquares()

    p.calculate()
    print p.predict(math.radians(0))

    for i in range(8):
        p.addShift(math.radians(i), {'x': i, 'y': i + 0.1234})

    p.calculate()
    print p.predict(math.radians(-25))
    print p.predict(math.radians(25))

