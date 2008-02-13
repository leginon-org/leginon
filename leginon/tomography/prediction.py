import scipy
import scipy.optimize
from scipy.linalg import lstsq

class TiltSeries(object):
    def __init__(self):
        self.tilt_groups = []

    def addTiltGroup(self, tilt_group):
        self.tilt_groups.append(tilt_group)

    def __len__(self):
        return len(self.tilt_groups)

    def getCurrentTiltGroup(self):
        return self.tilt_groups[-1]

class TiltGroup(object):
    def __init__(self):
        self.tilts = []
        self.xs = []
        self.ys = []

    def addTilt(self, tilt, x, y):
        self.tilts.append(tilt)
        self.xs.append(x)
        self.ys.append(y)

    def __len__(self):
        return len(self.tilts)

class Prediction(object):
    def __init__(self):
        self.tilt_series_list = []
        self.parameters = [0, 0, 0]

    def addTiltSeries(self, tilt_series):
        self.tilt_series_list.append(tilt_series)

    def newTiltSeries(self):
        if self.tilt_series_list and len(self.tilt_series_list[-1]) < 1:
            return
        tilt_series = TiltSeries()
        self.addTiltSeries(tilt_series)

    def getCurrentTiltSeries(self):
        return self.tilt_series_list[-1]

    def newTiltGroup(self):
        tilt_series = self.getCurrentTiltSeries()
        if tilt_series.tilt_groups and len(tilt_series.tilt_groups[-1]) < 1:
            return
        tilt_group = TiltGroup()
        tilt_series.addTiltGroup(tilt_group)

    def getCurrentTiltGroup(self):
        tilt_series = self.getCurrentTiltSeries()
        return tilt_series.getCurrentTiltGroup()

    def addPosition(self, tilt, position):
        tilt_group = self.getCurrentTiltGroup()
        if len(tilt_group) > 0:
            origin = {'x': tilt_group.xs[0],
                      'y': tilt_group.ys[0]}
            previous = {'x': tilt_group.xs[-1],
                        'y': tilt_group.ys[-1]}
        tilt_group.addTilt(tilt, position['x'], position['y'])

    def getCurrentParameters(self):
        return tuple(self.parameters[:2] + [self.parameters[-1]])

    def predict(self, tilt):
        tilt_series = self.getCurrentTiltSeries()
        tilt_group = self.getCurrentTiltGroup()
        n_tilt_series = len(self.tilt_series_list)
        n_tilt_groups = len(tilt_series)
        n_tilts = len(tilt_group)
        n = []
        for s in self.tilt_series_list:
            for g in s.tilt_groups:
                n.append(len(g))
        n_max = max(n)

        if n_tilts < 1:
            raise RuntimeError
        elif n_tilts < 2:
            x, y = tilt_group.xs[-1], tilt_group.ys[-1]
            z = 0.0
        # HACK: use residuals instead
        # elif n_tilts < 3 or n_max < 16:
        # calculate real z correction for all n_max
        elif n_tilts < 3:
            x, y = leastSquaresXY(tilt_group.tilts,
                                  tilt_group.xs,
                                  tilt_group.ys,
                                  tilt)
            z = 0.0
        else:
            x, y = leastSquaresXY(tilt_group.tilts,
                                  tilt_group.xs,
                                  tilt_group.ys,
                                  tilt)
            tilt_group.addTilt(tilt, x, y)

            self.calculate()

            del tilt_group.tilts[-1]
            del tilt_group.xs[-1]
            del tilt_group.ys[-1]

            x0 = tilt_group.xs[0]
            y0 = tilt_group.ys[0]
            tilt0 = tilt_group.tilts[0]
            cos_tilts = scipy.cos(scipy.array([tilt0, tilt]))
            sin_tilts = scipy.sin(scipy.array([tilt0, tilt]))
            parameters = self.getCurrentParameters()
            args_list = [(cos_tilts, sin_tilts, x0, y0, None, None)]
            result = model(parameters, args_list)
            z0 = result[-1][0][2]
            z = result[-1][-1][2] - z0

        result = {
            'x': float(x),
            'y': float(y),
            'z': float(z),
            'phi': float(self.parameters[0]),
            'optical axis': float(self.parameters[1]),
            'z0': float(self.parameters[-1]),
        }

        return result

    def model(self, tilts):
        parameters = self.getCurrentParameters()
        tilt_group = self.getCurrentTiltGroup()
        x0 = tilt_group.xs[0]
        y0 = tilt_group.ys[0]
        cos_tilts = scipy.cos(scipy.array(tilts))
        sin_tilts = scipy.sin(scipy.array(tilts))
        args_list = [(cos_tilts, sin_tilts, x0, y0, None, None)]
        result = model(parameters, args_list)
        return result[0]

    def calculate(self):
        tilt_group = self.getCurrentTiltGroup()
        if len(tilt_group) < 3:
            return
        if len(self.tilt_series_list) > 8:
            tilt_series_list = self.tilt_series_list[-8:]
        else:
            tilt_series_list = self.tilt_series_list
        self.parameters = leastSquaresModel(tilt_series_list)
        return self.parameters

