import scipy
import scipy.linalg
import scipy.linalg.basic
import scipy.optimize

class Prediction(object):
    def __init__(self):
        self.reset()

    def reset(self):
        self.tilts = []
        self.v_shifts = []
        self.x = [0, 0, 0, 0, 0, 0]

    def addShift(self, tilt, shift):
        self.tilts.append(tilt)
        v_shift = scipy.array((shift['x'], shift['y'], 0), scipy.Float)
        self.v_shifts.append(v_shift)

    def predict(self, tilt):
        if not self.tilts:
            return None
        x0, y0, z0 = model(self.x, tiltMatrices([self.tilts[0]]))[0]
        x, y, z = model(self.x, tiltMatrices([tilt]))[0]
        x = float(x)
        y = float(y)
        z = float(z) - float(z0)
        theta = self.x[0]
        return {'x': x, 'y': y, 'z': z, 'theta': theta}

    def calculate(self):
        n = len(self.tilts)
        if n >= 6:
            x = self.x
        elif n >= 3:
            x = [self.x[0], self.x[1], self.x[3]]
        elif n >= 2:
            x = [self.x[0], self.x[3]]
        elif n >= 1:
            x = [self.x[3]]
        else:
            return self.x
        x = leastSquares(x, self.tilts, self.v_shifts)
        n = len(x)
        if n == 6:
            self.x = x
        elif n == 3:
            self.x[0] = x[0]
            self.x[1] = x[1]
            self.x[3] = x[2]
        elif n == 2:
            self.x[1] = x[0]
            self.x[3] = x[1]
        elif n == 1:
            self.x[1] = x[0]
        return self.x

def leastSquares(x, tilts, v_shifts):
    m_tilts = tiltMatrices(tilts)
    args = (m_tilts, v_shifts)
    try:
        result = scipy.optimize.leastsq(residuals, x, args=args, full_output=1)
    except scipy.linalg.basic.LinAlgError:
        result = scipy.optimize.leastsq(residuals, x, args=args, full_output=0)
    try:
        x = list(result[0])
    except TypeError:
        x = [result[0]]
    return x

def tiltMatrices(tilts):
    m_tilts = []
    for tilt in tilts:
        m_tilt = scipy.identity(3, scipy.Float)
        m_tilt[0, 0] = scipy.cos(tilt)
        m_tilt[0, 2] = scipy.sin(tilt)
        m_tilt[2, 0] = -scipy.sin(tilt)
        m_tilt[2, 2] = scipy.cos(tilt)
        m_tilts.append(m_tilt)
    return m_tilts

def getParameters(x):
    m_stage = scipy.identity(3, scipy.Float)
    v_specimen = scipy.zeros(3, scipy.Float)
    v_optical_axis = scipy.zeros(3, scipy.Float)
    
    n = len(x)
    if n == 6:
        cg = scipy.cos(x[0])
        sg = scipy.sin(x[0])
        m_stage[0, 0] = cg
        m_stage[0, 1] = -sg
        m_stage[1, 0] = sg
        m_stage[1, 1] = cg
        v_specimen[0] = x[1]
        v_specimen[1] = x[2]
        v_specimen[2] = x[3]
        v_optical_axis[0] = x[4]
        v_optical_axis[1] = x[5]
    elif n == 3:
        cg = scipy.cos(x[0])
        sg = scipy.sin(x[0])
        m_stage[0, 0] = cg
        m_stage[0, 1] = -sg
        m_stage[1, 0] = sg
        m_stage[1, 1] = cg
        v_specimen[0] = x[1]
        v_specimen[2] = x[2]
    elif n == 2:
        v_specimen[0] = x[0]
        v_specimen[2] = x[1]
    elif n == 1:
        v_specimen[0] = x[0]

    return m_stage, v_specimen, v_optical_axis

def model(x, m_tilts):
    m_stage, v_specimen, v_optical_axis = getParameters(x)
    v_shifts = []
    for m_tilt in m_tilts:
        v_shift = scipy.dot(m_stage, scipy.dot(m_tilt, v_specimen))
        v_shift -= v_optical_axis
        v_shifts.append(v_shift)
    return v_shifts

def residuals(x, m_tilts, v_shifts):
    v_estimate = model(x, m_tilts)
    n = len(m_tilts)
    result = scipy.zeros(n, scipy.Float)
    for i in range(n):
        for j in range(2):
            result[i] += (v_shifts[i][j] - v_estimate[i][j])**2
    return result**0.5

