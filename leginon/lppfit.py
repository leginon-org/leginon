#!/usr/env/bin python
import numpy
import scipy.ndimage as nd
import math
from scipy.optimize import curve_fit

from pyami import mrc, numpil
from leginon import lattice

def makeRotatedLineProfile(arr, rot_angle):
	"""
	Return 1D array of intensity profile of LPP fringe with these steps:
	1. Rotate LPP fringe by rot_angle in degrees. Rotation is from y-axis toward x+.
	2. Crop the array to remove edge padding.
	3. Sum over x axis to return 1D array.

	The returning profile has a smaller dimension than the input y dimension depending
	on the rotation angle, while the center of the profile represents the center
	of the input position.
	"""
	shape0 = arr.shape
	if rot_angle != 0:
		arr = nd.rotate(arr, rot_angle,mode='nearest') # angle in degrees
		rot_shape = arr.shape
		# remove any part that comes from nearest fill
		bad = (int(math.tan(rot_angle*math.pi/180.0)*rot_shape[1]),
				int(math.tan(rot_angle*math.pi/180.0)*rot_shape[0]))
		arr = arr[bad[0]:-bad[0],bad[1]:-bad[1]]
	final = numpy.sum(arr, axis=1)
	return final

def findPeaks(y_data):
	"""
	Return positions of center of mass on peaks and valleys of unknown sine-like ripple.
	This is used instead of curve fitting because a reasonable starting frequency guess
	is needed for reliable incomplete sine wave fitting at very low frequency.
	"""
	offset = y_data.mean()
	amp = (y_data.max()-y_data.min()) / 2.0
	threshold_max = offset + amp * 0.5
	threshold_min = offset - amp * 0.5
	binary_data = numpy.where( abs(y_data - offset) > amp*0.5, 1,0) 
	binary_data = nd.binary_dilation(binary_data).astype(binary_data.dtype)
	binary_data = nd.binary_erosion(binary_data).astype(binary_data.dtype)
	l, num_labels = nd.label(binary_data)
	label_seq = list(map(lambda x:x+1, range(num_labels)))
	area = nd.sum_labels(binary_data, l, index=label_seq).tolist()
	c = numpy.array(nd.center_of_mass(y_data, l,label_seq))
	return c, area

def bestPointsToLattice(positions):
	"""
	Return positions that fits an estimated wave period in pixels.
	"""
	if len(positions) < 3:
		raise ValueError('Too few positions for reliable determination')
	positions.sort()
	center_index = len(positions) // 2
	center = positions[center_index]
	# use maximum of distance around the center in case one of them is shorter
	# than the lattice from local peak
	base_lattice = max(abs(positions[center_index+1]-center), abs(positions[center_index-1]-center))
	#make 2D points so we can use leginon.lattice
	temp_positions = list(positions)
	points = [(center,0),]
	points.extend(list(map((lambda x: (x,0)), temp_positions)))
	temp_positions.remove(center)
	points.extend(list(map((lambda x: (0,x)), temp_positions)))
	lat = lattice.pointsToLattice(points, base_lattice, 0.05, False)
	best_lattice_points = lat.points
	# convert back to 1D list
	best_positions = list(map((lambda x: x[0]), best_lattice_points))
	best_positions.sort()
	return best_positions, abs(lat.matrix[0,0])

def fit_cosine(x_data, y_data, amp0, freq0, phase0, offset0, x_center):
	def cosine_function(x, amp, freq, phase, offset):
		return amp * numpy.cos(freq * (x-x_center) + phase) + offset
	popt, pcov = curve_fit(cosine_function, x_data, y_data, p0=[amp0, freq0, phase0, offset0])
	return popt, pcov

def estimateLattice(center_of_mass_array, area):
	"""
	Return positions that fits an estimated wave period in pixels.
	"""
	cleaned_indices = list(filter(lambda x:area[x] > 10,range(len(area))))
	c_list = center_of_mass_array.tolist()
	cleaned_list = list(map((lambda x: c_list[x][0]), cleaned_indices))
	c_cleaned = numpy.array(cleaned_list)
	cleaned_points, lattice_spacing_half = bestPointsToLattice(cleaned_list)
	lattice_spacing = lattice_spacing_half*2
	return lattice_spacing, cleaned_points

def convert_phase(radians):
	while radians <= -math.pi:
		radians += math.pi*2
	while radians > math.pi:
		radians -= math.pi*2
	return radians

def convert_phase_degrees(phase_degrees):
	"""
	Keep the value between -180 and 180 degrees
	"""
	return (180.0/math.pi)*convert_phase(phase_degrees*math.pi/180)

def on_plane_function_left(x, center, amp):
	"""
	Return laser fringe period for x1 focus value in over-focus conditions.
	x < center
	"""
	return amp*(1/(x-center))

def on_plane_function_right(x, center, amp):
	"""
	Return laser fringe period for x1 focus value in under-focus conditions.
	x > center
	"""
	return amp*(1/(x-center))

