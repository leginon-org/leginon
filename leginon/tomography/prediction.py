# Due to the difficulty in building scipy on SuSE, we have created our
# own stripped down version of scipy.  It includes most of the optimize
# module (including non-linear least squares).  It does not include
# the linalg module, so we have to use the linear least squares function
# from numarray instead.  Otherwise, all other calls to scipy seem to
# work fine with our modified scipy.

import scipy
import scipy.optimize
try:
	from scipy.linalg import lstsq
	lsmod = scipy
except ImportError:
	from numarray.linear_algebra import linear_least_squares as lstsq
	import numarray
	lsmod = numarray

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
        self.tilt_groups = []
        self.parameters = [0, 0]

        self.min_points = 16
        n = 2**(11 + 4)
        self.max_absolute = scipy.hypot(n, n)
        n = 2**11
        self.max_relative = scipy.hypot(n, n)

    def reset(self):
        if len(self.tilt_groups) > 0:
            if len(self.tilt_groups[-1]) < self.min_points:
                del self.tilt_groups[-1]
        self.tilt_groups.append(TiltGroup())
        # HACK: fix me
        if len(self.tilt_groups) > 8:
            self.tilt_groups = self.tilt_groups[-8:]

    def addPosition(self, tilt, position):
        tilt_group = self.tilt_groups[-1]
        if len(tilt_group) > 0:
            origin = {'x': tilt_group.xs[0],
                      'y': tilt_group.ys[0]}
            previous = {'x': tilt_group.xs[-1],
                        'y': tilt_group.ys[-1]}
            if not self.valid(position, origin, previous):
                return False
        tilt_group.addTilt(tilt, position['x'], position['y'])
        return True

    def predict(self, tilt):
        tilt_group = self.tilt_groups[-1]
        if len(tilt_group) < 1:
            raise RuntimeError
        elif len(tilt_group) < 2:
            x, y = tilt_group.xs[-1], tilt_group.ys[-1]
            z = 0.0
        elif len(tilt_group) < 3:
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
            sin_tilts = scipy.sin(scipy.array([tilt0, tilt]))
            cos_tilts = scipy.cos(scipy.array([tilt0, tilt]))
            result = model(self.parameters, [x0], [y0], [sin_tilts], [cos_tilts])
            z0 = result[0][0][2]
            z = result[0][1][2] - z0

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
        tilt_group = self.tilt_groups[-1]
        x0 = tilt_group.xs[0]
        y0 = tilt_group.ys[0]
        sin_tilts = scipy.sin(scipy.array(tilts))
        cos_tilts = scipy.cos(scipy.array(tilts))
        return model(self.parameters, [x0], [y0], [sin_tilts], [cos_tilts])[0]

    def calculate(self):
        if len(self.tilt_groups[-1]) < 3:
            return
        self.parameters = leastSquaresModel(self.tilt_groups)
        return self.parameters

    def valid(self, position, origin, previous):
        absolute = scipy.hypot(position['x'] - origin['x'],
                               position['y'] - origin['y'])
        if absolute > self.max_absolute:
            return False

        relative = scipy.hypot(position['x'] - previous['x'],
                               position['y'] - previous['y'])
        if relative > self.max_relative:
            return False

        return True

def leastSquaresModel(tilt_groups):
    parameters = [0] + [0] + len(tilt_groups)*[0]
    x0_list = []
    y0_list = []
    sin_tilts_list = []
    cos_tilts_list = []
    x_list = []
    y_list = []
    for tilt_group in tilt_groups:
        tilts = scipy.array(tilt_group.tilts)
        sin_tilts_list.append(scipy.sin(tilts))
        cos_tilts_list.append(scipy.cos(tilts))

        x0_list.append(tilt_group.xs[0])
        y0_list.append(tilt_group.ys[0])

        x_list.append(scipy.array(tilt_group.xs))
        y_list.append(scipy.array(tilt_group.ys))

    x0_list = scipy.array(x0_list)
    y0_list = scipy.array(y0_list)

    args = (x0_list, y0_list, sin_tilts_list, cos_tilts_list, x_list, y_list)
    kwargs = {
        'args': args,
        #'full_output': 1,
        #'ftol': 1e-12,
        #'xtol': 1e-12,
        #'Dfun': jacobian,
    }
    result = scipy.optimize.leastsq(residuals, parameters, **kwargs)
    try:
        x = list(result[0])
    except TypeError:
        x = [result[0]]
    return x

