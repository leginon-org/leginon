#!/usr/bin/env python

from __future__ import division
import matplotlib
matplotlib.use('Agg')  #Removes the X11 requirement for pylab
import os
import sys
import glob
import time
import scipy
import scipy.interpolate
import pylab
import subprocess
import numpy as np
import multiprocessing as mp
import matplotlib.pyplot as plt
from appionlib import apDisplay
from appionlib.apImage import imagenorm
from pyami import mrc
from pyami import imagefun as imfun
from PIL import Image
from PIL import ImageDraw

try:
	from appionlib import apDatabase
	from appionlib import apTomo
except:
	apDisplay.printWarning("MySQLdb not found...database retrieval disabled")


def angstromsToProtomo(options):
	"""
	Dirty but reliable way to convert Angstroms to protomo units.
	"""
	options.lp=round((options.lowpass_diameter_x+options.lowpass_diameter_y)/2,1)
	options.r1_lp=round((options.r1_lowpass_diameter_x+options.r1_lowpass_diameter_y)/2,1)
	options.r2_lp=round((options.r2_lowpass_diameter_x+options.r2_lowpass_diameter_y)/2,1)
	options.r3_lp=round((options.r3_lowpass_diameter_x+options.r3_lowpass_diameter_y)/2,1)
	options.r4_lp=round((options.r4_lowpass_diameter_x+options.r4_lowpass_diameter_y)/2,1)
	options.r5_lp=round((options.r5_lowpass_diameter_x+options.r5_lowpass_diameter_y)/2,1)
	options.r6_lp=round((options.r6_lowpass_diameter_x+options.r6_lowpass_diameter_y)/2,1)
	options.r7_lp=round((options.r7_lowpass_diameter_x+options.r7_lowpass_diameter_y)/2,1)
	options.r8_lp=round((options.r8_lowpass_diameter_x+options.r8_lowpass_diameter_y)/2)
	options.map_size_z=int(2*options.thickness/options.map_sampling)
	
	try:
		options.thickness = options.thickness/options.pixelsize
	except:
		pass
	try:
		options.lowpass_diameter_x = 2*options.pixelsize*options.sampling/options.lowpass_diameter_x
	except:
		pass
	try:
		options.lowpass_diameter_y = 2*options.pixelsize*options.sampling/options.lowpass_diameter_y
	except:
		pass
	try:
		options.highpass_diameter_x = 2*options.pixelsize*options.sampling/options.highpass_diameter_x
	except:
		pass
	try:
		options.highpass_diameter_y = 2*options.pixelsize*options.sampling/options.highpass_diameter_y
	except:
		pass
	try:
		options.lowpass_apod_x = 2*options.pixelsize*options.sampling/options.lowpass_apod_x
	except:
		pass
	try:
		options.lowpass_apod_y = 2*options.pixelsize*options.sampling/options.lowpass_apod_y
	except:
		pass
	try:
		options.highpass_apod_x = 2*options.pixelsize*options.sampling/options.highpass_apod_x
	except:
		pass
	try:
		options.highpass_apod_y = 2*options.pixelsize*options.sampling/options.highpass_apod_y
	except:
		pass
	try:
		options.r1_lowpass_diameter_x = 2*options.pixelsize*options.r1_sampling/options.r1_lowpass_diameter_x
	except:
		pass
	try:
		options.r1_lowpass_diameter_y = 2*options.pixelsize*options.r1_sampling/options.r1_lowpass_diameter_y
	except:
		pass
	try:
		options.r1_highpass_diameter_x = 2*options.pixelsize*options.r1_sampling/options.r1_highpass_diameter_x
	except:
		pass
	try:
		options.r1_highpass_diameter_y = 2*options.pixelsize*options.r1_sampling/options.r1_highpass_diameter_y
	except:
		pass
	try:
		options.r1_lowpass_apod_x = 2*options.pixelsize*options.r1_sampling/options.r1_lowpass_apod_x
	except:
		pass
	try:
		options.r1_lowpass_apod_y = 2*options.pixelsize*options.r1_sampling/options.r1_lowpass_apod_y
	except:
		pass
	try:
		options.r1_highpass_apod_x = 2*options.pixelsize*options.r1_sampling/options.r1_highpass_apod_x
	except:
		pass
	try:
		options.r1_highpass_apod_y = 2*options.pixelsize*options.r1_sampling/options.r1_highpass_apod_y
		options.r1_body=(options.thickness/options.map_sampling)/options.cos_alpha
	except:
		pass
	try:
		options.r2_lowpass_diameter_x = 2*options.pixelsize*options.r2_sampling/options.r2_lowpass_diameter_x
	except:
		pass
	try:
		options.r2_lowpass_diameter_y = 2*options.pixelsize*options.r2_sampling/options.r2_lowpass_diameter_y
	except:
		pass
	try:
		options.r2_highpass_diameter_x = 2*options.pixelsize*options.r2_sampling/options.r2_highpass_diameter_x
	except:
		pass
	try:
		options.r2_highpass_diameter_y = 2*options.pixelsize*options.r2_sampling/options.r2_highpass_diameter_y
	except:
		pass
	try:
		options.r2_lowpass_apod_x = 2*options.pixelsize*options.r2_sampling/options.r2_lowpass_apod_x
	except:
		pass
	try:
		options.r2_lowpass_apod_y = 2*options.pixelsize*options.r2_sampling/options.r2_lowpass_apod_y
	except:
		pass
	try:
		options.r2_highpass_apod_x = 2*options.pixelsize*options.r2_sampling/options.r2_highpass_apod_x
	except:
		pass
	try:
		options.r2_highpass_apod_y = 2*options.pixelsize*options.r2_sampling/options.r2_highpass_apod_y
	except:
		pass
	try:
		options.r3_lowpass_diameter_x = 2*options.pixelsize*options.r3_sampling/options.r3_lowpass_diameter_x
	except:
		pass
	try:
		options.r3_lowpass_diameter_y = 2*options.pixelsize*options.r3_sampling/options.r3_lowpass_diameter_y
	except:
		pass
	try:
		options.r3_highpass_diameter_x = 2*options.pixelsize*options.r3_sampling/options.r3_highpass_diameter_x
	except:
		pass
	try:
		options.r3_highpass_diameter_y = 2*options.pixelsize*options.r3_sampling/options.r3_highpass_diameter_y
	except:
		pass
	try:
		options.r3_lowpass_apod_x = 2*options.pixelsize*options.r3_sampling/options.r3_lowpass_apod_x
	except:
		pass
	try:
		options.r3_lowpass_apod_y = 2*options.pixelsize*options.r3_sampling/options.r3_lowpass_apod_y
	except:
		pass
	try:
		options.r3_highpass_apod_x = 2*options.pixelsize*options.r3_sampling/options.r3_highpass_apod_x
	except:
		pass
	try:
		options.r3_highpass_apod_y = 2*options.pixelsize*options.r3_sampling/options.r3_highpass_apod_y
	except:
		pass
	try:
		options.r4_lowpass_diameter_x = 2*options.pixelsize*options.r4_sampling/options.r4_lowpass_diameter_x
	except:
		pass
	try:
		options.r4_lowpass_diameter_y = 2*options.pixelsize*options.r4_sampling/options.r4_lowpass_diameter_y
	except:
		pass
	try:
		options.r4_highpass_diameter_x = 2*options.pixelsize*options.r4_sampling/options.r4_highpass_diameter_x
	except:
		pass
	try:
		options.r4_highpass_diameter_y = 2*options.pixelsize*options.r4_sampling/options.r4_highpass_diameter_y
	except:
		pass
	try:
		options.r4_lowpass_apod_x = 2*options.pixelsize*options.r4_sampling/options.r4_lowpass_apod_x
	except:
		pass
	try:
		options.r4_lowpass_apod_y = 2*options.pixelsize*options.r4_sampling/options.r4_lowpass_apod_y
	except:
		pass
	try:
		options.r4_highpass_apod_x = 2*options.pixelsize*options.r4_sampling/options.r4_highpass_apod_x
	except:
		pass
	try:
		options.r4_highpass_apod_y = 2*options.pixelsize*options.r4_sampling/options.r4_highpass_apod_y
	except:
		pass
	try:
		options.r5_lowpass_diameter_x = 2*options.pixelsize*options.r5_sampling/options.r5_lowpass_diameter_x
	except:
		pass
	try:
		options.r5_lowpass_diameter_y = 2*options.pixelsize*options.r5_sampling/options.r5_lowpass_diameter_y
	except:
		pass
	try:
		options.r5_highpass_diameter_x = 2*options.pixelsize*options.r5_sampling/options.r5_highpass_diameter_x
	except:
		pass
	try:
		options.r5_highpass_diameter_y = 2*options.pixelsize*options.r5_sampling/options.r5_highpass_diameter_y
	except:
		pass
	try:
		options.r5_lowpass_apod_x = 2*options.pixelsize*options.r5_sampling/options.r5_lowpass_apod_x
	except:
		pass
	try:
		options.r5_lowpass_apod_y = 2*options.pixelsize*options.r5_sampling/options.r5_lowpass_apod_y
	except:
		pass
	try:
		options.r5_highpass_apod_x = 2*options.pixelsize*options.r5_sampling/options.r5_highpass_apod_x
	except:
		pass
	try:
		options.r5_highpass_apod_y = 2*options.pixelsize*options.r5_sampling/options.r5_highpass_apod_y
	except:
		pass
	try:
		options.r6_lowpass_diameter_x = 2*options.pixelsize*options.r6_sampling/options.r6_lowpass_diameter_x
	except:
		pass
	try:
		options.r6_lowpass_diameter_y = 2*options.pixelsize*options.r6_sampling/options.r6_lowpass_diameter_y
	except:
		pass
	try:
		options.r6_highpass_diameter_x = 2*options.pixelsize*options.r6_sampling/options.r6_highpass_diameter_x
	except:
		pass
	try:
		options.r6_highpass_diameter_y = 2*options.pixelsize*options.r6_sampling/options.r6_highpass_diameter_y
	except:
		pass
	try:
		options.r6_lowpass_apod_x = 2*options.pixelsize*options.r6_sampling/options.r6_lowpass_apod_x
	except:
		pass
	try:
		options.r6_lowpass_apod_y = 2*options.pixelsize*options.r6_sampling/options.r6_lowpass_apod_y
	except:
		pass
	try:
		options.r6_highpass_apod_x = 2*options.pixelsize*options.r6_sampling/options.r6_highpass_apod_x
	except:
		pass
	try:
		options.r6_highpass_apod_y = 2*options.pixelsize*options.r6_sampling/options.r6_highpass_apod_y
	except:
		pass
	try:
		options.r7_lowpass_diameter_x = 2*options.pixelsize*options.r7_sampling/options.r7_lowpass_diameter_x
	except:
		pass
	try:
		options.r7_lowpass_diameter_y = 2*options.pixelsize*options.r7_sampling/options.r7_lowpass_diameter_y
	except:
		pass
	try:
		options.r7_highpass_diameter_x = 2*options.pixelsize*options.r7_sampling/options.r7_highpass_diameter_x
	except:
		pass
	try:
		options.r7_highpass_diameter_y = 2*options.pixelsize*options.r7_sampling/options.r7_highpass_diameter_y
	except:
		pass
	try:
		options.r7_lowpass_apod_x = 2*options.pixelsize*options.r7_sampling/options.r7_lowpass_apod_x
	except:
		pass
	try:
		options.r7_lowpass_apod_y = 2*options.pixelsize*options.r7_sampling/options.r7_lowpass_apod_y
	except:
		pass
	try:
		options.r7_highpass_apod_x = 2*options.pixelsize*options.r7_sampling/options.r7_highpass_apod_x
	except:
		pass
	try:
		options.r7_highpass_apod_y = 2*options.pixelsize*options.r7_sampling/options.r7_highpass_apod_y
	except:
		pass
	try:
		options.r8_lowpass_diameter_x = 2*options.pixelsize*options.r8_sampling/options.r8_lowpass_diameter_x
	except:
		pass
	try:
		options.r8_lowpass_diameter_y = 2*options.pixelsize*options.r8_sampling/options.r8_lowpass_diameter_y
	except:
		pass
	try:
		options.r8_highpass_diameter_x = 2*options.pixelsize*options.r8_sampling/options.r8_highpass_diameter_x
	except:
		pass
	try:
		options.r8_highpass_diameter_y = 2*options.pixelsize*options.r8_sampling/options.r8_highpass_diameter_y
	except:
		pass
	try:
		options.r8_lowpass_apod_x = 2*options.pixelsize*options.r8_sampling/options.r8_lowpass_apod_x
	except:
		pass
	try:
		options.r8_lowpass_apod_y = 2*options.pixelsize*options.r8_sampling/options.r8_lowpass_apod_y
	except:
		pass
	try:
		options.r8_highpass_apod_x = 2*options.pixelsize*options.r8_sampling/options.r8_highpass_apod_x
	except:
		pass
	try:
		options.r8_highpass_apod_y = 2*options.pixelsize*options.r8_sampling/options.r8_highpass_apod_y
	except:
		pass
	return options


