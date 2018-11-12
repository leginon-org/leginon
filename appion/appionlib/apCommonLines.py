import os
import re
import time
import glob
import math
import numpy
import subprocess
import operator
from appionlib import apImagicFile
from appionlib import apDisplay
from appionlib import apIMAGIC
from appionlib import apParam
from appionlib import apThread
from appionlib import apFile
from appionlib import apFourier
from appionlib import apEulerCalc
from appionlib import apXmipp
from appionlib import apXmippProtocolsProjMatchBasic as xp
from pyami import mrc, spider





#======================                                        ====================
#======================                                        ====================
#======================       CORRELATION FUNCTIONS            ====================
#======================                                        ====================
#======================                                        ====================



	
def calculate_ccc_matrix_2d(class_averages):
	'''
	takes as input a stack of class averages, then for each image in the stack
	calculates a cross-correlation coefficient to each successive image. It then 
	returns a matrix of cross-correlation coefficients between the images. 
	'''
	
	### read class averages and estimate time for completion
	imagicdict = apImagicFile.readImagic(filename=class_averages, msg=True)
	partarray = imagicdict['images']
	numpart = partarray.shape[0]
	boxsize = partarray.shape[1]
	timeper = 17.0e-9
	apDisplay.printMsg("Computing cross-correlation values in %s" 
		%(apDisplay.timeString(timeper*numpart**2*boxsize**2)))
	
	### cross correlate each class average to each successive class average
	ccc_matrix = numpy.ones((numpart, numpart))
	ccc_file = os.path.join(os.getcwd(), "CCCs_2d.dat")
	f = open(ccc_file, "w")
	for i in range(numpart):
		for j in range(i+1, numpart):
			ccs = calculate_ccs(partarray[i], partarray[j])
			ccc_matrix[i,j] = ccs
			ccc_matrix[j,i] = ccs
			str1 = "%05d %05d %.10f\n" % (i+1, j+1, ccc_matrix[i,j])
			f.write(str1)
			str2 = "%05d %05d %.10f\n" % (j+1, i+1, ccc_matrix[j,i])
			f.write(str2)	
	f.close()
	
	return ccc_matrix
	
#=====================

def calculate_ccc_matrix_3d(volumedict, num_volumes):
	'''
	for each volume calculates a cross-correlation coefficient to each successive volume, then 
	returns a file corresponding to cross-correlation coefficients between the images. 
	'''
	
	apDisplay.printMsg("Creating cross-correlation similarity matrix for affinity propagation ...")		
		
	### create a similarity matrix using cross-correlation of aligned 3-D models
	rundir = os.getcwd()
	cc_matrix = numpy.ones((num_volumes, num_volumes))

	### create cross-correlation similarity matrix
	for i in range(len(volumedict)):
		for j in range(i+1, len(volumedict)):		
			model1 = mrc.read(volumedict[i+1])
			model2 = mrc.read(volumedict[j+1])
			ccs = calculate_ccs(model1, model2)
			cc_matrix[i,j] = ccs
			cc_matrix[j,i] = ccs
			
	### write similarities (CCCs) to file 
	simfile = os.path.join(rundir, "CCCs_3d.dat")
	f = open(simfile, "w")
	for i in range(num_volumes):
		for j in range((i+1), num_volumes):
			str1 = "%05d %05d %.10f\n" % (i+1, j+1, cc_matrix[i,j])
			f.write(str1)
			str2 = "%05d %05d %.10f\n" % (j+1, i+1, cc_matrix[j,i])
			f.write(str2)
	f.close()
	
	return simfile, cc_matrix

#=====================	

def calculate_ccs(imgarray1, imgarray2):
	'''  Pearson correlation coefficient between two arrays of identical dimensions '''
	ccs = pearsonr(numpy.ravel(imgarray1), numpy.ravel(imgarray2))
	return ccs
	
#=====================	

def pearsonr(x, y):
	### simple Pearson correlation coefficient taken from SciPy
	"""Calculates a Pearson correlation coefficient and the p-value for testing
	non-correlation.
	
	The Pearson correlation coefficient measures the linear relationship
	between two datasets. Strictly speaking, Pearson's correlation requires
	that each dataset be normally distributed. Like other correlation
	coefficients, this one varies between -1 and +1 with 0 implying no
	correlation. Correlations of -1 or +1 imply an exact linear
	relationship. Positive correlations imply that as x increases, so does
	y. Negative correlations imply that as x increases, y decreases.
	
	Parameters
	----------
	x : 1D array
	y : 1D array the same length as x
	
	Returns
	-------
	Pearson's correlation coefficient
	
	References
	----------
	http://www.statsoft.com/textbook/glosp.html#Pearson%20Correlation
	"""
	# x and y should have same length.
	x = numpy.asarray(x)
	y = numpy.asarray(y)
	n = len(x)
	mx = x.mean()
	my = y.mean()
	xm, ym = x-mx, y-my
	r_num = n*(numpy.add.reduce(xm*ym))
	r_den = n*numpy.sqrt(ss(xm)*ss(ym))
	r = (r_num / r_den)
	
	# Presumably, if r > 1, then it is only some small artifact of floating
	# point arithmetic.
	r = min(r, 1.0)
	df = n-2
	
	# Use a small floating point value to prevent divide-by-zero nonsense
	# fixme: TINY is probably not the right value and this is probably not
	# the way to be robust. The scheme used in spearmanr is probably better.
	TINY = 1.0e-20
	t = r*numpy.sqrt(df/((1.0-r+TINY)*(1.0+r+TINY)))
	return r

#=====================
	
def ss(a, axis=0):
	### taken from SciPy
	"""Squares each value in the passed array, adds these squares, and
	returns the result.
	
	Parameters
	----------
	a : array
	axis : int or None
	
	Returns
	-------
	The sum along the given axis for (a*a).
	"""
	a, axis = _chk_asarray(a, axis)
	return numpy.sum(a*a, axis)

#=====================	
    
def _chk_asarray(a, axis):
	### taken from SciPy
	if axis is None:
		a = numpy.ravel(a)
		outaxis = 0
	else:
		a = numpy.asarray(a)
		outaxis = axis
	return a, outaxis
        
#=====================	

def euclideanDist(x, y):
	''' Euclidean Distance between two arrays of identical dimensions '''
	return numpy.sqrt(numpy.sum((numpy.ravel(x)-numpy.ravel(y))**2))
	
#=====================

def normList(numberList, normalizeTo=1):
	'''normalize values of a list to make its max = normalizeTo'''
	vMax = max(numberList)
	return [x/(vMax*1.0)*normalizeTo for x in numberList]

#=====================

def create_difference_matrix(ccc_matrix, norm=False):
	''' inverts the similarity matrix to create a difference matrix based on (diff=1-sim) metric '''

	### take inverse of CCC & normalize
	diff_matrix = numpy.where(ccc_matrix < 1, 1-ccc_matrix, 0)
	if norm is True:
		min = numpy.where(diff_matrix > 0, diff_matrix, 1).min()
		max = diff_matrix.max()
		norm_diff_matrix = numpy.where(diff_matrix > 0, (diff_matrix - (min+0.0001))/(max-min), 0)
		norm_diff_matrix = numpy.where(diff_matrix == 1, 1 - numpy.random.uniform(0,1)*0.000001, diff_matrix)
		return norm_diff_matrix
	else:
		return diff_matrix
	
#=====================

def calculate_sequence_of_addition(avgs, numpart, ccc_matrix, first=None, 
	normlist=False, non_weighted_sequence=False, msg=False):
	''' 
	calculates a unique sequence of addition of class averages. function first initializes a random seed, then calculates
	the rest of the sequence based on the resulting weighted probability matrix generated from each successive addition
	NOTE: image numbering starts with 0!
	'''
		
	### initialize sequence (image queue) and weight matrix, which determines sequence calculation
	probability_list = numpy.zeros(numpart)
	sequence = []
		
	### if completely random sequence is desired, do that here
	if non_weighted_sequence is True:
		if msg is True:
			apDisplay.printMsg("calculating random sequence of image addition")
		im_list = []
		for i in range(numpart):
			im_list.append(i)		
		while im_list:
			r = numpy.random.randint(len(im_list))
			sequence.append(im_list[r]+1)
			del im_list[r]
		return sequence
		
	else:	
		if msg is True:
			apDisplay.printMsg("calculating weighted randomized sequence of image addition")
		### otherwise randomize first image selection and continue with weighted selection
		im_queue = []
		for i in range(numpart):
			im_queue.append(i)
		if first != None and isinstance(first, int):
			im_init = first
		else:
			im_init = numpy.random.randint(low=0, high=numpart)

		### create probability matrix from ccc matrix and append new image
		diff_matrix = create_difference_matrix(ccc_matrix, norm=False)
		probability_list = create_probability_list(im_init, probability_list, diff_matrix)
		sequence.append(im_init+1)

		### figure out the rest of the sequence, based on the first randomly selected image
		for image in range(len(im_queue)-1):
			next_choice = weighted_random_pick(im_queue, probability_list)
			probability_list = update_probability_list(next_choice, probability_list, diff_matrix)
			
			### check to make sure that the probability list does not contain all zeros 
			### (in which case there are duplicate images)
			break_weighted_randomization = False
			for item in probability_list:
				if sum(probability_list) == 0:
					### do not weight randomization, just add the remaining images
					break_weighted_randomization = True 
					for i in range(len(im_queue)):
						if i+1 not in sequence:
							sequence.append(i+1)
							
			if break_weighted_randomization is True:
				break
			if normlist is True:
				probability_list = normList(probability_list)
			sequence.append(next_choice+1)
			
		return sequence

