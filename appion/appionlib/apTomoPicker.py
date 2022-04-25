#!/usr/bin/env python


import math
import os
import sys
import shutil
import subprocess
import scipy.misc
import scipy.interpolate
import multiprocessing as mp
import numpy as np
from pyami import mrc
from appionlib import apDisplay
from appionlib.apImage import imagefilter


#=====================
def findLocalMaxima(tomogram, dog_tomogram, dimx, dimy, dimz, sidelength, particle_rad, edge_dist, mean, std, max_picks):
	'''Returns a dict of all local DoG peaks and their corresponding real space intensity mean'''
	def findStdDevs(percentile):
		'''Consults a standard normal table to determine the number standard deviations from the mean cutoff'''
		std_table = {'0.0': 0.5, '0.1': 0.5398, '0.2': 0.5793, '0.3': 0.6179, '0.4': 0.6554, '0.5': 0.6915, '0.6': 0.7257, '0.7': 0.758, '0.8': 0.7881, '0.9': 0.8159, '1': 0.8413, '1.1': 0.8643, '1.2': 0.8849, '1.3': 0.9032, '1.4': 0.9192, '1.5': 0.9332, '1.6': 0.9452, '1.7': 0.9554, '1.8': 0.9641, '1.9': 0.9713, '2': 0.9772, '2.1': 0.9821, '2.2': 0.9861, '2.3': 0.9893, '2.4': 0.9918, '2.5': 0.9938, '2.6': 0.9953, '2.7': 0.9965, '2.8': 0.9974, '2.9': 0.9981, '3': 0.9987, '3.1': 0.999, '3.2': 0.9993, '3.3': 0.9995, '3.4': 0.9997, '3.5': 0.9998, '3.7': 0.9999}
		stds, value = min(list(std_table.items()), key=lambda __val: abs(__val[1] - percentile))
		return float(stds)
	apDisplay.printMsg("Identifying all peaks...")
	pick_dict = []
	particle_diam = int(2*particle_rad*0.625)
	particle_rad = int(particle_rad*0.625)
	#First get the total number of so we can de novo filter out a certain number of peaks to consider further (this saves a lot of time later on)
	for z in range(edge_dist, dimz - edge_dist, particle_diam):
		for y in range(edge_dist, dimy - edge_dist, particle_diam):
			for x in range(edge_dist, dimx - edge_dist, particle_diam):
				mean_intensity = tomogram[z-particle_rad:z+particle_rad, y-particle_rad:y+particle_rad, x-particle_rad:x+particle_rad].mean()
				max_loc = list(np.unravel_index(dog_tomogram[z-particle_rad:z+particle_rad, y-particle_rad:y+particle_rad, x-particle_rad:x+particle_rad].argmax(), dog_tomogram[z-particle_rad:z+particle_rad, y-particle_rad:y+particle_rad, x-particle_rad:x+particle_rad].shape))
				max_loc = [i + j for i, j in zip(max_loc, [z-particle_rad, y-particle_rad, x-particle_rad])]
				max_val = dog_tomogram[z-particle_rad:z+particle_rad, y-particle_rad:y+particle_rad, x-particle_rad:x+particle_rad].max()
				pick_dict.append({'zcoord':max_loc[0], 'ycoord':max_loc[1], 'xcoord':max_loc[2], 'voxel_value':max_val, 'mean_intensity':mean_intensity})
	#Next obtain different thresholded picks for heuristics reasons
	percentile = 1-(max_picks/(10*len(pick_dict)))
	stds = findStdDevs(percentile)
	pick_dicts = [[],[],[],[],[],[],[],[],[],[],[]]
	thresholded_pick_dicts = [[],[],[],[],[],[],[],[],[],[],[]]
	thresholds = []
	for i in np.arange(1,2.1,0.1): #i is a heuristic factor
		thresholds.append(mean + stds*std*i)
	#threshold = mean + stds*std
	for z in range(edge_dist, dimz - edge_dist, particle_diam):
		for y in range(edge_dist, dimy - edge_dist, particle_diam):
			for x in range(edge_dist, dimx - edge_dist, particle_diam):
				mean_intensity = tomogram[z-particle_rad:z+particle_rad, y-particle_rad:y+particle_rad, x-particle_rad:x+particle_rad].mean()
				max_loc = list(np.unravel_index(dog_tomogram[z-particle_rad:z+particle_rad, y-particle_rad:y+particle_rad, x-particle_rad:x+particle_rad].argmax(), dog_tomogram[z-particle_rad:z+particle_rad, y-particle_rad:y+particle_rad, x-particle_rad:x+particle_rad].shape))
				max_loc = [i + j for i, j in zip(max_loc, [z-particle_rad, y-particle_rad, x-particle_rad])]
				max_val = dog_tomogram[z-particle_rad:z+particle_rad, y-particle_rad:y+particle_rad, x-particle_rad:x+particle_rad].max()
				i=0
				for threshold in thresholds:
					if max_val > threshold:
						pick_dicts[i].append({'zcoord':max_loc[0], 'ycoord':max_loc[1], 'xcoord':max_loc[2], 'voxel_value':max_val, 'mean_intensity':mean_intensity})
					else:
						thresholded_pick_dicts[i].append({'zcoord':max_loc[0], 'ycoord':max_loc[1], 'xcoord':max_loc[2], 'voxel_value':max_val, 'mean_intensity':mean_intensity})
					i+=1
	print(list(range(len(thresholds),0,-1)))
	for j in range(len(thresholds),0,-1):
		print(j)
		print(thresholds[j-1])
		print(len(pick_dicts[j-1]))
		if len(pick_dicts[j-1]) < 10*max_picks:
			print("True")
	sys.exit()
	
	#heuristics if there are still too many picks
	# print len(thresholded_pick_dict)
	# if len(thresholded_pick_dict) > 3*max_picks:
	# 	if len(thresholded_pick_dict) > 10*max_picks:
	# 		stds = 1.8*stds
	# 	elif len(thresholded_pick_dict) > 8*max_picks:
	# 		stds = 1.6*stds
	# 	elif len(thresholded_pick_dict) > 6*max_picks:
	# 		stds = 1.4*stds
	# 	elif len(thresholded_pick_dict) > 4*max_picks:
	# 		stds = 1.2*stds
	# 	else:
	# 		stds = 1.1*stds
	# 	pick_dict = []
	# 	thresholded_pick_dict = []
	# 	threshold = mean + stds*std
	# 	for z in range(edge_dist, dimz - edge_dist, particle_diam):
	# 		for y in range(edge_dist, dimy - edge_dist, particle_diam):
	# 			for x in range(edge_dist, dimx - edge_dist, particle_diam):
	# 				mean_intensity = tomogram[z-particle_rad:z+particle_rad, y-particle_rad:y+particle_rad, x-particle_rad:x+particle_rad].mean()
	# 				max_loc = list(np.unravel_index(dog_tomogram[z-particle_rad:z+particle_rad, y-particle_rad:y+particle_rad, x-particle_rad:x+particle_rad].argmax(), dog_tomogram[z-particle_rad:z+particle_rad, y-particle_rad:y+particle_rad, x-particle_rad:x+particle_rad].shape))
	# 				max_loc = [i + j for i, j in zip(max_loc, [z-particle_rad, y-particle_rad, x-particle_rad])]
	# 				max_val = dog_tomogram[z-particle_rad:z+particle_rad, y-particle_rad:y+particle_rad, x-particle_rad:x+particle_rad].max()
	# 				if max_val < threshold:
	# 					thresholded_pick_dict.append({'zcoord':max_loc[0], 'ycoord':max_loc[1], 'xcoord':max_loc[2], 'voxel_value':max_val, 'mean_intensity':mean_intensity})
	# 				else:
	# 					pick_dict.append({'zcoord':max_loc[0], 'ycoord':max_loc[1], 'xcoord':max_loc[2], 'voxel_value':max_val, 'mean_intensity':mean_intensity})
	return pick_dict, thresholded_pick_dict