def hyphen_range(s):
	"""
	Takes a range in form of "a-b" and generate a list of numbers between a and b inclusive.
	also accepts comma separated ranges like "a-b,c-d,f" will build a list which will include
	numbers from a to b, a to d, and f.
	Taken from http://code.activestate.com/recipes/577279-generate-list-of-numbers-from-hyphenated-and-comma/
	"""
	s="".join(s.split())#removes white space
	r=set()
	for x in s.split(','):
	    t=x.split('-')
	    if len(t) not in [1,2]: raise SyntaxError("hash_range is given its arguement as "+s+" which seems not correctly formated.")
	    r.add(int(t[0])) if len(t)==1 else r.update(set(range(int(t[0]),int(t[1])+1)))
	l=list(r)
	l.sort()
	return l


def nextLargestSize(limit):
	'''
	This returns the next largest integer that is divisible by 2, 3, 5, or 7, for FFT purposes.
	Algorithm by Scott Stagg.
	'''
	def lowestRoots(n,factor):
		r=n%factor
		p=n//factor
		while r==0 and p > factor:
			r=p%factor
			p=p//factor
		if p==factor and r==0:
			return p
		else:
			return p*factor+r
	
	primes=[2,3,5,7]
	good=[]
	for n in range(0,limit,2):
		lowest=lowestRoots(n,primes[0])
		if lowest==primes[0]:
			good.append(n)
		else:
			for p in primes[1:]:
				lowest=lowestRoots(lowest,p)
				if lowest==p:
					good.append(n)
					break
	return int(good[-1])


def removeHighlyShiftedImages(tiltfile, dimx, dimy, shift_limit, angle_limit):
	'''
	This removes the entry in the tiltfile for any shifts greater than shift_limit*dimension/100, if tilt is >= angle_limit.
	'''
	#Get image count from tlt file by counting how many lines have ORIGIN in them.
	cmd1="awk '/ORIGIN /{print}' %s | wc -l" % (tiltfile)
	proc=subprocess.Popen(cmd1, stdout=subprocess.PIPE, shell=True)
	(numimages, err) = proc.communicate()
	numimages=int(numimages)
	cmd2="awk '/IMAGE /{print $2}' %s | head -n +1" % (tiltfile)
	proc=subprocess.Popen(cmd2, stdout=subprocess.PIPE, shell=True)
	(tiltstart, err) = proc.communicate()
	tiltstart=int(tiltstart)
	
	with open(tiltfile) as f:
		lines=f.readlines()
	f.close()
	
	cmd="cp %s %s/original.tlt" % (tiltfile, os.path.dirname(tiltfile))
	os.system(cmd)
	
	bad_images=[]
	bad_kept_images=[]
	for i in range(tiltstart,numimages+tiltstart+1):
		#Get information from tlt file. This needs to versatile for differently formatted .tlt files, so awk it is.
		cmd1="awk '/IMAGE %s /{print}' %s | awk '{for (j=1;j<=NF;j++) if($j ~/ORIGIN/) print $(j+2)}'" % (i, tiltfile)
		proc=subprocess.Popen(cmd1, stdout=subprocess.PIPE, shell=True)
		(originx, err) = proc.communicate()
		originx=float(originx)
		cmd2="awk '/IMAGE %s /{print}' %s | awk '{for (j=1;j<=NF;j++) if($j ~/ORIGIN/) print $(j+3)}'" % (i, tiltfile)
		proc=subprocess.Popen(cmd2, stdout=subprocess.PIPE, shell=True)
		(originy, err) = proc.communicate()
		originy=float(originy)
		cmd3="awk '/IMAGE %s /{print}' %s | awk '{for (j=1;j<=NF;j++) if($j ~/TILT/) print $(j+2)}'" % (i, tiltfile)
		proc=subprocess.Popen(cmd3, stdout=subprocess.PIPE, shell=True)
		(tilt_angle, err) = proc.communicate()
		tilt_angle=float(tilt_angle)
		
		#Identify tilt images from .tlt file whose shift(s) exceed limits
		if (abs(dimx/2 - originx) > shift_limit*dimx/100) or (abs(dimy/2 - originy) > shift_limit*dimy/100):
			#If it's not a high tilt angle, then add it to the bad kept image list.
			if (abs(tilt_angle) >= angle_limit):
				bad_images.append(i)
			else:
				bad_kept_images.append(i)
	
	#Remove tilt images from .tlt file if shifts exceed limits and replace old tilt file
	if bad_images:
		with open(tiltfile,"w") as newtiltfile:
			for line in lines:
				if not any('IMAGE %s ' % (bad_image) in line for bad_image in bad_images):
					newtiltfile.write(line)
		newtiltfile.close()
	
	return bad_images, bad_kept_images


def removeDarkorBrightmages(tiltfile):
	'''
	This removes the entry in the tiltfile for any images whose average pixel values exceed N*stdev from the mean.
	This may be unecessary so it hasn't been implemented. Maybe later?
	'''
	image=mrc.read(mrcf)
	return bad_images, bad_kept_images


def removeImageFromTiltFile(tiltfile, imagenumber, remove_refimg):
	'''
	This removes all entries 'IMAGE $imagenumber' from a .tlt file. No backups made.
	Set $remove_refimg = "True" if it's okay to remove the reference image.
	'''
	#First check to make sure that the reference image is not being asked to be removed
	cmd="awk '/REFERENCE IMAGE /{print $3}' %s" % (tiltfile)
	proc=subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
	(refimg, err) = proc.communicate()
	refimg=int(refimg)
	if (remove_refimg != "True") and (refimg == imagenumber):
		apDisplay.printWarning("Unable to remove image #%s because it is the reference image!" % (imagenumber))
	else:
		with open(tiltfile) as f:
			lines=f.readlines()
		f.close()
		
		images=[]
		images.append(imagenumber)
		with open(tiltfile,"w") as newtiltfile:
			for line in lines:
				if not any('IMAGE %s ' % (imagenumber) in line for image in images):
					newtiltfile.write(line)
		newtiltfile.close()
	
	return


def removeHighTiltsFromTiltFile(tiltfile, negative=-90, positive=90):
	'''
	This removes all 'IMAGE imagenumber' entries from a .tlt file with
	tilt angles less than $negative and/or greater than $positive.
	Designed for use with reconstruction workflows.
	'''
	if (negative == -90) and (positive == 90):
		apDisplay.printWarning("You must choose valid ranges for image removal. Skipping image removal.")
		return [], 0, 0
	else:
		#Get image count from tlt file by counting how many lines have ORIGIN in them.
		cmd1="awk '/ORIGIN /{print}' %s | wc -l" % (tiltfile)
		proc=subprocess.Popen(cmd1, stdout=subprocess.PIPE, shell=True)
		(numimages, err) = proc.communicate()
		numimages=int(numimages)
		cmd2="awk '/IMAGE /{print $2}' %s | head -n +1" % (tiltfile)
		proc=subprocess.Popen(cmd2, stdout=subprocess.PIPE, shell=True)
		(tiltstart, err) = proc.communicate()
		tiltstart=int(tiltstart)
		
		removed_images=[]
		for i in range(tiltstart,numimages+tiltstart+1):
			try: #If the image isn't in the .tlt file, skip it
				#Get information from tlt file. This needs to versatile for differently formatted .tlt files, so awk it is.
				cmd="awk '/IMAGE %s /{print}' %s | awk '{for (j=1;j<=NF;j++) if($j ~/TILT/) print $(j+2)}'" % (i, tiltfile)
				proc=subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
				(tilt_angle, err) = proc.communicate()
				tilt_angle=float(tilt_angle)
			
				if tilt_angle < negative:
					removed_images.append(i)
				elif tilt_angle > positive:
					removed_images.append(i)
			except:
				pass
		
		for image in removed_images:
			removeImageFromTiltFile(tiltfile, image, remove_refimg="True")
		
		#Get new min and max tilt angles
		cmd1="awk '/ORIGIN /{print}' %s | wc -l" % (tiltfile)
		proc=subprocess.Popen(cmd1, stdout=subprocess.PIPE, shell=True)
		(numimages, err) = proc.communicate()
		numimages=int(numimages)
		cmd2="awk '/IMAGE /{print $2}' %s | head -n +1" % (tiltfile)
		proc=subprocess.Popen(cmd2, stdout=subprocess.PIPE, shell=True)
		(tiltstart, err) = proc.communicate()
		tiltstart=int(tiltstart)
		mintilt=0
		maxtilt=0
		for i in range(tiltstart-1,tiltstart+numimages):
			try: #If the image isn't in the .tlt file, skip it
				cmd="awk '/IMAGE %s /{print}' %s | awk '{for (j=1;j<=NF;j++) if($j ~/TILT/) print $(j+2)}'" % (i+1, tiltfile)
				proc=subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
				(tilt_angle, err) = proc.communicate()
				tilt_angle=float(tilt_angle)
				mintilt=min(mintilt,tilt_angle)
				maxtilt=max(maxtilt,tilt_angle)
			except:
				pass
	
	return removed_images, mintilt, maxtilt


