import math
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
		if self.tilt_groups:
			return self.tilt_groups[-1]
		else:
			return TiltGroup()

class TiltGroup(object):
	def __init__(self):
		self.tilts = []
		self.xs = []
		self.ys = []
		self.is_plus_tilt = False

	def addTilt(self, tilt, x, y):
		self.tilts.append(tilt)
		self.xs.append(x)
		self.ys.append(y)
		self.is_plus_tilt = self.getTiltDirection(self.tilts)

	def getTiltDirection(self,tilts):
		if tilts[-1] > 0:
			return True
		else:
			return False

	def __len__(self):
		return len(self.tilts)

class Prediction(object):
	def __init__(self):
		self.tilt_series_list = []
		self.tilt_series_pixel_size_list = []
		self.parameters = [0, 0, 0]
		self.image_pixel_size = 2e-9
		self.ucenter_limit = 2e-6
		self.fitdata = 4

	def resetTiltSeriesList(self):
		self.tilt_series_list = []
		self.tilt_series_pixel_size_list = []
		self.parameters = [0, 0, 0]

	def addTiltSeries(self, tilt_series):
		self.tilt_series_list.append(tilt_series)
		self.tilt_series_pixel_size_list.append(self.image_pixel_size)
		self.getValidTiltSeriesList()

	def newTiltSeries(self):
		if self.tilt_series_list and len(self.tilt_series_list[-1]) < 1:
			return
		tilt_series = TiltSeries()
		self.addTiltSeries(tilt_series)

	def getCurrentTiltSeries(self):
		return self.valid_tilt_series_list[-1]

	def getValidTiltSeriesList(self):
		self.valid_tilt_series_list = []
		self.valid_tilt_series_pixel_size_list = []
		current_pixel_size = self.tilt_series_pixel_size_list[-1]
		# Hack, need to clean up
		if current_pixel_size == [] and len(self.tilt_series_pixel_size_list) >= 2:
			current_pixel_size = self.tilt_series_pixel_size_list[-2]

		for i, tilt_series in enumerate(self.tilt_series_list):
			if self.tilt_series_pixel_size_list[i] == current_pixel_size:
				self.valid_tilt_series_list.append(tilt_series)
				self.valid_tilt_series_pixel_size_list.append(self.image_pixel_size)

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
		n_start_fit = 3
		if len(self.tilt_series_list) != len(self.valid_tilt_series_list):
			print "%s out of %s tilt series are used in prediction" %(len(self.valid_tilt_series_list),len(self.tilt_series_list))
		tilt_series = self.getCurrentTiltSeries()
		tilt_group = self.getCurrentTiltGroup()
		current_tilt_direction = tilt_group.is_plus_tilt
		n_tilt_series = len(self.valid_tilt_series_list)
		n_tilt_groups = len(tilt_series)
		n_tilts = len(tilt_group)
		n = []
		gmaxtilt = []
		gmintilt = []
		for s in self.valid_tilt_series_list:
			for g in s.tilt_groups:
				if g.is_plus_tilt is not current_tilt_direction:
					continue
				n.append(len(g))
				# old tilts may be aborted before start and therefore tilts=[]
				if len(g.tilts) > 0:
					gmaxtilt.append(max(g.tilts))
					gmintilt.append(min(g.tilts))
		maxtilt = max(gmaxtilt)
		mintilt = min(gmintilt)
		parameters = self.getCurrentParameters()
		if n_tilts < 1:
			raise RuntimeError
		elif n_tilts < 2:
			x, y = tilt_group.xs[-1], tilt_group.ys[-1]
			self.parameters = [parameters[0],parameters[1],0]
			parameters = self.getCurrentParameters()
			z = 0.0
		# calculate real z correction with current parameters 
		elif n_tilts < n_start_fit:
			x, y = tilt_group.xs[-1], tilt_group.ys[-1]
			
			x0 = tilt_group.xs[0]
			y0 = tilt_group.ys[0]
			tilt0 = tilt_group.tilts[0]
			cos_tilts = scipy.cos(scipy.array([tilt0, tilt]))
			sin_tilts = scipy.sin(scipy.array([tilt0, tilt]))
			parameters = self.getCurrentParameters()
			args_list = [(cos_tilts, sin_tilts, x0, y0, None, None)]
			result = self.model(parameters, args_list)
			z0 = result[-1][0][2]
			z = result[-1][-1][2] - z0
			x = result[-1][-1][0]
			y = result[-1][-1][1]

		else:
			if n_tilts != n_start_fit:
				self.forcemodel = False
			else:
				r2 = [0,0]
				r2[0] = abs(self._getCorrelationCoefficient(tilt_group.tilts[1:], tilt_group.xs[1:]))
				r2[1] = abs(self._getCorrelationCoefficient(tilt_group.tilts[1:], tilt_group.ys[1:]))
				r2xy = abs(self._getCorrelationCoefficient(tilt_group.xs[1:], tilt_group.ys[1:]))
				if max(r2) > 0.95 and r2xy > 0.95 and not self.fixed_model:
					self.forcemodel = True
				else:
					self.forcemodel = False
			# x,y is only a smooth polynomial fit
			x, y = self.leastSquaresXY(tilt_group.tilts,
								  tilt_group.xs,
								  tilt_group.ys,
								  tilt)
		#	tilt_group.addTilt(tilt, x, y)
			## calculate optical axis tilt and offset
			if (abs(maxtilt) < math.radians(30) and abs(mintilt) < math.radians(30)):
				## optical axis offset fit is not reliable at small tilts
				orig_fixed_model = self.fixed_model
				self.fixed_model = True
				self.calculate()
				self.fixed_model = orig_fixed_model
			else:
				self.calculate()

		#	del tilt_group.tilts[-1]
		#	del tilt_group.xs[-1]
		#	del tilt_group.ys[-1]

			x0 = tilt_group.xs[0]
			y0 = tilt_group.ys[0]
			tilt0 = tilt_group.tilts[0]
			cos_tilts = scipy.cos(scipy.array([tilt0, tilt]))
			sin_tilts = scipy.sin(scipy.array([tilt0, tilt]))
			parameters = self.getCurrentParameters()
			args_list = [(cos_tilts, sin_tilts, x0, y0, None, None)]
			result = self.model(parameters, args_list)
			z0 = result[-1][0][2]
			z = result[-1][-1][2] - z0

		phi,offset = self.convertparams(self.parameters[0],self.parameters[1])
		result = {
			'x': float(x),
			'y': float(y),
			'z': float(z),
			'phi': float(phi),
			'optical axis': float(offset),
			'z0': float(self.parameters[-1]),
		}

		return result

	def convertparams(self, phi, offset):
		if math.cos(phi) < 0:
			offset = -offset
		phi = math.atan(math.tan(phi))
		return phi,offset

	def calculate(self):
		tilt_group = self.getCurrentTiltGroup()
		if len(tilt_group) < 3:
			return
		if len(self.valid_tilt_series_list) > 8:
			tilt_series_list = self.valid_tilt_series_list[-8:]
		else:
			tilt_series_list = self.valid_tilt_series_list
		fitparameters = self.leastSquaresModel(tilt_series_list)
		print 'fit',fitparameters
		# Use the old, good parameter if the fitting result suggest a very large tilt axis z offset
		# max_delta_z0 should be larger than the z eucentric error ucenter_error in meters
		max_delta_z0 =  self.ucenter_limit / self.image_pixel_size
		if self.forcemodel or (fitparameters[-1]-self.parameters[-1])**2 <= max_delta_z0**2:
			self.parameters = fitparameters
		else:
			pass
		return

	def _getCorrelationCoefficient(self,xs,ys):
		if len(xs) != len(ys):
			return 0
		m = len(xs)
		xa = scipy.zeros((m, 1), scipy.dtype('d'))
		ya = scipy.zeros((m, 1), scipy.dtype('d'))
		for i in range(m):
			xa[i] = xs[i]
			ya[i] = ys[i]
		xmean = sum(xa)/m
		ssxx = sum(xa*xa) - m*xmean*xmean
		ymean = sum(ya)/m
		ssyy = sum(ya*ya) - m*ymean*ymean
		ssxy = sum(xa*ya) - m*xmean*ymean
		r2 = ssxy * ssxy / (ssxx * ssyy)
		return r2

	def acceptableindices(self,list,min,max,datalimit):
		array = scipy.array(list)
		larger = scipy.where(array >= min)
		smaller = scipy.where(array <= max)
		goodarrayindices = scipy.intersect1d(larger[0],smaller[0])
		goodindices = goodarrayindices.tolist()
		# The current tilt series may need an extra index to make up the number
		while len(goodindices) < datalimit and len(goodindices) > 0 and len(list) >= datalimit:
			nextindex = goodindices[-1]+1
			if nextindex not in range(0,len(list)):
				break
			goodindices.append(goodindices[-1]+1)
		return goodindices

	def leastSquaresModel(self, tilt_series_list):
		phi, optical_axis, z0 = self.getCurrentParameters()
		if self.fixed_model == True:
			phi = self.phi0
			optical_axis = self.offset0
		parameters = [phi, optical_axis]
		args_list = []
		current_tilt_group = self.getCurrentTiltGroup()
		current_tilt_direction = current_tilt_group.is_plus_tilt
		print "tilt_direction",current_tilt_direction
		current_tilt = current_tilt_group.tilts[-1]
		datalimit = self.fitdata
		if len(current_tilt_group) >= datalimit:
			previous_tilts = current_tilt_group.tilts[-datalimit:]
		else:
			previous_tilts = current_tilt_group.tilts[:]
		if self.fixed_model:
			# use previous 4 tilts for fixed phi, offset fitting of z0
			tolerance = 0.01
		else:
			# With all three parameters free to change, use all tilt points to stablize the fiting
			# The result is more an average phi, offset.
			tolerance = 1.62
		tiltmin = min(previous_tilts) - tolerance
		tiltmax = max(previous_tilts) + tolerance
		for tilt_series in tilt_series_list:
			for tilt_group in tilt_series.tilt_groups:
				if len(tilt_group.tilts) == 0  or len(tilt_group.xs) != len(tilt_group.tilts) or len(tilt_group.ys) != len(tilt_group.tilts):
					break
				# wrong direction tilt group should not be included in the fit
				elif tilt_group.is_plus_tilt is not current_tilt_direction:
					continue
				parameters.extend([0])
				
				acceptableindices = self.acceptableindices(tilt_group.tilts,tiltmin,tiltmax,datalimit)
				goodtilts = []
				goodxs = []
				goodys = []
				for i in acceptableindices:
					goodtilts.append(tilt_group.tilts[i])
					goodxs.append(tilt_group.xs[i])
					goodys.append(tilt_group.ys[i])
				tilts = scipy.array(goodtilts)
				cos_tilts = scipy.cos(tilts)
				sin_tilts = scipy.sin(tilts)

				x0 = tilt_group.xs[0]
				y0 = tilt_group.ys[0]

				x = scipy.array(goodxs)
				y = scipy.array(goodys)

				args_list.append((cos_tilts, sin_tilts, x0, y0, x, y))

		print 'starting parameters',parameters
		args = (args_list,)
		kwargs = {
			'args': args,
			#'full_output': 1,
			#'ftol': 1e-12,
			#'xtol': 1e-12,
		}
		#print 'starting residuals',self.residuals(parameters,args_list)
		result = scipy.optimize.leastsq(self.residuals, parameters, **kwargs)
		try:
			x = list(result[0])
		except TypeError:
			x = [result[0]]
		return x

	def getParameters(self, parameters):
		phi = parameters[0]
		optical_axis = parameters[1]
		if self.fixed_model == True:
			phi = self.phi0
			optical_axis = self.offset0
		zs = scipy.array(parameters[2:], scipy.dtype('d'))
		return phi, optical_axis, zs

	def model(self, parameters, args_list):
		phi, optical_axis, zs = self.getParameters(parameters)
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
			positions[:, 2] = sin_tilts*positions[:, 0] + cos_tilts*(z)
			positions[:, 0] = cos_tilts*positions[:, 0] - sin_tilts*(z)
			positions[:, 0] -= optical_axis
			x_positions = cos_phi*positions[:, 0] - sin_phi*positions[:, 1]
			y_positions = sin_phi*positions[:, 0] + cos_phi*positions[:, 1]
			positions[:, 0] = x_positions
			positions[:, 1] = y_positions
			position_groups.append(positions)
		return position_groups

	def residuals(self, parameters, args_list):
		# residual_list is the values which sum of squares is to be minimized
		residuals_list = []
		position_groups = self.model(parameters, args_list)
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

	def _leastSquaresXY(self, tilts, positions, tilt):
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

	def leastSquaresXY(self, tilts, xs, ys, tilt, n=5):
		n = self.fitdata + 1
		position = scipy.zeros(2, scipy.dtype('d'))
		for i, positions in enumerate((xs, ys)):
			position[i] = self._leastSquaresXY(tilts[-n:], positions[-n:], tilt)
		return position