#=====================
def removePicksByThreshold(pick_dict, mean, std, stds):
	'''If a pick has a voxel value too far below the mean it is removed'''
	apDisplay.printMsg("Removing picks based on threshold...")
	threshold = mean + stds*std
	for pick in pick_dict:
		if pick['voxel_value'] < threshold:
			pick_dict.remove(pick)
	return pick_dict

#=====================
def removeOverlappingPeaks(pick_dict, cutoff):
	'''Adapted from Neil Voss' 2D peak finder'''
	apDisplay.printMsg("Removing overlapping peaks...")
	def peakDistSq(a,b):
		x = a['xcoord']
		y = a['ycoord']
		z = a['zcoord']
		x2 = b['xcoord']
		y2 = b['ycoord']
		z2 = b['zcoord']
		return (x-x2)**2 + (y-y2)**2 + (z-z2)**2
	def _peakCompareSmallBig(a, b):
		if float(a['voxel_value']) > float(b['voxel_value']):
			return 1
		else:
			return -1
	cutsq = cutoff**2 + 1
	pick_dict.sort(_peakCompareSmallBig)
	i=0
	while i < len(pick_dict):
		j = i+1
		while j < len(pick_dict):
			distsq = peakDistSq(pick_dict[i], pick_dict[j])
			if(distsq < cutsq):
				del pick_dict[i]
				i -= 1
				j = len(pick_dict)
			j += 1
		i += 1
	
	return pick_dict