def unShiftTiltFile(tiltfile, dimx, dimy, shift_limit):
	'''
	Replaces the origin in a .tlt file with [ dimx/2, dimy/2 ] if any shifts are greater than the shift_limit*dimension/100.
	This code isn't currently being used.
	'''
	#Get image count from tlt file by counting how many lines have ORIGIN in them.
	cmd="awk '/ORIGIN /{print}' %s | wc -l" % (tiltfile)
	proc=subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
	(numimages, err) = proc.communicate()
	numimages=int(numimages)
	
	# Determine if any of the shifts exceed the shift limit
	max_x=0
	max_y=0
	for i in range(numimages):
		#Get information from tlt file. This needs to versatile for differently formatted .tlt files, so awk it is.
		cmd1="awk '/IMAGE %s /{print}' %s | awk '{for (j=1;j<=NF;j++) if($j ~/ORIGIN/) print $(j+2)}'" % (i+1, tiltfile)
		proc=subprocess.Popen(cmd1, stdout=subprocess.PIPE, shell=True)
		(originx, err) = proc.communicate()
		originx=float(originx)
		cmd2="awk '/IMAGE %s /{print}' %s | awk '{for (j=1;j<=NF;j++) if($j ~/ORIGIN/) print $(j+3)}'" % (i+1, tiltfile)
		proc=subprocess.Popen(cmd2, stdout=subprocess.PIPE, shell=True)
		(originy, err) = proc.communicate()
		originy=float(originy)
		
		if abs(dimx/2 - originx) > max_x:
			max_x=abs(dimx/2 - originx)
		if abs(dimy/2 - originy) > max_y:
			max_y=abs(dimy/2 - originy)
		
		
	if (max_x > shift_limit*dimx/100) or (max_y > shift_limit*dimy/100):	
		# Find originx and originy in tlt file and replace them one-by-one with dim/2
		for i in range(numimages):
			#Get information from tlt file. This needs to versatile for differently formatted .tlt files, so awk it is.
			cmd1="awk '/IMAGE %s /{print}' %s | awk '{for (j=1;j<=NF;j++) if($j ~/ORIGIN/) print $(j+2)}'" % (i+1, tiltfile)
			proc=subprocess.Popen(cmd1, stdout=subprocess.PIPE, shell=True)
			(originx, err) = proc.communicate()
			originx=float(originx)
			cmd2="awk '/IMAGE %s /{print}' %s | awk '{for (j=1;j<=NF;j++) if($j ~/ORIGIN/) print $(j+3)}'" % (i+1, tiltfile)
			proc=subprocess.Popen(cmd2, stdout=subprocess.PIPE, shell=True)
			(originy, err) = proc.communicate()
			originy=float(originy)
			
			#Replace values
			cmd3="sed -i 's/ %s / %s00 /g' %s; sed -i 's/ %s0 / %s00 /g' %s; sed -i 's/ %s00 / %s00 /g' %s" % (originx, round(dimx/2,3), tiltfile, originx, round(dimx/2), tiltfile, originx, round(dimx/2,3), tiltfile)
			os.system(cmd3)
			cmd4="sed -i 's/ %s / %s00 /g' %s; sed -i 's/ %s0 / %s00 /g' %s; sed -i 's/ %s00 / %s00 /g' %s" % (originy, round(dimy/2,3), tiltfile, originy, round(dimy/2), tiltfile, originy, round(dimy/2,3), tiltfile)
			os.system(cmd4)


def fixImages(rawpath):
	'''
	Reads raw image mrcs into pyami, normalizes, converts datatype to float32, and writes them back out. No transforms. This fixes Protomo issues.
	'''
	os.chdir(rawpath)
	mrcs=glob.glob('*mrc')
	for image in mrcs:
		f=mrc.read(image)
		f=imagenorm.normStdev(f)
		f=np.float32(f)
		mrc.write(f,image)
	

def removeForRestart(restart_iteration, name, rundir):
	'''
	Performs file removal necessary for restarting refinement.
	'''
	# Remove cache files
	os.system("rm %s/cache/%s* 2>/dev/null" % (rundir, name))
	
	# Remove tlt files
	tlt_list=glob.glob("%s/%s*.tlt" % (rundir, name))
	if len(tlt_list) != 0:
		tlt_list.sort()
		tlt_list.append('dummy') #because Python lists as ranges end one before the end.
		for tlt in tlt_list[restart_iteration:-1]:
			os.system('rm %s 2>/dev/null' % tlt)
	
	# Remove corr files
	corr_list=glob.glob("%s/%s*.corr" % (rundir, name))
	if len(corr_list) != 0:
		corr_list.sort()
		corr_list.append('dummy')
		for corr in corr_list[restart_iteration:-1]:
			os.system('rm %s 2>/dev/null' % corr)
	
	# Remove out dir files
	cor_list=glob.glob("%s/out/%s*_cor*.mrc" % (rundir, name))
	if len(cor_list) != 0:
		cor_list.sort()
		cor_list.append('dummy')
		for cor in cor_list[restart_iteration:-1]:
			os.system('rm %s 2>/dev/null' % cor)
	bck_list=glob.glob("%s/out/%s*_bck*.mrc" % (rundir, name))
	if len(bck_list) != 0:
		bck_list.sort()
		bck_list.append('dummy')
		for bck in bck_list[restart_iteration:-1]:
			os.system('rm %s 2>/dev/null' % bck)
	
	# Remove media
	os.system('rm %s/media/quality_assessment/%s* 2>/dev/null' % (rundir, name))
	os.system('rm %s/media/angle_refinement/%s* 2>/dev/null' % (rundir, name))
	tilt_mp4_list=glob.glob("%s/media/tiltseries/%s*.mp4" % (rundir, name))
	if len(tilt_mp4_list) != 0:
		tilt_mp4_list.sort()
		tilt_mp4_list.append('dummy')
		for tilt_mp4 in tilt_mp4_list[restart_iteration:-1]:
			os.system('rm %s* 2>/dev/null' % tilt_mp4[:-3])
	recon_mp4_list=glob.glob("%s/media/reconstructions/%s*.mp4" % (rundir, name))
	if len(recon_mp4_list) != 0:
		recon_mp4_list.sort()
		recon_mp4_list.append('dummy')
		for recon_mp4 in recon_mp4_list[restart_iteration:-1]:
			os.system('rm %s* 2>/dev/null' % recon_mp4[:-3])
	corr_mp4_list=glob.glob("%s/media/correlations/%s*.mp4" % (rundir, name))
	if len(corr_mp4_list) != 0:
		corr_mp4_list.sort()
		corr_mp4_list.append('dummy')
		for corr_mp4 in corr_mp4_list[restart_iteration:-1]:
			os.system('rm %s* 2>/dev/null' % corr_mp4[:-3])
	corr_gif_list=glob.glob("%s/media/corrplots/%s*_coa*" % (rundir, name))
	if len(corr_gif_list) != 0:
		corr_gif_list.sort()
		corr_gif_list.append('dummy')
		for corr_gif in corr_gif_list[restart_iteration:-1]:
			os.system('rm %s* 2>/dev/null' % corr_gif[:-7])
	
	os.system('rm %s/best* 2>/dev/null' % rundir)
	os.system('rm %s/worst* 2>/dev/null' % rundir)
	


def makeCorrPeakVideos(seriesname, iteration, rundir, outdir, video_type, align_step):
	'''
	Creates Cross Correlation Peak Videos for Coarse Alignment.
	'''
	os.environ["MAGICK_THREAD_LIMIT"] = "1"
	os.system("mkdir -p %s/media/correlations 2>/dev/null" % rundir)
	try: #If anything fails, it's likely that something isn't in the path
		if align_step == "Coarse":
			img=seriesname+'00_cor.img'
			mrcf=seriesname+'00_cor.mrc'
			gif=seriesname+'00_cor.gif'
			ogv=seriesname+'00_cor.ogv'
			mp4=seriesname+'00_cor.mp4'
			webm=seriesname+'00_cor.webm'
		else: #align_step == "Refinement"
			iteration=format(iteration[1:] if iteration.startswith('0') else iteration) #Protomo filenaming conventions are %2d unless iteration number is more than 2 digits.
			iteration_depiction='%03d' % int(iteration)
			img=seriesname+iteration+'_cor.img'
			mrcf=seriesname+iteration+'_cor.mrc'
			gif=seriesname+iteration_depiction+'_cor.gif'
			ogv=seriesname+iteration_depiction+'_cor.ogv'
			mp4=seriesname+iteration_depiction+'_cor.mp4'
			webm=seriesname+iteration_depiction+'_cor.webm'
		png='*.png'
		pngff='slice%04d.png'
		out_path=os.path.join(rundir, outdir)
		img_full=out_path+'/'+img
		mrc_full=out_path+'/'+mrcf
		vid_path=os.path.join(rundir,'media','correlations')
		gif_full=vid_path+'/'+gif
		ogv_full=vid_path+'/'+ogv
		mp4_full=vid_path+'/'+mp4
		webm_full=vid_path+'/'+webm
		png_full=vid_path+'/'+png
		pngff_full=vid_path+'/'+pngff
		# Convert the corr peak *.img file to mrc for further processing
		os.system("i3cut -fmt mrc %s %s" % (img_full, mrc_full))
		
		volume = mrc.read(mrc_full)
		slices = len(volume) - 1
		# Convert the *.mrc to a series of pngs
		apDisplay.printMsg("Creating correlation peak video...")
		for i in range(0, slices+1):
			slice = os.path.join(vid_path,"slice%04d.png" % (i))
			scipy.misc.imsave(slice, volume[i])
			#Add frame numbers
			command = "convert -gravity South -background white -splice 0x18 -annotate 0 'Frame: %s/%s' %s %s" % (i+1, slices+1, slice, slice)
			os.system(command)
		
		#Convert pngs to either a gif or to HTML5 videos
		if video_type == "gif":
			if align_step == "Coarse":
				command2 = "convert -delay 22 -loop 0 %s %s;" % (png_full, gif_full)
				command2 += 'ffmpeg -y -v 0 -framerate 4.5 -pattern_type glob -i "%s" -codec:v libx264 -profile:v baseline -pix_fmt yuv420p -g 30 %s' % (png_full, mp4_full)
			else: #align_step == "Refinement"... Just changing the speed with the delay option
				command2 = "convert -delay 15 -loop 0 %s %s;" % (png_full, gif_full)
				command2 += 'ffmpeg -y -v 0 -framerate 5.5 -pattern_type glob -i "%s" -codec:v libx264 -profile:v baseline -pix_fmt yuv420p -g 30 %s' % (png_full, mp4_full)
		else: #video_type == "html5vid"
			if align_step == "Coarse":
				command2 = "convert -delay 22 -loop 0 %s %s;" % (png_full, gif_full)
				command2 += 'ffmpeg -y -v 0 -framerate 4.5 -pattern_type glob -i "%s" -codec:v libtheora -b:v 3000K -g 30 %s;' % (png_full, ogv_full)
				command2 += 'ffmpeg -y -v 0 -framerate 4.5 -pattern_type glob -i "%s" -codec:v libx264 -profile:v baseline -pix_fmt yuv420p -g 30 %s;' % (png_full, mp4_full)
				command2 += 'ffmpeg -y -v 0 -framerate 4.5 -pattern_type glob -i "%s" -codec:v libvpx -b:v 3000K -g 30 %s' % (png_full, webm_full)
			else: #align_step == "Refinement"... Just changing the speed with the framerate option
				command2 = 'ffmpeg -y -v 0 -framerate 5.5 -pattern_type glob -i "%s" -codec:v libtheora -b:v 3000K -g 30 %s;' % (png_full, ogv_full)
				command2 += 'ffmpeg -y -v 0 -framerate 5.5 -pattern_type glob -i "%s" -codec:v libx264 -profile:v baseline -pix_fmt yuv420p -g 30 %s;' % (png_full, mp4_full)
				command2 += 'ffmpeg -y -v 0 -framerate 5.5 -pattern_type glob -i "%s" -codec:v libvpx -b:v 3000K -g 30 %s' % (png_full, webm_full)
		os.system(command2)
		command3 = "rm %s; rm %s" % (png_full, img_full)
		os.system(command3)
		apDisplay.printMsg("Done creating correlation peak video!")
		if video_type == "gif":
			return gif_full, None, None
		else: #video_type == "html5vid"
			return ogv_full, mp4_full, webm_full
	except:
		apDisplay.printWarning("Alignment Correlation Peak Images and/or Videos could not be generated. Make sure i3, ffmpeg, and imagemagick are in your $PATH. Make sure that pyami and scipy are in your $PYTHONPATH.\n")