#=====================	

def create_probability_list(selection, probability_list, diff_matrix):
	''' creates the list that stores probability values used for weighted randomized selection '''
	
	for i in range(len(probability_list)):
		probability_list[i] += diff_matrix[i][selection]
#			if probability_list[i] == 0: ### slightly perturb to avoid identical selections in sequence
#				probability_list[i] = 0 + numpy.random.uniform(0,1) * 0.000001			
	return probability_list
	
#=====================	

def update_probability_list(selection, probability_list, diff_matrix):
	''' updates the list that stores probability values used for weighted randomized selection '''

	for i in range(len(probability_list)):
		if probability_list[i] != 0:
			probability_list[i] *= diff_matrix[i][selection]
	probability_list[selection] = 0 ### don't use this selection anymore

	return probability_list

#=====================

def weighted_random_pick(im_queue, probability_list):
	''' 
	based on the given probabilities of the existing choices, this function 
	determines what the next image will be. It uses a weighted randomized 
	decision-making strategy that takes into account how different the images are 
	from each other
	'''
	
	weight_total = sum((p for p in probability_list))
	n = numpy.random.uniform(0, weight_total)
	cumulative_p = 0.0
	for image, image_probability in zip(im_queue, probability_list):
		cumulative_p += image_probability
		if n < cumulative_p: break
				
	return image

#=====================	
	
def check_for_duplicates_in_sequence(sequence):
	### make sure that the sequence does not contain duplicate selections
	for j, s1 in enumerate(sequence):
		for k, s2 in enumerate(sequence):
			if j == k: pass
			else:
				if s1 == s2:
					apDisplay.printError("%d, %d, equivalent values in final sequence" % (s1, s2))
	return			
	
	
	
	
#======================                                        ====================
#======================                                        ====================
#======================       BATCH FILE FOR IMAGIC            ====================
#======================                                        ====================
#======================                                        ====================




def imagic_batch_file(sequence, iteration, avgs, symmetry, asqfilt, linmask, apix, 
	box, ang_inc, keep_ordered_num, ham_win, lpfilt, threes=False, do_not_remove=False):
	''' IMAGIC batch file creation for angular reconstitution '''
	
	rundir = os.getcwd()
	imagicroot = apIMAGIC.checkImagicExecutablePath()
	### convert sequence from a list to a string for 1st 3 and sequential projections
	proj_init = str(sequence[0])+";"+str(sequence[1])+";"+str(sequence[2])
	sequence = sequence[3:]
	if len(sequence) > 125: ### IMAGIC only accepts strings of a specified length
		numiter = int(math.ceil(len(sequence) / 125.0))
		sequences = []
		for i in range(numiter):
			if i != (numiter-1):
				proj_rest = ""
				for j in range(i*125,(i+1)*125):
					proj_rest = proj_rest+str(sequence[j])+";"
				sequences.append(proj_rest)
			else:
				proj_rest = ""
				for j in range(i*125,i*125+(len(sequence) % 125)):
					proj_rest = proj_rest+str(sequence[j])+";"
				sequences.append(proj_rest)
	else:
		proj_rest = ""
		for imagenum in sequence:
			proj_rest = proj_rest+str(imagenum)+";"
		
	### initial params & conversions
	clsavgs = avgs[:-4]
	rundir = os.path.join(rundir, "angular_reconstitution")
	filename = os.path.join(rundir, "imagicCreate3d"+str(iteration)+".batch")
	f = open(filename, 'w')
	f.write("#!/bin/csh -f\n")
	f.write("setenv IMAGIC_BATCH 1\n")
	f.write("cd "+rundir+"/\n")

	### 1st iteration of angular reconstitution using 3 initial projections for C1, 
	### OR simply 1st 3 additions for other symmetries
	f.write(str(imagicroot)+"/angrec/euler.e <<EOF > 3d"+str(iteration)+".log\n")
	f.write(symmetry+"\n")
#		f.write("c1\n")
	lowercase = str(symmetry).lower()
	if lowercase != "c1":
		f.write("0\n")
	f.write("new\n")
	f.write("fresh\n")
	f.write(str(clsavgs)+"\n")	
	f.write(proj_init+"\n")
	f.write("ordered"+str(iteration)+"\n")
	f.write("sino_ordered"+str(iteration)+"\n")
	if asqfilt is True:
		f.write("yes\n")
	else:
		f.write("no\n")
	f.write("%.3f\n" % (linmask / apix / box * 2))
	f.write("my_sine"+str(iteration)+"\n")
	f.write("%i\n" % (ang_inc))	
	if lowercase == "c1":
		f.write("30\n")
	f.write("no\n")
	f.write("EOF\n")

	if threes is False:
		### now calculate Euler angles for the rest of the projections in a brute force search
		if len(sequence) > 125: ### IMAGIC only accepts strings of a specified length
			for seq in sequences:
				f.write(str(imagicroot)+"/angrec/euler.e <<EOF >> 3d"+str(iteration)+".log\n")
				f.write(symmetry+"\n")
				if lowercase != "c1":
					f.write("0\n")
				f.write("new\n")
				f.write("add\n")
				f.write(str(clsavgs)+"\n")
				f.write(str(seq)+"\n")
				f.write("ordered"+str(iteration)+"\n")
				f.write("sino_ordered"+str(iteration)+"\n")
				if asqfilt is True:
					f.write("yes\n")
				else:
					f.write("no\n")
				f.write("%.3f\n" % (linmask / apix / box * 2))
				f.write("my_sine"+str(iteration)+"\n")
				f.write("%i\n" % (ang_inc))
				f.write("yes\n")
				f.write("EOF\n")
		else:
			f.write(str(imagicroot)+"/angrec/euler.e <<EOF >> 3d"+str(iteration)+".log\n")
			f.write(symmetry+"\n")
			if lowercase != "c1":
				f.write("0\n")
			f.write("new\n")
			f.write("add\n")
			f.write(str(clsavgs)+"\n")
			f.write(proj_rest+"\n")
			f.write("ordered"+str(iteration)+"\n")
			f.write("sino_ordered"+str(iteration)+"\n")
			if asqfilt is True:
				f.write("yes\n")
			else:
				f.write("no\n")
			f.write("%.3f\n" % (linmask / apix / box * 2))
			f.write("my_sine"+str(iteration)+"\n")
			f.write("%i\n" % (ang_inc))
			f.write("yes\n")
			f.write("EOF\n")
		
		### sort based on error in angular reconstitution
		f.write(str(imagicroot)+"/incore/excopy.e <<EOF >> 3d"+str(iteration)+".log\n")
		f.write("2D_IMAGES\n")
		f.write("SORT\n")
		f.write("ordered"+str(iteration)+"\n")
		f.write("ordered"+str(iteration)+"_sort\n")
		f.write("ANGULAR_ERROR\n")
		f.write("UP\n")
		f.write("%i\n" % (keep_ordered_num))	
		f.write("EOF\n")
		
	else:
		f.write(str(imagicroot)+"/stand/im_rename.e <<EOF \n")
		f.write("ordered"+str(iteration)+"\n")
		f.write("ordered"+str(iteration)+"_sort\n")
		f.write("EOF\n")		
	
	### build a 3-D model
	f.write(str(imagicroot)+"/threed/true_3d.e <<EOF >> 3d"+str(iteration)+".log\n")
	f.write("no\n")
	f.write("ALL_IN_ONE\n")
	f.write(symmetry+"\n")
	f.write("yes\n")
	f.write("ordered"+str(iteration)+"_sort\n")
	f.write("ANGREC_HEADER_VALUES\n")
	f.write("3d"+str(iteration)+"_ordered"+str(iteration)+"\n")
	f.write("rep"+str(iteration)+"_ordered"+str(iteration)+"\n")
	f.write("err"+str(iteration)+"_ordered"+str(iteration)+"\n")
	f.write("no\n")
	f.write("%f\n" % (ham_win))		
	f.write("0.8\n")		
	f.write("EOF\n")
	
	### low-pass filter
	lp_filt = lpfilt
	filtval = 2 * apix / lp_filt
	if filtval > 1:
		filtval = 1
	f.write(str(imagicroot)+"/threed/filter3d.e FORW FILTER <<EOF >> 3d"+str(iteration)+".log\n")
	f.write("lowpass\n")
	f.write("3d"+str(iteration)+"_ordered"+str(iteration)+"\n")
	f.write("3d"+str(iteration)+"_ordered"+str(iteration)+"_filt\n")
	f.write(str(filtval)+"\n")
	f.write("EOF\n")
	
	### write out a .plt file with all Euler angles
	f.write(str(imagicroot)+"/stand/headers.e <<EOF >> 3d"+str(iteration)+".log\n")
