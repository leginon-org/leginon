import math
import scipy
import scipy.optimize
from scipy.linalg import lstsq
from scipy.stats import linregress
import numpy as np

from leginon.tomography.prediction import TiltSeries
from leginon.tomography.prediction import TiltGroup
from leginon.tomography.prediction import Prediction
from leginon.tomography.prediction import PredictionError

def debug_print(msg):
	#print msg
	pass

class TiltSeries2(TiltSeries):
	def __init__(self):
		super(TiltSeries2,self).__init__()

	def getCurrentTiltGroup(self):
		if self.tilt_groups:
			return self.current_group
		else:
			newgroup = TiltGroup2()
			self.addTiltGroup(newgroup)
			self.current_group = self.tilt_groups[-1]
			return self.current_group

class TiltGroup2(TiltGroup):
	'''
	TiltGroup has a range of tilts.
	'''
	def __init__(self):
		super(TiltGroup2,self).__init__()
		self.pxs = []
		self.pys = []
	
	def addTilt(self,tilt, x, y, px=None, py=None):		
		self.tilts.append(tilt)
		self.xs.append(x)						# measured positions
		self.ys.append(y)
		self.pxs.append(px)						# predicted positions
		self.pys.append(py)

class Prediction2(Prediction):
	
	def __init__(self):
		super(Prediction2,self).__init__()
		self.cutoff = None						# acceptable tolerance 
		self.maxfitpoints = 10 					# maximum number of points to consider for fitting. has to be at least 3
		
	def setcutoff(self,cutoff):
		self.cutoff = cutoff 
	
	def set_maxfitpoints(self,maxpoints):
		self.maxfitpoints = max(4,maxpoints)
		if maxpoints > 4:
			self.maxfitpoints = maxpoints
		else:
			self.maxfitpoints = 4
		
	def newTiltSeries(self):
		# override function comment out the next two lines guarantees a new tilt series. 
		#if self.tilt_series_list and len(self.tilt_series_list[-1]) < 1:		
		#	return
		tilt_series = TiltSeries2()
		self.addTiltSeries(tilt_series)

	def newTiltGroup(self):
		tilt_series = self.getCurrentTiltSeries()
		tilt_group = TiltGroup2()
		tilt_series.addTiltGroup(tilt_group)
		
	def addPosition(self, tilt, position, predicted = None):
		tilt_group = self.getCurrentTiltGroup()
		if predicted is None:
			tilt_group.addTilt(tilt, position['x'], position['y'])
		else:
			tilt_group.addTilt(tilt, position['x'], position['y'], predicted['x'], predicted['y'])

	def isdefocus(self):
		return False
	
	def ispredict(self):
		# Determine if we can predict. 
		tilt_group = self.getCurrentTiltGroup()
		current_group_index = self.getCurrentTiltGroupIndex()
		n_start_fit = self.fitdata[current_group_index]
		n_tilts = len(tilt_group.tilts)			# this is how many tilts have been processed

		if n_tilts < 3 or n_tilts < n_start_fit or \
			(not self.reliablefit()): 			# can't use prediction until at least 3 tilts have been processed. 
			return False
		else:
			return True

	def getPreviousError(self):
		tilt_series = self.getCurrentTiltSeries()
		tilt_group = self.getCurrentTiltGroup()
		
		x = tilt_group.xs[-1]
		y = tilt_group.ys[-1]
		px = tilt_group.pxs[-1]
		py = tilt_group.pys[-1]
		assert px is not None and py is not None

		return math.sqrt((x-px)**2 + (y-py)**2)
	
	def reliablefit(self):					# determine if we have reliable fit of position data based on RMSD
		fit_values = self.fit()
		tilt_series = self.getCurrentTiltSeries()
		tilt_group = self.getCurrentTiltGroup()
		error = self.getPreviousError()
		
		print "cutoff: %f" % self.cutoff
		print "Std_error:"		
		print np.sqrt(sum(np.array(fit_values['std_error'])**2))
		print "Previous error: %f" % error
		print
		
		if np.sqrt(sum(np.array(fit_values['std_error'])**2)) < self.cutoff and error < self.cutoff:
			return True
		else:
			return False

	def fit(self):	
		try:		
			tilt_series = self.getCurrentTiltSeries()
			tilt_group = self.getCurrentTiltGroup()
			n_tilts = len(tilt_group.tilts)
			sequence = range(1,n_tilts+1)
			xs = tilt_group.xs
			ys = tilt_group.ys
			
			nfitpoints = min(n_tilts,self.maxfitpoints)
			assert(nfitpoints >= 2)								# have to fit atleast 2 previous points
			
			if nfitpoints <= 4:	
				seq = sequence[-nfitpoints:]
				x = xs[-nfitpoints:]
				y = ys[-nfitpoints:]					
				xslope, xintercept = linregress(seq,x)[:2]
				yslope, yintercept = linregress(seq,y)[:2]
				if nfitpoints == 2:
					xstd = None 
					ystd = None 
				else:
					xstd = np.sqrt(np.sum([(x[j]-xintercept-xslope*seq[j])**2 for j in range(nfitpoints)])/(len(sequence)-2))
					ystd = np.sqrt(np.sum([(y[j]-yintercept-yslope*seq[j])**2 for j in range(nfitpoints)])/(len(sequence)-2))
					
			else:		
				nfits = nfitpoints - 3							# fitting more than last 4 points
				xstd = np.zeros(nfits)						
				ystd = np.zeros(nfits)
				xslope = np.zeros(nfits)
				yslope = np.zeros(nfits)
				xintercept = np.zeros(nfits)
				yintercept = np.zeros(nfits)
				for i in range(nfitpoints-3):
					nfitpoints_ = nfitpoints - i
					x = xs[-nfitpoints_:]
					y = ys[-nfitpoints_:]
					seq = sequence[-nfitpoints_:]
					xs_, xi_ = linregress(seq,x)[:2]
					ys_, yi_ = linregress(seq,y)[:2]
					xslope[i] = xs_
					yslope[i] = ys_
					xintercept[i] = xi_
					yintercept[i] = yi_
					
					xstd[i] = np.sqrt(np.sum([(x[j]-xi_ - xs_*seq[j])**2 for j in range(nfitpoints_)])/(nfitpoints_-2))
					ystd[i] = np.sqrt(np.sum([(y[j]-yi_ - ys_*seq[j])**2 for j in range(nfitpoints_)])/(nfitpoints_-2))
				
				std = [sum(xy) for xy in zip(xstd,ystd)]
				allstd = std[0]
				idx_minstd = np.argmin(std)
				minstd = std[idx_minstd]
				
				if allstd/minstd < 1.3:				# accept fitting with all points 
					xstd = xstd[0]
					ystd = ystd[0]
					xslope = xslope[0]
					yslope = yslope[0]
					xintercept = xintercept[0]
					yintercept = yintercept[0]
				else:								# drop points until we get std/minstd <= 1.1
					idx = 0
					idxbest = idx_minstd
					while idx < idx_minstd:
						if std[idx]/minstd <= 1.1:
							idxbest = idx
							break
						else:
							idx += 1
					xstd = xstd[idxbest]
					ystd = ystd[idxbest]
					xslope = xslope[idxbest]
					yslope = yslope[idxbest]
					xintercept = xintercept[idxbest]
					yintercept = yintercept[idxbest]

		except Exception as e:
			import traceback
			traceback.print_exc()
			print "OIHEOIHEOIHE"
			rpdb.set_trace()
			print 	
		
		return {'slope':(xslope,yslope), 'intercept':(xintercept,yintercept), 'std_error':(xstd,ystd)}
	
	def predict(self, tilt, seq):
		debug_print(' ')
		debug_print('Predicting %.2f' % math.degrees(tilt))
		
		tilt_series = self.getCurrentTiltSeries()
		tilt_group = self.getCurrentTiltGroup()
		current_group_index = self.getCurrentTiltGroupIndex()
		n_start_fit = self.fitdata[current_group_index]
		n_smooth_fit = self.fitdata[current_group_index]
		#n_tilt_series = len(self.valid_tilt_series_list)
		n_tilt_groups = len(tilt_series)
		n_tilts = len(tilt_group.tilts)

		parameters = self.getCurrentParameters()
		debug_print('z0 at start of prediction %.2f' % parameters[-1])
		debug_print('using %d tilts' % n_tilts)
		debug_print('tilts are: %s' % tilt_group.tilts)
		
		#if n_tilts < 1:
		#	raise RuntimeError
		if n_tilts < 2:		# can't predict until at least two tilts have been processed. 
			x = None
			y = None
		else:
			# fitting is possible
			# x,y is only a smooth polynomial fit
			fit_values = self.fit()
			x = fit_values['intercept'][0] + fit_values['slope'][0]*(seq[1]+1)		# TODO: potentially have to convert units. 
			y = fit_values['intercept'][1] + fit_values['slope'][1]*(seq[1]+1)
				
		# self.parameters may be altered after model fit.
		phi, optical_axis, z0 = self.getCurrentParameters()
		
		#TODO: need to predict z from eucentric error and optical axis offset and shift during tilt? 
		z = 0

		#debug_print("z0s of all tilt series: %s" % self.parameters[current_group_index])
		#debug_print("currentparameters z0 %s" % z0)
		phi,offset = self.convertparams(phi,optical_axis)
		result = {
			'x': x,
			'y': y,
			'z': z,
			'phi': float(phi),
			'optical axis': float(offset),
			'z0': float(self.parameters[current_group_index][-1]),
		}
		debug_print('calculate result: %s' % result)
		return result