def leastSquaresModel(tilt_series_list):
    parameters = [0, 0]
    args_list = []
    for tilt_series in tilt_series_list:
        for tilt_group in tilt_series.tilt_groups:
            parameters.extend([0])

            tilts = scipy.array(tilt_group.tilts)
            cos_tilts = scipy.cos(tilts)
            sin_tilts = scipy.sin(tilts)

            x0 = tilt_group.xs[0]
            y0 = tilt_group.ys[0]

            x = scipy.array(tilt_group.xs)
            y = scipy.array(tilt_group.ys)

            args_list.append((cos_tilts, sin_tilts, x0, y0, x, y))

    args = (args_list,)
    kwargs = {
        'args': args,
        #'full_output': 1,
        #'ftol': 1e-12,
        #'xtol': 1e-12,
    }
    result = scipy.optimize.leastsq(residuals, parameters, **kwargs)
    try:
        x = list(result[0])
    except TypeError:
        x = [result[0]]
    return x

def getParameters(parameters):
    phi = parameters[0]
    optical_axis = parameters[1]
    zs = scipy.array(parameters[2:], scipy.dtype('d'))
    return phi, optical_axis, zs

def model(parameters, args_list):
    phi, optical_axis, zs = getParameters(parameters)
    sin_phi = scipy.sin(phi)
    cos_phi = scipy.cos(phi)
    position_groups = []
    for i, (cos_tilts, sin_tilts, x0, y0, x, y) in enumerate(args_list):
        positions = scipy.zeros((cos_tilts.shape[0], 3), 'd')
        z = zs[i]
        # transform position, rotate, inverse transform to get rotated x, y, z
        positions[:, 0] = cos_phi*x0 + sin_phi*y0
        positions[:, 1] = -sin_phi*x0 + cos_phi*y0
        positions[:, 0] += optical_axis
        positions[:, 2] = sin_tilts*positions[:, 0] + cos_tilts*z
        positions[:, 0] = cos_tilts*positions[:, 0] - sin_tilts*z
        positions[:, 0] -= optical_axis
        x_positions = cos_phi*positions[:, 0] - sin_phi*positions[:, 1]
        y_positions = sin_phi*positions[:, 0] + cos_phi*positions[:, 1]
        positions[:, 0] = x_positions
        positions[:, 1] = y_positions
        position_groups.append(positions)
    return position_groups

def residuals(parameters, args_list):
    residuals_list = []
    position_groups = model(parameters, args_list)
    for i, positions in enumerate(position_groups):
        n = positions.shape[0]
        cos_tilts, sin_tilts, x0, y0, x, y = args_list[i]
        residuals = scipy.zeros((n, 2), scipy.dtype('d'))
        residuals[:, 0] = x
        residuals[:, 1] = y
        residuals -= positions[:, :2]
        residuals_list.extend(residuals[:, 0])
        residuals_list.extend(residuals[:, 1])
    residuals_list = scipy.array(residuals_list, scipy.dtype('d'))
    residuals_list.shape = (residuals_list.size,)
    return residuals_list

def _leastSquaresXY(tilts, positions, tilt):
    m = len(tilts)
    n = 3
    a = scipy.zeros((m, n), scipy.dtype('d'))
    b = scipy.zeros((m, 1), scipy.dtype('d'))
    for i in range(m):
        v = tilts[i]
        for j in range(n):
            a[i, j] = v**j
        b[i] = positions[i]
    x, resids, rank, s = lstsq(a, b)
    position = 0
    for j in range(n):
        position += x[j]*tilt**j
    return position

def leastSquaresXY(tilts, xs, ys, tilt, n=5):
    position = scipy.zeros(2, scipy.dtype('d'))
    for i, positions in enumerate((xs, ys)):
        position[i] = _leastSquaresXY(tilts[-n:], positions[-n:], tilt)
    return position