#		f.write("ordered"+str(iteration)+"_sort\n")
	f.write("PLT_OUT\n")
	f.write("THREED\n")
	if threes is False:
		f.write("ordered"+str(iteration)+"\n")
	else:
		f.write("ordered"+str(iteration)+"_sort\n")
	f.write("ordered"+str(iteration)+"_Eulers.plt\n")
	f.write("EOF\n")
	
	### convert to SPIDER format, but first rotate volume by 180 degrees around IMAGIC y, 
	### to make sure that the image remains UNCHANGED
	### a (0,180,0) rotation in IMAGIC is equivalent to a (180,180,0) rotation in 
	### Spider / Xmipp, due to the difference in coordinate systems
	f.write(str(imagicroot)+"/threed/rotate3d.e <<EOF >> 3d"+str(iteration)+".log\n")
	f.write("3d"+str(iteration)+"_ordered"+str(iteration)+"_filt\n")
	f.write("3d"+str(iteration)+"_ordered"+str(iteration)+"_filt_rot\n")
	f.write("FORWARD\n")	
	f.write("0,180,0\n")
	f.write("0,0,0\n")
	f.write("EOF\n")
	f.write(str(imagicroot)+"/stand/em2em.e <<EOF >> 3d"+str(iteration)+".log\n")
	f.write("IMAGIC\n")
	f.write("SPIDER\n")
	f.write("SINGLE_FILE\n")
	f.write("3D\n")
	f.write("3d"+str(iteration)+"_ordered"+str(iteration)+"_filt_rot\n")
	f.write("3d"+str(iteration)+"_ordered"+str(iteration)+"_filt.vol\n")
	f.write("LINUX\n")
	f.write("YES\n")
	f.write("EOF\n")
	
	### remove unecessary files, keeping only .batch, .lis, .plt & .log files
	if do_not_remove is False:
		if threes is False:
			f.write(str(imagicroot)+"/stand/imdel.e <<EOF >> 3d"+str(iteration)+".log\n")
			f.write("ordered%d\n" % (iteration))
			f.write("EOF\n")
		f.write(str(imagicroot)+"/stand/imdel.e <<EOF >> 3d"+str(iteration)+".log\n")
		f.write("sino_ordered%d\n" % (iteration))
		f.write("EOF\n")
		f.write(str(imagicroot)+"/stand/imdel.e <<EOF >> 3d"+str(iteration)+".log\n")
		f.write("err%d_ordered%d\n" % (iteration,iteration))
		f.write("EOF\n")
		f.write(str(imagicroot)+"/stand/imdel.e <<EOF >> 3d"+str(iteration)+".log\n")
		f.write("3d%d_ordered%d\n" % (iteration,iteration))
		f.write("EOF\n")
		f.write(str(imagicroot)+"/stand/imdel.e <<EOF >> 3d"+str(iteration)+".log\n")
		f.write("3d%d_ordered%d_filt_rot\n" % (iteration,iteration))
		f.write("EOF\n")
		f.write(str(imagicroot)+"/stand/imdel.e <<EOF >> 3d"+str(iteration)+".log\n")
		f.write("3d%d_ordered%d_filt\n" % (iteration,iteration))
		f.write("EOF\n")
		f.write(str(imagicroot)+"/stand/imdel.e <<EOF >> 3d"+str(iteration)+".log\n")
		f.write("my_sine%d\n" % (iteration
		))
		f.write("EOF\n")

	f.close()

	return filename	
	
	
	

	
#===================                                       ====================	
#===================                                       ====================
#===================        3D ALIGNMENT USING ML3D        ====================
#===================                                       ====================
#===================                                       ====================	
	
	
	
	
def xmipp_max_like_3d_align(volumedict, nproc, threadnproc, nref):
	''' 3-D maximum likelihood alignment of all models resulting from iterative 3d0 creation '''
	
	rundir = os.getcwd()
	### create necessary input .sel & .doc files
	selfile = open(os.path.join(rundir, "volumes.sel"), "w")
	for v in sorted(volumedict):
		selfile.write("%s 1\n" % volumedict[v])
	selfile.close()
	docfile = open(os.path.join(rundir, "volumes.doc"), "w")
	for v in sorted(volumedict):
		docfile.write(" ; %s\n" % volumedict[v])
		docfile.write(str(v)+" 10 0 0 0 0 0 0 0 0 0 0\n")
	docfile.close()
	
	### run 3-D maximum-likelihood alignment
	rundir = os.path.join(rundir, "max_like_alignment")
	if not os.path.isdir(rundir):
		os.mkdir(rundir)
	if nproc > 1:
		xmippcmd1 = "mpirun -np %d xmipp_mpi_ml_tomo " % nproc
	else:
		xmippcmd1 = "xmipp_ml_tomo "
	xmippcmd1+= "-i volumes.sel -o max_like_alignment/nref%d_15deg " % nref
	xmippcmd1+= "-nref %d -doc volumes.doc -iter 5 -ang 15 -dim 32 -perturb" % nref
	if threadnproc > 1:
		xmippcmd1 += " -thr "+str(threadnproc)
	apParam.runCmd(xmippcmd1, package="Xmipp")
	'''
	if nproc > 1:
		xmippcmd2 = "mpirun -np %d xmipp_mpi_ml_tomo " % nproc
	else:
		xmippcmd2 = "xmipp_ml_tomo "
	xmippcmd2+= "-i volumes.sel -o max_like_alignment/nref%d_10deg " % nref
	xmippcmd2+= "-nref %d -doc max_like_alignment/nref%d_15deg_it000005.doc -keep_angles " % (nref, nref) 
	xmippcmd2+= "-iter 5 -ang 10 -ang_search 50 -maxres 0.35 -perturb"
	if threadnproc > 1:
		xmippcmd2 += " -thr "+str(threadnproc)			
	apParam.runCmd(xmippcmd2, package="Xmipp")

	if nproc > 1:
		xmippcmd3 = "mpirun -np %d xmipp_mpi_ml_tomo " % nproc
	else:
		xmippcmd3 = "xmipp_ml_tomo "
	xmippcmd3+= "-i volumes.sel -o max_like_alignment/nref%d_5deg " % nref
	xmippcmd3+= "-nref %d -doc max_like_alignment/nref%d_10deg_it000005.doc -keep_angles " % (nref, nref)
	xmippcmd3+= "-iter 5 -ang 5 -ang_search 25 -maxres 0.35 -perturb"
	if threadnproc > 1:
		xmippcmd3 += " -thr "+str(threadnproc)
	apParam.runCmd(xmippcmd3, package="Xmipp")
	'''
	vol_doc_file, alignref = findAlignmentParams(rundir, nref)		
	return vol_doc_file, alignref
		
#=====================

def findAlignmentParams(rundir, nref):
	
#
#		ANGULAR INCREMENT SET TO 15
#
	### check for all iterations, just in case Xmipp ended early, sometimes it converges before 5th iteration
	i = 5
	while i > 0:
		vol_doc_file = os.path.join(rundir, "nref%d_15deg_it00000%d.doc") % (nref, i)
		alignref = os.path.join(rundir, "nref%d_15deg_it00000%d_ref000001.vol") % (nref, i)
		if os.path.isfile(vol_doc_file):
			return vol_doc_file, alignref
		else:
			i -= 1
	if i == 0:
		apDisplay.printError("ERROR IN 3-D MAXIMUM LIKELIHOOD RUN")	

#=====================

def read_vol_doc_file(vol_doc_file, num_volumes):
	''' read and return all alignment parameters from 3-D maximum likelihood '''
	
	f = open(vol_doc_file, "r")
	f.readline() # first line is header info
	lines = f.readlines()
	alignparams = []
	for i in range(num_volumes):
		volume = lines[2*i].strip().split()[1]
		rot = lines[2*i+1].strip().split()[2]
		tilt = lines[2*i+1].strip().split()[3]
		psi = lines[2*i+1].strip().split()[4]
		Xoff = lines[2*i+1].strip().split()[5]
		Yoff = lines[2*i+1].strip().split()[6]
		Zoff = lines[2*i+1].strip().split()[7]
		ref = lines[2*i+1].strip().split()[8]
		params = [volume, Xoff, Yoff, Zoff, rot, tilt, psi, ref]
		alignparams.append(params)
	f.close()

	return alignparams
	
#=====================

def align_volumes(alignparams, alignref, num_volumes, threadnproc, apix=1.0):
	''' align the volumes to the resulting reference from maximum-likelihood '''
	
	transcmds = []
	rotcmds = []
	emancmds = []
	for i in range(num_volumes):
		ref = int(float(alignparams[i][7]))
		xmippcmd_trans = "xmipp_align_volumes -i1 %s -i2 %s" % (alignref, alignparams[i][0]) +\
			" -x "+str(alignparams[i][1])+" "+str(alignparams[i][1])+" 1"\
			" -y "+str(alignparams[i][2])+" "+str(alignparams[i][2])+" 1"\
			" -z "+str(alignparams[i][3])+" "+str(alignparams[i][3])+" 1 -apply"
		transcmds.append(xmippcmd_trans)
		xmippcmd_rot = "xmipp_align_volumes -i1 %s -i2 %s " % (alignref, alignparams[i][0]) +\
			" -rot "+str(alignparams[i][4])+" "+str(alignparams[i][4])+" 1"\
			" -tilt "+str(alignparams[i][5])+" "+str(alignparams[i][5])+" 1"\
			" -psi "+str(alignparams[i][6])+" "+str(alignparams[i][6])+" 1 -apply"
		rotcmds.append(xmippcmd_rot)
		emancmd = "proc3d "+str(alignparams[i][0])+" "+str(alignparams[i][0])[:-4]+".mrc apix="+str(apix)
		emancmds.append(emancmd)
	apDisplay.printColor("aligning volumes translationally", "cyan")
	apThread.threadCommands(transcmds, nproc=threadnproc, pausetime=10)
	apDisplay.printColor("aligning volumes rotationally", "cyan")
	apThread.threadCommands(rotcmds, nproc=threadnproc, pausetime=10)
#	apDisplay.printColor("converting to MRC format", "cyan")	
#	apThread.threadCommands(emancmds, nproc=threadnproc, pausetime=10)
		
	return	
	
	
	
	

