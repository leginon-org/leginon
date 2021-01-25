#!/usr/bin/env python
'''
This script is used to characterize the rolling shutter movie
saving of a camera in its on-set delay and variation of the
real frame time at different requested frame time.
It loops through a series of
rolling shutter movie frame time so to find the delay of
frame saving on-set and variation in the total time.

Direct modification is required within the script below to
set to your camera.  Example is provided for simulated camera
and, in comment, Ceta or CetaD camera.
'''
#-----------------------
# change these for your testing
#-----------------------
# import the module of your camera
#from pyscope import feicam
from pyscope import simccdcamera2
# create instance of this camera
#c = feicam.Ceta()
#movie_dir = c.getFeiConfig('camera','tia_exported_data_dir')
c = simccdcamera2.SimCCDCamera()
movie_dir = './'
# total length of movie in seconds
movie_time = 20.0
#------------------------
# no change required below
#------------------------
import time
import os
import glob
import math

def cleanUp(paths=[]):
	for p in paths:
		if not os.path.isdir(p):
			os.remove(p)
		else:
			shutil.rmtree(p)

def testCameraSpeed(cam_obj, movie_time, exp_time_ms):
	display_scale = 1
	display_unit = 'ms'

	calc_nframes = int(math.ceil(movie_time * 1000.0 / exp_time_ms))
	print '-----'
	print 'expected number of frames for %.1f ms frame_time is\t %d' % (exp_time_ms, calc_nframes)
	file_code = '%d_%d' % (int(movie_time), int(exp_time_ms))
	filename = file_code +'.bin'
	cam_obj.setExposureTime(exp_time_ms)
	t0 = time.time()
	cam_obj.startMovie(filename, exp_time_ms)
	time.sleep(movie_time)
	cam_obj.stopMovie(filename, exp_time_ms)
	t1 = time.time()
	real_time = t1 - t0
	print 'save movie at %.1f %s took\t %8.3f seconds' % (exp_time_ms, display_unit, real_time)
	movie_pattern = os.path.join(movie_dir, file_code + '*')
	movies = glob.glob(movie_pattern)
	#print movies
	cleanUp(movies)
	series_length = cam_obj.getSeriesLength()
	print 'difference in series length is %d' % (series_length - calc_nframes)

def loop(cam_obj, center_time, step_time, half_loop_number):
	'''
	Equally spaced time loop centered around a value.
	time in ms
	'''
	loop_number = half_loop_number*2 + 1
	for i in range(loop_number):
		target_time = (i-half_loop_number)*step_time + center_time
		if target_time >=movie_time*1000 or target_time < 50:
			print 'invalid target time: %.2f seconds, ignored' %(target_time)
			continue
		testCameraSpeed(cam_obj, movie_time, target_time)

if __name__ == '__main__':
	print "Edit file to set instrument"
	# Check from 40 s to 140 ms target time
	# milliseconds
	loop(c, 800, 100, 2)