def makeQualityAssessment(seriesname, iteration, rundir, corrfile):
	'''
	Updates a text file with quality assessment statistics.
	'''
	try: #If anything fails, it's likely that something isn't in the path
		os.system("mkdir -p %s/media/quality_assessment 2>/dev/null" % rundir)
		txtqa_full=rundir+'/media/quality_assessment/'+seriesname+'_quality_assessment.txt'
		if iteration == 0:
			os.system("rm %s/media/quality_assessment/*txt 2>/dev/null" % rundir)
			f = open(txtqa_full,'w')
			f.write("#iteration avg_correction_x avg_correction_y stdev_x stdev_y sum_shift avg_correction_angle stdev_angle sum_angle avg_correction_scale stdev_scale sum_scale sum_of_sums\n")
			f.close()
		
		corrdata=np.loadtxt(corrfile)
		f=open(corrfile,'r')
		lines=f.readlines()
		f.close()
		
		coa=[]
		cofx=[]
		cofy=[]
		cofscale=[]
		for line in lines:
			words=line.split()
			coa.append(float(words[1]))
			cofx.append(float(words[2]))
			cofy.append(float(words[3]))
			cofscale.append(float(words[5]))
		
		avgangle=0
		avgx=0
		avgy=0
		avgscale=0
		for element in coa: #Calculate average distance from 0
			avgangle += abs(element)
		avgangle = avgangle/len(coa)
		for element in cofx: #Calculate average distance from 1.0
			avgx += abs(element - 1)
		avgx = avgx/len(cofx)
		for element in cofy: #Calculate average distance from 1.0
			avgy += abs(element - 1)
		avgy = avgy/len(cofy)
		for element in cofscale: #Calculate average distance from 1.0
			avgscale += abs(element - 1)
		avgscale = avgscale/len(cofscale)
		stdangle = corrdata[:,1].std()
		stdx = corrdata[:,2].std()
		stdy = corrdata[:,3].std()
		stdscale = corrdata[:,5].std()
		ccms_rots=avgangle + stdangle
		ccms_shift=avgx + avgy + stdx + stdy
		ccms_scale=avgscale + stdscale
		normalization=0  #CCMS_(sum) needs to be normalized so that we can compare iterations with or without varying correction factors.
		if stdangle != 0:
			normalization+=1
		if stdx + stdy != 0:
			normalization+=1
		if stdscale != 0:
			normalization+=1
		
		ccms_sum=(ccms_rots*14.4/360 + ccms_shift + ccms_scale)/normalization   #This is a scaled sum where ccms_rots is put on the same scale as ccms_shift (14.4/360 = 0.02; ie. 0.5 degrees is now equal to 0.02, both linear scales)
		
		f = open(txtqa_full,'a')
		f.write("%s %s %s %s %s %s %s %s %s %s %s %s %s\n" % (iteration+1, avgx, avgy, stdx, stdy, ccms_shift, avgangle, stdangle, ccms_rots, avgscale, stdscale, ccms_scale, ccms_sum))
		f.close()
		
		return ccms_shift, ccms_rots, ccms_scale, ccms_sum
	except:
		apDisplay.printWarning("Quality assessment statistics could not be generated. Make sure numpy is in your $PYTHONPATH.\n")


def makeQualityAssessmentImage(tiltseriesnumber, sessionname, seriesname, rundir, r1_iters, r1_sampling, r1_lp, r2_iters=0, r2_sampling=0, r2_lp=0, r3_iters=0, r3_sampling=0, r3_lp=0, r4_iters=0, r4_sampling=0, r4_lp=0, r5_iters=0, r5_sampling=0, r5_lp=0, r6_iters=0, r6_sampling=0, r6_lp=0, r7_iters=0, r7_sampling=0, r7_lp=0, r8_iters=0, r8_sampling=0, r8_lp=0, scaling="False", elevation="False"):
	'''
	Creates Quality Assessment Plot Image for Depiction.
	Adds best and worst iteration to qa text file.
	Returns best iteration number and CCMS_sum value.
	'''
	def line_prepender(filename, line):
		with open(filename, 'r+') as f:
			content = f.read()
			f.seek(0, 0)
			f.write(line.rstrip('\r\n') + '\n' + content)
	font="full"
	try: #If anything fails, it's likely that something isn't in the path
		apDisplay.printMsg("Creating quality assessment plot image...")
		figqa_full=rundir+'/media/quality_assessment/'+seriesname+'_quality_assessment.png'
		txtqa_full=rundir+'/media/quality_assessment/'+seriesname+'_quality_assessment.txt'
		if (r2_iters != 0 and r3_iters != 0 and r4_iters != 0 and r5_iters != 0 and r6_iters != 0 and r7_iters != 0 and r8_iters != 0): #R1-R8
			title="Session %s, Tilt-Series #%s | R1: Iters 1-%s @ bin=%s, lp=%s $\AA$ | R2: Iters %s-%s @ bin=%s, lp=%s $\AA$\nR3: Iters %s-%s @ bin=%s, lp=%s $\AA$ | R4: Iters %s-%s @ bin=%s, lp=%s $\AA$ | R5: Iters %s-%s @ bin=%s, lp=%s $\AA$\nR6: Iters %s-%s @ bin=%s, lp=%s $\AA$ | R7: Iters %s-%s @ bin=%s, lp=%s $\AA$ | R8: Iters %s-%s @ bin=%s, lp=%s $\AA$" % (sessionname, tiltseriesnumber, r1_iters, r1_sampling, r1_lp, r1_iters+1, r1_iters+r2_iters, r2_sampling, r2_lp, r1_iters+r2_iters+1, r1_iters+r2_iters+r3_iters, r3_sampling, r3_lp, r1_iters+r2_iters+r3_iters+1, r1_iters+r2_iters+r3_iters+r4_iters, r4_sampling, r4_lp, r1_iters+r2_iters+r3_iters+r4_iters+1, r1_iters+r2_iters+r3_iters+r4_iters+r5_iters, r5_sampling, r5_lp, r1_iters+r2_iters+r3_iters+r4_iters+r5_iters+1, r1_iters+r2_iters+r3_iters+r4_iters+r5_iters+r6_iters, r6_sampling, r6_lp, r1_iters+r2_iters+r3_iters+r4_iters+r5_iters+r6_iters+1, r1_iters+r2_iters+r3_iters+r4_iters+r5_iters+r6_iters+r7_iters, r7_sampling, r7_lp, r1_iters+r2_iters+r3_iters+r4_iters+r5_iters+r6_iters+r7_iters+1, r1_iters+r2_iters+r3_iters+r4_iters+r5_iters+r6_iters+r7_iters+r8_iters, r8_sampling, r8_lp)
			font="small"
		elif (r2_iters != 0 and r3_iters != 0 and r4_iters != 0 and r5_iters != 0 and r6_iters != 0 and r7_iters != 0 and r8_iters == 0): #R1-R7
			title="Session %s, Tilt-Series #%s | R1: Iters 1-%s @ bin=%s, lp=%s $\AA$ | R2: Iters %s-%s @ bin=%s, lp=%s $\AA$\nR3: Iters %s-%s @ bin=%s, lp=%s $\AA$ | R4: Iters %s-%s @ bin=%s, lp=%s $\AA$ | R5: Iters %s-%s @ bin=%s, lp=%s $\AA$\nR6: Iters %s-%s @ bin=%s, lp=%s $\AA$ | R7: Iters %s-%s @ bin=%s, lp=%s $\AA$" % (sessionname, tiltseriesnumber, r1_iters, r1_sampling, r1_lp, r1_iters+1, r1_iters+r2_iters, r2_sampling, r2_lp, r1_iters+r2_iters+1, r1_iters+r2_iters+r3_iters, r3_sampling, r3_lp, r1_iters+r2_iters+r3_iters+1, r1_iters+r2_iters+r3_iters+r4_iters, r4_sampling, r4_lp, r1_iters+r2_iters+r3_iters+r4_iters+1, r1_iters+r2_iters+r3_iters+r4_iters+r5_iters, r5_sampling, r5_lp, r1_iters+r2_iters+r3_iters+r4_iters+r5_iters+1, r1_iters+r2_iters+r3_iters+r4_iters+r5_iters+r6_iters, r6_sampling, r6_lp, r1_iters+r2_iters+r3_iters+r4_iters+r5_iters+r6_iters+1, r1_iters+r2_iters+r3_iters+r4_iters+r5_iters+r6_iters+r7_iters, r7_sampling, r7_lp)
			font="small"
		elif (r2_iters != 0 and r3_iters != 0 and r4_iters != 0 and r5_iters != 0 and r6_iters != 0 and r7_iters == 0 and r8_iters == 0): #R1-R6
			title="Session %s, Tilt-Series #%s\nR1: Iters 1-%s @ bin=%s, lp=%s $\AA$ | R2: Iters %s-%s @ bin=%s, lp=%s $\AA$ | R3: Iters %s-%s @ bin=%s, lp=%s $\AA$\nR4: Iters %s-%s @ bin=%s, lp=%s $\AA$ | R5: Iters %s-%s @ bin=%s, lp=%s $\AA$ | R6: Iters %s-%s @ bin=%s, lp=%s $\AA$" % (sessionname, tiltseriesnumber, r1_iters, r1_sampling, r1_lp, r1_iters+1, r1_iters+r2_iters, r2_sampling, r2_lp, r1_iters+r2_iters+1, r1_iters+r2_iters+r3_iters, r3_sampling, r3_lp, r1_iters+r2_iters+r3_iters+1, r1_iters+r2_iters+r3_iters+r4_iters, r4_sampling, r4_lp, r1_iters+r2_iters+r3_iters+r4_iters+1, r1_iters+r2_iters+r3_iters+r4_iters+r5_iters, r5_sampling, r5_lp, r1_iters+r2_iters+r3_iters+r4_iters+r5_iters+1, r1_iters+r2_iters+r3_iters+r4_iters+r5_iters+r6_iters, r6_sampling, r6_lp)
			font="medium"
		elif (r2_iters != 0 and r3_iters != 0 and r4_iters != 0 and r5_iters != 0 and r6_iters == 0 and r7_iters == 0 and r8_iters == 0): #R1-R5
			title="Session %s, Tilt-Series #%s\nR1: Iters 1-%s @ bin=%s, lp=%s $\AA$ | R2: Iters %s-%s @ bin=%s, lp=%s $\AA$ | R3: Iters %s-%s @ bin=%s, lp=%s $\AA$\nR4: Iters %s-%s @ bin=%s, lp=%s $\AA$ | R5: Iters %s-%s @ bin=%s, lp=%s $\AA$" % (sessionname, tiltseriesnumber, r1_iters, r1_sampling, r1_lp, r1_iters+1, r1_iters+r2_iters, r2_sampling, r2_lp, r1_iters+r2_iters+1, r1_iters+r2_iters+r3_iters, r3_sampling, r3_lp, r1_iters+r2_iters+r3_iters+1, r1_iters+r2_iters+r3_iters+r4_iters, r4_sampling, r4_lp, r1_iters+r2_iters+r3_iters+r4_iters+1, r1_iters+r2_iters+r3_iters+r4_iters+r5_iters, r5_sampling, r5_lp)
			font="medium"
		elif (r2_iters != 0 and r3_iters != 0 and r4_iters != 0 and r5_iters == 0 and r6_iters == 0 and r7_iters == 0 and r8_iters == 0): #R1-R4
			title="Session %s, Tilt-Series #%s\nR1: Iters 1-%s @ bin=%s, lp=%s $\AA$ | R2: Iters %s-%s @ bin=%s, lp=%s $\AA$\nR3: Iters %s-%s @ bin=%s, lp=%s $\AA$ | R4: Iters %s-%s @ bin=%s, lp=%s $\AA$" % (sessionname, tiltseriesnumber, r1_iters, r1_sampling, r1_lp, r1_iters+1, r1_iters+r2_iters, r2_sampling, r2_lp, r1_iters+r2_iters+1, r1_iters+r2_iters+r3_iters, r3_sampling, r3_lp, r1_iters+r2_iters+r3_iters+1, r1_iters+r2_iters+r3_iters+r4_iters, r4_sampling, r4_lp)
			font="large"
		elif (r2_iters != 0 and r3_iters != 0 and r4_iters == 0 and r5_iters == 0 and r6_iters == 0 and r7_iters == 0 and r8_iters == 0): #R1-R3
			title="Session %s, Tilt-Series #%s\nR1: Iters 1-%s @ bin=%s, lp=%s $\AA$ | R2: Iters %s-%s @ bin=%s, lp=%s $\AA$\nR3: Iters %s-%s @ bin=%s, lp=%s $\AA$" % (sessionname, tiltseriesnumber, r1_iters, r1_sampling, r1_lp, r1_iters+1, r1_iters+r2_iters, r2_sampling, r2_lp, r1_iters+r2_iters+1, r1_iters+r2_iters+r3_iters, r3_sampling, r3_lp)
			font="large"
		elif (r2_iters != 0 and r3_iters == 0 and r4_iters == 0 and r5_iters == 0 and r6_iters == 0 and r7_iters == 0 and r8_iters == 0): #R1-R2
			title="Session %s, Tilt-Series #%s\nR1: Iters 1-%s @ bin=%s, lp=%s $\AA$ | R2: Iters %s-%s @ bin=%s, lp=%s $\AA$" % (sessionname, tiltseriesnumber, r1_iters, r1_sampling, r1_lp, r1_iters+1, r1_iters+r2_iters, r2_sampling, r2_lp)
		elif (r2_iters == 0 and r3_iters == 0 and r4_iters == 0 and r5_iters == 0 and r6_iters == 0 and r7_iters == 0 and r8_iters == 0): #R1
			title="Session %s, Tilt-Series #%s\nR1: Iters 1-%s @ bin=%s, lp=%s $\AA$" % (sessionname, tiltseriesnumber, r1_iters, r1_sampling, r1_lp)
		
		f=open(txtqa_full,'r')
		lines=f.readlines()
		f.close()
		
		ccms_shift=[]
		ccms_rots=[]
		ccms_scale=[]
		ccms_sum=[]
		well_aligned1=[]
		well_aligned2=[]
		well_aligned3=[]
		iterlines=iter(lines)
		next(iterlines)  #Skip comment line
		for line in iterlines:
			words=line.split()
			ccms_shift.append(float(words[5]))
			ccms_rots.append(float(words[8]))
			ccms_scale.append(float(words[11]))
			ccms_sum.append(float(words[12]))
			well_aligned1.append(0.02)
			well_aligned2.append(0.5)
			well_aligned3.append(0.02)
		
		x=[]
		for i in range(1,len(ccms_shift)+1):
			x.append(i)
		
		plt.clf()
		fig_base=plt.figure()
		fig1=fig_base.add_subplot(111)
		plt.grid(True)
		
		l1=fig1.plot(x, ccms_shift, 'DarkOrange', linestyle='-', marker='.', label='CCMS(shifts)')
		l2=fig1.plot(x, ccms_scale, 'DarkOrange', linestyle='-', marker='*', label='CCMS(scale)')
		l12=fig1.plot(x, well_aligned1, 'DarkOrange', linestyle='-')
		l3=fig1.plot(x, ccms_sum, 'k', linestyle='-', linewidth=1.75, label='Scaled Sum')
		l33=fig1.plot(x, well_aligned3, 'k', linestyle='--', linewidth=1.5)
		plt.xlabel('Iteration')
		plt.ylabel('CCMS(shift & scale)')
		
		fig2=fig1.twinx()
		l4=fig2.plot(x, ccms_rots, 'c-', label='CCMS(rotations)')
		lz2=fig2.plot(x, well_aligned2, 'c', linestyle='--')
		plt.ylabel('CCMS(rotations)')
		
		h1,l1=fig1.get_legend_handles_labels()
		h2,l2=fig2.get_legend_handles_labels()
		try:
			fig1.legend(h2+h1,l2+l1,loc='best', frameon=False, fontsize=10)
		except:
			fig1.legend(h2+h1,l2+l1,loc='best')
			apDisplay.printMsg("Some plotting features won't work because you are using an old version of Matplotlib.")
		
		fig1.yaxis.label.set_color('DarkOrange')
		try:
			fig1.tick_params(axis='y', colors='DarkOrange')
		except:
			pass #Old Matplotlib
		fig2.yaxis.label.set_color('c')
		try:
			fig2.tick_params(axis='y', colors='c')
		except:
			pass #Old Matplotlib
		
		plt.gca().set_xlim(xmin=1)
		plt.gca().set_ylim(ymin=0.0)
		plt.minorticks_on()
		
		if font=="small":
			plt.rcParams["axes.titlesize"] = 9.5
		elif font=="medium":
			plt.rcParams["axes.titlesize"] = 10.5
		elif font=="large":
			plt.rcParams["axes.titlesize"] = 11.25
		plt.title(title)
		
		plt.savefig(figqa_full, bbox_inches='tight')
		plt.clf()
		
		#rename png to be a gif so that Appion will display it properly (this is a ridiculous redux workaround to display images with white backgrounds by changing png filename extensions to gif and then using loadimg.php?rawgif=1 to load them, but oh well)
		os.system('mv %s %s' % (figqa_full,figqa_full[:-3]+"gif"))
		
		#Guess which iteration is the best
		best=min(ccms_sum)
		best=[i for i, j in enumerate(ccms_sum) if j == best][0]+1
		worst=max(ccms_sum)
		worst=[i for i, j in enumerate(ccms_sum) if j == worst][0]+1
		line_prepender(txtqa_full, "#Worst iteration: %s with CCMS(sum) = %s\n" % (worst, max(ccms_sum)))
		line_prepender(txtqa_full, "#Best iteration: %s with CCMS(sum) = %s\n" % (best, min(ccms_sum)))
		
		#Guess which binned by 1 or 2 iteration is the best
		binlist=[]
		for i in range(r1_iters):
			binlist.append(r1_sampling)
		for i in range(r2_iters):
			binlist.append(r2_sampling)
		for i in range(r3_iters):
			binlist.append(r3_sampling)
		for i in range(r4_iters):
			binlist.append(r4_sampling)
		for i in range(r5_iters):
			binlist.append(r5_sampling)
		for i in range(r6_iters):
			binlist.append(r6_sampling)
		for i in range(r7_iters):
			binlist.append(r7_sampling)
		for i in range(r8_iters):
			binlist.append(r8_sampling)
		
		best_bin1or2=999999
		for i,j in zip(ccms_sum, range(len(ccms_sum))):
			if (binlist[j] == 1 or binlist[j] == 2):
				best_bin1or2 = min(best_bin1or2, i)
		
		os.system("cd media/quality_assessment; rm %s/best* 2> /dev/null; rm %s/worst* 2> /dev/null" % (rundir,rundir))
		
		if best_bin1or2!=999999:
			best_bin1or2=[i for i, j in enumerate(ccms_sum) if j == best_bin1or2][0]+1
			open("best_bin1or2.%s" % best_bin1or2,"a").close()
		open("best.%s" % best,"a").close()
		open("worst.%s" % worst,"a").close()
		apDisplay.printMsg("Done creating quality assessment statistics and plot!")
		return best, min(ccms_sum), figqa_full
	except:
		apDisplay.printWarning("Quality assessment plot image could not be generated. Make sure matplotlib and numpy are in your $PYTHONPATH.\n")