#======================                                        ====================
#======================                                        ====================
#======================                  3D PCA                ====================
#======================                                        ====================
#======================                                        ====================
	
	
	
	

def runPrincipalComponentAnalysis(volumedict, num_volumes, numeigens, box, 
	apix, recalculate=False):
	''' 
	runs principal component analysis to reduce dimensionality of dataset and 
	returns the correlation file corresponding to the similarity of each point
	in factor space
	'''
	
	### default number of eigenvolumes
	rundir = os.getcwd()
	if num_volumes < 69:
		numeigens = num_volumes
	else:
		numeigens = numeigens
	apDisplay.printMsg("using %d Eigenvectors (Eigenvolumes) to reduce dimensionality of dataset and calculate volume similarities" % (numeigens))
		
	### create input array from all volumes 	
	volumes = numpy.empty([num_volumes, box, box, box])
	for v in sorted(volumedict):
#		vol = mrc.read(volumedict[v])
		vol = spider.read(volumedict[v])
		volumes[(v-1)] += vol
	num_volumes = volumes.shape[0]
	numpixels = volumes.shape[1]*volumes.shape[2]*volumes.shape[3]
	inputs = volumes.reshape(num_volumes, numpixels)
	meaninput = inputs.mean(axis=0)
	inputs = inputs - meaninput

	### run PCA
	apDisplay.printMsg("using covariance method to calculate eigenvectors")
	covar = numpy.dot(inputs, inputs.transpose())
	evals, evecs = numpy.linalg.eigh(covar)
	evals = evals[:-(numeigens+1):-1]	# order according to most representative eigenvector
	evecs = evecs[:-(numeigens+1):-1]	# order according to most representative eigenvector
	transposed_evecs = evecs.transpose()
	transformed_points = numpy.dot(evecs, inputs)

	### coordinates of each image in factor space
	new_coordinates = numpy.dot(transformed_points, inputs.transpose())

	### calculate correlations between volumes using Euclidean distance in factor space
	apDisplay.printMsg("calculating correlations after dimension reduction")
	diff_matrix = numpy.zeros((num_volumes, num_volumes))
	for i in range(num_volumes):
		for j in range(i+1, num_volumes):
			model1 = new_coordinates[:,i]
			model2 = new_coordinates[:,j]
			dist = euclideanDist(model1, model2)
			diff_matrix[i,j] = dist
			diff_matrix[j,i] = dist
#		sim_matrix = numpy.where(diff_matrix != 0, 1/diff_matrix, 1) ### this doesn't work very well
	max = diff_matrix.max()
	min = numpy.where(diff_matrix > 0, diff_matrix, max).min()
	norm_diff_matrix = numpy.where(diff_matrix > 0, (diff_matrix - (min))/(max-min), 0)
	sim_matrix = numpy.where(norm_diff_matrix >= 0, 1-norm_diff_matrix, 0)
				
	### write similarities (CCCs) to file 
	apDisplay.printMsg("writing similarities to file CCCs_3d.dat")
	simfile = os.path.join(rundir, "CCCs_3d.dat")
	f = open(simfile, "w")
	for i in range(num_volumes):
		for j in range((i+1), num_volumes):
			str1 = "%05d %05d %.10f\n" % (i+1, j+1, sim_matrix[i,j])
			f.write(str1)
			str2 = "%05d %05d %.10f\n" % (j+1, i+1, sim_matrix[j,i])
			f.write(str2)
	f.close()
		
	### write out the first 3 eigenvectors (eigenvolumes)
	header = {'xorigin' : 0, 'yorigin' : 0, 'zorigin' : 0, 'xlen' : box*apix, 
		'ylen' : box*apix, 'zlen' : box*apix}
	for i in range(3):
		eigim = transformed_points[i]
		eigim = eigim.reshape(volumes.shape[1], volumes.shape[2], volumes.shape[3])
		mrc.write(eigim, "eigenvolume%d.mrc" % (i+1), header)

	### recalculate images
	if recalculate is True:
		if not os.path.isdir(os.path.join(rundir, "new_mrcs")):
			os.mkdir(os.path.join(rundir, "new_mrcs"))
		myarray = []
		newimages = numpy.dot(transposed_evecs, transformed_points)
		for j in range(num_volumes):
			newim = (newimages[j]+meaninput).reshape(volumes.shape[1], volumes.shape[2], volumes.shape[3])
			mrc.write(newim, os.path.join(rundir, "new_mrcs", str(j+1)+".mrc"), header)
			
	return simfile, sim_matrix

#=====================

def set_preferences(sim_matrix, preftype, num_volumes):
	''' set preference value for affinity propagation and dump to file '''
	
	### Preference value stats
	apDisplay.printMsg("similarity stats:\n %.5f +/- %.5f\n %.5f <> %.5f"
			% (numpy.where(sim_matrix<1, sim_matrix, 0).mean(), numpy.where(sim_matrix<1,
				sim_matrix, 0).std(), sim_matrix.min(), numpy.where(sim_matrix<1, sim_matrix, 0).max()))

	### Determine preference value baed on specified type
	if preftype == 'minlessrange':
		apDisplay.printMsg("Determine minimum minus total range (fewest classes) preference value")
		prefvalue = sim_matrix.min() - (numpy.where(sim_matrix<1, sim_matrix, 0).max() - sim_matrix.min())
	elif preftype == 'minimum':
		apDisplay.printMsg("Determine minimum (few classes) preference value")
		prefvalue = sim_matrix.min()
	elif preftype == 'median':
		apDisplay.printMsg("Determine median (normal classes) preference value")
		onedarray = sim_matrix.copy().reshape(-1)
		onedarray.sort()
		index = int(len(onedarray)*0.5)
		medianpref = onedarray[index]
		prefvalue = medianpref
	else:
		apDisplay.printMsg("Determine maximum (most classes) preference value")
		prefvalue = numpy.where(sim_matrix<1, sim_matrix, 0).max()

	apDisplay.printColor("Final preference value %.6f" % (prefvalue), "cyan")

	### dump value to file
	preffile = os.path.join(os.getcwd(), 'affinity_propagation_preferences.dat')
	apDisplay.printMsg("Dumping preference value to file")
	f = open(preffile, 'w')
	for i in range(0,num_volumes):
		f.write('%.10f\n' % (prefvalue))
	f.close()
	
	return preffile

#=====================
	
def run_affinity_propagation(volumedict, simfile, preffile, box, apix):
	''' Use Affinity Propagation to classify and average all aligned 3-D models '''
	
	apDisplay.printMsg("running Affinity Propagation on aligned 3-D models")

	### run Affinity Propagation
	apclusterexe = "apcluster.exe"
	outfile = os.path.join(os.getcwd(), "cluster_affiliation.dat")
	apFile.removeFile(outfile)
	clustercmd = apclusterexe+" "+simfile+" "+preffile+" "+outfile
	clusttime = time.time()
	proc = subprocess.Popen(clustercmd, shell=True)
	proc.wait()
	apDisplay.printMsg("apCluster time: "+apDisplay.timeString(time.time()-clusttime))
	if not os.path.isfile(outfile):
		apDisplay.printError("apCluster did not run")

	### Parse apcluster output file: clusters.out
	apDisplay.printMsg("Parse apcluster output file: "+outfile)
	clustf = open(outfile, "r")
	### each line is the particle and the number is the class
	partnum = 0
	classes = {}
	for line in clustf:
		sline = line.strip()
		if sline:
			partnum += 1
			classnum = int(sline)
			if not classnum in classes:
				classes[classnum] = [partnum,]
			else:
				classes[classnum].append(partnum)
	clustf.close()
	apDisplay.printMsg("Found %d classes"%(len(classes.keys())))

	### Create model averages
	header = {'xorigin' : 0, 'yorigin' : 0, 'zorigin' : 0, 'xlen' : box*apix, 
		'ylen' : box*apix, 'zlen' : box*apix}
	classnames = classes.keys()
	for classnum in classnames:
		avgclass = numpy.zeros(((box,box,box)))
		num_members = 0
		for member in classes[classnum]:
			num_members += 1
#			avgclass += mrc.read(volumedict[member])
			avgclass += spider.read(volumedict[member])
		avgclass = avgclass / num_members
		mrc.write(avgclass, os.path.join(os.getcwd(), (str(classnum)+".mrc")), header)
				
	return classes	

	
	
	
