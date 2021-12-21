import math
import scipy
import scipy.optimize
from scipy.linalg import lstsq
import numpy

def debug_print(msg):
	#print msg
	pass

class PredictionError(Exception):
	pass

class TiltSeries(object):
	def __init__(self):
		self.tilt_groups = []

	def addTiltGroup(self, tilt_group):
		self.tilt_groups.append(tilt_group)
		self.current_group = self.tilt_groups[-1]
		self.current_group_index = len(self.tilt_groups)-1

	def __len__(self):
		return len(self.tilt_groups)

	def getCurrentTiltGroup(self):
		if self.tilt_groups:
			return self.current_group
		else:
			newgroup = TiltGroup()
			self.addTiltGroup(newgroup)
			self.current_group = self.tilt_groups[-1]
			return self.current_group

	def setCurrentTiltGroup(self, index):
		if len(self.tilt_groups) <= index:
			raise ValueError
		self.current_group = self.tilt_groups[index]
		self.current_group_index = index

	def getCurrentTiltGroupIndex(self):
		return self.current_group_index

class TiltGroup(object):
	'''
	TiltGroup has a range of tilts.
	'''
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
		self.tilt_series_pixel_size_list = []
		self.parameters = [[0, 0, 0],[0, 0, 0]]
		self.initial_params = [[0, 0, 0],[0, 0, 0]]
		self.image_pixel_size = 2e-9
		self.ucenter_limit = 2e-6
		self.fitdata = [4,4]
		self.fixed_model = True
		self.valid_tilt_series_list = []

	def resetTiltSeriesList(self):
		self.tilt_series_list = []
		self.tilt_series_pixel_size_list = []
		self.parameters = [[0, 0, 0],[0, 0, 0]]

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
		if self.valid_tilt_series_list:
			return self.valid_tilt_series_list[-1]
		# FIX ME not sure this works right
		debug_print('found no valid tilt series, make a new one')
		self.newTiltSeries()
		self.newTiltGroup()
		self.newTiltGroup()
		return self.tilt_series_list[-1]

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
			else:
				debug_print('invaid tilt series: index %d' % i)
				debug_print('  %d groups in it' % len(tilt_series.tilt_groups))
				for g in tilt_series.tilt_groups:
					debug_print(g.tilts)

	def newTiltGroup(self):
		tilt_series = self.getCurrentTiltSeries()
		# Fix me: WHY prevent adding new group if nothing is there ?
		#if tilt_series.tilt_groups and len(tilt_series.tilt_groups[-1]) < 1:
		#	print 'previous tilt group has no value, tiltgroup not added. But why?'
		#	return
		tilt_group = TiltGroup()
		tilt_series.addTiltGroup(tilt_group)

	def getCurrentTiltGroup(self):
		tilt_series = self.getCurrentTiltSeries()
		return tilt_series.getCurrentTiltGroup()

	def setCurrentTiltGroup(self, index):
		tilt_series = self.getCurrentTiltSeries()
		return tilt_series.setCurrentTiltGroup(index)

	def getCurrentTiltGroupIndex(self):
		tilt_series = self.getCurrentTiltSeries()
		g = tilt_series.getCurrentTiltGroupIndex()
		return g

	def addPosition(self, tilt, position):
		tilt_group = self.getCurrentTiltGroup()
		tilt_group.addTilt(tilt, position['x'], position['y'])

	def setParameters(self, index, params):
		self.parameters[index] = params

	def setFixedParameters(self, index, params):
		'''
		Set initial params for model that does not change through the tilt series.
		This should only be set once.
		'''
		self.initial_params[index] = params

	def getFixedParameters(self):
		'''
		Get initial params for model that does not change through the tilt series
		'''
		index = self.getCurrentTiltGroupIndex()
		return self.initial_params[index]

	def getCurrentParameters(self):
		'''
		get most recent LeastSquaredModel fit results.
		'''
		i = self.getCurrentTiltGroupIndex()
		# The returned values are phi, optical_axis, z0
		return tuple(self.parameters[i][:2] + [self.parameters[i][-1]])


	def getMinMaxTiltsOfTiltSeriesList(self, tiltgroup_index):
		n = []
		gmaxtilt = []
		gmintilt = []
		for s in self.valid_tilt_series_list:
			g = s.tilt_groups[tiltgroup_index]
			n.append(len(g))
			# old tilts may be aborted before start and therefore tilts=[]
			if len(g.tilts) > 0:
				gmaxtilt.append(max(g.tilts))
				gmintilt.append(min(g.tilts))
		# default maxtilt/mintilt to 0.0 so that the fit uses fix model
		if gmaxtilt:
			maxtilt = max(gmaxtilt)
		else:
			maxtilt = 0.0
		if gmintilt:
			mintilt = max(gmintilt)
		else:
			mintilt = 0.0
		return mintilt, maxtilt

	def predict(self, tilt):
		debug_print(' ')
		debug_print('Predicting %.2f' % math.degrees(tilt))

		tilt_series = self.getCurrentTiltSeries()
		tilt_group = self.getCurrentTiltGroup()
		current_group_index = self.getCurrentTiltGroupIndex()
		n_start_fit = self.fitdata[current_group_index]
		n_smooth_fit = self.fitdata[current_group_index]
		n_tilt_series = len(self.valid_tilt_series_list)
		n_tilt_groups = len(tilt_series)
		n_tilts = len(tilt_group.tilts)

		#####
		parameters = self.getCurrentParameters()
		debug_print('z0 at start of prediction %.2f' % parameters[-1])
		debug_print('using %d tilts' % n_tilts)
		debug_print('tilts are: %s' % tilt_group.tilts)
		if n_tilts < 1:
			raise RuntimeError
		elif n_tilts < n_start_fit and not parameters[-1] == 0.0 and not self.fixed_model:
			debug_print('set to input value since no fit, yet')
			# one tilt : set to the input value
			# x, y, z unchanged
			x, y = tilt_group.xs[-1], tilt_group.ys[-1]
			z = 0.0
		elif n_tilts < n_start_fit:
			debug_print('set use input model as prediction')
			# number of tilts not enough to calculate modeled position.
			# calculate real z correction with current parameters
			x0 = tilt_group.xs[0]
			y0 = tilt_group.ys[0]
			tilt0 = tilt_group.tilts[0]
			cos_tilts = scipy.cos(scipy.array([tilt0, tilt]))
			sin_tilts = scipy.sin(scipy.array([tilt0, tilt]))
			parameters = self.getCurrentParameters()
			args_list = [(cos_tilts, sin_tilts, x0, y0, None, None)]

			if len(self.tilt_series_list) != len(self.valid_tilt_series_list):
				debug_print("%s out of %s tilt series are used in prediction" %(len(self.valid_tilt_series_list),len(self.tilt_series_list)))
			result = self.model(parameters, args_list)
			z0 = parameters[2]
			z = result[-1][-1][2] - z0
			x = result[-1][-1][0]
			y = result[-1][-1][1]

		else:
			# fitting is possible
			if n_tilts != n_start_fit:
				self.forcemodel = False
			else:
				# When it is fitted the first time, force the prediction
				# to be used if it has the same trend as the earlier tilts.
				# Otherwise it would slip off too much.
				r2 = [0,0]
				r2[0] = abs(self._getCorrelationCoefficient(tilt_group.tilts[1:], tilt_group.xs[1:]))
				r2[1] = abs(self._getCorrelationCoefficient(tilt_group.tilts[1:], tilt_group.ys[1:]))
				r2xy = abs(self._getCorrelationCoefficient(tilt_group.xs[1:], tilt_group.ys[1:]))
				if max(r2) > 0.95 and r2xy > 0.95 and not self.fixed_model:
					self.forcemodel = True
					debug_print('force to use fitted model')
				else:
					debug_print( 'trend is not strong: %.4f, %.4f <=0.95' % (max(r2), r2xy))
					debug_print('or fixed model (%s) is True' % (self.fixed_model))
					self.forcemodel = False
			# x,y is only a smooth polynomial fit
			x, y = self.leastSquaresXY(tilt_group.tilts,
								  tilt_group.xs,
								  tilt_group.ys,
								  tilt,
									n_smooth_fit)
			## calculate optical axis tilt and offset
			mintilt, maxtilt = self.getMinMaxTiltsOfTiltSeriesList(current_group_index)
			if (abs(maxtilt) < math.radians(30) and abs(mintilt) < math.radians(30)):
				## optical axis offset fit is not reliable at small tilts
				## calculate new model parameters to get new z0
				## and then revert the fixed_model option value
				orig_fixed_model = self.fixed_model
				self.fixed_model = True
				self.calculate()
				self.fixed_model = orig_fixed_model
			else:
				self.calculate()


			# use the tilt and tilt0 x,y values to calculate the model z0
			x0 = tilt_group.xs[0]
			y0 = tilt_group.ys[0]
			tilt0 = tilt_group.tilts[0]
			cos_tilts = scipy.cos(scipy.array([tilt0, tilt]))
			sin_tilts = scipy.sin(scipy.array([tilt0, tilt]))
			parameters = self.getCurrentParameters()
			args_list = [(cos_tilts, sin_tilts, x0, y0, None, None)]
			debug_print("parameters go in model (%.4f,%.4f,%.1f)" % parameters)
			result = self.model(parameters, args_list)
			z0 = result[-1][0][2]
			debug_print("model result z0 in pixels: %.1f" % z0)
			debug_print("model results %s " % result)
			z = result[-1][-1][2] - z0

		# self.parameters may be altered after model fit.
		phi, optical_axis, z0 = self.getCurrentParameters()
		debug_print("z0s of all tilt series: %s" % self.parameters[current_group_index])
		debug_print("currentparameters z0 %s" % z0)
		phi,offset = self.convertparams(phi,optical_axis)
		result = {
			'x': float(x),
			'y': float(y),
			'z': float(z),
			'phi': float(phi),
			'optical axis': float(offset),
			'z0': float(self.parameters[current_group_index][-1]),
		}
		debug_print('calculate result: %s' % result)
		return result

	def convertparams(self, phi, offset):
		# convert to consistent convention
		if math.cos(phi) < 0:
			offset = -offset
		phi = math.atan(math.tan(phi))
		return phi,offset

	def calculate(self):
		'''
		calculate new model parameters through fitting of previous tilt series
		'''
		tilt_group = self.getCurrentTiltGroup()
		tilt_group_index = self.getCurrentTiltGroupIndex()
		# do nothing if not enough tilts in tilt_group
		if len(tilt_group) < 3:
			return
		# use maximal of 8 previous tilt series for fitting
		if len(self.valid_tilt_series_list) > 8:
			tilt_series_list = self.valid_tilt_series_list[-8:]
		else:
			tilt_series_list = self.valid_tilt_series_list
		fitparameters = self.leastSquaresModel(tilt_series_list)
		# Use the old, good parameter if the fitting result suggest a very large tilt axis z offset
		# max_delta_z0 should be larger than the z eucentric error ucenter_error in meters
		max_delta_z0 =  self.ucenter_limit / self.image_pixel_size
		debug_print('z diffi %.1f, %.1f' % (fitparameters[-1],self.parameters[tilt_group_index][-1]))
		debug_print('max_delta_z0 %.1f' % max_delta_z0)
		if self.forcemodel or (fitparameters[-1]-self.parameters[tilt_group_index][-1])**2 <= max_delta_z0**2:
			self.parameters[tilt_group_index] = fitparameters
		else:
			debug_print('model not used for update: %s' % fitparameters)
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
		'''
		Return indices for a list only item values in the range of min and max.
		When there are fewer items that pass the criteria than datalimit, try
		to include more at the end of the list
		'''
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
			phi, optical_axis, z0 = self.getFixedParameters()
		parameters = [phi, optical_axis]
		args_list = []
		current_tilt_group = self.getCurrentTiltGroup()
		current_group_index = self.getCurrentTiltGroupIndex()
		current_tilt = current_tilt_group.tilts[-1]
		datalimit = self.fitdata[current_group_index]
		if len(current_tilt_group) >= datalimit:
			previous_tilts = current_tilt_group.tilts[-datalimit:]
		else:
			previous_tilts = current_tilt_group.tilts[:]
		if self.fixed_model:
			# Accept accurate tilts only for fixed phi, offset fitting of z0
			tolerance = 0.01
		else:
			# With all three parameters free to change, use all tilt points to stablize the fiting
			# The result is more an average phi, offset.
			tolerance = 1.62
		tiltmin = min(previous_tilts) - tolerance
		tiltmax = max(previous_tilts) + tolerance
		for s, tilt_series in enumerate(tilt_series_list):
			debug_print('leastSquareModel: series number %d' % (s,))
			tilt_group = tilt_series.tilt_groups[current_group_index]
			if len(tilt_group.tilts) == 0  or len(tilt_group.xs) != len(tilt_group.tilts) or len(tilt_group.ys) != len(tilt_group.tilts):
				# invalid tilt_group, skip
				debug_print('skipped: series number %d with %d tilts' % (s,len(tilt_group.tilts)))
				continue
			debug_print('leastSquareModel use tilt_group index %d' % (current_group_index,))
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

			# leastsq function gives improper parameters error if too many input data array are empty
			# This happens if 6 or more preceeding tilt series have much lower end tilt angle
			# than the current. We will ignore them.
			if cos_tilts.size < 1:
				args_list.pop()
				parameters.pop()
				debug_print('popped: series number %d' % (s,))
			else:
				debug_print('%d tilts are included for fitting from series %d' % (len(goodtilts),s))
		# There should be at least one tilt series (current one) left at this point
		debug_print('%d tilt series left for fitting' % len(args_list))
		args = (args_list,)
		kwargs = {
			'args': args,
			#'full_output': 1,
			#'ftol': 1e-12,
			#'xtol': 1e-12,
		}
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
			phi, optical_axis, z0 = self.getFixedParameters()
		zs = scipy.array(parameters[2:], scipy.dtype('d'))
		return phi, optical_axis, zs

	def model(self, parameters, args_list):
		'''
		x, y positions according to phi, optical axis and each zs
		'''
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
		'''
		Calculate residual list which sum of squares is to be minimized.
		'''
		residuals_list = []
		position_groups = self.model(parameters, args_list)
		for i, positions in enumerate(position_groups):
			n = positions.shape[0]
			cos_tilts, sin_tilts, x0, y0, x, y = args_list[i]
			residuals = scipy.zeros((n, 2), scipy.dtype('d'))
			residuals[:, 0] = x
			residuals[:, 1] = y
			residuals -= positions[:, :2]
			# put in list
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

	def leastSquaresXY(self, tilts, xs, ys, tilt, n_smooth_fit=4):
		n = n_smooth_fit+1
		position = scipy.zeros(2, scipy.dtype('d'))
		for i, positions in enumerate((xs, ys)):
			position[i] = self._leastSquaresXY(tilts[-n:], positions[-n:], tilt)
		return position

	def setCalibratedDefocusDeltas(self, tilts, deltas):
		'''
		Sorted tilts and defecus deltas. Tilts are in radians. Underfocus is positive.
		'''
		if len(tilts) != len(deltas):
			raise ValueError('Number of alibrated delta defocii and tilts not matched')
		self.cal_tilts = tilts
		self.cal_deltas = deltas

	def getCalibratedDefocusDelta(self, tilt):
		# underfocus is positive in deltas
		# interpolate
		xp = self.cal_tilts
		fp = self.cal_deltas
		return numpy.interp(tilt, xp, fp)