def checkCCMSValues(seriesname, rundir, iteration, threshold):
	'''
	Checks the individual CCMS values for a quality_assessment txt file after processed by makeQualityAssessmentImage.
	If all CCMS values are below the threshold, True is returned.
	'''
	txtqa_full=rundir+'/media/quality_assessment/'+seriesname+'_quality_assessment.txt'
	iteration = int(iteration) + 2  #comment lines
	
	f=open(txtqa_full,'r')
	lines=f.readlines()
	f.close()
	
	ccms_shift=float(lines[iteration].split()[5])
	ccms_rots=float(lines[iteration].split()[8])*14.4/360
	ccms_scale=float(lines[iteration].split()[11])
	if (ccms_shift <= threshold) and (ccms_rots <= threshold) and (ccms_scale <= threshold):
		return True
	else:
		return False


def makeCorrPlotImages(seriesname, iteration, rundir, corrfile):
	'''
	Creates Correction Factor Plot Images for Depiction
	'''
	import warnings
	warnings.filterwarnings("ignore", category=DeprecationWarning) #Otherwise matplotlib will complain to the user that something is depreciated
	try: #If anything fails, it's likely that something isn't in the path
		apDisplay.printMsg("Creating correction factor plot images...")
		os.system("mkdir -p %s/media/corrplots 2>/dev/null" % rundir)
		figcoa_full=rundir+'/media/corrplots/'+seriesname+iteration+'_coa.png'
		figcofx_full=rundir+'/media/corrplots/'+seriesname+iteration+'_cofx.png'
		figcofy_full=rundir+'/media/corrplots/'+seriesname+iteration+'_cofy.png'
		figrot_full=rundir+'/media/corrplots/'+seriesname+iteration+'_rot.png'
		figscl_full=rundir+'/media/corrplots/'+seriesname+iteration+'_scl.png'
		tiltfile=corrfile[:-4]+'tlt'
		
		cmd1="awk '/FILE /{print}' %s | wc -l" % (tiltfile)
		proc=subprocess.Popen(cmd1, stdout=subprocess.PIPE, shell=True)
		(rawimagecount, err) = proc.communicate()
		rawimagecount=int(rawimagecount)
		cmd2="awk '/IMAGE /{print $2}' %s | head -n +1" % (tiltfile)
		proc=subprocess.Popen(cmd2, stdout=subprocess.PIPE, shell=True)
		(tiltstart, err) = proc.communicate()
		tiltstart=int(tiltstart)
		mintilt=0
		maxtilt=0
		for i in range(tiltstart-1,tiltstart+rawimagecount-1):
			try:
				cmd3="awk '/IMAGE %s /{print}' %s | awk '{for (j=1;j<=NF;j++) if($j ~/TILT/) print $(j+2)}'" % (i+1, tiltfile)
				proc=subprocess.Popen(cmd3, stdout=subprocess.PIPE, shell=True)
				(tilt_angle, err) = proc.communicate()
				tilt_angle=float(tilt_angle)
				mintilt=min(mintilt,tilt_angle)
				maxtilt=max(maxtilt,tilt_angle)
			except: #Gap in tilt image #s
				pass
		
		corrdata=np.loadtxt(corrfile)
		f=open(corrfile,'r')
		lines=f.readlines()
		f.close()
		
		rot=[]
		cofx=[]
		cofy=[]
		coa=[]
		scl=[]
		for line in lines:
			words=line.split()
			rot.append(float(words[1]))
			cofx.append(float(words[2]))
			cofy.append(float(words[3]))
			coa.append(float(words[4]))
			scl.append(float(words[5]))
		meanx=[]
		stdx=[]
		x=[]
		y=[]
		for i in range(len(cofx)):
			meanx.append(corrdata[:,2].mean())
			stdx.append(corrdata[:,2].std())
			x.append(i)
			y.append(1)
		meany=[]
		stdy=[]
		for i in range(len(cofy)):
			meany.append(corrdata[:,3].mean())
			stdy.append(corrdata[:,3].std())
		meanscl=[]
		stdscl=[]
		for i in range(len(scl)):
			meanscl.append(corrdata[:,5].mean())
			stdscl.append(corrdata[:,5].std())
		meanx_plus_stdx=[i + j for i, j in zip(meanx, stdx)]
		meanx_minus_stdx=[i - j for i, j in zip(meanx, stdx)]
		meany_plus_stdy=[i + j for i, j in zip(meany, stdy)]
		meany_minus_stdy=[i - j for i, j in zip(meany, stdy)]
		meanscl_plus_stdscl=[i + j for i, j in zip(meanscl, stdscl)]
		meanscl_minus_stdscl=[i - j for i, j in zip(meanscl, stdscl)]
		
		if (meanx[0] > 0.99 and meanx[0] < 1.01):
			meanx_color='-g'
		else:
			meanx_color='-r'
		if (meany[0] > 0.99 and meany[0] < 1.01):
			meany_color='-g'
		else:
			meany_color='-r'
		if (meanscl[0] > 0.99 and meanscl[0] < 1.01):
			meanscl_color='-g'
		else:
			meanscl_color='-r'
		
		if stdx[0] < 0.005:
			stdx_color='--g'
		else:
			stdx_color='--r'
		if stdy[0] < 0.005:
			stdy_color='--g'
		else:
			stdy_color='--r'
		if stdscl[0] < 0.005:
			stdscl_color='--g'
		else:
			stdscl_color='--r'
		
		plt.clf()
		fig_base=plt.figure()
		fig1=fig_base.add_subplot(111)
		fig1.set_xlim(0,len(x)-1)
		l1=fig1.plot(x, coa, 'Blue')
		plt.xlabel("Tilt Image")
		plt.ylabel("Relative Angle (degrees)")
		fig2=fig1.twiny()
		fig2.set_xlim(int(round(mintilt)),int(round(maxtilt)))
		fig2.set_xlabel("Tilt Angle (degrees)")
		plt.savefig(figcoa_full)
		
		plt.clf()
		fig_base=plt.figure()
		fig1=fig_base.add_subplot(111)
		fig1.set_xlim(0,len(x)-1)
		l1=fig1.plot(x, y, '-k')
		l2=fig1.plot(cofx, label='correction factor (x)')
		l3=fig1.plot(x, meanx, meanx_color, alpha=0.75, label='mean')
		l4=fig1.plot(x, meanx_plus_stdx, stdx_color, alpha=0.6, label="1 stdev")
		l5=fig1.plot(x, meanx_minus_stdx, stdx_color, alpha=0.6)
		pylab.legend(loc='best', fancybox=True, prop=dict(size=11))
		plt.xlabel("Tilt Image")
		plt.ylabel("Geometric Differences not yet Corrected (% relative to 1.0)")
		fig2=fig1.twiny()
		fig2.set_xlim(int(round(mintilt)),int(round(maxtilt)))
		fig2.set_xlabel("Tilt Angle (degrees)")
		plt.savefig(figcofx_full, bbox_inches='tight')
		
		plt.clf()
		fig_base=plt.figure()
		fig1=fig_base.add_subplot(111)
		fig1.set_xlim(0,len(x)-1)
		l1=fig1.plot(x, y, '-k')
		l2=fig1.plot(cofy, label='correction factor (y)')
		l3=fig1.plot(x, meany, meany_color, alpha=0.75, label='mean')
		l4=fig1.plot(x, meany_plus_stdy, stdy_color, alpha=0.6, label="1 stdev")
		l5=fig1.plot(x, meany_minus_stdy, stdy_color, alpha=0.6)
		pylab.legend(loc='best', fancybox=True, prop=dict(size=11))
		plt.xlabel("Tilt Image")
		plt.ylabel("Geometric Differences not yet Corrected (% relative to 1.0)")
		fig2=fig1.twiny()
		fig2.set_xlim(int(round(mintilt)),int(round(maxtilt)))
		fig2.set_xlabel("Tilt Angle (degrees)")
		plt.savefig(figcofy_full, bbox_inches='tight')
		
		plt.clf()
		fig_base=plt.figure()
		fig1=fig_base.add_subplot(111)
		fig1.set_xlim(0,len(x)-1)
		l1=fig1.plot(x, rot, 'Blue')
		plt.xlabel("Tilt Image")
		plt.ylabel("Rotational Differences not yet Corrected (degrees)")
		fig2=fig1.twiny()
		fig2.set_xlim(int(round(mintilt)),int(round(maxtilt)))
		fig2.set_xlabel("Tilt Angle (degrees)")
		plt.savefig(figrot_full, bbox_inches='tight')
		
		plt.clf()
		fig_base=plt.figure()
		fig1=fig_base.add_subplot(111)
		fig1.set_xlim(0,len(x)-1)
		l1=fig1.plot(x, y, '-k')
		l2=fig1.plot(scl, label='scaling factor')
		l3=fig1.plot(x, meanscl, meanscl_color, alpha=0.75, label='mean')
		l4=fig1.plot(x, meanscl_plus_stdscl, stdscl_color, alpha=0.6, label="1 stdev")
		l5=fig1.plot(x, meanscl_minus_stdscl, stdscl_color, alpha=0.6)
		pylab.legend(loc='best', fancybox=True, prop=dict(size=11))
		plt.xlabel("Tilt Image")
		plt.ylabel("Scaling Differences not yet Corrected (% relative to 1.0)")
		fig2=fig1.twiny()
		fig2.set_xlim(int(round(mintilt)),int(round(maxtilt)))
		fig2.set_xlabel("Tilt Angle (degrees)")
		plt.savefig(figscl_full, bbox_inches='tight')
		plt.clf()
		
		#rename pngs to be gifs so that Appion will display them properly (this is a ridiculous redux workaround to display images with white backgrounds by changing png filename extensions to gif and then using loadimg.php?rawgif=1 to load them, but oh well)
		os.system('mv %s %s;mv %s %s;mv %s %s;mv %s %s;mv %s %s' % (figcoa_full,figcoa_full[:-3]+"gif",figcofx_full,figcofx_full[:-3]+"gif",figcofy_full,figcofy_full[:-3]+"gif",figrot_full,figrot_full[:-3]+"gif",figscl_full,figscl_full[:-3]+"gif"))
		
		apDisplay.printMsg("Done creating correction factor plots!")
		
		return figcoa_full[:-3]+"gif", figcofx_full[:-3]+"gif", figcofy_full[:-3]+"gif", figrot_full[:-3]+"gif", figscl_full[:-3]+"gif"
	except:
		apDisplay.printWarning("Correction Factor Plots could not be generated. Make sure matplotlib and numpy are in your $PYTHONPATH.\n")
	