#======================                                        ====================
#======================                                        ====================
#======================             3D REFINEMENT              ====================
#======================                                        ====================
#======================                                        ====================



	
	
	
def refine_volume(basedir, clsavgs, volnum, mask_radius, inner_radius, outer_radius, apix, 
	nproc, memory='2gb'):
	''' Xmipp projection-matching based refinement of volume generated by common lines '''
	
	refinedir = os.path.abspath(os.path.join(basedir, "refinement"))
	rundir = os.path.join(refinedir, "refine_%d" % volnum)
	if not os.path.isdir(rundir):
		os.mkdir(rundir)

	### set projection-matching parameters
	SelFileName = "partlist.sel"
	ReferenceFileName = os.path.join(refinedir, "%d.vol" % volnum)
	WorkingDir = os.path.basename(rundir)
	ProjectDir = os.getcwd()
	MaskRadius = mask_radius / apix   # in pixels
	InnerRadius = inner_radius / apix # in pixels
	OuterRadius = outer_radius / apix # in pixels
	AvailableMemory = memory
	ResolSam = apix
	NumberOfMpiProcesses = nproc

	### optional parameters
	NumberofIterations = 12
	AngSamplingRateDeg = '4x10 4x5 4x3'
	MaxChangeInAngles = '4x1000 4x20 4x9'
	MaxChangeOffset = '4x1000 4x100 4x10'
	Search5DShift = '4x5 4x3 1'
	Search5DStep = '8x2 1'
	FourierMaxFrequencyOfInterest = '0.35'
	ConstantToAddToFiltration = '0.35'

	### do projection-matching
	apDisplay.printColor("refining volume %d by projection-matching" % volnum, "cyan")

	if NumberOfMpiProcesses < 2:
		DoParallel = False	
	else:
		DoParallel = True
		
	xp.projection_matching_protocol_basic(
				SelFileName,
				ReferenceFileName,
				WorkingDir,
				ProjectDir,
				MaskRadius,
				InnerRadius,
				OuterRadius,
				AvailableMemory,
				ResolSam,
				NumberOfMpiProcesses,
				_NumberofIterations=NumberofIterations,
				_AngSamplingRateDeg=AngSamplingRateDeg,
				_MaxChangeInAngles=MaxChangeInAngles,
				_MaxChangeOffset=MaxChangeOffset,
				_Search5DShift=Search5DShift,
				_Search5DStep=Search5DStep,
				_FourierMaxFrequencyOfInterest=FourierMaxFrequencyOfInterest,
				_ConstantToAddToFiltration=ConstantToAddToFiltration,
				_DoParallel=DoParallel
				)
	
#		### do projection-matching
#		apDisplay.printColor("refining volume %d by projection-matching" % volnum, "cyan")
#		xp.projection_matching_protocol_basic(
#					SelFileName,
#					ReferenceFileName,
#					WorkingDir,
#					ProjectDir,
#					MaskRadius,
#					InnerRadius,
#					OuterRadius,
#					AvailableMemory,
#					ResolSam,
#					NumberOfMpiProcesses
#					)
	
	### remove unecessary files
	os.chdir(rundir)
	count = 0
	for root, dirs, files in os.walk(rundir):
		for file in files:
			m = re.search("reference_volume", file)
			if m is not None:
				count += 1
				apFile.removeFile(os.path.join(root, file), warn=False)
				
	### create files for model assessment
	if count == 0:
		count = NumberofIterations
	box = apFile.getBoxSize(clsavgs)[0]
	refinement_quality_criteria(count, box, apix, nproc)

	### link / summarize final files
	if os.path.islink(os.path.join(rundir, "3d%d_refined.vol" % volnum)):
		os.system("rm -rf %s " % os.path.join(rundir, "3d%d_refined.vol" % volnum))
	os.symlink(os.path.join("Iter_%d" % count, "Iter_%d_reconstruction.vol" % count),
		os.path.join(rundir, "3d%d_refined.vol" % volnum))
	if os.path.islink(os.path.join(rundir, "3d%d_refined.frc" % volnum)):
		os.system("rm -rf %s " % os.path.join(rundir, "3d%d_refined.frc" % volnum))
	os.symlink(os.path.join("Iter_%d" % count, "reconstruction_2.vol.frc"),
		os.path.join(rundir, "3d%d_refined.frc" % volnum))
	if os.path.islink(os.path.join(rundir, "3d%d_refined_projections.hed" % volnum)):
		os.system("rm -rf %s " % os.path.join(rundir, "3d%d_refined_projections.hed" % volnum))
	os.symlink(os.path.join("Iter_%d" % count, "Iter_%d_projections_noflip.hed" % count),
		os.path.join(rundir, "3d%d_refined_projections.hed" % volnum))
	if os.path.islink(os.path.join(rundir, "3d%d_refined_projections.img" % volnum)):
		os.system("rm -rf %s " % os.path.join(rundir, "3d%d_refined_projections.img" % volnum))
	os.symlink(os.path.join("Iter_%d" % count, "Iter_%d_projections_noflip.img" % count),
		os.path.join(rundir, "3d%d_refined_projections.img" % volnum))
	apXmipp.removeMirrorFromDocfile(os.path.join(rundir, "Iter_%d" % count, "Iter_%d_current_angles.doc" % count),
		os.path.join(rundir, "3d%d_refined_angles.doc" % volnum))
	avgs = apImagicFile.readImagic(clsavgs)['images']
	repjs = apImagicFile.readImagic(os.path.join(rundir, "3d%d_refined_projections.hed" % volnum))['images']
	comparison = []
	for i in range(len(avgs)):
		comparison.append(avgs[i])
		comparison.append(repjs[i])
	apImagicFile.writeImagic(comparison, os.path.join(rundir, "clsavg_reprojection_comparison.hed"))
	
	os.chdir(refinedir)
	
	return	
	
#=====================
	
def refinement_quality_criteria(iteration, box, apix, nproc):
	''' this function constructs the necessary files for CCPR and FSC calculations of each refined volume'''
	
	basedir = os.getcwd()
	workingdir = os.path.join(basedir, "Iter_%d" % iteration)
	os.chdir(workingdir)

	### Xmipp files for CCPR calculation - projection doc / sel file
	docdict = apXmipp.readDocfile("Iter_%d_current_angles.doc" % iteration)
	tempdoc = open("temp.doc", "w")
	projectdoc = open("Iter_%d_projections_noflip.doc" % iteration, "w")
	tempsel = open("temp.sel", "w")
	projectsel = open("Iter_%d_projections_noflip.sel" % iteration, "w")
	reconfile = open("reconstruction.sel", "w")
	tempdoc.write(" ; Headerinfo columns: rot (1), tilt (2), psi (3), Xoff (4), Yoff (5)\n")
	projectdoc.write(" ; Headerinfo columns: rot (1), tilt (2), psi (3), Xoff (4), Yoff (5)\n")
	for k in sorted(docdict.iterkeys()):
		vals = docdict[k]['values']
		rot = float(vals[2])
		tilt = float(vals[3])
		psi = float(vals[4])
		flip = bool(float(vals[8]))
		if flip == 1:
			rot, tilt, psi = apXmipp.calculate_equivalent_Eulers_without_flip(rot, tilt, psi)
		tempdoc.write(" ; %s\n" % os.path.join(workingdir, "proj%.6d.xmp" % (k+1)))
		tempdoc.write("%5d 5 %11.5f%11.5f%11.5f%11.5f%11.5f\n" \
			% ((k+1), rot, tilt, psi, float(vals[5]), float(vals[6])))
		projectdoc.write(" ; %s\n" % os.path.join(workingdir, "proj%.6d.appl" % (k+1)))
		projectdoc.write("%5d 5 %11.5f%11.5f%11.5f%11.5f%11.5f\n" \
			% ((k+1), rot, tilt, psi, 0, 0))
		tempsel.write("%s 1\n" % os.path.join(workingdir, "proj%.6d.xmp" % (k+1)))
		projectsel.write("%s 1\n" % os.path.join(workingdir, "proj%.6d.appl" % (k+1)))
		reconfile.write("%s 1\n" % docdict[k]['filename'])
	tempdoc.close()
	projectdoc.close()
	tempsel.close()
	projectsel.close()

	### projection file
	f = open("project.params", "w")
	f.write("Iter_%d_reconstruction.vol\n" % iteration)
	f.write("proj 1 xmp\n")
	f.write("%d %d\n" % (box, box))
	f.write("%s rot tilt psi\n" % "temp.doc")
	f.write("NULL\n")
	f.write("0 0\n")
	f.write("0 0\n")
	f.write("0 0\n")
	f.write("0 0\n")
	f.write("0 0\n")
	f.close()
	apParam.runCmd("xmipp_project -i project.params", "Xmipp")

	### apply transformation parameters calculated by Xmipp
	resetcmd = "xmipp_header_reset -i temp.sel"
	apParam.runCmd(resetcmd, "Xmipp")
	assigncmd = "xmipp_header_assign -i temp.doc -verb -columns 0 0 0 -4 -5"
	apParam.runCmd(assigncmd, "Xmipp")
	applycmd = "xmipp_header_apply -i temp.sel -oext appl"
	apParam.runCmd(applycmd, "Xmipp")
	apXmipp.gatherSingleFilesIntoStack("Iter_%d_projections_noflip.sel" \
		% iteration, "Iter_%d_projections_noflip.hed" % iteration)

	### remove unnecessary files
	os.remove("temp.doc")
	os.remove("temp.sel")
	os.remove("tempappl.sel")
	projfiles = glob.glob("*.xmp")
	for file in projfiles:
		os.remove(file)
	appfiles = glob.glob("*.appl")
	for file in appfiles:
		os.remove(file)

	time.sleep(5)
	### Xmipp files for FSC calculations
	splitcmd = "xmipp_selfile_split -i reconstruction.sel"
	apParam.runCmd(splitcmd, "Xmipp")
	doccmd1 = "xmipp_docfile_select_subset -i Iter_%d_current_angles.doc -sel reconstruction_1.sel -o Iter_%d_current_angles_1.doc" \
		% (iteration, iteration)
	apParam.runCmd(doccmd1, "Xmipp")
	doccmd2 = "xmipp_docfile_select_subset -i Iter_%d_current_angles.doc -sel reconstruction_2.sel -o Iter_%d_current_angles_2.doc" \
		% (iteration, iteration)
	apParam.runCmd(doccmd2, "Xmipp")
	reconcmd1 = "mpirun -np %d xmipp_mpi_reconstruct_fourier -i reconstruction_1.sel -o reconstruction_1.vol -sym c1 -doc Iter_%d_current_angles_1.doc -thr %d" \
		% (nproc, iteration, nproc)
	apParam.runCmd(reconcmd1, "Xmipp")
	reconcmd2 = "mpirun -np %d xmipp_mpi_reconstruct_fourier -i reconstruction_2.sel -o reconstruction_2.vol -sym c1 -doc Iter_%d_current_angles_2.doc -thr %d" \
		% (nproc, iteration, nproc)			
	apParam.runCmd(reconcmd2, "Xmipp")
	fsccmd = "xmipp_resolution_fsc -ref reconstruction_1.vol -i reconstruction_2.vol -sam %.3f" % apix
	apParam.runCmd(fsccmd, "Xmipp")
	
	os.chdir(basedir)
	return




