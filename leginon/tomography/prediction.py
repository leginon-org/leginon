import scipy
import scipy.linalg
import scipy.linalg.basic
import scipy.optimize

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
        self.parameters = [0, 0, 0, 0, 0]

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
        elif len(tilt_group) < 3 or len(self.tilt_groups) < 2:
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

            tilt_matrices = scipy.zeros((1, 3, 3), scipy.Float)
            initial_tilt = tilt_group.tilts[0]
            tilt_matrices[0, :, :] = tiltMatrix(initial_tilt)
            z0 = model(self.parameters, [tilt_matrices])[0][0][2]

            tilt_matrices[0, :, :] = tiltMatrix(tilt)
            z = model(self.parameters, [tilt_matrices])[0][0][2] - z0

        result = {
            'x': float(x),
            'y': float(y),
            'z': float(z),
            #'phi': self.parameters[0],
            #'optical axis': {
            #    'x': self.parameters[1],
            #    'y': self.parameters[2],
            #},
            #'specimen': {
            #    'x': self.parameters[-2],
            #    'z': self.parameters[-1],
            #},
        }

        return result

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
    parameters = [0] + [0, 0] + len(tilt_groups)*[0, 0]
    tilt_matrices_list = []
    x_list = []
    y_list = []
    for tilt_group in tilt_groups:
        n = len(tilt_group.tilts)
        tilt_matrices = scipy.zeros((n, 3, 3), scipy.Float)
        for i in range(n):
            tilt_matrices[i, :, :] = tiltMatrix(tilt_group.tilts[i])
        tilt_matrices_list.append(tilt_matrices)

        x_list.append(tilt_group.xs)
        y_list.append(tilt_group.ys)

    args = (tilt_matrices_list, x_list, y_list)
    kwargs = {
        #'full_output': 1,
        'ftol': 1e-12,
        'xtol': 1e-12,
    }
    result = scipy.optimize.leastsq(residuals, parameters, args=args, **kwargs)
    try:
        x = list(result[0])
    except TypeError:
        x = [result[0]]
    return x

def tiltMatrix(tilt):
    matrix = scipy.identity(3, scipy.Float)
    matrix[0, 0] = scipy.cos(tilt)
    matrix[0, 2] = -scipy.sin(tilt)
    matrix[2, 0] = scipy.sin(tilt)
    matrix[2, 2] = scipy.cos(tilt)
    return matrix

def getParameters(parameters):
    phi = scipy.identity(3, scipy.Float)
    cos_phi = scipy.cos(parameters[0])
    sin_phi = scipy.sin(parameters[0])
    phi[0, 0] = cos_phi
    phi[0, 1] = sin_phi
    phi[1, 0] = -sin_phi
    phi[1, 1] = cos_phi

    #psi = scipy.identity(3, scipy.Float)
    #cos_psi = scipy.cos(parameters[1])
    #sin_psi = scipy.sin(parameters[1])
    #psi[1, 1] = cos_psi
    #psi[1, 2] = sin_psi
    #psi[2, 1] = -sin_psi
    #psi[2, 2] = cos_psi

    optical_axis = scipy.zeros(3, scipy.Float)
    optical_axis[0] = parameters[1]
    optical_axis[1] = parameters[2]

    n = (len(parameters) - 3)/2
    specimens = scipy.zeros((n, 3), scipy.Float)
    specimens[:, 0] = parameters[3::2]
    specimens[:, 2] = parameters[4::2]

    return phi, optical_axis, specimens

def model(parameters, thetas_list):
    phi, optical_axis, specimens = getParameters(parameters)
    position_groups = []
    for i, thetas in enumerate(thetas_list):
        positions = scipy.dot(thetas, specimens[i, :])
        positions += optical_axis
        for i in range(positions.shape[0]):
            positions[i, :] = scipy.dot(phi, positions[i, :])
        position_groups.append(positions)
    return position_groups

def residuals(parameters, tilt_matrices_list, x_list, y_list):
    n = len(tilt_matrices_list)
    residuals_list = []
    position_groups = model(parameters, tilt_matrices_list)
    for i in range(len(position_groups)):
        positions = position_groups[i]
        n = positions.shape[0]
        residuals = scipy.zeros((n, 2), scipy.Float)
        residuals[:, 0] = x_list[i]
        residuals[:, 1] = y_list[i]
        residuals -= positions[:, :2]
        residuals_list.extend(residuals[:, 0])
        residuals_list.extend(residuals[:, 1])
    return scipy.array(residuals_list, scipy.Float).flat

def _leastSquaresXY(tilts, positions, tilt):
    m = len(tilts)
    n = 3
    a = scipy.zeros((m, n), scipy.Float)
    b = scipy.zeros((m, 1), scipy.Float)
    for i in range(m):
        v = tilts[i]
        for j in range(n):
            a[i, j] = v**j
        b[i] = positions[i]
    x, resids, rank, s = scipy.linalg.lstsq(a, b)
    position = 0
    for j in range(n):
        position += x[j]*tilt**j
    return position

def leastSquaresXY(tilts, xs, ys, tilt, n=5):
    position = scipy.zeros(2, scipy.Float)
    for i, positions in enumerate((xs, ys)):
        position[i] = _leastSquaresXY(tilts[-n:], positions[-n:], tilt)
    return position