def tiltMatrix(tilt):
    matrix = scipy.matrix(scipy.identity(3, scipy.dtype('d')))
    matrix[0, 0] = scipy.cos(tilt)
    matrix[0, 2] = -scipy.sin(tilt)
    matrix[2, 0] = scipy.sin(tilt)
    matrix[2, 2] = scipy.cos(tilt)
    return matrix

def getParameters(parameters):
    phi = parameters[0]
    optical_axis = parameters[1]
    zs = scipy.array(parameters[2:], scipy.dtype('d'))

    return phi, optical_axis, zs

def model(parameters, x0_list, y0_list, sin_tilts_list, cos_tilts_list):
    phi, optical_axis, zs = getParameters(parameters)
    sin_phi = scipy.sin(phi)
    cos_phi = scipy.cos(phi)
    position_groups = []
    m = len(sin_tilts_list)
    for i in range(m):
        sin_tilts = sin_tilts_list[i]
        cos_tilts = cos_tilts_list[i]

        positions = scipy.zeros((sin_tilts.shape[0], 3), 'd')
        # transform position, rotate, inverse transform to get rotated x, y, z
        positions[:, 0] = cos_phi*x0_list[i] + sin_phi*y0_list[i]
        positions[:, 1] = -sin_phi*x0_list[i] + cos_phi*y0_list[i]
        positions[:, 0] -= optical_axis
        positions[:, 2] = sin_tilts*positions[:, 0] + cos_tilts*zs[i]
        positions[:, 0] = cos_tilts*positions[:, 0] - sin_tilts*zs[i]
        positions[:, 0] += optical_axis
        x_positions = cos_phi*positions[:, 0] - sin_phi*positions[:, 1]
        y_positions = sin_phi*positions[:, 0] + cos_phi*positions[:, 1]
        positions[:, 0] = x_positions
        positions[:, 1] = y_positions

        position_groups.append(positions)
    return position_groups

def residuals(parameters, x0_list, y0_list, sin_tilts_list, cos_tilts_list, x_list, y_list):
    n = len(sin_tilts_list)
    residuals_list = []
    args = (parameters, x0_list, y0_list, sin_tilts_list, cos_tilts_list)
    position_groups = model(*args)
    for i in range(len(position_groups)):
        positions = position_groups[i]
        n = positions.shape[0]
        residuals = scipy.zeros((n, 2), scipy.dtype('d'))
        residuals[:, 0] = x_list[i]
        residuals[:, 1] = y_list[i]
        residuals -= positions[:, :2]
        residuals_list.extend(residuals[:, 0])
        residuals_list.extend(residuals[:, 1])
    residuals_list = scipy.array(residuals_list, scipy.dtype('d'))
    residuals_list.shape = (residuals_list.size,)
    return residuals_list

def _leastSquaresXY(tilts, positions, tilt):
    m = len(tilts)
    n = 3
    if lsmod is scipy:
      a = scipy.zeros((m, n), scipy.dtype('d'))
      b = scipy.zeros((m, 1), scipy.dtype('d'))
    else:
      a = numarray.zeros((m, n), numarray.Float64)
      b = numarray.zeros((m, 1), numarray.Float64)
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