#=====================                                    =====================
#=====================                                    =====================
#=====================       EULER ANGLE FUNCTIONS        =====================
#=====================	                                   =====================
#=====================                                    =====================




			
def distanceBetweenEulers(t1, t2):
	R = numpy.dot(numpy.transpose(t1), t2)
	trace = R.trace()
	s = math.acos((R[0][0] + R[1][1] + R[2][2] - 1) / 2.0)
	if s == 0:
		d = 0
	else:
		d = math.fabs(s/(2*math.sin(s))) * math.sqrt((R[0][1]-R[1][0])**2 + 
		(R[0][2]-R[2][0])**2 + (R[1][2]-R[2][1])**2)
	d = d*180/math.pi
		
	return d
	
#=====================

def getEulerValuesForModels(alignparams, basedir, num_volumes, numpart, threes=False):
	'''
	reads the Euler angle assignment for each class average in IMAGIC, transforms
	them based on the rotation matrix, then returns an "euler_array", which 
	contains the Euler angles for each model, for each class average, mapped to its
	original randomized assignment index
	'''
	
	### read in randomization assignments for each class average
	seq_file = open(os.path.join(basedir, "image_sequences.dat"), "r")
	seq_array = []
	for i in range(num_volumes):
		sequence = seq_file.readline().strip().strip("[").strip("]")
		sequence = sequence.split(",")		
		seq_array.append(sequence)
	seq_file.close()
	
	### read in Euler angles as a tuple of (alpha, beta, gamma) for each model 
	### and store them in an euler list for each volume
	euler_array = []
	for i in range(num_volumes):
		eulerFile = open(os.path.join(basedir, "angular_reconstitution", 
			"ordered"+str(i+1)+"_Eulers.plt"))
		eulerlist = []
		if threes is True:
			for j in range(3):
				vals = eulerFile.readline().strip().split()
				eulers = (float(vals[0]), float(vals[1]), float(vals[2]))
				eulerlist.append(eulers)	
		else:
			for j in range(numpart):
				vals = eulerFile.readline().strip().split()
				eulers = (float(vals[0]), float(vals[1]), float(vals[2]))
				eulerlist.append(eulers)
		eulerFile.close()
		euler_array.append(eulerlist)

	### map Euler angles to the corresponding class average in the original 
	### template stack, according to the randomization sequence
	euler_array_mapped = []
	for i in range(num_volumes):
		eulerdict_mapped = {}
		if threes is True:
			for j in range(3):
				value = int(seq_array[i][j])
				eulers = euler_array[i][j] ### IMAGIC format starts with 1
				eulerdict_mapped[str(value)] = eulers	
		else:
			for j in range(numpart):
				value = int(seq_array[i][j])
				eulers = euler_array[i][j] ### IMAGIC format starts with 1
				eulerdict_mapped[str(value)] = eulers
		euler_array_mapped.append(eulerdict_mapped)

	### apply Euler angle transformation based on alignment parameters
	euler_array_transformed = {}
	for i in range(num_volumes):
		eulerdict_transformed = {}
		### read in rotation parameters from Xmipp doc file
		rot = float(alignparams[i][4])
		tilt = float(alignparams[i][5])
		psi = float(alignparams[i][6])
		transform_matrix = numpy.matrix(apEulerCalc.EulersToRotationMatrix3DEM(rot, tilt, psi))
		
		for key, value in euler_array_mapped[i].items():
			### old Euler angles and rotation matrix
			alpha = float(value[0]) 
			beta = float(value[1])
			gamma = float(value[2])
			R1 = numpy.matrix(apEulerCalc.EulersToRotationMatrix3DEM(gamma-90, beta, alpha+90))
			### get new Euler angles from the multiplied transformation matrices
			R2 = R1 * transform_matrix.I
			rot_new, tilt_new, psi_new = apEulerCalc.rotationMatrixToEulers3DEM(R2)
			### save in new dictionary
			eulerdict_transformed[key] = (rot_new, tilt_new, psi_new)
		euler_array_transformed[str(i+1)] = (eulerdict_transformed)
			
	return euler_array_transformed

#=====================	
	
def calculateMeanEulerJumpForModelClass(classes, euler_array_transformed, 
	presumed_sym, numpart):
	'''
	takes as input a dictionary of Euler values for each model along with a dictionary key for the model class containing
	separate 3D reconstructions. It then calculates, for each class average, the mean Euler angle difference (Euler jump),
	between all combinations of models within that class.  
	'''
	
	l = []
	symmetry=presumed_sym

	for i in range(numpart): ### for each class average
		for j in range(len(classes)):
			if len(classes) == 1:
				l.append(0)
			else:
				for k in range(j+1, len(classes)):
#					print type(euler_array_transformed[str(classes[j])])
#					print euler_array_transformed[str(classes[j])], "euler array j"
					jassess = euler_array_transformed[str(classes[j])].has_key(str(i+1))
					kassess = euler_array_transformed[str(classes[k])].has_key(str(i+1))
					if jassess is True and kassess is True:
						rot1 = euler_array_transformed[str(classes[j])][str(i+1)][0]
						tilt1 = euler_array_transformed[str(classes[j])][str(i+1)][1]
						psi1 = euler_array_transformed[str(classes[j])][str(i+1)][2]
						rot2 = euler_array_transformed[str(classes[k])][str(i+1)][0]
						tilt2 = euler_array_transformed[str(classes[k])][str(i+1)][1]
						psi2 = euler_array_transformed[str(classes[k])][str(i+1)][2]
						
						### convert to EMAN format
						alt1, az1, phi1 = apEulerCalc.convertXmippEulersToEman(rot1, tilt1, psi1)
						alt2, az2, phi2 = apEulerCalc.convertXmippEulersToEman(rot2, tilt2, psi2)
						e1 = {'euler1':alt1, 'euler2':az1, 'euler3':phi1}
						e2 = {'euler1':alt2, 'euler2':az2, 'euler3':phi2} 
	
						### apply symmetry to Euler angle calculation
						if symmetry == "c1":
							d = apEulerCalc.eulerCalculateDistance(e1, e2, inplane=True)
						else:
							d = apEulerCalc.eulerCalculateDistanceSym(e1, e2, sym=symmetry, inplane=True)
						l.append(d)
	meanjump = numpy.asarray(l).mean()
	
	return meanjump
						




#=====================                                    =====================
#=====================                                    =====================
#=====================        3D CLASS ASSESSMENT         =====================
#=====================	                                  =====================
#=====================                                    =====================




	
			
def avgCCCBetweenProjectionsAndReprojections(classes, ordered_file, reproj_file):
	'''
	takes in a dictionary key for the model class, which contains all the separate 3D reconstructions going into class, 
	then calculates the average cross-correlation between the projections and reprojections for each separate 3D. This 
	function looks at the initial 3D model calculated by common lines. 
	'''
	
	CCCs = []
	for m in classes:
		of = apImagicFile.readImagic(filename=ordered_file, msg=False)
		orderedarray = of['images']
		rf = apImagicFile.readImagic(filename=reproj_file, msg=False)
		reparray = rf['images']
		if orderedarray.shape != reparray.shape:
			apDisplay.printError("projection image file %s does not match reprojection file %s") \
				% (ordered_file, reproj_file)
		ccc = 0
		for i in range(orderedarray.shape[0]):
			ccc += calculate_ccs(orderedarray[i], reparray[i])
		avgCCC = ccc / orderedarray.shape[0]
		CCCs.append(avgCCC)
	classCCC = sum(CCCs) / len(CCCs)

	return classCCC

#=====================

