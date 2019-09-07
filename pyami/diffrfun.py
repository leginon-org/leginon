#!/usr/bin/env python
import numpy
import scipy.ndimage as nd
import scipy.signal as sig
import math

import pyami.quietscipy
from pyami import imagefun, fftfun, ellipse
from pyami import mrc

def makeBeamStopMask(a, m2, scale):
	'''
	Simple rectangular mask from the left (small x) of the image.
	Also threshold the array at a multiple of standard deviation
	above the mean and return whether the area around the mask edge
	has significant intensity
	'''
	a_center = (a.shape[0]//2, a.shape[1]//2)
	# TODO: make it a round shape
	a[a_center[0]-m2*0.5:a_center[0]+m2*0.5,:a_center[1]+m2]=0
	a[a_center[0]-m2:a_center[0]+m2,a_center[1]-m2*0.5:a_center[1]+m2*0.5]=0
	a[a_center[0]-m2*0.7:a_center[0]+m2*0.7,a_center[1]-m2*0.7:a_center[1]+m2*0.7]=0
	t = a.mean()+scale*a.std()
	thresh_array = numpy.where(a < t, 0, 1)
	d = 10 #dilating distance for clearance test.
	around = thresh_array[a_center[0]-m2-d:a_center[0]+m2+d,a_center[1]-m2-d:a_center[1]+m2+d]
	if around.sum() > 0.1*m2:
		# The surrounding area has significant intensity
		return thresh_array, False
	else:
		# The surrounding area is clean
		return thresh_array, True

def _getValueStart(a, reverse=False):
	'''
	Get the first index in a 1-D binary(0,1) array that has the value 1.
	'''
	try:
		a_list = a.tolist()
		if reverse:
			a_list.reverse()
		i = a_list.index(1)
		if reverse:
			i = len(a_list)-i
	except ValueError:
		return None
	return i

def _getEndArray(thresh_array, m2):
	'''
	Get a cleanup array at the large columns of the array.
	To get a good axis 0 center estimate, the binary ring can not
	be cut off at the near corner at axis 0.
	'''
	a_shape = thresh_array.shape
	a_center = (a_shape[0]//2, a_shape[1]//2)
	end = thresh_array.copy()
	d = 1
	m2_end = m2 + 0
	end[:,:a_center[1]+m2]=0
	if end[:,-1].sum() > a_shape[0]*0.002:
		# end touch the edge
		touch_index = _getValueStart(end[0,:],False)
		if touch_index is not None:
			m2_end = touch_index-a_center[1]
		# here we check if a 10*d by 10*d area at the near corners has non-zero values.
		# push the mask boundary further if so.
		while end[:10*d,a_center[1]+m2_end:a_center[1]+m2_end+10*d].sum() > 0 or end[-10*d:-1,a_center[1]+m2_end:a_center[1]+m2_end+10*d].sum() > 0:
			end[:,a_center[1]+m2:a_center[1]+m2_end+10*d]=0
			m2_end += 10*d
	return end

def _getBottomArray(a, m2):
	return numpy.transpose(_getEndArray(numpy.transpose(a), m2))

def _getRightArray(a, m2):
	return _getEndArray(a, m2)

def getCenterOutsideMask(thresh_array,m2):
	a_shape = thresh_array.shape
	a_center = (thresh_array.shape[0]//2, thresh_array.shape[1]//2)
	#mrc.write(thresh_array,'t.mrc')
	# right
	right = _getRightArray(thresh_array, m2)
	#mrc.write(right,'right.mrc')
	right_center=nd.measurements.center_of_mass(right)
	# bottom
	bottom = _getBottomArray(thresh_array, m2)
	#mrc.write(bottom,'bottom.mrc')
	bottom_center=nd.measurements.center_of_mass(bottom)

	# assemble center
	center = (right_center[0],bottom_center[1])
	return center

def findCenter(a):
	last_c = (a.shape[0]/2.0, a.shape[1]/2.0)
	# mask beam stop and low resolution
	a_shape_min = min(a.shape)
	# fine steps.
	for m_factor in (0.15,0.175,0.2,0.225,0.25,0.275,0.3,0.35,0.375):
		# half masksize
		masksize = int(m_factor*a_shape_min)
		m2 = masksize//2
		if m_factor < 0.2:
			# diffraction images with rings closer to origin is stronger
			scale=5
		elif 0.2 <= m_factor and m_factor < 0.25:
			scale=4
		elif 0.25 <= m_factor and m_factor < 0.275:
			scale=3.5
		else:
			scale=3
		thresh_array, is_clean_around_mask = makeBeamStopMask(a, m2, scale)
		c = getCenterOutsideMask(thresh_array,m2)
		if is_clean_around_mask:
			last_c = c
			break
		if int(last_c[0]) == int(c[0]) and int(last_c[1]) == int(c[1]):
			break
		last_c = c
	return last_c

def calculateRadialAverage(a, center):
	'''
	Get 1D array of the radial value averaged over all angles.
	'''
	#maximal radius. Use to crop to square array
	r = min(int(center[0]),int(a.shape[0]-center[0]),int(center[1]),int(a.shape[1]-center[1]))
	r -= 1 # minus one in case of truncation error.
	sq_a = a[center[0]-r:center[0]+r,center[1]-r:center[1]+r]
	nbin_t = 1
	pbin,r_centers,t_center = imagefun.polarBin(sq_a, min(sq_a.shape),nbin_t)
	# r_centers are the radius values of each bin.
	return r_centers,pbin[:,0]

def calculateCameraLength(d_spacing, radius, ht, cam_psize,image_bin):
	'''
	Camera length calculation
	d_spacing in Angstrum
	radius in binned pixels
	ht in volts
	cam_psize in meters
	image_bin as integer
	'''
	wavelength = fftfun.getElectronWavelength(ht)
	pixel_ring_diameter = radius*2 #pixels
	# camera physical pixel size in meters
	meter_ring_diameter = pixel_ring_diameter*cam_psize*image_bin
	theta = math.asin((wavelength*1e10)/(2*d_spacing)) #radians
	camera_length = meter_ring_diameter/2.0/(math.tan(2*theta)) #meters
	rpixel_size = 1/(radius*d_spacing*1e-10)
	return camera_length, rpixel_size

def getCompleteResolution(a, center, cam_length, ht, cam_psize,image_bin):
	'''
	Calculate the highest resolution in meters that has 100 % completeness.
	cam_length in meters
	center in binned pixels
	ht in volts
	cam_psize in meters
	image_bin as integer
	'''
	#maximal radius. Use to crop to square array
	complete_edge_radius = min(int(center[0]),int(a.shape[0]-center[0]),int(center[1]),int(a.shape[1]-center[1]))
	pixel_ring_diameter = complete_edge_radius*2 # binned pixels
	meter_ring_diameter = pixel_ring_diameter*cam_psize*image_bin
	wavelength = fftfun.getElectronWavelength(ht)
	d_spacing = wavelength/(math.atan2(meter_ring_diameter/2.0, cam_length))
	edge_res = d_spacing
	return edge_res # meters

def calibrate(a, ht, cam_psize, image_bin):
	'''
	Calibrate the input diffraction pattern against Au-Pd diffraction
	of cross-grating replica standard.  Must have at least the first
	diffraction ring present at corners if not complete.
	'''
	center = findCenter(a)
	r_centers, radial_value = calculateRadialAverage(a, center)
	# order is used to low-pass filter the value to return only relmax in broader
	# peaks.
	(peaks,) = sig.argrelmax(radial_value, order=40)
	# Cross-Grating Au-Pd (222 is removed because it shows as a shoulder
	d = [2.31,2.00,1.41,1.21,1.00]
	i = 0
	cam_lengths = []
	for p in peaks.tolist():
		if i < 1 and radial_value[p] < radial_value.mean()+3*radial_value.std():
			# first peak may be from scattering around the beam stop. Ignore is if weak.
			continue
		if i >= len(d):
			break
		position = r_centers[p]
		cam_length,r_pixel = calculateCameraLength(d[i], position, ht, cam_psize,image_bin)
		#print p, position, cam_length
		cam_lengths.append(cam_length)
		i += 1
	return cam_lengths, center, radial_value

def test(a, ht, cam_psize, image_bin):
	cam_lengths, center, radial_values = calibrate(a, ht, cam_psize, image_bin)
	print('center(pixels): x=%.1f, y=%.1f' % (center[1],center[0]))
	if cam_lengths:
		avg_cam_length = numpy.array(cam_lengths).mean()
		std_cam_length_str = ''
		if len(cam_lengths) > 1:
			std_cam_length = numpy.array(cam_lengths).std()
			std_cam_length_str = '+/-%.3f' % (std_cam_length)
			if std_cam_length > 0.05:
				print('suspecious', center, cam_lengths)
		edge_res = getCompleteResolution(a, center, avg_cam_length, ht, cam_psize,image_bin)
		print('cam_length(m) = %.3f%s (n=%d) edge_res(Angs) = %.2f' % (avg_cam_length, std_cam_length_str, len(cam_lengths), edge_res*1e10))
	try:
		plot(radial_values)
	except:
		pass

def plot(values):
	import matplotlib.pyplot as pyplot
	fig = pyplot.figure(1)
	pyplot.plot(range(len(values)), values,'-')
	pyplot.show()

if __name__=='__main__':
	import sys
	imagepath = sys.argv[1]
	a = mrc.read(imagepath)
	test(a, 200000, 1.4e-5, 2)