def makeTiltSeriesVideos(seriesname, iteration, tiltfilename, rawimagecount, rundir, raw_path, pixelsize, map_sampling, image_file_type, video_type, tilt_clip, parallel, align_step):
	'''
	Creates Tilt-Series Videos for Depiction
	'''
	os.environ["MAGICK_THREAD_LIMIT"] = "1"
	def processTiltImages(i,j,tiltfilename,raw_path,image_file_type,map_sampling,rundir,pixelsize,rawimagecount,tilt_clip):
		try: #If the image isn't in the .tlt file, skip it
			#Get information from tlt file. This needs to versatile for differently formatted .tlt files, so awk it is.
			cmd1="awk '/IMAGE %s /{print}' %s | awk '{for (j=1;j<=NF;j++) if($j ~/FILE/) print $(j+1)}' | tr '\n' ' ' | sed 's/ //g'" % (i+1, tiltfilename)
			proc=subprocess.Popen(cmd1, stdout=subprocess.PIPE, shell=True)
			(filename, err) = proc.communicate()
			cmd2="awk '/IMAGE %s /{print}' %s | awk '{for (j=1;j<=NF;j++) if($j ~/ORIGIN/) print $(j+2)}'" % (i+1, tiltfilename)
			proc=subprocess.Popen(cmd2, stdout=subprocess.PIPE, shell=True)
			(originx, err) = proc.communicate()
			originx=float(originx)
			cmd3="awk '/IMAGE %s /{print}' %s | awk '{for (j=1;j<=NF;j++) if($j ~/ORIGIN/) print $(j+3)}'" % (i+1, tiltfilename)
			proc=subprocess.Popen(cmd3, stdout=subprocess.PIPE, shell=True)
			(originy, err) = proc.communicate()
			originy=float(originy)
			cmd4="awk '/IMAGE %s /{print}' %s | awk '{for (j=1;j<=NF;j++) if($j ~/ROTATION/) print $(j+1)}'" % (i+1, tiltfilename)
			proc=subprocess.Popen(cmd4, stdout=subprocess.PIPE, shell=True)
			(rotation, err) = proc.communicate()
			rotation=float(rotation)
			cmd5="awk '/IMAGE %s /{print}' %s | awk '{for (j=1;j<=NF;j++) if($j ~/TILT/) print $(j+2)}'" % (i+1, tiltfilename)
			proc=subprocess.Popen(cmd5, stdout=subprocess.PIPE, shell=True)
			(tilt_angle, err) = proc.communicate()
			tilt_angle=float(tilt_angle)
			
			#Convert raw image to mrc if necessary
			mrcf=raw_path+'/'+filename+'.'+image_file_type
			if image_file_type != 'mrc':
				f2=mrcf
				mrcf=raw_path+'/'+filename+'.mrc'
				cmd="proc2d %s %s mrc" % (f2, mrcf)
				os.system(cmd)
			
			#Load image
			image=mrc.read(mrcf)
			image=imagenorm.normStdev(image)
			
			#Clip values greater than 5 sigma above or below the mean
			if tilt_clip == "true":
				clip_min=image.mean()-5*image.std()
				clip_max=image.mean()+5*image.std()
				image=np.clip(image,clip_min,clip_max)
				image=imagenorm.normStdev(image)
			
			dimx=len(image[0])
			dimy=len(image)
			
			transx=int((dimx/2) - originx)
			transy=int((dimy/2) - originy)
			
			#Shifts are relative to protomo output; ie. as seen in tomoalign-gui. Note: tomoalign-gui is flipped vertically.
			#Translate pixels left or right?
			if originx > dimx/2:    #shift left
				image=np.roll(image,transx,axis=1)
				for k in range(-1,transx-1,-1):
					image[:,k]=0
			elif originx < dimx/2:    #shift right
				image=np.roll(image,transx,axis=1)
				for k in range(transx):
					image[:,k]=0
			# dont shift if originx = dimx/2
			
			#Translate pixels up or down?
			if originy < dimy/2:    #shift down
				image=np.roll(image,transy,axis=0)
				for k in range(transy):
					image[k]=0
			elif originy > dimy/2:    #shift up
				image=np.roll(image,transy,axis=0)
				for k in range(-1,transy-1,-1):
					image[k]=0
			# dont shift if originy = dimy/2
			
			#Downsample image
			if (map_sampling != 1):
				image=imfun.bin2f(image,map_sampling)
			
			#Write translated image
			vid_path=os.path.join(rundir,'media','tiltseries')
			if align_step == "Initial":
				tiltimage = os.path.join(vid_path,"initial_tilt%04d.png" % (j))
			elif align_step == "Coarse":
				tiltimage = os.path.join(vid_path,"coarse_tilt%04d.png" % (j))
			else: #align_step == "Refinement"
				tiltimage = os.path.join(vid_path,"tilt%04d.png" % (j))
			os.system("mkdir -p %s 2>/dev/null" % (vid_path))
			scipy.misc.imsave(tiltimage, image)
			
			#Rotate
			if (rotation != 0.000):
				image=Image.open(tiltimage)
				image.rotate(rotation).save(tiltimage)
			
			#Add scalebar
			scalesize=2500/(pixelsize * map_sampling)    #250nm scaled by sampling
			command = "convert -gravity South -background white -splice 0x20 -strokewidth 0 -stroke black -strokewidth 5 -draw \"line %s,%s,5,%s\" -gravity SouthWest -pointsize 13 -fill black -strokewidth 0  -draw \"translate 50,0 text 0,0 '250 nm'\" %s %s" % (scalesize, dimy/map_sampling+3, dimy/map_sampling+3, tiltimage, tiltimage)
			os.system(command)
			
			#Add frame numbers and tilt angles
			tilt_degrees = float("{0:.1f}".format(tilt_angle))
			degrees='deg'  #I've tried getting the degrees symbol working, but can't
			command3 = "convert -gravity South -annotate 0 'Tilt Image: %s/%s' -gravity SouthEast -annotate 0 '%s %s' %s %s" % (j+1, rawimagecount, tilt_degrees, degrees, tiltimage, tiltimage)
			os.system(command3)
		except:
			pass
	
	try: #If anything fails, it's likely that something isn't in the path
		if (parallel=="True" and align_step=="Coarse"):
			procs=3
		elif parallel=="True":
			procs=max(mp.cpu_count()-1,2)
		else:
			procs=1
		
		#Get the starting number b/c Protomo tlt files don't require that you start from 1. Lame.
		cmd="awk '/IMAGE /{print $2}' %s | head -n +1" % tiltfilename
		proc=subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
		(start, err) = proc.communicate()
		start=int(start)
		
		if (map_sampling == 1):
			apDisplay.printMsg("No downsampling will be performed on the depiction images.")
			apDisplay.printWarning("Warning: Depiction video might be so large that it breaks your web browser!")
		
		if procs == 1:
			for i in range(start, start+rawimagecount+1):
				processTiltImages(i,i,tiltfilename,raw_path,image_file_type,map_sampling,rundir,pixelsize,rawimagecount,tilt_clip)
		else: #Parallel process the images
			for i,j in zip(range(start-1, start+rawimagecount+1),range(rawimagecount+1)):
				p2 = mp.Process(target=processTiltImages, args=(i,j,tiltfilename,raw_path,image_file_type,map_sampling,rundir,pixelsize,rawimagecount,tilt_clip,))
				p2.start()
				
				if (i % (int(procs/3)) == 0) and (i != 0):
					[p2.join() for p2 in mp.active_children()]
			[p2.join() for p2 in mp.active_children()]
		
		#Turn pngs into a video with Frame # and delete pngs
		if align_step == "Initial":
			gif='initial_'+seriesname+'.gif'
			ogv='initial_'+seriesname+'.ogv'
			mp4='initial_'+seriesname+'.mp4'
			webm='initial_'+seriesname+'.webm'
			png='initial_*.png'
			pngff='initial_tilt%04d.png'
		elif align_step == "Coarse":
			gif='coarse_'+seriesname+'.gif'
			ogv='coarse_'+seriesname+'.ogv'
			mp4='coarse_'+seriesname+'.mp4'
			webm='coarse_'+seriesname+'.webm'
			png='coarse_*.png'
			pngff='coarse_tilt%04d.png'
		else: #align_step == "Refinement"
			gif=seriesname+iteration+'.gif'
			ogv=seriesname+iteration+'.ogv'
			mp4=seriesname+iteration+'.mp4'
			webm=seriesname+iteration+'.webm'
			png='*.png'
			pngff='tilt%04d.png'
		vid_path=os.path.join(rundir,'media','tiltseries')
		png_full=vid_path+'/'+png
		pngff_full=vid_path+'/'+pngff
		gif_full=vid_path+'/'+gif
		ogv_full=vid_path+'/'+ogv
		mp4_full=vid_path+'/'+mp4
		webm_full=vid_path+'/'+webm
		
		#Convert pngs to either a gif or to HTML5 videos
		if video_type == "gif":
			command = "convert -delay 22 -loop 0 %s %s;" % (png_full, gif_full)
			command += 'ffmpeg -y -v 0 -framerate 4.5 -pattern_type glob -i "%s" -codec:v libx264 -profile:v baseline -pix_fmt yuv420p -g 30 %s' % (png_full, mp4_full)
		else: #video_type == "html5vid"
			command = 'ffmpeg -y -v 0 -framerate 4.5 -pattern_type glob -i "%s" -codec:v libtheora -b:v 3000K -g 30 %s;' % (png_full, ogv_full)
			command += 'ffmpeg -y -v 0 -framerate 4.5 -pattern_type glob -i "%s" -codec:v libx264 -profile:v baseline -pix_fmt yuv420p -g 30 %s;' % (png_full, mp4_full)
			command += 'ffmpeg -y -v 0 -framerate 4.5 -pattern_type glob -i "%s" -codec:v libvpx -b:v 3000K -g 30 %s' % (png_full, webm_full)
		os.system(command)
		command2 = "rm %s" % (png_full)
		os.system(command2)
		
		if align_step == "Initial":
			apDisplay.printMsg("Done creating initial tilt-series video!")
		elif align_step == "Coarse":
			apDisplay.printMsg("Done creating coarse tilt-series video!")
		else: #align_step == "Refinement"
			apDisplay.printMsg("Done creating tilt-series video!")
		
		if video_type == "gif":
			return gif_full, None, None
		else: #video_type == "html5vid"
			return ogv_full, mp4_full, webm_full
	except:
		apDisplay.printWarning("Tilt-Series Images and/or Videos could not be generated. Make sure ffmpeg and imagemagick is in your $PATH. Make sure that pyami, scipy, numpy, and PIL are in your $PYTHONPATH.\n")
		