def assess_3Dclass_quality(basedir, voldict, sim_matrix, classes, euler_array_transformed, 
	box, apix, avgs, presumed_sym, numpart, ejassess=True):
	''' assesses each model based on multiple criteria '''

	apDisplay.printColor("Parsing through resulting 3D classes to assess the quality of each 3D model", "yellow")
	
	### make ssnr directory
	if not os.path.isdir(os.path.join(basedir, "ssnr_data")):
		os.mkdir(os.path.join(basedir, "ssnr_data"))

	### calculate final model statistics using similarity array
	classnames = classes.keys()
	bestavg = 0
	mf = open(os.path.join(basedir, "final_model_members.dat"), "w")
	vf = open(os.path.join(basedir, "final_model_stats.dat"), "w")
	vf.write("%9s %5s %8s %8s %8s %8s %8s\n" \
		% ("MODEL", "NUM", "CCPR", "EJ", "CCC", "STDEV", "SSNR"))		
	for classnum in classnames:
		sims = []
		volarray = numpy.zeros((((len(classes[classnum]),box,box,box))))
		for i in range(len(classes[classnum])):
			for j in range(i+1, len(classes[classnum])):
				sim = sim_matrix[(classes[classnum][i]-1), (classes[classnum][j]-1)]
				sims.append(sim)
			if len(classes[classnum]) == 1:
				sims.append(1) ### when a single model is in a class, its self-similarity is 1
			volarray[i] += spider.read(voldict[classes[classnum][i]])
			
		### get SSNR of volume class
		if len(classes[classnum]) == 1:
			res = apix * 2
		else:
			try:
				res = apFourier.spectralSNR3d(volarray, apix)	
			except:
				apDisplay.printWarning("resolution not calculated")
				res = 2 * apix
			os.rename(os.path.join(basedir, "ssnr.dat"), os.path.join(basedir, "ssnr_data", "ssnr_model_%d.dat" % (classnum)))
		
		### assess quality of class by comparing the summed CCC between projections and reprojections
		ordered_file = avgs
		reproj_file = os.path.join(
			basedir, "angular_reconstitution", "refine_%d" % m, "3d%d_refined_projections.hed" % m
			)
		CCC = avgCCCBetweenProjectionsAndReprojections(classes[classnum], ordered_file, reproj_file)
			
		### assess Euler jumpers for class (mean value for ALL class averages)
		mj = calculateMeanEulerJumpForModelClass(classes[classnum], 
			euler_array_transformed, presumed_sym, numpart)
		
		### print and write to file
		normsims = normList(sims)
		classccc = numpy.asarray(normsims).mean()
		classstd = numpy.asarray(normsims).std()
		print "volumes in model %d_r.mrc: %s \n" % (classnum, classes[classnum])
		mf.write("%d_r.mrc: %s \n" % (classnum, classes[classnum]))
		p = "model %d_r.mrc, " % classnum
		p+= "%d members with " % len(classes[classnum])
		p+= "average proj/reproj CCC %f, " % CCC
		if ejassess is True:
			p+= "mean Euler jump %f, " % mj
		p+= "and resolution %f" % res
		print p
		if ejassess is True:
			vf.write("%5d_r.mrc %5d %8.3f %8.3f %8.3f %8.3f %8.3f\n" \
				% (classnum, len(classes[classnum]), CCC, mj, classccc, classstd, res))
		else:
			vf.write("%5d_r.mrc %5d %8.3f %8.3f %8.3f %8.3f\n" \
				% (classnum, len(classes[classnum]), CCC, classccc, classstd, res))
	mf.close()
	vf.close()
		
	return

#=====================

def assess_3Dclass_quality2(basedir, voldict, sim_matrix, classes, euler_array_transformed, 
	box, refinebox, refineapix, refineavgs, presumed_sym, numpart, ejassess=True):
	''' assesses each model based on multiple criteria, refinement only '''

	apDisplay.printColor("Parsing through resulting 3D classes to assess the quality of each 3D model", "yellow")

	### calculate final model statistics using similarity array
	classnames = classes.keys()
	bestavg = 0
	mf = open(os.path.join(basedir, "final_model_members.dat"), "w")
	vf = open(os.path.join(basedir, "final_model_stats.dat"), "w")
	vf.write("%11s %5s %8s %8s %8s %8s %8s\n" \
		% ("MODEL", "NUM", "CCPR", "EJ", "CCC", "STDEV", "FSC"))		
	for classnum in classnames:
		sims = []
		volarray = numpy.zeros((((len(classes[classnum]),box,box,box))))
		for i in range(len(classes[classnum])):
			for j in range(i+1, len(classes[classnum])):
				sim = sim_matrix[(classes[classnum][i]-1), (classes[classnum][j]-1)]
				sims.append(sim)
			if len(classes[classnum]) == 1:
				sims.append(1) ### when a single model is in a class, its self-similarity is 1
			volarray[i] += spider.read(voldict[classes[classnum][i]])
			
		### get FSC of volume class
		try:
			res = getResolutionFromGenericFSCFile(					
				os.path.join(basedir, "refinement", "refine_%d" % classnum, "3d%d_refined.frc" % classnum),
				refinebox, refineapix)
		except:
			apDisplay.printWarning("resolution not calculated")
			res = 2 * refineapix
		
		### assess quality of class by comparing the summed CCC between projections and reprojections
		ordered_file = refineavgs
		reproj_file = os.path.join(
			basedir, "refinement", "refine_%d" % classnum, "3d%d_refined_projections.hed" % classnum
			)
		CCC = avgCCCBetweenProjectionsAndReprojections(classes[classnum], ordered_file, reproj_file)
			
		### assess Euler jumpers for class (mean value for ALL class averages)
		if ejassess is True:
			mj = calculateMeanEulerJumpForModelClass(classes[classnum], 
				euler_array_transformed, presumed_sym, numpart)
		
		### print and write to file
		normsims = normList(sims)
		classccc = numpy.asarray(normsims).mean()
		classstd = numpy.asarray(normsims).std()
		print "volumes in model %d_r.mrc: %s \n" % (classnum, classes[classnum])
		mf.write("%d_r.mrc: %s \n" % (classnum, classes[classnum]))
		p = "model %d_r.mrc, " % classnum
		p+= "%d members with " % len(classes[classnum])
		p+= "average proj/reproj CCC %f, " % CCC
		if ejassess is True:
			p+= "mean Euler jump %f, " % mj
		p+= "and resolution %f" % res
		print p
		if ejassess is True:
			vf.write("%5d_r.mrc %5d %8.3f %8.3f %8.3f %8.3f %8.3f\n" \
				% (classnum, len(classes[classnum]), CCC, mj, classccc, classstd, res))
		else:
			vf.write("%5d_r.mrc %5d %8.3f %8.3f %8.3f %8.3f\n" \
				% (classnum, len(classes[classnum]), CCC, classccc, classstd, res))		
		
	mf.close()
	vf.close()
		
	return

#=====================

def getResolutionFromGenericFSCFile(fscfile, boxsize, apix, filtradius=3, msg=False):
	"""
	parses standard 2-column FSC file with 1) spatial frequency and 2) FRC, returns resolution
	"""
	if not os.path.isfile(fscfile):
		apDisplay.printWarning("fsc file does not exist")
	if msg is True:
		apDisplay.printMsg("box: %d, apix: %.3f, file: %s"%(boxsize, apix, fscfile))

	f = open(fscfile, 'r')
	fscfileinfo = f.readlines()
	f.close()
	fscdata = numpy.zeros((int(boxsize)/2), dtype=numpy.float32)
	for i, info in enumerate(fscfileinfo):		# skip commented out lines
		if info[0] == "#":
			pass
		else: 
			fscfileinfo = fscfileinfo[i:]
			break
	for j, info in enumerate(fscfileinfo):      
		frc = float(info.split()[1])
		fscdata[j] = frc
	res = apFourier.getResolution(fscdata, apix, boxsize, filtradius=filtradius)

	return res





#=====================                                    =====================
#=====================                                    =====================
#=====================         SCORE COMBINATION          =====================
#=====================	                                   =====================
#=====================                                    =====================



	
	

def combineMetrics(statfilename, outfile, **kwargs):
	''' 
	takes all calculated metrics and combines them into a single Rcrit value, 
	according to: Rossmann, M. G., et al. (2001). "Combining electron microscopic 
	with x-ray crystallographic structures." J Struct Biol 136(3): 190-200.
	metrics are combined as follows: 
	
	Rcrit = sum(weight[i] * sign[i] * ((v[i] - mean(v)) / (stdev(v)))) * sqrt(sum(weight[i])), where: 
	weight is a weight for each given criterion, 
	v is the criterion used to evaluate data,
	sign is (+/-)1, depending on whether the criterion has to be minimized or maximized

	*** the more general case: each keyword argument is a dictionary, where key=name
	of metric, value=(weight of metric, sign of metric)
	'''

	### read data
	f = open(statfilename, "r")
	flines = f.readlines()
	fnames = flines[0]
	fvals = flines[1:]
	f.close()
	mnames_split = fnames.strip().split()
	vals_split = [line.strip().split() for line in fvals]

	### model names
	names = []
	for list in vals_split:
		names.append(str(list[0]))

	### set value lists
	toEvaluate = {}
	list_names = {}
	for key, value in kwargs.iteritems():
		toEvaluate[key] = {"weight": value[0], "sign": value[1], "vals": []}
		for i, name in enumerate(mnames_split):
			if name == key:
				list_names[key] = i
	for name, index in list_names.iteritems():
		for l in vals_split:
			toEvaluate[name]['vals'].append(float(l[index]))

	### output should be sorted according to the weights
	sorted_metrics = sorted(kwargs.iteritems(), key=operator.itemgetter(1), reverse=True)
#	print "using the following criteria to evaluate Rcrit: ", sorted_metrics 

	### for each model, evaluate Rcrit based on all selected criteria
	Rcritdict1 = {} # for sorting only
	Rcritdict2 = {}
	weightsum = 0
	for valnames, allvals in toEvaluate.iteritems():
		weight = allvals['weight']
		weightsum += abs(weight)
	for i in range(len(fvals)):
		Rcrit = 0
		Rcritdict2[names[i]] = {}
		for valname, allvals in toEvaluate.iteritems():
			weight = allvals['weight']
			sign = allvals['sign']
			vals = allvals['vals']
			if float(numpy.std(vals)) == 0.0:
				std = 1
			else:
				std = numpy.std(vals)
			R = weight * sign * ((vals[i] - numpy.mean(vals)) / std) / weightsum
			Rcrit += R
			Rcritdict2[names[i]][valname] = vals[i] 
		Rcritdict1[names[i]] = Rcrit

	### write out values, sorted by Rcrit
	sorted_Rcritlist = sorted(Rcritdict1.iteritems(), key=operator.itemgetter(1))
	sorted_Rcritlist.reverse()
	f = open(outfile, "w")
	f.write("%11s %9s " % ("MODEL", "RCRIT"))
	for m in sorted_metrics:
		f.write("%9s " % m[0])
	f.write("\n")
	for i in range(len(sorted_Rcritlist)):
		d = Rcritdict2[sorted_Rcritlist[i][0]]
		f.write("%11s %9.4f " % (sorted_Rcritlist[i][0], Rcritdict1[sorted_Rcritlist[i][0]]))
		for m in sorted_metrics:
			f.write("%9.4f " % d[m[0]])
		f.write("\n")
	f.close()
	