if __name__ == "__main__":
	
	import numpy as n
	import matplotlib.pyplot as plt
	#intercept = 100
	#slope = 20
	#size = 512
	cutoff = n.sqrt(2)*1000*0.02
	#maxfitpoints = 10
	#sig = 512*.02
	#tilts = n.linspace(0,n.pi/3,10)
	#sequence = n.arange(1,tilts.shape[0]+1)
	
	#prediction = [{'x':None,'y':None},{'x':None,'y':None},{}{}{}{}{},{}]
				
	sequence = [(0,i) for i in range(14)]
	measured_positions = [{'x': 861.030724, 'y': 35.631712},
						{'x': 849.655798, 'y': 38.390576},
						{'x': 842.524215, 'y': 40.413069},
						{'x': 822.733695, 'y': 45.991190},
						{'x': 793.856151, 'y': 53.321055},
						{'x': 751.217347, 'y': 68.752713},
						{'x': 703.094594, 'y': 86.922355},
						{'x': 645.646759, 'y': 95.695818},
						{'x': 577.255464, 'y': 105.772303},
						{'x': 500.428214, 'y': 115.701015},
						{'x': 415.315790, 'y': 125.503824},
						{'x': 322.313329, 'y': 137.371518},
						{'x': 219.971961, 'y': 149.002215},
						{'x': 108.673496, 'y': 162.550677},
						{'x': 975.676954, 'y': 85.903463}]


	pred = Prediction2()
	pred.setcutoff(cutoff)
	#pred.set_maxfitpoints(maxfitpoints)
	
	for i in range(len(sequence)):
		predicted_position = pred.predict(0,sequence[i])
		pred.addPosition(0, measured_positions[i], predicted_position) 	# Add measured and predicted position.

		print pred.ispredict()