#=====================
def removeJunk(pick_dict, junk_tolerance):
	'''Removes picks based on intensity difference of rastered box from the mean tomogram intensity'''
	apDisplay.printMsg("Removing potential junk...")
	intensity_list = []
	for pick in pick_dict:
		intensity_list.append(pick['mean_intensity'])
	intensity_list = np.asarray(intensity_list)
	mean_pick_intensity = intensity_list.mean()
	std_pick_intensity = intensity_list.std()
	filtered_pick_dict = []
	for pick in pick_dict:
		if (abs(pick['mean_intensity']) < mean_pick_intensity + 0.25*junk_tolerance*std_pick_intensity):
			filtered_pick_dict.append(pick)
	return filtered_pick_dict

#=====================
def dogPicker3D(picker_dir, tomogram, particle_diam, diam_variance, max_picks, junk_tolerance, lowpass_type, pixelsize=1, binning=1):
	"""
	DoG picker for 3D volumes; intended for tomograms. tomogram = mrc input.
	Lowpasses the tomogram twice separately with either two user-inputted values corresponding to the minimum and maximum dimensions of the desired object,
	or if only one dimension is inputted then the tomogram will be lowpassed twice with +-10% the inputted value.
	Rasters a cube across the tomogram correlation map, finding local maxima within the search volume.
	Written by: Alex Noble
	"""
	print("")
	def proc3dLowpass(command):
		try:
			proc=subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
			(code, err) = proc.communicate()
		except:
			apDisplay.printMsg("EMAN's proc3d not found. Aborting...")
			sys.exit()
	tomogram_fullpath = os.path.join(picker_dir, os.path.basename(tomogram))
	tomogram_basename = os.path.splitext(os.path.basename(tomogram_fullpath))[0]
	tomogram = mrc.read(tomogram_fullpath)
	particle_diam = (particle_diam/pixelsize)/binning
	particle_rad = int(particle_diam/2)
	pixelsize = pixelsize*binning
	edge_dist = particle_rad+2
	dimx = len(tomogram[0][0])
	dimy = len(tomogram[0])
	dimz = len(tomogram)
	
	#if lowpass_type == 'fermi':
		
	#elif lowpass_type == 'tanh':
		
	#elif #lowpass_type == 'gaussian':
		
	#else: proc3d lowpass
	top_lp = particle_diam*(1+(diam_variance/100))*pixelsize
	top_lp_filename = tomogram_basename+'lp'+str(top_lp)+'.mrc'
	top_lp_fullpath = os.path.join(picker_dir, top_lp_filename)
	bottom_lp = particle_diam*(1-(diam_variance/100))*pixelsize
	bottom_lp_filename = tomogram_basename+'lp'+str(bottom_lp)+'.mrc'
	bottom_lp_fullpath = os.path.join(picker_dir, bottom_lp_filename)
	if (dimx*dimy*dimz) > 1000000000:
		apDisplay.printMsg("Generating a Difference of Gaussian tomogram for picking.")
		apDisplay.printMsg("This may take tens of minutes to hours. Consider picking on more highly binned tomograms.")
	elif (dimx*dimy*dimz) > 100000000:
		apDisplay.printMsg("Generating a Difference of Gaussian tomogram for picking.")
		apDisplay.printMsg("This may take a few of minutes to tens of minutes...")
	else:
		apDisplay.printMsg("Generating a Difference of Gaussian tomogram for picking...")
	cmd1 = 'proc3d %s %s apix=%f lp=%f' % (tomogram_fullpath, top_lp_fullpath, pixelsize, top_lp)
	cmd2 = 'proc3d %s %s apix=%f lp=%f' % (tomogram_fullpath, bottom_lp_fullpath, pixelsize, bottom_lp)
	
	jobs=[]
	jobs.append(mp.Process(target=proc3dLowpass, args=(cmd1,)))
	jobs.append(mp.Process(target=proc3dLowpass, args=(cmd2,)))
	for job in jobs:
		job.start()
	for job in jobs:
		job.join()
	top_lp_tomogram = mrc.read(top_lp_fullpath)
	bottom_lp_tomogram = mrc.read(bottom_lp_fullpath)
	dog_tomogram = top_lp_tomogram - bottom_lp_tomogram
	dog_tomogram_path = os.path.join(picker_dir, '%s_DoG_tomogram.mrc' % tomogram_basename)
	mrc.write(dog_tomogram, dog_tomogram_path)
	
	# Find local maxima within search volumes
	pick_dict, thresholded_pick_dict = findLocalMaxima(tomogram, dog_tomogram, dimx, dimy, dimz, particle_diam, particle_rad, edge_dist, dog_tomogram.mean(), dog_tomogram.std(), max_picks)
	
	initial_picks = len(pick_dict)
	apDisplay.printMsg("Found %d peaks. %d peaks were removed by thresholding." % (initial_picks, len(thresholded_pick_dict)))
	
	# Remove duplicates/close picks
	pick_dict = removeOverlappingPeaks(pick_dict, particle_diam+1)
	
	removed_picks2 = initial_picks - len(pick_dict)
	pick_count = len(pick_dict)
	apDisplay.printMsg("Removed %d overlapping peaks." % removed_picks2)
	
	# Remove low voxel value picks
	pick_dict = pick_dict[-max_picks:]
	
	removed_picks3 = pick_count - len(pick_dict)
	pick_count = len(pick_dict)
	apDisplay.printMsg("Removed %d low correlation peaks." % removed_picks3)
	
	# Remove junk picks
	pick_dict = removeJunk(pick_dict, junk_tolerance)
	
	removed_picks4 = pick_count - len(pick_dict)
	apDisplay.printMsg("Removed %d junk peaks." % removed_picks4)
	
	unbinned_tbl_path = os.path.join(picker_dir, '%s_bin1_%ddogpicks_%.2fangstromobjects.tbl' % (tomogram_basename, len(pick_dict), particle_diam*pixelsize))
	unbinned_tbl = open(unbinned_tbl_path,'w')
	unbinned_coords_path = os.path.join(picker_dir, '%s_bin1_%ddogpicks_%.2fangstromobjects.coords' % (tomogram_basename, len(pick_dict), particle_diam*pixelsize))
	unbinned_coords = open(unbinned_coords_path,'w')
	unbinned_bild_path = os.path.join(picker_dir, '%s_bin1_%ddogpicks_%.2fangstromobjects.bild' % (tomogram_basename, len(pick_dict), particle_diam*pixelsize))
	unbinned_bild = open(unbinned_bild_path,'w')
	tilt_range = tomogram_basename.split('ang')[1].split('thick')[0].rstrip('_').split('to')
	for i in range(len(pick_dict)):
		unbinned_tbl.write("%d 1 1 0 0 0 0 0 0 0 0 0 1 %f %f %f %f 0 0 1 0 0 0 %d %d %d 0 0 0 0 0 1 0 0 0\n" % (i+1, float(tilt_range[0]), float(tilt_range[1]), float(tilt_range[0]), float(tilt_range[1]), pick_dict[i]['xcoord']*binning, pick_dict[i]['ycoord']*binning, pick_dict[i]['zcoord']*binning))
		unbinned_coords.write("%d %d %d\n" % (pick_dict[i]['xcoord']*binning, pick_dict[i]['ycoord']*binning, pick_dict[i]['zcoord']*binning))
		unbinned_bild.write(".color blue\n.dot %d %d %d\n" % (pick_dict[i]['xcoord']*binning, pick_dict[i]['ycoord']*binning, pick_dict[i]['zcoord']*binning))
	unbinned_tbl.close()
	unbinned_coords.close()
	unbinned_bild.close()
	if binning > 1:
		binned_tbl_path = os.path.join(picker_dir, '%s_bin%d_%ddogpicks_%.2fangstromobjects.tbl' % (tomogram_basename, binning, len(pick_dict), particle_diam*pixelsize))
		binned_tbl = open(binned_tbl_path,'w')
		binned_coords_path = os.path.join(picker_dir, '%s_bin%d_%ddogpicks_%.2fangstromobjects.coords' % (tomogram_basename, binning, len(pick_dict), particle_diam*pixelsize))
		binned_coords = open(binned_coords_path,'w')
		binned_bild_path = os.path.join(picker_dir, '%s_bin%d_%ddogpicks_%.2fangstromobjects.bild' % (tomogram_basename, binning, len(pick_dict), particle_diam*pixelsize))
		binned_bild = open(binned_bild_path,'w')
		for i in range(len(pick_dict)):
			binned_tbl.write("%d 1 1 0 0 0 0 0 0 0 0 0 1 %f %f %f %f 0 0 1 0 0 0 %d %d %d 0 0 0 0 0 1 0 0 0\n" % (i+1, float(tilt_range[0]), float(tilt_range[1]), float(tilt_range[0]), float(tilt_range[1]), pick_dict[i]['xcoord'], pick_dict[i]['ycoord'], pick_dict[i]['zcoord']))
			binned_coords.write("%d %d %d\n" % (pick_dict[i]['xcoord'], pick_dict[i]['ycoord'], pick_dict[i]['zcoord']))
			binned_bild.write(".color blue\n.dot %d %d %d\n" % (pick_dict[i]['xcoord'], pick_dict[i]['ycoord'], pick_dict[i]['zcoord']))
		binned_tbl.close()
		binned_coords.close()
		binned_bild.close()
	
	os.system("rm %s %s" % (top_lp_fullpath, bottom_lp_fullpath))
	
	apDisplay.printMsg("\033[1mTotal particles picked: %d\033[0m" % len(pick_dict))
	apDisplay.printMsg("\033[1mDone!\033[0m")
	apDisplay.printMsg("The picked tomogram, DoG tomogram, and picks (coords, Dynamo tbl, and Chimera bild) are here:")
	print(picker_dir)
	
	apDisplay.printMsg("You can view the picks in Dynamo by doing the following:")
	apDisplay.printMsg("\tType dynamo x to enter the Dynamo command line,")
	apDisplay.printMsg("\tInput: dynamo_tomoview %s" % tomogram_fullpath)
	apDisplay.printMsg("\tIn the 'Model pool' menu in tomoview choose 'Import external file as a model into pool (memory)',")
	if binning > 1:
		apDisplay.printMsg("\tChoose %s and create model," % binned_tbl_path)
	else:
		apDisplay.printMsg("\tChoose %s and create model," % unbinned_tbl_path)
	apDisplay.printMsg("\tIn tomoview click 'Show models',")
	apDisplay.printMsg("\tUse the position scroller to move through the tomogram.\n")