#=====================

def combineMetrics1(N=False, wN=1, CCPR=True, wCCPR=1, EJ=True, wEJ=1, CCC=False,
	wCCC=1, STDEV=False, wSTDEV=1, SSNR=True, wSSNR=1):
	''' 
	takes all calculated metrics and combines them into a single Rcrit value, 
	according to: Rossmann, M. G., et al. (2001). "Combining electron microscopic 
	with x-ray crystallographic structures." J Struct Biol 136(3): 190-200.
	metrics are combined as follows: 
	
	Rcrit = sum(weight[i] * sign[i] * ((v[i] - mean(v)) / (stdev(v)))) * sqrt(sum(weight[i])), where: 
	weight is a weight for each given criterion, 
	v is the criterion used to evaluate data,
	sign is (+/-)1, depending on whether the criterion has to be minimized or maximized

	*** the more general case: each keyword argument is a dictionary, where key=name
	of metric, value=(weight of metric, sign of metric)
	'''
	
	### read data
	f = open("final_model_stats.dat", "r")
	flines = f.readlines()[1:]
	f.close()
	strip = [line.strip() for line in flines]
	split = [line.split() for line in strip]
	
	### set value lists
	toEvaluate = {}
	names = []
	Ns = []
	CCPRs = []
	EJs = []
	CCCs = []
	STDEVs = []
	SSNRs = []
	if N is True:			### number of models
		toEvaluate["N"] = {"weight": wN, "sign": 1, "vals": Ns}
	if CCPR is True:		### cross-correlation b/w projections & reprojections
		toEvaluate["CCPR"] = {"weight": wCCPR, "sign": 1, "vals": CCPRs}
	if EJ is True:			### average Euler jump
		toEvaluate["EJ"] = {"weight": wEJ, "sign": -1, "vals": EJs}
	if CCC is True:			### avg CCC within the model class
		toEvaluate["CCC"] = {"weight": wCCC, "sign": 1, "vals": CCCs}
	if STDEV is True:		### avg stdev of CCC within the model class
		toEvaluate["STDEV"] = {"weight": wSTDEV, "sign": -1, "vals": STDEVs}
	if SSNR is True:		### SSNR of the model class
		toEvaluate["SSNR"] = {"weight": wSSNR, "sign": -1, "vals": SSNRs}
		
	for list in split:
		### put all relevant parameters to list
		names.append(str(list[0]))
		Ns.append(int(float(list[1])))			
		CCPRs.append(float(list[2]))
		EJs.append(float(list[3]))
		CCCs.append(float(list[4]))
		STDEVs.append(float(list[5]))
		SSNRs.append(float(list[6]))	
			
	### for each model, evaluate Rcrit based on all selected criteria
	print "using the following criteria to evaluate Rcrit: ", toEvaluate.keys()
	Rcritdict1 = {}
	Rcritdict2 = {}
	weightsum = 0
	for valnames, allvals in toEvaluate.iteritems():
		weight = allvals['weight']
		weightsum += weight
	for i in range(len(names)):
		Rcrit = 0
		for valname, allvals in toEvaluate.iteritems():
			weight = allvals['weight']
			sign = allvals['sign']
			vals = allvals['vals']
			R = weight * sign * ((vals[i] - numpy.mean(vals)) / (numpy.std(vals))) / weightsum
			Rcrit += R
		Rcritdict1[names[i]] = Rcrit
		Rcritdict2[names[i]] = \
			{"Rcrit":Rcrit, "Mnum":names[i], "N":Ns[i], "CCPR":CCPRs[i], "EJ":EJs[i],
				 "CCC":CCCs[i], "STDEV":STDEVs[i], "SSNR":SSNRs[i]}
	
	### write out values, sorted by Rcrit
	f = open("final_model_stats_sorted_by_Rcrit.dat", "w")
	f.write("%9s %8s %5s %8s %8s %8s %8s %8s\n" \
		% ("MODEL", "RCRIT", "NUM", "CCPR", "EJ", "CCC", "STDEV", "SSNR"))
	sorted_Rcritlist = sorted(Rcritdict1.iteritems(), key=operator.itemgetter(1))
	sorted_Rcritlist.reverse()
	for i in range(len(sorted_Rcritlist)):
		d = Rcritdict2[sorted_Rcritlist[i][0]]
		f.write("%9s %8.4f %5d %8.3f %8.3f %8.3f %8.3f %8.3f\n" \
			% (d['Mnum'], d['Rcrit'], d['N'], d['CCPR'], d['EJ'], d['CCC'], d['STDEV'], d['SSNR']))
	f.close()
	
	return

#=====================

def combineMetrics2(N=False, wN=1, CCPR=True, wCCPR=1, EJ=True, wEJ=1, CCC=False, 
	wCCC=1, STDEV=False, wSTDEV=1, FSC=True, wFSC=1):
	''' 
	takes all calculated metrics and combines them into a single Rcrit value, 
	according to: Rossmann, M. G., et al. (2001). "Combining electron microscopic 
	with x-ray crystallographic structures." J Struct Biol 136(3): 190-200.
	metrics are combined as follows: 
	
	Rcrit = sum(weight[i] * sign[i] * ((v[i] - mean(v)) / (stdev(v)))) * sqrt(sum(weight[i])), where: 
	weight is a weight for each given criterion, 
	v is the criterion used to evaluate data,
	sign is (+/-)1, depending on whether the criterion has to be minimized or maximized

	*** the more general case: each keyword argument is a dictionary, where key=name
	of metric, value=(weight of metric, sign of metric)
	'''
	
	### read data
	f = open("final_model_stats.dat", "r")
	flines = f.readlines()[1:]
	f.close()
	strip = [line.strip() for line in flines]
	split = [line.split() for line in strip]
	
	### set value lists
	toEvaluate = {}
	names = []
	Ns = []
	CCPRs = []
	EJs = []
	CCCs = []
	STDEVs = []
	FSCs = []
	if N is True:			### number of models
		toEvaluate["N"] = {"weight": wN, "sign": 1, "vals": Ns}
	if CCPR is True:		### cross-correlation b/w projections & reprojections
		toEvaluate["CCPR"] = {"weight": wCCPR, "sign": 1, "vals": CCPRs}
	if EJ is True:			### average Euler jump
		toEvaluate["EJ"] = {"weight": wEJ, "sign": -1, "vals": EJs}
	if CCC is True:			### avg CCC within the model class
		toEvaluate["CCC"] = {"weight": wCCC, "sign": 1, "vals": CCCs}
	if STDEV is True:		### avg stdev of CCC within the model class
		toEvaluate["STDEV"] = {"weight": wSTDEV, "sign": -1, "vals": STDEVs}
	if FSC is True:		### FSC of the model class
		toEvaluate["FSC"] = {"weight": wFSC, "sign": -1, "vals": FSCs}
		
	for list in split:
		### put all relevant parameters to list
		names.append(str(list[0]))
		Ns.append(int(float(list[1])))			
		CCPRs.append(float(list[2]))
		EJs.append(float(list[3]))
		CCCs.append(float(list[4]))
		STDEVs.append(float(list[5]))
		FSCs.append(float(list[6]))	
			
	### for each model, evaluate Rcrit based on all selected criteria
	print "using the following criteria to evaluate Rcrit: ", toEvaluate.keys()
	Rcritdict1 = {}
	Rcritdict2 = {}
	weightsum = 0
	for valnames, allvals in toEvaluate.iteritems():
		weight = allvals['weight']
		weightsum += weight
	for i in range(len(names)):
		Rcrit = 0
		for valname, allvals in toEvaluate.iteritems():
			weight = allvals['weight']
			sign = allvals['sign']
			vals = allvals['vals']
			R = weight * sign * ((vals[i] - numpy.mean(vals)) / (numpy.std(vals))) / weightsum
			Rcrit += R
		Rcritdict1[names[i]] = Rcrit
		Rcritdict2[names[i]] = \
			{"Rcrit":Rcrit, "Mnum":names[i], "N":Ns[i], "CCPR":CCPRs[i], "EJ":EJs[i], 
				"CCC":CCCs[i], "STDEV":STDEVs[i], "FSC":FSCs[i]}
	
	### write out values, sorted by Rcrit
	f = open("final_model_stats_sorted_by_Rcrit.dat", "w")
	f.write("%11s %8s %5s %8s %8s %8s %8s %8s\n" \
		% ("MODEL", "RCRIT", "NUM", "CCPR", "EJ", "CCC", "STDEV", "FSC"))
	sorted_Rcritlist = sorted(Rcritdict1.iteritems(), key=operator.itemgetter(1))
	sorted_Rcritlist.reverse()
	for i in range(len(sorted_Rcritlist)):
		d = Rcritdict2[sorted_Rcritlist[i][0]]
		f.write("%11s %8.4f %5d %8.3f %8.3f %8.3f %8.3f %8.3f\n" \
			% (d['Mnum'], d['Rcrit'], d['N'], d['CCPR'], d['EJ'], d['CCC'], d['STDEV'], d['FSC']))
	f.close()
	
	return
	
	