def jacobian(parameters, x0_list, y0_list, sin_tilts_list, cos_tilts_list, x_list, y_list):
    print parameters
    phi, n, z0 = getParameters(parameters)
    print phi, n, z0
    sin_phi = scipy.sin(phi)
    cos_phi = scipy.cos(phi)
    groups = []
    m = len(sin_tilts_list)
    for i in range(m):
        x0 = x0_list[i]
        y0 = y0_list[i]
        sin_theta = sin_tilts_list[i]
        cos_theta = cos_tilts_list[i]

        shape = (sin_theta.shape[0], len(parameters))
        x_jacobians = scipy.zeros(shape, 'd')
        y_jacobians = scipy.zeros(shape, 'd')

        # rows
        #[-2*cos_theta*cos_phi*x0*sin_phi+2*cos_theta*cos_phi**2*y0-cos_theta*y0+sin_phi*cos_theta*n+sin_phi*z0*sin_theta-sin_phi*n+2*sin_phi*x0*cos_phi-2*y0*cos_phi**2+y0, -(cos_theta-1)*cos_phi, -sin_theta*cos_phi]
        #[-cos_theta*x0+2*cos_theta*x0*cos_phi**2+2*sin_phi*cos_theta*y0*cos_phi-cos_phi*cos_theta*n-cos_phi*z0*sin_theta+cos_phi*n+x0-2*x0*cos_phi**2-2*cos_phi*y0*sin_phi, -(cos_theta-1)*sin_phi, -sin_theta*sin_phi]
        #[-(x0*sin_phi-y0*cos_phi)*sin_theta, -sin_theta, cos_theta]

        indices = scipy.arange(2, x_jacobians.shape[1])
        x_jacobians[:, 0] = -2*cos_theta*cos_phi*x0*sin_phi+2*cos_theta*cos_phi**2*y0-cos_theta*y0+sin_phi*cos_theta*n+sin_phi*z0*sin_theta-sin_phi*n+2*sin_phi*x0*cos_phi-2*y0*cos_phi**2+y0
        x_jacobians[:, 1] = -(cos_theta-1)*cos_phi
        for j in indices:
            x_jacobians[:, j] = -sin_theta*cos_phi

        indices = scipy.arange(2, y_jacobians.shape[1])
        y_jacobians[:, 0] = -cos_theta*x0+2*cos_theta*x0*cos_phi**2+2*sin_phi*cos_theta*y0*cos_phi-cos_phi*cos_theta*n-cos_phi*z0*sin_theta+cos_phi*n+x0-2*x0*cos_phi**2-2*cos_phi*y0*sin_phi
        y_jacobians[:, 1] = -(cos_theta-1)*sin_phi
        for j in indices:
            y_jacobians[:, j] = -sin_theta*sin_phi

        jacobians = scipy.zeros((shape[0]*2, shape[1]))
        jacobians[:shape[0], :] = x_jacobians
        jacobians[shape[0]:, :] = y_jacobians

        groups.append(jacobians)

    groups = scipy.array(groups, scipy.dtype('d'))
    groups.shape = (groups.size/groups.shape[2], groups.shape[2])
    print groups
    print
    return groups

def leastSquaresXY(tilts, xs, ys, tilt, n=5):
    position = scipy.zeros(2, scipy.dtype('d'))
    for i, positions in enumerate((xs, ys)):
        position[i] = _leastSquaresXY(tilts[-n:], positions[-n:], tilt)
    return position

if __name__ == '__main__':
    parameters = (45, 0, 0)
    x0 = 1
    y0 = 2
    tilts = scipy.array((0, 15, 30, 45), 'd')*scipy.pi/180
    sin_tilts = scipy.sin(tilts)
    cos_tilts = scipy.cos(tilts)
    x = scipy.array(scipy.arange(0, 4), 'd')
    y = scipy.array((0, 0, 0, 0), 'd')
    result = residuals(parameters, [x0], [y0], [sin_tilts], [cos_tilts], [x], [y])
    print result
    result = jacobian(parameters, [x0], [y0], [sin_tilts], [cos_tilts], [x], [y])
    print result

