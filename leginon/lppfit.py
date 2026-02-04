#!/usr/env/bin python
import numpy
import scipy.ndimage as nd
import math
from scipy.optimize import curve_fit

from pyami import mrc, numpil
from leginon import lattice, fringe_fit_real_space, fringe_fit_fft

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

def on_node_function(x, offset, tilt, amp):
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
	popt, pcov = curve_fit(on_node_function, x_data, y_data,p0=[-10,0,amp0])
	return popt #(phase_shift_to_apply at on-plane focus, amplitude for conversion)

def get_fringe_angle_period(a, number_of_lpps,number_of_fringe_guess=4):
	# Use fft diffraction peaks to get accurate angle of rotation
	number_of_peaks = number_of_lpps * 2
	peaks = fringe_fit_fft.get_fringe_angle_period(a, number_of_peaks)
	return peaks

def run_fringe_fit(a,number_of_lpps):
	peaks = get_fringe_angle_period(a, number_of_lpps)
	all_results = {}
	# Use real space fit to get accurate period and phase shift
	for n in range(number_of_lpps):
		key = n+1
		result1 = fringe_fit_real_space.run_fringe_fit(a, peaks[key]['image_rotation'], peaks[key]['wave_period'])
		all_results[key] = result1
	return all_results

def run_1d_fringe_fit(a):
	return run_fringe_fit(a,1)

def run_2d_fringe_fit(a):
	return run_fringe_fit(a,2)

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

def calculateOnPlaneOnNode(data, is_over_focus=False, display=False):
	print(data)
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
	a2 = popt[2] #2nd order amplitude
	s2 = popt[1] #slope->phase plate plane tilt
	print('pixel shift per 0.001 phase plate defocus when on-plane', s2*0.001)
	m2 = popt[0] #offset-> phase shift
	nearest_m2 = convert_phase_degrees(m2)
	print('phase_shift_needed for maximum', nearest_m2)
	# display fit results with m2 before convertion to phase shift
	# to within -180 to 180
	if display:
		show_on_node_on_plane_fit_results(x1_data, z_data, m2, s2, a2)
	return f_center, nearest_m2, s2, a2

def show_on_node_on_plane_fit_results(x_data, y_data, offset, slope, amp):
	# index sequence
	fit_data = amp*x_data*x_data + slope*x_data + offset
	#
	import matplotlib.pyplot as plt
	plt.plot(x_data, y_data, 'o', label='Data')
	plt.plot(x_data, fit_data, '-', label='Fit')
	#plt.legend()
	plt.xlabel('x')
	plt.ylabel('y')
	plt.title('Defocus sequence fitting')
	plt.show()

if __name__=='__main__':
	import os, sys
	lpp_number = int(input('number of lpp?'))
	start_n = int(input('start target number?'))
	total = int(input('total loop number?'))
	mrc_path_f = input('mrc file path format i.e. "n25jun17a_%05d.mrc"?')
	rf = '%7.2f\t%7.2f'
	rf = 'lpp%d\t%7.2f\t shift_to_max in deg %7.2f p-p pixels\t%7.2f image rotation deg'
	for i in range(total):
		n = start_n + i
		print(mrc_path_f, n)
		mrc_path = mrc_path_f % (n)
		print(mrc_path)
		if not os.access(mrc_path, os.R_OK):
			print('Error: file not accessibale')
			sys.exit(1)
		a = mrc.read(mrc_path)
		# test fitting with display
		if lpp_number == 1:
			results = run_1d_fringe_fit(a)
		else:
			results = run_2d_fringe_fit(a)
		for k in results.keys():
			r = results[k]
			print(rf % (k,r['phase_shift_to_max'],r['wave_period'],r['image_rotation']))
