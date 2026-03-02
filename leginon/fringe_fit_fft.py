#!/usr/env/bin python
import numpy
import scipy.ndimage as nd
import math
from scipy.optimize import curve_fit

from pyami import mrc, numpil, imagefun
from leginon import lattice
if __name__=='__main__':
	from leginon import fringe_fit_real_space

def get_hanning(shape):
	hanning_y = numpy.hanning(shape[0])
	hanning_x = numpy.hanning(shape[1])
	window_2d = numpy.outer(hanning_y, hanning_x)
	return window_2d

def mask_array_around_center(arr, center, radius):
	arr[center[0]-radius:center[0]+radius,center[1]-radius:center[1]+radius] = 0

def _find_peak_locations(arr, mask_radius, number):
	"""
	Return a list of peak coordinates (row,col).
	arr: 2d array input.
	mask_radius: in pixels, defines a square mask erase
	the last peak found in the iteration.
	number: number of peaks to return.
	"""
	peak_locations = []
	for i in range(number):
		max_idx = numpy.argmax(arr)
		peak_coord = numpy.unravel_index(max_idx, arr.shape)
		peak_locations.append(peak_coord)
		mask_array_around_center(arr, peak_coord, mask_radius)
	if __name__=='__main__':
		fringe_fit_real_space.show_array(arr)
	return peak_locations