def makeReconstructionVideos(seriesname, iteraion, rundir, rx, ry, show_window_size, outdir, pixelsize, sampling, map_sampling, lowpass, thickness, video_type, keep_recons, parallel, align_step):
	'''
	Creates Reconstruction Videos for Depiction
	'''
	os.environ["MAGICK_THREAD_LIMIT"] = "1"
	def processReconImages(i,slices,vid_path,volume,minval,maxval,pixelsize,map_sampling,dimx,dimy,show_window_size,rx,ry):
		filename="slice%04d.png" % (i)
		slice = os.path.join(vid_path,filename)
		
		#Pixel density scaling
		#scipy.misc.imsave(slice, volume[i])  #This command scales pixel values per-image
		scipy.misc.toimage(volume[i], cmin=minval, cmax=maxval).save(slice)  #This command scales pixel values over the whole volume
		
		#Add rectangle showing the search area, but only to the sections that were aligned to
		if (show_window_size == 'true' and (slices+1)/4 < i and slices+1-((slices+1)/4) > i):
			x1=int((dimx-rx)/2)
			y1=int((dimy-ry)/2)
			x2=int(dimx-x1)
			y2=int(dimy-y1)
			
			im=Image.open(slice)
			im.convert("RGB")
			draw=ImageDraw.Draw(im)
			draw.rectangle([x1,y1,x2,y2])
			im.save(slice)
		
		#Add scalebar
		scalesize=2500/(pixelsize * map_sampling)    #250nm scaled by sampling
		cmd = "convert -gravity South -background white -splice 0x20 -strokewidth 0 -stroke black -strokewidth 5 -draw \"line %s,%s,5,%s\" -gravity SouthWest -pointsize 13 -fill black -strokewidth 0  -draw \"translate 50,0 text 0,0 '250 nm'\" %s %s;" % (scalesize, dimy+3, dimy+3, slice, slice)
		#Add frame numbers
		cmd += "convert -gravity South -annotate 0 'Z-Slice: %s/%s' -gravity SouthEast -annotate 0 'bin=%s, lp=%s, thick=%s' %s %s" % (i+1, slices+1, map_sampling, lowpass, thickness, slice, slice)
		os.system(cmd)
	
	try: #If anything fails, it's likely that something isn't in the path
		os.system("mkdir -p %s/media/reconstructions 2>/dev/null" % rundir)
		if align_step == "Coarse":
			img=seriesname+'00_bck.img'
			mrcf=seriesname+'.mrc'
			gif=seriesname+'.gif'
			ogv=seriesname+'.ogv'
			mp4=seriesname+'.mp4'
			webm=seriesname+'.webm'
		else: #align_step == "Refinement"
			img=seriesname+iteraion+'_bck.img'
			mrcf=seriesname+iteraion+'_bck.mrc'
			gif=seriesname+iteraion+'_bck.gif'
			ogv=seriesname+iteraion+'_bck.ogv'
			mp4=seriesname+iteraion+'_bck.mp4'
			webm=seriesname+iteraion+'_bck.webm'
		png='*.png'
		pngff='slice%04d.png'
		img_full=outdir+'/'+img
		mrc_full=outdir+'/'+mrcf
		vid_path=os.path.join(rundir,'media','reconstructions')
		gif_full=vid_path+'/'+gif
		ogv_full=vid_path+'/'+ogv
		mp4_full=vid_path+'/'+mp4
		webm_full=vid_path+'/'+webm
		png_full=vid_path+'/'+png
		pngff_full=vid_path+'/'+pngff
		rx=int(rx/map_sampling)
		ry=int(ry/map_sampling)
		
		# Convert the reconstruction *.img file to mrc for further processing
		os.system("i3cut -fmt mrc %s %s" % (img_full, mrc_full))
		#Normalizing here doesn't change video normalization.
		
		apDisplay.printMsg("Done generating reconstruction...")
		
		volume = mrc.read(mrc_full)
		slices = len(volume) - 1
		dimx=len(volume[0][0])
		dimy=len(volume[0])
		minval=np.amin(volume)
		maxval=np.amax(volume)
		
		# Convert the *.mrc to a series of pngs
		
		if parallel=="True":
			procs=mp.cpu_count()
		else:
			procs=1
		apDisplay.printMsg("Creating reconstruction video...")
		if procs == 1:
			for i in range(0,slices+1):
				processReconImages(i,slices,vid_path,volume,minval,maxval,pixelsize,map_sampling,dimx,dimy,show_window_size,rx,ry)
		else: #Parallelize
			for i in range(0,slices+1):
				p3 = mp.Process(target=processReconImages, args=(i,slices,vid_path,volume,minval,maxval,pixelsize,map_sampling,dimx,dimy,show_window_size,rx,ry,))
				p3.start()
				
				if ((i % (procs-1) == 0) and (i != 0)) or (procs == 1):
					[p3.join() for p3 in mp.active_children()]
		
		if video_type == "gif":
			command = "convert -delay 11 -loop 0 -layers Optimize %s %s;" % (png_full, gif_full)
			command += 'ffmpeg -y -v 0 -framerate 9 -pattern_type glob -i "%s" -codec:v libx264 -profile:v baseline -pix_fmt yuv420p -g 30 %s' % (png_full, mp4_full)
		else: #video_type == "html5vid"
			command = 'ffmpeg -y -v 0 -framerate 9 -pattern_type glob -i "%s" -codec:v libtheora -b:v 3000K -g 30 %s;' % (png_full, ogv_full)
			command += 'ffmpeg -y -v 0 -framerate 9 -pattern_type glob -i "%s" -codec:v libx264 -profile:v baseline -pix_fmt yuv420p -g 30 %s;' % (png_full, mp4_full)
			command += 'ffmpeg -y -v 0 -framerate 9 -pattern_type glob -i "%s" -codec:v libvpx -b:v 3000K -g 30 %s' % (png_full, webm_full)
		os.system(command)
		command2 = "rm %s" % (png_full)
		os.system(command2)
		if keep_recons == "false":
			command3 = "rm %s %s" % (img_full, mrc_full)
			os.system(command3)
		apDisplay.printMsg("Done creating reconstruction video!")
		
		if video_type == "gif":
			return gif_full, None, None
		else: #video_type == "html5vid"
			return ogv_full, mp4_full, webm_full
	except:
		apDisplay.printWarning("Alignment Images and/or Videos could not be generated. Make sure i3, ffmpeg, and imagemagick are in your $PATH. Make sure that pyami and scipy are in your $PYTHONPATH.\n")
		