def fit_on_plane(x_data, y_data, is_over_focus):
	"""
	Return fitted on_plane focus
	"""
	center0 = abs((x_data[0]*y_data[0]-x_data[1]*y_data[1])/(y_data[0]-y_data[1]))
	if is_over_focus:
		popt, pcov = curve_fit(on_plane_function_right, x_data, y_data,p0=[center0,1])
	else:
		popt, pcov = curve_fit(on_plane_function_left, x_data, y_data,p0=[center0,1])
	return popt # (focus_center, amplitude)

def on_node_function(x, offset, amp, tilt):
	"""
	Return phase shift offset for on-node condition.  This is a
	Second order polynomial centered at laser phane x1 focus.
	"""
	return amp*x*x+tilt*x+ offset

def fit_on_node(x_data, y_data):
	"""
	fit phase shift as y_data vs defocus from laser plane as x_data
	as the on_node_function.
	"""
	amp0 = (y_data[-1]-y_data[-2])/(x_data[-1]**2-x_data[-2]**2)
	popt, pcov = curve_fit(on_node_function, x_data, y_data,p0=[-10,amp0,0])
	return popt #(phase_shift_to_apply at on-plane focus, amplitude for conversion)

def show_fringe_fit_results(x_data, y_data, x_center, amp_fit, freq_fit, phase_fit, offset_fit):
	# index sequence
	fit_data = amp_fit * numpy.cos(freq_fit * (x_data-x_center) + phase_fit) + offset_fit
	#
	import matplotlib.pyplot as plt
	plt.plot(x_data, y_data, 'o', label='Data')
	plt.plot(x_data, fit_data, '-', label='Fit')
	#plt.legend()
	plt.xlabel('x')
	plt.ylabel('y')
	plt.title('Sine wave fitting')
	plt.show()

def run_fringe_fit(a, rotation_angle_degrees=5.0):
	y_data = makeRotatedLineProfile(a, rotation_angle_degrees)
	center_of_mass_array, area = findPeaks(y_data)
	wave_period, x_cleaned_list = estimateLattice(center_of_mass_array, area)
	# fitting
	freq0 = math.pi*2/wave_period
	x_center = y_data.shape[0]//2
	x_data = numpy.array(range(y_data.shape[0]))
	y_cleaned = numpy.array(list(map((lambda x: y_data[int(x)]), x_cleaned_list)))
	popt, pcov = fit_cosine(x_data, y_data, (y_data.max()-y_data.min())/2, freq0, 0.0, y_cleaned.mean(), x_center)
	amp_fit, freq_fit, phase_fit, offset_fit = popt
	if amp_fit < 0:
		amp_fit = abs(amp_fit)
		phase_fit = phase_fit - math.pi
	period_fit = math.pi*2/freq_fit
	phase_shift_to_max_degrees = 180.0 * convert_phase(phase_fit) / math.pi
	if __name__=='__main__':
		show_fringe_fit_results(x_data, y_data, x_center, amp_fit, freq_fit, phase_fit, offset_fit)
	return amp_fit, freq_fit, phase_fit, offset_fit, period_fit, phase_shift_to_max_degrees

def convertPhasesToContinuous(x1_data, z_data):
	x1_list = x1_data.tolist()
	min_index = 0 # The value ar x1 losest to zero
	z0 = z_data[min_index]
	# use closest to zero to start
	if abs(z0+360) < abs(z0):
		z0 = z0+360
	for i,z in enumerate(z_data.tolist()):
		if i == 0:
			z_data[0] = z0
		else:
			if abs(z-z_data[i-1]) > abs(360.0+z-z_data[i-1]):
				z_data[i] += 360.0
			if abs(z-z_data[i-1]) > abs(z-360.0-z_data[i-1]):
				z_data[i] -= 360.0
	return z_data

def calculateOnPlaneOnNode(data, is_over_focus=False):
	start, end = 0, data.shape[0]
	# on-plane phase plate focus is popt[0]
	x_data = data[start:end,0]
	y_data = data[start:end:,1]
	z_data = data[start:end:,2]
	popt = fit_on_plane(x_data, y_data, is_over_focus)
	f_center = popt[0]
	a1 = popt[1]
	print('focus_center', f_center)
	# on-node fit uses f_center as x offset
	x1_data = x_data - numpy.ones(x_data.shape)*f_center
	z_data = convertPhasesToContinuous(x1_data, z_data)
	popt = fit_on_node(x1_data, z_data)
	a2 = popt[1]
	m2 = popt[0]
	print('phase_shift_needed for maximum', m2)
	return f_center, m2

if __name__=='__main__':
	import os, sys
	mrc_path = input('mrc file path ?')
	if not os.access(mrc_path, os.R_OK):
		print('Error: file not accessibale')
		sys.exit(1)
	a = mrc.read(mrc_path)
	# test fitting with display
	amp_fit, freq_fit, phase_fit, offset_fit, period_fit, phase_shift_to_max_degrees = run_fringe_fit(a, 5.0)
	print(phase_fit, phase_shift_to_max_degrees)
