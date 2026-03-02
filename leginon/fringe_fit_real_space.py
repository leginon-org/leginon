#!/usr/env/bin python
import numpy
import scipy.ndimage as nd
import math
from scipy.optimize import curve_fit

from pyami import mrc, numpil
from leginon import lattice

def show_array(arr):
	import matplotlib.pyplot as plt
	d = 3
	vmin = arr.mean() - d * arr.std()
	vmax = arr.mean() + d * arr.std()
	plt.imshow(arr, cmap='grey', vmin=vmin, vmax=vmax)
	plt.show()

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

def getBadRotatedEdgeLengths(rot_shape, rot_angle):
	"""
	Return edge length in (row, col) that would be filled by nearest.
	"""
	bad = (abs(int(math.tan(rot_angle*math.pi/180.0)*rot_shape[1])),
			abs(int(math.tan(rot_angle*math.pi/180.0)*rot_shape[0])))
	return bad

def makeRotatedImage(arr, rot_angle):
	"""
	Rotate LPP fringe by rot_angle in degrees. Rotation is from +y-axis toward x+.
	2. Crop the array to remove edge padding.
	The center of represents the center
	of the input position.
	"""
	if rot_angle >= 45:
		while rot_angle >=45:
			arr = nd.rotate(arr, 90,mode='nearest') # angle in degrees
			rot_angle -= 90
	elif rot_angle <=-45:
		while rot_angle <=-45:
			arr = nd.rotate(arr, 90,mode='nearest') # angle in degrees
			rot_angle += 90
	shape0 = arr.shape
	if rot_angle != 0:
		arr = nd.rotate(arr, rot_angle,mode='nearest') # angle in degrees
		if __name__ == '__main__':
			show_array(arr)
		rot_shape = arr.shape
	return arr

def simu_fringe(shape, periods, phases_deg, image_rotation=0.0):
	shape0 = shape
	rot = math.radians(image_rotation)
	need_transpose = False
	if abs(math.tan(rot)) > 1:
		need_transpose = True
		while image_rotation > 45:
			image_rotation -= 90
		while image_rotation < -45:
			image_rotation += 90
	# Finel values
	rot = math.radians(image_rotation)
	abs_rot = abs(rot)
	sq_size = max(shape)
	if abs(image_rotation) > 0.5:
		# Run twice so the trimming is enough
		sq_size = int(sq_size*math.cos(abs_rot)+sq_size*math.sin(abs_rot))+2
		sq_size = int(sq_size*math.cos(abs_rot)+sq_size*math.sin(abs_rot))+2
	pad_shape = (sq_size,sq_size)
	is_xlpp = len(periods) == 2
	center = (pad_shape[0]//2, pad_shape[1]//2)
	amp = 100.0
	img = numpy.zeros(pad_shape)
	# index = 0
	axis = 0
	# first lpp is propogate along y-axis
	fringe = list(map((lambda x: amp*math.cos(math.pi*2*(x-center[axis])/periods[axis]-phases_deg[axis]*math.pi/180.0)), range(pad_shape[axis])))
	img += numpy.array(pad_shape[1]*fringe).reshape((pad_shape[1],pad_shape[0]))
	if not need_transpose:
		img = img.T
	if is_xlpp:
		# index = 1
		# second lpp is propogate along x-axis
		axis = 1
		fringe = list(map((lambda x: amp*math.cos(math.pi*2*(x-center[axis])/periods[axis]-phases_deg[axis]*math.pi/180.0)), range(pad_shape[axis])))
		img += numpy.array(pad_shape[0]*fringe).reshape((pad_shape[0],pad_shape[1]))
	if abs(image_rotation) >= 0.5:
		arr = nd.rotate(img, image_rotation, mode='nearest') # angle in degrees
		bad = getBadRotatedEdgeLengths(arr.shape, image_rotation) # (row,col)
		# remove any part that comes from nearest fill
		arr = arr[bad[0]:-bad[0],bad[1]:-bad[1]]
	else:
		arr = img 
	trimmed_shape = arr.shape
	offset = ((trimmed_shape[0]-shape0[0])//2,(trimmed_shape[1]-shape0[1])//2)
	arr = arr[offset[0]:shape0[0]+offset[0],
			offset[1]:shape0[1]+offset[1]]
	if __name__ == '__main__':
		show_array(arr)
	return arr

def makeRotatedLineProfile(arr, rot_angle):
	arr = makeRotatedImage(arr, rot_angle)
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

def run_fringe_fit(a, rotation_angle_degrees=5.0, wave_period0=None):
	"""
	Real space cosine wave fitting. Accurate rotation_angle is
	required for 1d projection.
	"""
	# unrotate the fringe.
	y_data = makeRotatedLineProfile(a, -rotation_angle_degrees)
	center_of_mass_array, area = findPeaks(y_data)
	if wave_period0 is None:
		wave_period, x_cleaned_list = estimateLattice(center_of_mass_array, area)
	else:
		wave_period = wave_period0
		x_cleaned_list =  list(map((lambda x: x[0]), center_of_mass_array.tolist()))
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
	return {
			'image_rotation': rotation_angle_degrees,
			'wave_amp': amp_fit,
			'wave_freq': freq_fit,
			'wave_phase': phase_fit,
			'value_offset': offset_fit,
			'wave_period': period_fit,
			'phase_shift_to_max': phase_shift_to_max_degrees,
	}

def run_2d_fringe_fit(a, rotations=(-10.0,90.0)):
	fit_results = {}
	for i, angle in enumerate(rotations):
		axis = i+1
		fit_results[axis] = run_fringe_fit(a, rotation_angle_degrees=angle)
	return fit_results

if __name__=='__main__':
	import os, sys
	lpp_number = int(input('number of lpp?'))
	start_n = int(input('start target number?'))
	total = int(input('total loop number?'))
	mrc_path_f = input('mrc file path format i.e. "n25jun17a_%05d.mrc"?')
	angle1 = float(input('lpp1 wavevector angle in degrees:'))
	if lpp_number == 2:
		angle2 = float(input('lpp2 wavevector angle in degrees:'))
	# End of input

	rf = '%7.2f\t shift_to_max in deg %7.2f p-p pixels\t%7.2f image rotation deg'
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
		results = run_fringe_fit(a, angle1)
		print(rf % (results['phase_shift_to_max'],results['wave_period'],results['image_rotation']))
		if lpp_number == 2:
			results = run_fringe_fit(a, angle2)
			print(rf % (results['phase_shift_to_max'],results['wave_period'],results['image_rotation']))