def makeDefocusPlot(rundir, seriesname, defocus_file_full):
	'''
	Creates a plot of the measured and interpolated defocus values.
	'''
	try: #If anything fails, it's likely that something isn't in the path
		os.system("mkdir -p %s/media/ctf_correction 2>/dev/null" % rundir)
		defocus_fig_full=rundir+'/media/ctf_correction/'+seriesname+'_defocus.png'
		
		f=open(defocus_file_full,'r')
		lines=f.readlines()
		f.close()
		
		iterlines=iter(lines)
		angles=[]
		defocus=[]
		for line in iterlines:
			vals=line.split()
			angles.append(float(vals[3]))
			defocus.append(float(vals[4])/1000)
		
		pylab.clf()
		pylab.plot(angles,defocus)
		pylab.xlabel("Tilt Image Angle (degrees)")
		pylab.ylabel("Defocus (microns)")
		pylab.title("Measured and Interpolated Defoci for all Images")
		plt.gca().set_xlim(min(angles), max(angles))
		pylab.grid(True)
		pylab.minorticks_on()
		pylab.savefig(defocus_fig_full, bbox_inches='tight')
		pylab.clf()
		
		#rename pngs to be gifs so that Appion will display them properly (this is a ridiculous redux workaround to display images with white backgrounds by changing png filename extensions to gif and then using loadimg.php?rawgif=1 to load them, but oh well)
		os.system('mv %s %s' % (defocus_fig_full,defocus_fig_full[:-3]+"gif"))
		apDisplay.printMsg("Done creating Defocus Plot!")
	except:
		apDisplay.printWarning("Defocus plot could not be generated. Make sure pylab is in your $PATH. Make sure that scipy are in your $PYTHONPATH.\n")


def makeCTFPlot(rundir, seriesname, defocus_file_full, voltage, cs):
	'''
	Creates a plot of the CTF function squared based on the average of the estimated defocus values.
	Here we use Joachim Frank's CTF and Envelope definitions from section 3 of
	Three-Dimensional Electron Microscopy of Macromolecular Assemblies 2nd Ed., 2006.
	'''
	try: #If anything fails, it's likely that something isn't in the path
		os.system("mkdir -p %s/media/ctf_correction 2>/dev/null" % rundir)
		ctf_fig_full=rundir+'/media/ctf_correction/'+seriesname+'_ctf.png'
		f=open(defocus_file_full,'r')
		lines=f.readlines()
		f.close()
		
		iterlines=iter(lines)
		defocus=[]
		for line in iterlines:
			vals=line.split()
			defocus.append(float(vals[4])*10**-9)
		
		defocus=np.array(defocus)
		avgdefocus=defocus.mean()
		def_spread=750*10**-10  #750 angstrom defocus spread
		q0=0.5
		voltage=voltage*1000
		cs=cs/1000
		wavelength=(1.226426025488137*10**-9)/((voltage + (voltage**2)*(9.784756346657094*10**-7)))**(1/2)
		
		x=np.linspace(0, 2.5*10**9, 5000)
		y=(np.sin((-np.pi*avgdefocus*wavelength*x**2)+(np.pi*cs*(wavelength**3)*x**4)/2)*np.exp(-(np.pi**2)*(q0**2)*(cs*(wavelength**3)*(x**3)-avgdefocus*wavelength*x)**2)*np.exp(-(np.pi*def_spread*wavelength*(x**2)/2)**2))**2
		
		plt.clf()
		plt.figure()
		plt.plot(x,y)
		plt.xlabel("Spatial Frequency (1/$\AA$)")
		plt.ylabel("Approximate Phase Contrast Delivered")
		plt.title("Estimated CTF^2 of Tilt-Series")
		plt.grid(True)
		plt.minorticks_on()
		plt.savefig(ctf_fig_full, bbox_inches='tight')
		plt.clf()
		
		#rename pngs to be gifs so that Appion will display them properly (this is a ridiculous redux workaround to display images with white backgrounds by changing png filename extensions to gif and then using loadimg.php?rawgif=1 to load them, but oh well)
		os.system('mv %s %s' % (ctf_fig_full,ctf_fig_full[:-3]+"gif"))
		apDisplay.printMsg("Done creating CTF Plot!")
	except:
		apDisplay.printWarning("CTF plot could not be generated. Make sure pylab is in your $PATH. Make sure that scipy are in your $PYTHONPATH.\n")


def makeDosePlots(rundir, seriesname, tilts, accumulated_dose_list, dose_a, dose_b, dose_c):
	'''
	Creates a plot of the accumulated dose vs tilt image and tilt image angle.
	Creates a plot of the dose compensation performed.
	'''
	import warnings
	warnings.simplefilter("ignore", RuntimeWarning)  #supresses an annoying power warningthat doesn't affect anything.
	try: #If anything fails, it's likely that something isn't in the path
		os.system("mkdir -p %s/media/dose_compensation 2>/dev/null" % rundir)
		dose_full=rundir+'/media/dose_compensation/'+seriesname+'_dose.png'
		dose_compensation_full=rundir+'/media/dose_compensation/'+seriesname+'_dose_compensation.png'
		pylab.clf()
		
		pylab.plot(tilts, accumulated_dose_list, '.')
		pylab.xlabel("Tilt Image Angle (degrees)")
		pylab.ylabel("Accumulated Dose (e-/$\AA$^2)")
		pylab.title("Accumulated Dose for Tilt-Series Images")
		pylab.grid(True)
		pylab.minorticks_on()
		pylab.savefig(dose_full, bbox_inches='tight')
		pylab.clf()
		
		plt.clf()
		upperlim=int(max(accumulated_dose_list) + 9.9999) // 10 * 10
		x=np.linspace(0, upperlim, 200)
		y=(dose_a/(x - dose_c))**(1/dose_b)  #equation (3) from Grant & Grigorieff, 2015
		plt.figure()
		plt.plot(x,y)
		plt.xlabel("Accumulated Dose (e-/$\AA$^2)")
		plt.ylabel("Lowpass Filter ($\AA$)")
		plt.title("Dose Compensation Applied\n(a=%s, b=%s, c=%s)" % (dose_a, dose_b, dose_c))
		plt.grid(True)
		plt.minorticks_on()
		plt.savefig(dose_compensation_full, bbox_inches='tight')
		plt.clf()
		
		#rename pngs to be gifs so that Appion will display them properly (this is a ridiculous redux workaround to display images with white backgrounds by changing png filename extensions to gif and then using loadimg.php?rawgif=1 to load them, but oh well)
		os.system('mv %s %s;mv %s %s' % (dose_full,dose_full[:-3]+"gif",dose_compensation_full,dose_compensation_full[:-3]+"gif"))
		
	except:
		apDisplay.printWarning("Dose plots could not be generated. Make sure pylab is in your $PATH\n")


def makeAngleRefinementPlots(rundir, seriesname):
	'''
	Creates a plot of the tilt azimuth, a plot of only orientation angles,
	and a plot of the tilt elevation (see Protomo user guide or doi:10.1016/j.ultramic.2005.07.007)
	over all completed iterations.
	'''
	try: #If anything fails, it's likely that something isn't in the path
		apDisplay.printMsg("Creating angle refinement plot images...")
		os.chdir(rundir)
		os.system("mkdir -p %s/media/angle_refinement 2>/dev/null" % rundir)
		azimuth_full=rundir+'/media/angle_refinement/'+seriesname+'_azimuth.png'
		orientation_full=rundir+'/media/angle_refinement/'+seriesname+'_orientation.png'   #Temporarily(?) keeping the name as theta for backwards compatibility
		elevation_full=rundir+'/media/angle_refinement/'+seriesname+'_elevation.png'
		pylab.clf()
		
		tiltfiles=glob.glob("%s*.tlt" % seriesname)
		tiltfiles.sort()
		
		i=0
		iters=[]
		azimuths=[]
		psis=[]
		thetas=[]
		phis=[]
		elevations=[]
		for tiltfile in tiltfiles:
			cmd1="awk '/AZIMUTH /{print $3}' %s" % tiltfile
			proc=subprocess.Popen(cmd1, stdout=subprocess.PIPE, shell=True)
			(azimuth, err) = proc.communicate()
			azimuth=float(azimuth)
			azimuths.append(azimuth)
			
			cmd2="awk '/PSI /{print $2}' %s" % tiltfile
			proc=subprocess.Popen(cmd2, stdout=subprocess.PIPE, shell=True)
			(psi, err) = proc.communicate()
			if psi == '':  #tlt file from Coarse Alignment has no psi estimation.
				psi=0
			else:
				psi=float(psi)
			psis.append(psi)
			
			cmd3="awk '/THETA /{print $2}' %s" % tiltfile
			proc=subprocess.Popen(cmd3, stdout=subprocess.PIPE, shell=True)
			(theta, err) = proc.communicate()
			if theta == '':  #tlt file from Coarse Alignment has no theta estimation.
				theta=0
			else:
				theta=float(theta)
			thetas.append(theta)
			
			cmd4="awk '/PHI /{print $2}' %s" % tiltfile
			proc=subprocess.Popen(cmd4, stdout=subprocess.PIPE, shell=True)
			(phi, err) = proc.communicate()
			if phi == '':  #tlt file from Coarse Alignment has no phi estimation.
				phi=0
			else:
				phi=float(phi)
			phis.append(phi)
			
			cmd5="awk '/ELEVATION /{print $3}' %s" % tiltfile
			proc=subprocess.Popen(cmd5, stdout=subprocess.PIPE, shell=True)
			(elevation, err) = proc.communicate()
			if elevation == '':  #tlt file may not have ELEVATION
				elevation=0
			else:
				elevation=float(elevation)
			elevations.append(elevation)
			
			iters.append(float(i))
			i+=1
		
		pylab.plot(iters, azimuths)
		pylab.rcParams["axes.titlesize"] = 12
		pylab.xlabel("Iteration")
		pylab.ylabel("Azimuth (degrees)")
		pylab.title("Tilt Azimuth Refinement")
		pylab.grid(True)
		pylab.minorticks_on()
		pylab.savefig(azimuth_full, bbox_inches='tight')
		pylab.clf()
		
		pylab.plot(iters, psis, label='Psi')
		pylab.plot(iters, thetas, label='Theta')
		pylab.plot(iters, phis, label='Phi')
		pylab.rcParams["axes.titlesize"] = 12
		pylab.legend(loc='best', fancybox=True, prop=dict(size=11))
		pylab.xlabel("Iteration")
		pylab.ylabel("Orientation angles (degrees)")
		pylab.title("Orientation Angle Refinement")
		pylab.grid(True)
		pylab.minorticks_on()
		pylab.savefig(orientation_full, bbox_inches='tight')
		pylab.clf()
		
		pylab.plot(iters, elevations)
		pylab.rcParams["axes.titlesize"] = 12
		pylab.xlabel("Iteration")
		pylab.ylabel("Elevation (degrees)")
		pylab.title("Tilt Elevation Refinement")
		pylab.grid(True)
		pylab.minorticks_on()
		pylab.savefig(elevation_full, bbox_inches='tight')
		pylab.clf()
		
		#rename pngs to be gifs so that Appion will display it properly (this is a ridiculous redux workaround to display images with white backgrounds by changing png filename extensions to gif and then using loadimg.php?rawgif=1 to load them, but oh well)
		os.system('mv %s %s' % (azimuth_full,azimuth_full[:-3]+"gif"))
		os.system('mv %s %s' % (orientation_full,orientation_full[:-3]+"gif"))
		os.system('mv %s %s' % (elevation_full,elevation_full[:-3]+"gif"))
		
		apDisplay.printMsg("Done creating angle refinement plots!")
	except:
		apDisplay.printWarning("Angle refinement plots could not be generated. Make sure pylab is in your $PATH.\n")