def find_peak_positions(arr, number_of_peaks, mask_radius=40):
	# remove generously around center
	size = min(arr.shape)
	center = [size // 2, size // 2]
	mask_array_around_center(arr, center, mask_radius)
	peak_positions = _find_peak_locations(arr, mask_radius, number_of_peaks)
	return peak_positions

def analyze_peaks(fourier_shifted, peak_positions, clipped_size):
	"""
	Return a dictionary of data describing the diffraction peaks.
	"""
	fourier_shape = fourier_shifted.shape
	center = fourier_shifted.shape[0] // 2 # symmetric size
	number = len(peak_positions)
	p_array = numpy.array(peak_positions)
	row_indices = p_array[:,0]
	col_indices = p_array[:,1]
	values = fourier_shifted[row_indices, col_indices]
	amps = numpy.abs(values)
	phases = numpy.angle(values, deg=True)
	phase_at_center = 0
	p_array = numpy.array(peak_positions) - numpy.array(number*(center,center)).reshape((number,2))
	p_complex = p_array[:,0]+1j*p_array[:,1]
	p_freqs = numpy.abs(p_complex) # highest is fourier_size/2
	p_periods = numpy.array(number*(fourier_shape[0],)).reshape((number,))/p_freqs
	p_angs = numpy.angle(p_complex, deg=True)
	data = {}
	# return peak data with angle closest to zero and 90 degrees
	near_0_index = numpy.argmin(numpy.abs(p_angs))
	near_0_angle = p_angs[near_0_index]
	near_90_index = numpy.argmin(numpy.abs(p_angs - numpy.array(number*(near_0_angle+90,))))
	near_90_angle = p_angs[near_90_index]
	k = 0
	indices = [near_0_index]
	if number > 2:
		indices.append(near_90_index)
	for i in indices:
		key = k+1
		v = {'wave_freq': p_freqs[i],
			'image_rotation': p_angs[i],
			'wave_period': p_periods[i],
			'wave_amp': amps[i],
			'wave_phase':phases[i],
			'position': p_array[i],
			'phase_shift_to_max': -phases[i]
			}
		data[key] = v
		k += 1
	return data

def get_fft_size(clipped_size, binning):
	"""
	Return an array size to pad around the image to be used around
	array binned by binning as the input to fft2.
	"""
	# initial fft2 size
	if binning > 1:
		size = clipped_size//binning * 32 # start assuming 4 fringes
	else:
		size = clipped_size # start with clipped_size
	# keep the size in 1024 to 2048
	while size > 2048:
		size = size // 2
	while size < 1200:
		size = size * 2
	return size

def _get_rough_angle_period(img_clipped, binning, number_of_peaks, number_of_fringe_guess):
	"""
	Using Fourier space representation to find fringe angle and period.
	Based on code by Eric Cooper. Binned image is pad to move
	the diffraction peak in the fft away from the center.
	"""
	# make binned image to increase S/N
	clipped_size = img_clipped.shape[0] # symmetric
	if binning == 1:
		raise ValueError('Low binning peaks often buried in edge wrapping spike.  Please use higher binning')
	else:
		img_binned = imagefun.bin(img_clipped, binning)
		if __name__ == "__main__":
			fringe_fit_real_space.show_array(img_binned)
	size = get_fft_size(clipped_size, binning)
	img_binned_size = img_binned.shape[0] # symmetric
	# fft2 with shift
	fourier = numpy.fft.fft2(img_binned - numpy.mean(img_binned), (size,size))
	fourier_shifted = numpy.fft.fftshift(fourier)
	mask_radius = (size // number_of_fringe_guess) // 16 # keep mask smaller than 1/2 guess fringe frequency
	abs_fourier = numpy.abs(fourier_shifted)
	while True:
		peak_positions = find_peak_positions(abs_fourier.copy(), number_of_peaks, mask_radius)
			
		peak_data = analyze_peaks(fourier_shifted, peak_positions, clipped_size)
		angles = list(map((lambda x: x['image_rotation']), peak_data.values()))
		if len(angles) < 2:
			break
		# increasing mask radius in case a second peak is picked up within the same diffraction.
		delta = abs(angles[1] - angles[0])
		if delta > 45 or delta < -45:
			break
		mask_radius *= 2

	scale = clipped_size / img_binned_size
	lpp_keys = list(peak_data.keys())
	lpp_keys.sort()
	for k in lpp_keys:
		peak_data[k]['wave_period'] *= scale
		peak_data[k]['wave_freq'] /= scale
	for k in lpp_keys:
		print('period','phase','diffr angle',peak_data[k]['wave_period'],peak_data[k]['image_rotation'])
	return numpy.abs(fourier_shifted), numpy.angle(fourier_shifted), peak_data

def get_fringe_angle_period(img, number_of_peaks, number_of_fringe_guess=4):
	"""
	Using Fourier space representation to find fringe angle and period.
	binned image
	This gives peaks with accurate fringe rotation agains the image,
	rough fringe period, but poor fringe phase relative to the center.
	"""
	# make a square image that will be used in the calculation
	binning = min(img.shape)//(8*number_of_fringe_guess) # keep peak away from the center
	offset = tuple(map(lambda x: (x - (x // binning)*binning)//2, img.shape))
	clipped_size = (min(img.shape)//binning)*binning
	img_clipped = img[offset[0]:clipped_size+offset[0],
					offset[1]:clipped_size+offset[1]]
	# actually run
	rough_amp, rough_phase, rough_peaks = _get_rough_angle_period(img_clipped, binning, number_of_peaks, number_of_fringe_guess)
	lpp_keys = list(rough_peaks.keys())
	number_of_fringes = clipped_size // int(rough_peaks[lpp_keys[0]]['wave_period'])
	return rough_peaks

if __name__=='__main__':
	import os, sys
	is_xlpp = True
	number_of_peaks = 2 + 2*int(is_xlpp) # Friedel pair
	number_of_fringe_guess = 4 
	#session_image_path = '/Users/anchi.cheng/testdata/leginon/26jan23a/rawdata'
	session_image_path = '/Users/anchi.cheng/Downloads'
	filename = 'n25jun20a_00141fa.mrc'
	#filename = 'n25may28c_00094ffen.mrc'
	#filename = '26jan23a_00005en.mrc'
	#session_image_path = '/Users/anchi.cheng/Downloads'
	#filename = 'n25jul09a_00504fy.mrc'
	mrc_path = os.path.join(session_image_path, filename)
	a = mrc.read(mrc_path)
	shape = a.shape
	# alternative simulation for testing
	#a = fringe_fit_real_space.simu_fringe(shape,(200,210),(30,0), 0)
	#a = fringe_fit_real_space.simu_fringe(shape,(128.75,),(100,), 90)
	fringe_fit_real_space.show_array(a)
	#
	# This gives peaks with accurate fringe rotation agains the image,
	# rough fringe period, but poor fringe phase relative to the center.
	peaks = get_fringe_angle_period(a, number_of_peaks, number_of_fringe_guess)
	# Fit in real space once angle and rough wave_period are determined.
	rf = '%7.2f\t shift_to_max in deg %7.2f p-p pixels\t%7.2f image rotation deg'
	results = fringe_fit_real_space.run_fringe_fit(a, peaks[1]['image_rotation'], peaks[1]['wave_period'])
	print(rf % (results['phase_shift_to_max'],results['wave_period'],results['image_rotation']))
	if is_xlpp:
		results = fringe_fit_real_space.run_fringe_fit(a, peaks[2]['image_rotation'])
		print(rf % (results['phase_shift_to_max'],results['wave_period'],results['image_rotation']))
	
