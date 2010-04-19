#!/usr/bin/env python

'''
Automated Angular Reconstitution: A method for iteratively creating ab initio 3d models from a stack of class averages. 
The algorithm inputs a weighted and randomly generated sequence of class averages into angular reconstitution N times 
to create N different 3D models (user specified). It then uses a combination of maximum-likelihood 3D alignment and 3D 
multivariate statistical analysis to sort through the resulting 3D models. The last step is affinity propagation clustering, 
which parses through the output and classifies the models without relying on a specified number of clusters.
'''

#python
import os
import sys
import re
import time
import math
import shutil
import subprocess

#appion
from appionlib import appionScript
from appionlib import appiondata
from appionlib import apEulerCalc
from appionlib import apImagicFile
from appionlib import apDisplay
from appionlib import apFile
from appionlib import apFourier
from appionlib import apIMAGIC
from appionlib import apSymmetry
from appionlib import apParam
from appionlib import apThread

#scipy
from scipy import stats

#pyami
from pyami import mrc

#numpy
import numpy

#=====================															=======================
#=====================					APPION SPECIFIC FUNCTIONS				=======================
#=====================															=======================
	
class automatedAngularReconstitution(appionScript.AppionScript):
#class automatedAngularReconstitution:

	def setupParserOptions(self):
		self.parser.set_usage( "Usage: %prog --file=<name> --apix=<pixel> --rundir=<dir> "
			+"[options]")		
			
		### basic params
		self.parser.add_option("--nproc", dest="nproc", type="int", default=1,
			help="number of processors to use", metavar="int")
		self.parser.add_option("--templatestackid", dest="templatestackid",
			help="ID of template stack used for iterative model creation", metavar="int")
		self.parser.add_option("--clusterid", dest="clusterid",
			help="ID of cluster stack used for iterative model creation", metavar="int")
			
		### pre-processing of class averages
		self.parser.add_option("--prealign", dest="prealign", default=False, action="store_true",
			help="OPTIONAL: iteratively align the class averages to each other prior to carrying out iterative angular reconstitution. \
				This option has been very helpful in cases when the class averages may not be perfectly translationally aligned, which \
				would produce poor results when input into angular reconstitution")		
		self.parser.add_option("--scale", dest="scale", default=False, action="store_true",
			help="scale the class averages to a boxsize of 64x64 prior to iterative model creation")
			
		### Angular Reconstitution
		self.parser.add_option("--symmetry", dest="symid", type="int", default=25,
			help="symmetry of the object (ID from Appion Database). This is automatically defaulted to the suggested C1 symmetry", metavar="INT")
		self.parser.add_option("--num_volumes", dest="num_volumes", type="int",
			help="number of volumes to create using angular reconstitution", metavar="INT")
		self.parser.add_option("--ang_inc", dest="ang_inc", type="int", default=2,
			help="angular increment for Euler search within the sinogram", metavar="INT")
		self.parser.add_option("--keep_ordered", dest="keep_ordered", type="int", default=90,
			help="percentage of the best class averages to keep for the actual 3D reconstruction. \
				This value is determined by the error in angular reconstitution for each input class average", metavar="INT")
			
		### 3D reconstruction
		self.parser.add_option("--ham_win", dest="ham_win", type="float", default=0.8,
			help="similar to lp-filtering parameter, smooths out the filter used in 3d reconstruction", metavar="float")
		self.parser.add_option("--3d_lpfilt", dest="3d_lpfilt", type="int", default=10,
			help="low-pass filter the reconstructed 3-D model to specified resolution (Angstroms) prior to masking", metavar="INT")
			
		### Xmipp maximum-likelihood alignment
		self.parser.add_option("--nref", dest="nref", type="int", default=1,
			help="number of 3D references to generate for Xmipp maximum-likelihood alignment", metavar="INT")	
			
		### Principal Component Analysis (Multivariate Statistical Analysis)
		self.parser.add_option("--numeigens", dest="numeigens", type="int", default=69,
			help="number of 3D Eigenvectors (Eigenimages) to create during Principal Component Analysis for data reduction", metavar="INT")
		self.parser.add_option("--PCA", dest="PCA", default=False, action="store_true",
			help="use Principal Component Analysis to reduce the dimensionality of the resulting 3D volumes prior to clustering. \
				the input coordinates will then be put into affinity propagation to determine 3D class averages")
		self.parser.add_option("--recalculate_volumes", dest="recalculate", default=False, action="store_true",
			help="optional parameter: specify ONLY if you wish to recalculate the 3D volumes after PCA data reduction. \
				does NOT affect any results, and is only present for visualization purposes of the effects of PCA")
				
		### Affinity propagation clustering
		self.parser.add_option("--preftype", dest="preftype", type="str", default="median",
			help="preference value for affinity propation which influences the resulting number of 3D class averages. \
				choose from 'median', 'minimum', or 'minlessrange'. 'median' will result in the greatest amount of classes, \
				followed by 'minimum', while 'minlessrange' results in the fewest", metavar="STR")
				
		### Miscellaneous
		self.parser.add_option("--non_weighted_sequence", dest="non_weighted_sequence", default=False, action="store_true",
			help="if this is specified, then the sequence of addition into angular reconstitution will \
				be completely randomized, rather than weighted and randomized")
		self.parser.add_option("--do_not_remove", dest="do_not_remove", default=False, action="store_true",
			help="specify if you want to keep miscellaneous files associated with angular reconstitution (e.g. sinograms) \
				NOTE: keeping these files takes up huge amounts of diskspace")
							
		return
		
	#=====================
	#=====================
	#=====================	

	def checkConflicts(self):

		### check for IMAGIC installation
		d = os.environ
		if d.has_key('IMAGIC_ROOT'):
			self.imagicroot = d['IMAGIC_ROOT']
		else:
			apDisplay.printError("$IMAGIC_ROOT directory is not specified, please specify this in your .cshrc / .bashrc")

		### check for basic input parameters
		if self.params['templatestackid'] is None and self.params['clusterid'] is None:
			apDisplay.printError("enter either a template stack ID or a cluster ID for the run")
		if self.params['templatestackid'] is not None and self.params['clusterid'] is not None:
			apDisplay.printError("please specify EITHER a template stack id OR a cluster id, not both")
		if self.params['num_volumes'] is None:
			apDisplay.printError("please specify the number of volumes that you wish to produce from the class averages")
		

		return

	#=====================
	#=====================
	#=====================	

	def setRunDir(self):

		if self.params['templatestackid'] is not None:
			stackdata = appiondata.ApTemplateStackData.direct_query(self.params['templatestackid'])
		elif self.params['clusterid'] is not None:
			stackdata = appiondata.ApClusteringStackData.direct_query(self.params['clusterid'])
		else:
			apDisplay.printError("class averages not in the database")
			
		path = os.path.abspath(os.path.join(stackdata['path']['path'], "../..", "angular_reconstitution"))
		self.params['rundir'] = os.path.join(path, self.params['runname'])
		
		return

	#=============================															===============================
	#=============================					CORRELATION FUNCTIONS					===============================
	#=============================															===============================
		
	def calculate_ccc_matrix_2d(self, class_averages):
		'''
		takes as input a stack of class averages, then for each image in the stack
		calculates a cross-correlation coefficient to each successive image. It then 
		returns a matrix of cross-correlation coefficients between the images. 
		'''
		
		### read class averages and estimate time for completion
		imagicdict = apImagicFile.readImagic(filename=class_averages, msg=True)
		partarray = imagicdict['images']
		numpart = partarray.shape[0]
		self.params['boxsize'] = partarray.shape[1]
		timeper = 17.0e-9
		apDisplay.printMsg("Computing cross-correlation values in %s" 
			%(apDisplay.timeString(timeper*numpart**2*self.params['boxsize']**2)))
		
		### cross correlate each class average to each successive class average
		ccc_matrix = numpy.ones((numpart, numpart))
		ccc_file = os.path.join(os.getcwd(), "CCCs_2d.dat")
		f = open(ccc_file, "w")
		for i in range(numpart):
			for j in range(i+1, numpart):
				ccs = self.calculate_ccs(partarray[i], partarray[j])
				ccc_matrix[i,j] = ccs[0]
				ccc_matrix[j,i] = ccs[0]
				str1 = "%05d %05d %.10f\n" % (i+1, j+1, ccc_matrix[i,j])
				f.write(str1)
				str2 = "%05d %05d %.10f\n" % (j+1, i+1, ccc_matrix[j,i])
				f.write(str2)	
		f.close()
		
		return ccc_matrix
		
	#=====================
	#=====================
	#=====================

	def calculate_ccc_matrix_3d(self):
		'''
		for each volume calculates a cross-correlation coefficient to each successive volume, then 
		returns a file corresponding to cross-correlation coefficients between the images. 
		'''
		
		apDisplay.printMsg("Creating cross-correlation similarity matrix for affinity propagation ...")		
			
		### create a similarity matrix using cross-correlation of aligned 3-D models
		self.params['rundir'] = os.getcwd()
		cc_matrix = numpy.ones((self.params['num_volumes'], self.params['num_volumes']))

		### create cross-correlation similarity matrix
		for i in range(self.params['num_volumes']):
			for j in range(i+1, self.params['num_volumes']):				
				model1 = mrc.read(os.path.join(self.params['rundir'], "volumes", "3d%d_ordered%d_filt.mrc" % (i+1,i+1)))
				model2 = mrc.read(os.path.join(self.params['rundir'], "volumes", "3d%d_ordered%d_filt.mrc" % (j+1,j+1)))
				ccs = self.calculate_ccs(model1, model2)
				cc_matrix[i,j] = ccs[0]
				cc_matrix[j,i] = ccs[0]

		### write similarities (CCCs) to file 
		simfile = os.path.join(self.params['rundir'], "CCCs_3d.dat")
		f = open(simfile, "w")
		for i in range(self.params['num_volumes']):
			for j in range((i+1), self.params['num_volumes']):
				str1 = "%05d %05d %.10f\n" % (i+1, j+1, cc_matrix[i,j])
				f.write(str1)
				str2 = "%05d %05d %.10f\n" % (j+1, i+1, cc_matrix[j,i])
				f.write(str2)
		f.close()
		
		return simfile, cc_matrix

	#=====================
	#=====================
	#=====================	

	def calculate_ccs(self, imgarray1, imgarray2):
		'''  Pearson correlation coefficient between two arrays of identical dimensions '''
		ccs = stats.pearsonr(numpy.ravel(imgarray1), numpy.ravel(imgarray2))
		return ccs

	#=====================
	#=====================
	#=====================	
			
	def euclideanDist(self, x, y):
		''' Euclidean Distance between two arrays of identical dimensions '''
		return numpy.sqrt(numpy.sum((numpy.ravel(x)-numpy.ravel(y))**2))
		
	#=====================
	#=====================
	#=====================	

	def normList(self, numberList, normalizeTo=1):
		'''normalize values of a list to make its max = normalizeTo'''
		vMax = max(numberList)
		return [x/(vMax*1.0)*normalizeTo for x in numberList]

	#=====================
	#=====================
	#=====================		
	
	def create_difference_matrix(self, ccc_matrix):
		''' inverts the similarity matrix to create a difference matrix based on (diff=1-sim) metric '''

		### take inverse of CCC & normalize
		diff_matrix = numpy.where(ccc_matrix < 1, 1-ccc_matrix, 0)

		return diff_matrix
		
	#=====================
	#=====================
	#=====================	

	def calculate_sequence_of_addition(self, avgs, ccc_matrix):
		''' 
		calculates a unique sequence of addition of class averages. function first initializes a random seed, then calculates
		the rest of the sequence based on the resulting weighted probability matrix generated from each successive addition
		'''
			
		### initialize sequence (image queue) and weight matrix, which determines sequence calculation
		probability_list = numpy.zeros(self.params['numpart'])
		sequence = []

		### create image list with all particles
		im_list = []
		for i in range(self.params['numpart']):
			im_list.append(i)
			
		### if completely random sequence is desired, do that here
		if self.params['non_weighted_sequence'] is True:
			while im_list:
				r = numpy.random.randint(len(im_list))
				sequence.append(im_list[r]+1)
				del im_list[r]

		### otherwise randomize first image selection and continue with weighted selection
		else:
			im_init = numpy.random.randint(low=0, high=self.params['numpart'])
			
			### create probability matrix from ccc matrix and append new image
			diff_matrix = self.create_difference_matrix(ccc_matrix)
			probability_list = self.create_probability_list(im_init, probability_list, diff_matrix)
			sequence.append(im_init+1)
			
			### figure out the rest of the sequence, based on the first randomly selected image
			for image in range(len(im_list)-1):
				next_choice = self.weighted_random_pick(im_list, probability_list)
				probability_list = self.update_probability_list(next_choice, probability_list, diff_matrix)
				sequence.append(next_choice+1)
			
		return sequence

	#=====================
	#=====================
	#=====================
		
	def create_probability_list(self, selection, probability_list, diff_matrix):
		''' creates the list that stores probability values used for weighted randomized selection '''
		
		for i in range(len(probability_list)):
			probability_list[i] += diff_matrix[i][selection]
			
		return probability_list
		
	#=====================
	#=====================
	#=====================
		
	def update_probability_list(self, selection, probability_list, diff_matrix):
		''' updates the list that stores probability values used for weighted randomized selection '''

		for i in range(len(probability_list)):
			if probability_list[i] != 0:
				probability_list[i] = probability_list[i] * diff_matrix[i][selection]
		probability_list[selection] = 0 ### don't use this selection anymore
		if max(probability_list) != 0:
			probability_list = self.normList(probability_list)

		return probability_list

	#=====================
	#=====================
	#=====================

	def weighted_random_pick(self, im_list, probability_list, ):
		''' 
		based on the given probabilities of the existing choices, this function determines what the next image will be. 
		It uses a weighted randomized decision-making strategy that takes into account how different the images are from each other
		'''
		
		weight_total = sum((p for p in probability_list))
		n = numpy.random.uniform(0, weight_total)
		cumulative_p = 0.0
		for image, image_probability in zip(im_list, probability_list):
			cumulative_p += image_probability
			if n < cumulative_p: break
			
		return image
			
	#=====================
	#=====================
	#=====================

	def prealignClassAverages(self):
		''' function to iteratively align class averages to each other prior to input into angular reconstitution (optional) '''
		
		batchfile = os.path.join(self.params['rundir'], "prealignClassAverages.batch")
		f = open(batchfile, 'w')
		f.write("#!/bin/csh -f\n")
		f.write("setenv IMAGIC_BATCH 1\n")
		f.write("cd "+self.params['rundir']+"/\n")		
	
		f.write(str(self.imagicroot)+"/align/alirefs.e <<EOF > prealignClassAverages.log\n")
		f.write("ALL\n")
		f.write("CCF\n")
		f.write(str(self.params['avgs'])[:-4]+"\n")
		f.write("NO\n")
		f.write("0.99\n")
		f.write(str(self.params['avgs'])[:-4]+"_aligned\n")
		f.write("-999.\n")
		f.write("0.2\n")
		f.write("-180,180\n")
		f.write("NO\n")
		f.write("5\n")
		f.write("NO\n")
		f.write("EOF\n")
		f.close()
		
		self.params['avgs'] = self.params['avgs'][:-4]+"_aligned.img"
		
		proc = subprocess.Popen('chmod 755 '+batchfile, shell=True)
		proc.wait()
		apParam.runCmd(batchfile, "IMAGIC") 
		
		return self.params['avgs']

	#=====================
	#=====================
	#=====================

	def imagic_batch_file(self, sequence, iteration):
		''' IMAGIC batch file creation for angular reconstitution '''
		
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
		syminfo = apSymmetry.findSymmetry(self.params['symid'])	
		symmetry = syminfo['eman_name']
		clsavgs = self.params['avgs'][:-4]
		rundir = os.path.join(self.params['rundir'], "angular_reconstitution")
		filename = os.path.join(rundir, "imagicCreate3d"+str(iteration)+".batch")
		f = open(filename, 'w')
		f.write("#!/bin/csh -f\n")
		f.write("setenv IMAGIC_BATCH 1\n")
		f.write("cd "+rundir+"/\n")

		### 1st iteration of angular reconstitution using 3 initial projections for C1, OR simply 1st 3 additions for other symmetries
		f.write(str(self.imagicroot)+"/angrec/euler.e <<EOF > 3d"+str(iteration)+".log\n")
		f.write(symmetry+"\n")
		lowercase = str(symmetry).lower()
		if lowercase != "c1":
			f.write("0\n")
		f.write("new\n")
		f.write("fresh\n")
		f.write(str(clsavgs)+"\n")	
		f.write(proj_init+"\n")
		f.write("ordered"+str(iteration)+"\n")
		f.write("sino_ordered"+str(iteration)+"\n")
		f.write("yes\n")
		f.write(".9\n")
		f.write("my_sine"+str(iteration)+"\n")
		f.write("%i\n" % (self.params['ang_inc']))	
		if lowercase == "c1":
			f.write("30\n")
		f.write("no\n")
		f.write("EOF\n")

		### now calculate Euler angles for the rest of the projections in a brute force search
		if len(sequence) > 125: ### IMAGIC only accepts strings of a specified length
			for seq in sequences:
				f.write(str(self.imagicroot)+"/angrec/euler.e <<EOF >> 3d"+str(iteration)+".log\n")
				f.write(symmetry+"\n")
				if lowercase != "c1":
					f.write("0\n")
				f.write("new\n")
				f.write("add\n")
				f.write(str(clsavgs)+"\n")
				f.write(str(seq)+"\n")
				f.write("ordered"+str(iteration)+"\n")
				f.write("sino_ordered"+str(iteration)+"\n")
				f.write("yes\n")
				f.write("0.9\n")
				f.write("my_sine"+str(iteration)+"\n")
				f.write("%i\n" % (self.params['ang_inc']))
				f.write("yes\n")
				f.write("EOF\n")
		else:
			f.write(str(self.imagicroot)+"/angrec/euler.e <<EOF >> 3d"+str(iteration)+".log\n")
			f.write(symmetry+"\n")
			if lowercase != "c1":
				f.write("0\n")
			f.write("new\n")
			f.write("add\n")
			f.write(str(clsavgs)+"\n")
			f.write(proj_rest+"\n")
			f.write("ordered"+str(iteration)+"\n")
			f.write("sino_ordered"+str(iteration)+"\n")
			f.write("yes\n")
			f.write("0.9\n")
			f.write("my_sine"+str(iteration)+"\n")
			f.write("%i\n" % (self.params['ang_inc']))
			f.write("yes\n")
			f.write("EOF\n")
		
		### remove the worst ___ % of avgs, based on the error in angular reconstitution, then put them back in for recalculation with better references
		
		### sort based on error in angular reconstitution
		f.write(str(self.imagicroot)+"/incore/excopy.e <<EOF >> 3d"+str(iteration)+".log\n")
		f.write("2D_IMAGES\n")
		f.write("SORT\n")
		f.write("ordered"+str(iteration)+"\n")
		f.write("ordered"+str(iteration)+"_sort\n")
		f.write("ANGULAR_ERROR\n")
		f.write("UP\n")
		f.write("%i\n" % (self.params['keep_ordered']))	
		f.write("EOF\n")
		
		### build a 3-D model
		f.write(str(self.imagicroot)+"/threed/true_3d.e <<EOF >> 3d"+str(iteration)+".log\n")
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
		f.write("%f\n" % (self.params['ham_win']))		
		f.write("0.8\n")		
		f.write("EOF\n")
		
		### low-pass filter
		lp_filt = self.params['3d_lpfilt']
		filtval = 2 * self.params['apix'] / lp_filt
		if filtval > 1:
			filtval = 1
		f.write(str(self.imagicroot)+"/threed/filter3d.e FORW FILTER <<EOF >> 3d"+str(iteration)+".log\n")
		f.write("lowpass\n")
		f.write("3d"+str(iteration)+"_ordered"+str(iteration)+"\n")
		f.write("3d"+str(iteration)+"_ordered"+str(iteration)+"_filt\n")
		f.write(str(filtval)+"\n")
		f.write("EOF\n")
		
		### write out a .plt file with all Euler angles
		f.write(str(self.imagicroot)+"/stand/headers.e <<EOF >> 3d"+str(iteration)+".log\n")
#		f.write("ordered"+str(iteration)+"_sort\n")
		f.write("PLT_OUT\n")
		f.write("THREED\n")
		f.write("ordered"+str(iteration)+"\n")
		f.write("ordered"+str(iteration)+".plt\n")
		f.write("EOF\n")
		
		### convert to SPIDER format, but first rotate volume by 180 degrees around IMAGIC y, to make sure that the image remains UNCHANGED
		### a (0,180,0) rotation in IMAGIC is equivalent to a (180,180,0) rotation in Spider / Xmipp, due to the difference in coordinate systems
		f.write(str(self.imagicroot)+"/threed/rotate3d.e <<EOF >> 3d"+str(iteration)+".log\n")
		f.write("3d"+str(iteration)+"_ordered"+str(iteration)+"_filt\n")
		f.write("3d"+str(iteration)+"_ordered"+str(iteration)+"_filt_rot\n")
		f.write("FORWARD\n")
		f.write("0,180,0\n")
		f.write("0,0,0\n")
		f.write("EOF\n")
		f.write(str(self.imagicroot)+"/stand/em2em.e <<EOF >> 3d"+str(iteration)+".log\n")
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
		if self.params['do_not_remove'] is False:
			f.write(str(self.imagicroot)+"/stand/imdel.e <<EOF >> 3d"+str(iteration)+".log\n")
			f.write("ordered%d\n" % (iteration))
			f.write("EOF\n")
			f.write(str(self.imagicroot)+"/stand/imdel.e <<EOF >> 3d"+str(iteration)+".log\n")
			f.write("sino_ordered%d\n" % (iteration))
			f.write("EOF\n")
			f.write(str(self.imagicroot)+"/stand/imdel.e <<EOF >> 3d"+str(iteration)+".log\n")
			f.write("err%d_ordered%d\n" % (iteration,iteration))
			f.write("EOF\n")
			f.write(str(self.imagicroot)+"/stand/imdel.e <<EOF >> 3d"+str(iteration)+".log\n")
			f.write("3d%d_ordered%d\n" % (iteration,iteration))
			f.write("EOF\n")
			f.write(str(self.imagicroot)+"/stand/imdel.e <<EOF >> 3d"+str(iteration)+".log\n")
			f.write("3d%d_ordered%d_filt_rot\n" % (iteration,iteration))
			f.write("EOF\n")
			f.write(str(self.imagicroot)+"/stand/imdel.e <<EOF >> 3d"+str(iteration)+".log\n")
			f.write("3d%d_ordered%d_filt\n" % (iteration,iteration))
			f.write("EOF\n")
			f.write(str(self.imagicroot)+"/stand/imdel.e <<EOF >> 3d"+str(iteration)+".log\n")
			f.write("my_sine%d\n" % (iteration
			))
			f.write("EOF\n")

		f.close()

		return filename

	#=====================
	#=====================
	#=====================
	
	def xmipp_max_like_3d_align(self):
		''' 3-D maximum likelihood alignment of all models resulting from iterative 3d0 creation '''
		
		### create necessary input .sel & .doc files
		selfile = open(os.path.join(self.params['rundir'], "volumes.sel"), "w")
		for i in range(self.params['num_volumes']):
			selfile.write("volumes/3d"+str(i+1)+"_ordered"+str(i+1)+"_filt.vol 1\n")
		selfile.close()
		docfile = open(os.path.join(self.params['rundir'], "volumes.doc"), "w")
		for i in range(self.params['num_volumes']):
			docfile.write(" ; volumes/3d"+str(i+1)+"_ordered"+str(i+1)+"_filt.vol\n")
			docfile.write(str(i+1)+" 10 0 0 0 0 0 0 0 0 0 0\n")
		docfile.close()
		
		### run 3-D maximum-likelihood alignment
		rundir = os.path.join(self.params['rundir'], "max_like_alignment")
		if not os.path.isdir(rundir):
			os.mkdir(rundir)
		xmippcmd1 = "xmipp_ml_tomo -i volumes.sel -o max_like_alignment/nref%d_15deg -nref %d -doc volumes.doc -iter 5 -ang 15 -dim 32 -perturb" \
					% (self.params['nref'], self.params['nref'])
		if self.params['nproc'] > 1:
			xmippcmd1 += " -thr "+str(self.params['nproc'])
		apParam.runCmd(xmippcmd1, package="Xmipp")
		xmippcmd2 = "xmipp_ml_tomo -i volumes.sel -o max_like_alignment/nref%d_10deg -nref %d -doc max_like_alignment/nref%d_15deg_it000015.doc -keep_angles -iter 5 -ang 10 -ang_search 50 -maxres 0.35 -perturb" \
					% (self.params['nref'], self.params['nref'], self.params['nref'])
		if self.params['nproc'] > 1:
			xmippcmd2 += " -thr "+str(self.params['nproc'])
		apParam.runCmd(xmippcmd2, package="Xmipp")
		xmippcmd3 = "xmipp_ml_tomo -i volumes.sel -o max_like_alignment/nref%d_5deg -nref %d -doc max_like_alignment/nref%d_10deg_it000005.doc -keep_angles -iter 5 -ang 5 -ang_search 25 -maxres 0.35 -perturb" \
					% (self.params['nref'], self.params['nref'], self.params['nref'])
		if self.params['nproc'] > 1:
			xmippcmd3 += " -thr "+str(self.params['nproc'])
		apParam.runCmd(xmippcmd3, package="Xmipp")

		### check for all iterations, just in case Xmipp ended early, sometimes it converges before 5th iteration
		i = 5
		while i > 0:
			vol_doc_file = os.path.join(rundir, "nref%d_5deg_it00000%d.doc") % (self.params['nref'], i)
			if os.path.isfile(vol_doc_file):
				return vol_doc_file
			else:
				i -= 1
		if i == 0:
			apDisplay.printError("ERROR IN 3-D MAXIMUM LIKELIHOOD RUN")
			
	#=====================
	#=====================
	#=====================

	def read_vol_doc_file(self, vol_doc_file):
		''' read and return all alignment parameters from 3-D maximum likelihood '''
		
		f = open(vol_doc_file, "r")
		f.readline() # first line is header info
		lines = f.readlines()
		alignparams = []
		for i in range(self.params['num_volumes']):
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
	#=====================
	#=====================
		
	def align_volumes(self, alignparams):
		''' align the volumes to the resulting reference from maximum-likelihood '''
		
		transcmds = []
		rotcmds = []
		emancmds = []
		for i in range(self.params['num_volumes']):
			ref = int(float(alignparams[i][7]))
			xmippcmd_trans = "xmipp_align_volumes -i1 max_like_alignment/nref%d_5deg_ref00000%d.vol -i2 " % (self.params['nref'], ref) \
				+str(alignparams[i][0])+\
				" -x "+str(alignparams[i][1])+" "+str(alignparams[i][1])+" 1"\
				" -y "+str(alignparams[i][2])+" "+str(alignparams[i][2])+" 1"\
				" -z "+str(alignparams[i][3])+" "+str(alignparams[i][3])+" 1 -apply"
			transcmds.append(xmippcmd_trans)
			xmippcmd_rot = "xmipp_align_volumes -i1 max_like_alignment/nref%d_5deg_ref00000%d.vol -i2 " % (self.params['nref'], ref) \
				+str(alignparams[i][0])+\
				" -rot "+str(alignparams[i][4])+" "+str(alignparams[i][4])+" 1"\
				" -tilt "+str(alignparams[i][5])+" "+str(alignparams[i][5])+" 1"\
				" -psi "+str(alignparams[i][6])+" "+str(alignparams[i][6])+" 1 -apply"
			rotcmds.append(xmippcmd_rot)
			emancmd = "proc3d "+str(alignparams[i][0])+" "+str(alignparams[i][0])[:-4]+".mrc apix="+str(self.params['apix'])
			emancmds.append(emancmd)
		apThread.threadCommands(transcmds, nproc=self.params['nproc'], pausetime=10)
		apThread.threadCommands(rotcmds, nproc=self.params['nproc'], pausetime=10)
		apThread.threadCommands(emancmds, nproc=self.params['nproc'], pausetime=10)
			
		return
		
	#=====================
	#=====================
	#=====================

	def runPrincipalComponentAnalysis(self, recalculate=False):
		''' 
		runs principal component analysis to reduce dimensionality of dataset and returns the correlation file
		corresponding to the similarity of each point in factor space
		'''
		
		### default number of eigenimages
		self.params['rundir'] = os.getcwd()
		if self.params['num_volumes'] < 69:
			numeigens = self.params['num_volumes']
		else:
			numeigens = 69
		apDisplay.printMsg("using %d Eigenvectors (Eigenvolumes) to reduce dimensionality of dataset and calculate volume similarities" % (numeigens))
			
		### create input array from all volumes 	
		volumes = numpy.empty([self.params['num_volumes'], self.params['boxsize'], self.params['boxsize'], self.params['boxsize']])
		for i in range(self.params['num_volumes']):
			vol = mrc.read(os.path.join(self.params['rundir'], "volumes", "3d%d_ordered%d_filt.mrc" % (i+1,i+1)))
			volumes[i] += vol
		self.params['num_volumes'] = volumes.shape[0]
		numpixels = volumes.shape[1]*volumes.shape[2]*volumes.shape[3]
		inputs = volumes.reshape(self.params['num_volumes'], numpixels)
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
		diff_matrix = numpy.zeros((self.params['num_volumes'], self.params['num_volumes']))
		for i in range(self.params['num_volumes']):
			for j in range(i+1, self.params['num_volumes']):
				model1 = new_coordinates[:,i]
				model2 = new_coordinates[:,j]
				dist = self.euclideanDist(model1, model2)
				diff_matrix[i,j] = dist
				diff_matrix[j,i] = dist
		sim_matrix = numpy.where(diff_matrix != 0, 1/diff_matrix, 1)
					
		### write similarities (CCCs) to file 
		apDisplay.printMsg("writing similarities to file %s" % ("CCCs_3d.dat"))
		simfile = os.path.join(self.params['rundir'], "CCCs_3d.dat")
		f = open(simfile, "w")
		for i in range(self.params['num_volumes']):
			for j in range((i+1), self.params['num_volumes']):
				str1 = "%05d %05d %.10f\n" % (i+1, j+1, sim_matrix[i,j])
				f.write(str1)
				str2 = "%05d %05d %.10f\n" % (j+1, i+1, sim_matrix[j,i])
				f.write(str2)
		f.close()
			
		### write out the first 3 eigenvectors (eigenvolumes)
		header = {'xorigin' : 0, 'yorigin' : 0, 'zorigin' : 0, 'xlen' : self.params['boxsize']*self.params['apix'], 
			'ylen' : self.params['boxsize']*self.params['apix'], 'zlen' : self.params['boxsize']*self.params['apix']}
		for i in range(3):
			eigim = transformed_points[i]
			eigim = eigim.reshape(volumes.shape[1], volumes.shape[2], volumes.shape[3])
			mrc.write(eigim, "eigenvolume%d.mrc" % (i+1), header)

		### recalculate images
		if recalculate is True:
			if not os.path.isdir(os.path.join(self.params['rundir'], "new_mrcs")):
				os.mkdir(os.path.join(self.params['rundir'], "new_mrcs"))
			myarray = []
			newimages = numpy.dot(transposed_evecs, transformed_points)
			for j in range(self.params['num_volumes']):
				newim = (newimages[j]+meaninput).reshape(volumes.shape[1], volumes.shape[2], volumes.shape[3])
				mrc.write(newim, os.path.join(self.params['rundir'], "new_mrcs", str(j+1)+".mrc"), header)
				
		return simfile, sim_matrix

	#=====================
	#=====================
	#=====================
		
	def set_preferences(self, sim_matrix, preftype):
		''' set preference value for affinity propagation and dump to file '''
		
		### Preference value stats
		apDisplay.printMsg("similarity stats:\n %.5f +/- %.5f\n %.5f <> %.5f"
				% (numpy.where(sim_matrix<1, sim_matrix, 0).mean(), numpy.where(sim_matrix<1, sim_matrix, 0).std(), 
				sim_matrix.min(), numpy.where(sim_matrix<1, sim_matrix, 0).max()))

		### Determine preference value baed on specified type
		print self.params['preftype']
		if self.params['preftype'] == 'minlessrange':
			apDisplay.printMsg("Determine minimum minus total range (fewest classes) preference value")
			prefvalue = sim_matrix.min() - (numpy.where(sim_matrix<1, sim_matrix, 0).max() - sim_matrix.min())
		elif self.params['preftype'] == 'minimum':
			apDisplay.printMsg("Determine minimum (few classes) preference value")
			prefvalue = sim_matrix.min()
		elif self.params['preftype'] == 'median':
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
		preffile = os.path.join(self.params['rundir'], 'affinity_propataion_preferences.dat')
		apDisplay.printMsg("Dumping preference value to file")
		f = open(preffile, 'w')
		for i in range(0,self.params['num_volumes']):
			f.write('%.10f\n' % (prefvalue))
		f.close()
		
		return preffile
		
	#=====================
	#=====================
	#=====================
	
	def run_affinity_propagation(self, simfile, preffile):
		''' Use Affinity Propagation to classify and average all aligned 3-D models '''
		
		apDisplay.printMsg("running Affinity Propagation on aligned 3-D models")

		### run Affinity Propagation
		apclusterexe = os.path.join(apParam.getAppionDirectory(), "bin/apcluster.exe")
		outfile = os.path.join(self.params['rundir'], "cluster_affiliation.dat")
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
		header = {'xorigin' : 0, 'yorigin' : 0, 'zorigin' : 0, 'xlen' : self.params['boxsize']*self.params['apix'], 
			'ylen' : self.params['boxsize']*self.params['apix'], 'zlen' : self.params['boxsize']*self.params['apix']}
		classnames = classes.keys()
		for classnum in classnames:
			avgclass = numpy.zeros(((self.params['boxsize'],self.params['boxsize'],self.params['boxsize'])))
			num_members = 0
			for member in classes[classnum]:
				num_members += 1
				avgclass += mrc.read(os.path.join(self.params['rundir'], "volumes", "3d"+str(member)+"_ordered"+str(member)+"_filt.mrc"))
			avgclass = avgclass / num_members
			mrc.write(avgclass, os.path.join(self.params['rundir'], (str(classnum)+".mrc")), header)
					
		return classes
		
	#=============================															===============================
	#=============================					EULER ANGLE FUNCTIONS					===============================
	#=============================															===============================
	
	def EulersToTransformationMatrix(self, rot, tilt, psi):
		''' 
		takes Euler angles as rotation, tilt, and psi (in degrees) and converts to a 3x3 transformation matrix, according to ZYZ convention.
		This follows the standard 3DEM convention
		'''
		
	#	rotmat = numpy.array(([math.cos(rotation), math.sin(rotation), 0], [-math.sin(rotation), math.cos(rotation), 0], [0, 0, 1]))
	#	tiltmat = numpy.array(([math.cos(tilt), 0, -math.sin(tilt)], [0, 1, 0], [math.sin(tilt), 0, math.cos(tilt)]))
	#	psimat = numpy.array(([math.cos(psi), math.sin(psi), 0], [-math.sin(psi), math.cos(psi), 0], [0, 0, 1]))
	#	m = numpy.dot(psimat, numpy.dot(tiltmat, rotmat))

		rot *= math.pi / 180
		tilt *= math.pi / 180
		psi *= math.pi / 180

		m = numpy.zeros((3,3), dtype=numpy.float32)
		m[0][0] = math.cos(psi)*math.cos(tilt)*math.cos(rot) - math.sin(psi)*math.sin(rot)
		m[0][1] = math.cos(psi)*math.cos(tilt)*math.sin(rot) + math.sin(psi)*math.cos(rot)
		m[0][2] = -math.cos(psi)*math.sin(tilt)
		m[1][0] = -math.sin(psi)*math.cos(tilt)*math.cos(rot) - math.cos(psi)*math.sin(rot)
		m[1][1] = -math.sin(psi)*math.cos(tilt)*math.sin(rot) + math.cos(psi)*math.cos(rot)
		m[1][2] = math.sin(psi)*math.sin(tilt)
		m[2][0] = math.sin(tilt)*math.cos(rot)
		m[2][1] = math.sin(tilt)*math.sin(rot)
		m[2][2] = math.cos(tilt)
		
		### round off any values close to 0, default set to 0.001
		default = 0.000001
		m = numpy.where(abs(m) < default, 0, m)
		
		return m
		
	#=====================
	#=====================
	#=====================
	
	def EulersFromTransformationMatrix(self, transform_matrix):
		''' 
		recovers Euler angles in degrees from 3x3 transformation matrix or array. Procedure assumes that the tilt Euler angle is < 180, i.e. pi.
		This follows the ZYZ convention of 3DEM with a standard coordinate system.
		'''
		
		if type(transform_matrix) is not numpy.ndarray:
			transform_matrix = numpy.asarray(transform_matrix)
			
		### round off any values close to 0, default set to 0.001
		default = 0.000001
		transform_matrix = numpy.where(abs(transform_matrix) < default, 0, transform_matrix)
		
		tilt = math.acos(transform_matrix[2][2])
		if tilt > 0 and tilt < math.pi: 		
			rot = math.atan2(transform_matrix[2][1], transform_matrix[2][0])
			if transform_matrix[0][2] == 0: ### atan2(0.0,-0.0) returns 180, but we need 0
				psi = math.atan2(transform_matrix[1][2], transform_matrix[0][2])
			else:
				psi = math.atan2(transform_matrix[1][2], -transform_matrix[0][2])
		elif round(tilt,4) == round(0,4):
			rot = 0
			if transform_matrix[1][0] == 0: ### atan2(0.0,-0.0) returns 180, but we need 0
				psi = math.atan2(transform_matrix[1][0], transform_matrix[0][0])
			else:
				psi = math.atan2(-transform_matrix[1][0], transform_matrix[0][0])
		elif round(tilt,4) == round(math.pi,4):
			rot = 0
			if transform_matrix[0][0] == 0: ### atan2(0.0,-0.0) returns 180, but we need 0
				psi = math.atan2(transform_matrix[1][0], transform_matrix[0][0])
			else:
				psi = math.atan2(transform_matrix[1][0], -transform_matrix[0][0])
		else:
			rot = 0
			if transform_matrix[1][0] == 0: ### atan2(0.0,-0.0) returns 180, but we need 0
				psi = math.atan2(transform_matrix[1][0], transform_matrix[0][0])
			else:
				psi = math.atan2(-transform_matrix[1][0], transform_matrix[0][0])
		tilt *= 180 / math.pi
		rot *= 180 / math.pi
		psi *= 180 / math.pi
			
		return rot, tilt, psi
		
	#=====================
	#=====================
	#=====================
			
	def distanceBetweenEulers(self, t1, t2):
		R = numpy.dot(numpy.transpose(t1), t2)
		trace = R.trace()
		s = math.acos((R[0][0] + R[1][1] + R[2][2] - 1) / 2.0)
		if s == 0:
			d = 0
		else:
			d = math.fabs(s/(2*math.sin(s))) * math.sqrt((R[0][1]-R[1][0])**2 + (R[0][2]-R[2][0])**2 + (R[1][2]-R[2][1])**2)
		d = d*180/math.pi
			
		return d
		
	#=====================
	#=====================
	#=====================	
	
	def getEulerValuesForModels(self, alignparams):
		'''
		reads the Euler angle assignment for each class average in IMAGIC, transforms them based on the rotation matrix, 
		then returns an "euler_array", which contains the Euler angles for each model, for each class average, mapped to its
		original randomized assignment index
		'''
		
		### read in randomization assignments for each class average
		seq_file = open(os.path.join(self.params['rundir'], "sequences_for_angular_reconstitution.dat"), "r")
		seq_array = []
		for i in range(self.params['num_volumes']):
			sequence = seq_file.readline().strip().strip("[").strip("]")
			sequence = sequence.split(",")		
			seq_array.append(sequence)
		seq_file.close()
		
		### read in Euler angles as a tuple of (alpha, beta, gamma) for each model and store them in an euler list for each volume
		euler_array = []
		for i in range(self.params['num_volumes']):
			eulerFile = open(os.path.join(self.params['rundir'], "angular_reconstitution", "ordered"+str(i+1)+".plt"))
			eulerlist = []
			for j in range(self.params['numpart']):
				vals = eulerFile.readline().strip().split()
				eulers = (float(vals[0]), float(vals[1]), float(vals[2]))
				eulerlist.append(eulers)
			eulerFile.close()
			euler_array.append(eulerlist)

		### map Euler angles to the corresponding class average in the original template stack, according to the randomization sequence
		euler_array_mapped = []
		for i in range(self.params['num_volumes']):
			eulerdict_mapped = {}
			for j in range(self.params['numpart']):
				value = int(seq_array[i][j])
				eulers = euler_array[i][j] ### IMAGIC format starts with 1
				eulerdict_mapped[str(value)] = eulers
			euler_array_mapped.append(eulerdict_mapped)

		### apply Euler angle transformation based on alignment parameters
		euler_array_transformed = {}
		for i in range(self.params['num_volumes']):
			eulerdict_transformed = {}
			### read in rotation parameters from Xmipp doc file
			rot = float(alignparams[i][4])
			tilt = float(alignparams[i][5])
			psi = float(alignparams[i][6])
			transform_matrix = numpy.matrix(self.EulersToTransformationMatrix(rot, tilt, psi))
			
			for key, value in euler_array_mapped[i].items():
				### old Euler angles and rotation matrix
				alpha = float(value[0]) 
				beta = float(value[1])
				gamma = float(value[2])
				R1 = numpy.matrix(self.EulersToTransformationMatrix(gamma-90, beta, alpha+90))
				### get new Euler angles from the multiplied transformation matrices
				R2 = R1 * transform_matrix.I
				rot_new, tilt_new, psi_new = self.EulersFromTransformationMatrix(R2)
				### save in new dictionary
				eulerdict_transformed[key] = (rot_new, tilt_new, psi_new)
			euler_array_transformed[str(i+1)] = (eulerdict_transformed)
				
		return euler_array_transformed
	
	#=====================
	#=====================
	#=====================	
				
	def calculateMeanEulerJumpForModelClass(self, classes, euler_array_transformed):
		'''
		takes as input a dictionary of Euler values for each model along with a dictionary key for the model class containing
		separate 3D reconstructions. It then calculates, for each class average, the mean Euler angle difference (Euler jump),
		between all combinations of models within that class.  
		'''
		
		l = []
		for i in range(self.params['numpart']): ### for each class average
			for j in range(len(classes)):
				for k in range(j+1, len(classes)):
					rot1 = euler_array_transformed[str(classes[j])][str(i+1)][0]
					tilt1 = euler_array_transformed[str(classes[j])][str(i+1)][1]
					psi1 = euler_array_transformed[str(classes[j])][str(i+1)][2]
					rot2 = euler_array_transformed[str(classes[k])][str(i+1)][0]
					tilt2 = euler_array_transformed[str(classes[k])][str(i+1)][1]
					psi2 = euler_array_transformed[str(classes[k])][str(i+1)][2]
					t1 = self.EulersToTransformationMatrix(rot1, tilt1, psi1)
					t2 = self.EulersToTransformationMatrix(rot2, tilt2, psi2)
					d = apEulerCalc.computeDistance(t1,t2)
#					d = self.distanceBetweenEulers(t1,t2)
#					print "distance between average %d for volume %d and %d is %.3f" % (i+1, classes[j], classes[k], d)
					l.append(d)
		meanjump = numpy.asarray(l).mean()
		
		return meanjump
						
	#=============================															===============================
	#=============================					3D CLASS ASSESSMENT						===============================
	#=============================															===============================	
			
	def avgCCCBetweenProjectionsAndReprojections(self, classes):
		'''
		takes in a dictionary key for the model class, which contains all the separate 3D reconstructions going into class, 
		then calculates the average cross-correlation between the projections and reprojections for each separate 3D
		'''
		
		CCCs = []
		for m in classes:
			ordered_file = os.path.join(self.params['rundir'], "angular_reconstitution", "ordered%d_sort.hed" % (m))
			reproj_file = os.path.join(self.params['rundir'], "angular_reconstitution", "rep%d_ordered%d.hed" % (m, m))
			of = apImagicFile.readImagic(filename=ordered_file, msg=False)
			orderedarray = of['images']
			rf = apImagicFile.readImagic(filename=reproj_file, msg=False)
			reparray = rf['images']
			if orderedarray.shape != reparray.shape:
				apDisplay.printError("projection image file %s does not match reprojection file %s") \
					% (ordered_file, reproj_file)
			ccc = 0
			for i in range(orderedarray.shape[0]):
				ccc += self.calculate_ccs(orderedarray[i], reparray[i])[0]
			avgCCC = ccc / orderedarray.shape[0]
			CCCs.append(avgCCC)
		classCCC = sum(CCCs) / len(CCCs)

		return classCCC
	
	#=====================
	#=====================
	#=====================	
	
	def assess_3Dclass_quality(self, sim_matrix, classes, euler_array_transformed):
		''' 
		parses the similarity matrix, created either using Principal Component Analysis decomposition or 
		a simple cross-correlation criteria, then returns the best model, based on intra-class variance
		'''

		apDisplay.printColor("Parsing through resulting 3D classes to assess the quality of each 3D model", "yellow")
		
		### make ssnr directory
		if not os.path.isdir(os.path.join(self.params['rundir'], "ssnr_data")):
			os.mkdir(os.path.join(self.params['rundir'], "ssnr_data"))

		### calculate final model statistics using similarity array
		classnames = classes.keys()
		bestavg = 0
		mf = open(os.path.join(self.params['rundir'], "final_model_members.dat"), "w")
		vf = open(os.path.join(self.params['rundir'], "final_model_stats.dat"), "w")
		vf.write("modelname \t\t # members \t\t avg CCC \t\t mean Euler jump \t\t avg similarity (normalized) \t\t stdev (normalized) \t\t ssnr_res\n")
		for classnum in classnames:
			sims = []
			volarray = numpy.zeros((((len(classes[classnum]),self.params['boxsize'], self.params['boxsize'], self.params['boxsize']))))
			for i in range(len(classes[classnum])):
				for j in range(i+1, len(classes[classnum])):
					sim = sim_matrix[(classes[classnum][i]-1), (classes[classnum][j]-1)]
					sims.append(sim)
				if len(classes[classnum]) == 1:
					sims.append(1) ### when a single model is in a class, its self-similarity is 1
				volarray[i] += mrc.read(os.path.join(self.params['rundir'], "volumes", "3d%d_ordered%d_filt.mrc" % (classes[classnum][i], classes[classnum][i])))
				
			### get SSNR of volume class
			if len(classes[classnum]) == 1:
				res = self.params['apix'] * 2
			else:
				res = apFourier.spectralSNR3d(volarray, self.params['apix'])	
				os.rename(os.path.join(self.params['rundir'], "ssnr.dat"), os.path.join(self.params['rundir'], "ssnr_data", "ssnr_model_%d.dat" % (classnum)))
			
			### assess quality of class by comparing the summed CCC between projections and reprojections
			CCC = self.avgCCCBetweenProjectionsAndReprojections(classes[classnum])
				
			### assess Euler jumpers for class (mean value for ALL class averages)
			mj = self.calculateMeanEulerJumpForModelClass(classes[classnum], euler_array_transformed)
			
			### print and write to file
			normsims = self.normList(sims)
			print "volumes going into model %d.mrc: %s \n" % (classnum, classes[classnum])
			mf.write("%d.mrc: %s \n" % (classnum, classes[classnum]))
			print "model %d.mrc, %d members with average proj/reproj CCC %f, mean Euler jump %f, similarity %f, standard deviation %f, and resolution %f" \
				% (classnum, len(classes[classnum]), CCC, mj, numpy.asarray(normsims).mean(), numpy.asarray(normsims).std(), res)
			vf.write("%d.mrc \t\t %d \t\t %f \t\t %f \t\t %f \t\t %f \t\t %f\n" \
				% (classnum, len(classes[classnum]), CCC, mj, numpy.asarray(normsims).mean(), numpy.asarray(normsims).std(), res))
		mf.close()
		vf.close()
			
		return

	def upload(self):
		''' insert into database, if commit is checked '''
		
		### path object
		pathq = appiondata.ApPathData()
		pathq['path'] = self.params['rundir']

		### aar run object
		aarq = appiondata.ApBootstrappedAngularReconstitutionRunData()
		aarq['path'] = pathq
		aarq['runname'] = self.params['runname']
		### check unique run
		uniquerun = aarq.query(results=1)
		if uniquerun:
			apDisplay.printError("runname already exists in the database")
		
		### aar params object
		aarparamq = appiondata.ApBootstrappedAngularReconstitutionParamsData()
		aarparamq['num_averages'] = self.params['numpart']
		aarparamq['num_volumes'] = self.params['num_volumes']
		aarparamq['symmetry'] = appiondata.ApSymmetryData.direct_query(self.params['symid'])
		aarparamq['num_alignment_refs'] = self.params['nref']
		aarparamq['angular_increment'] = self.params['ang_inc']
		aarparamq['keep_ordered'] = self.params['keep_ordered']
		aarparamq['threed_lpfilt'] = self.params['3d_lpfilt']
		aarparamq['hamming_window'] = self.params['ham_win']
		aarparamq['non_weighted_sequence'] = self.params['non_weighted_sequence']
		aarparamq['PCA'] = self.params['PCA']
		aarparamq['numeigens'] = self.params['numeigens']
		aarparamq['prealign_avgs'] = self.params['prealign']
		aarparamq['scale'] = self.params['scale']
		aarparamq['recalculate_volumes'] = self.params['recalculate']
		aarparamq['preference_type'] = self.params['preftype']
#		aarparamq['do_not_remove'] = self.params['do_not_remove']

		### finish aar run object	
		aarq['aar_params'] = aarparamq
		aarq['pixelsize'] = self.params['apix']
		aarq['boxsize'] = self.params['boxsize']
		if self.params['templatestackid'] is not None:
			aarq['templatestackid'] = appiondata.ApTemplateStackData.direct_query(self.params['templatestackid'])
		else:
			aarq['clusterid'] = appiondata.ApClusteringStackData.direct_query(self.params['clusterid'])
		aarq['description'] = self.params['description']
		aarq['project|projects|project'] = self.params['projectid']
		aarq['hidden'] = False
		
		if self.params['commit'] is True:
			aarq.insert()
		else:
			apDisplay.printWarning("NOT commiting results to database")
			
		return

	####################################################################### 
	###																	###
	###						MAIN ALGORITHM						    	###
	###																	###
	#######################################################################	

	def start(self):
		''' 
		automated Angular Reconstitution 
		'''

		##############################################		Set Initial Parameters		##############################################

		'''
		
		self.params = {}
		rundir = "/ami/data00/appion/Dmitry_aar/test_33_70S_Frank_1000avgs_nonweighted" ; self.params['rundir'] = rundir
		os.chdir(self.params['rundir'])
		class_averages = os.path.join(self.params['rundir'], "templatestack8.img") ; self.params['avgs'] = class_averages
		self.params['numpart'] = apFile.numImagesInStack(class_averages)
		nproc = 8 ; self.params['nproc'] = nproc
		apix = 5.73 ; self.params['apix'] = apix
		boxsize = 64 ; self.params['boxsize'] = boxsize
		num_volumes = 1000 ; self.params['num_volumes'] = num_volumes
		symid = 25 ; self.params['symid'] = symid
		nref = 1 ; self.params['nref'] = nref
		ang_inc = 2 ; self.params['ang_inc'] = ang_inc
		keep_ordered = 80 ; self.params['keep_ordered'] = keep_ordered
		lp_filt = 10 ; self.params['3d_lpfilt'] = lp_filt
		ham_win = 0.8 ; self.params['ham_win'] = ham_win
		non_weighted_sequence = True; self.params['non_weighted_sequence'] = non_weighted_sequence
		PCA = True ; self.params['PCA'] = PCA
		scale = True ; self.params['scale'] = scale
		recalculate = False ; self.params['recalculate'] = recalculate
		preftype = "minimum" ; self.params['preftype'] = preftype
		do_not_remove = False ; self.params['do_not_remove'] = do_not_remove

		'''

		### get initial parameters and copy class averages into working directory
		if self.params['templatestackid'] is not None:
			stackdata = appiondata.ApTemplateStackData.direct_query(self.params['templatestackid'])
			clsname = stackdata['templatename']
			self.params['apix'] = stackdata['apix']
			self.params['boxsize'] = stackdata['boxsize']
		elif self.params['clusterid'] is not None:
			stackdata = appiondata.ApClusteringStackData.direct_query(self.params['clusterid'])
			clsname = stackdata['avg_imagicfile']
			self.params['apix'] = stackdata['clusterrun']['pixelsize']
			self.params['boxsize'] = stackdata['clusterrun']['boxsize']
		self.params['avgs'] = os.path.join(self.params['rundir'], clsname)
		shutil.copyfile(os.path.join(stackdata['path']['path'], clsname[:-4]+".hed"), self.params['avgs'][:-4]+".hed")
		shutil.copyfile(os.path.join(stackdata['path']['path'], clsname[:-4]+".img"), self.params['avgs'][:-4]+".img")
		apIMAGIC.copyFile(self.params['rundir'], clsname, headers=True)
		self.params['numpart'] = apFile.numImagesInStack(self.params['avgs'])

		#######################################		scale class averages, if necessary		##########################################

		### scale class averages to 64x64, if scaling is specified
		if self.params['scale'] is True:
			scalefactor = float(64.0 / self.params['boxsize'])
			self.params['apix'] = self.params['apix'] / scalefactor
			self.params['boxsize'] = 64
			emancmd = "proc2d %s %s_scaled.img scale=%.3f clip=%i,%i,%i edgenorm" \
				% (self.params['avgs'], self.params['avgs'][:-4], scalefactor, 64, 64, 64)
			self.params['avgs'] = self.params['avgs'][:-4]+"_scaled.img"
			while os.path.isfile(self.params['avgs']):
				apFile.removeStack(self.params['avgs'])
			apParam.runCmd(emancmd, "EMAN")
			
		if self.params['prealign'] is True:
			self.params['avgs'] = self.prealignClassAverages()
		
		'''
		
		##############################################		create multiple 3d0s		##############################################

		apDisplay.printColor("Calculating similarity matrix", "cyan")
		ccc_matrix = self.calculate_ccc_matrix_2d(self.params['avgs'])
		angrecondir = os.path.join(self.params['rundir'], "angular_reconstitution")
		clsavgs = os.path.split(self.params['avgs'])[1][:-4]
		if not os.path.isdir(angrecondir):
			os.mkdir(angrecondir)
		if not os.path.islink(os.path.join(angrecondir, clsavgs+".hed")):
			os.symlink(os.path.join(self.params['rundir'], clsavgs+".hed"), os.path.join(angrecondir, clsavgs+".hed"))
		if not os.path.islink(os.path.join(angrecondir, clsavgs+".img")):
			os.symlink(os.path.join(self.params['rundir'], clsavgs+".img"), os.path.join(angrecondir, clsavgs+".img"))

		cmdlist = []
		seqfile = open(os.path.join(self.params['rundir'], "sequences_for_angular_reconstitution.dat"), "w")
		apDisplay.printColor("Running multiple IMAGIC 3d0 creations", "cyan")
		for i in range(self.params['num_volumes']):
			sequence = self.calculate_sequence_of_addition(self.params['avgs'], ccc_matrix)
			seqfile.write(str(sequence)+"\n")
			### create IMAGIC batch file for each model construction & append them to be threaded
			batchfile = self.imagic_batch_file(sequence, i+1)
			proc = subprocess.Popen('chmod 755 '+batchfile, shell=True)
			proc.wait()
			cmdlist.append(batchfile)
			os.chdir(self.params['rundir'])
		seqfile.close()
		apThread.threadCommands(cmdlist, nproc=self.params['nproc'], pausetime=100)
			
		### check for errors after execution
		for i in range(self.params['num_volumes']):
			apIMAGIC.checkLogFileForErrors(os.path.join(self.params['rundir'], "angular_reconstitution", "3d"+str(i+1)+".log"))
				
		#####################################   convert 3-D models to SPIDER format for Xmipp   ######################################
					
		### create volume directory
		volumedir = os.path.join(self.params['rundir'], "volumes")
		if not os.path.isdir(volumedir):
			os.mkdir(volumedir)

		### move volumes into volume directory		
		apDisplay.printColor("Converting IMAGIC volumes to Spider format for Xmipp 3-D Maximum Likelihood", "cyan")	
		emancmds = []
		for i in range(self.params['num_volumes']):
			volume1 = os.path.join(self.params['rundir'], "angular_reconstitution", "3d"+str(i+1)+"_ordered"+str(i+1)+"_filt.vol")
			volume2 = os.path.join(volumedir, "3d"+str(i+1)+"_ordered"+str(i+1)+"_filt.vol")
			shutil.move(volume1, volume2)
			
		##############################################			align 3-D models		##############################################
							
		### run Maximum Likelihood 3-D alignment & align resulting volumes
		apDisplay.printColor("Running Xmipp maximum likelihood 3-D alignment", "cyan")
		vol_doc_file = self.xmipp_max_like_3d_align()
		alignparams = self.read_vol_doc_file(vol_doc_file)
		apDisplay.printColor("Aligning volumes based on 3-D ML parameters", "cyan")
		self.align_volumes(alignparams)

		'''

		##############################################    Principal Component Analysis   #############################################
		vol_doc_file = os.path.join(self.params['rundir'], "max_like_alignment", "nref1_15deg_it000005.doc")
		alignparams = self.read_vol_doc_file(vol_doc_file)
		apDisplay.printColor("Calculating inter-volume similarity", "cyan")
		if self.params['PCA'] is True:
			simfile, sim_matrix = self.runPrincipalComponentAnalysis(recalculate=self.params['recalculate'])
		else:
			simfile, sim_matrix = self.calculate_ccc_matrix_3d()
				
		##############################################    3-D affinity propagation		##############################################

		### 3-D Affinity Propagation
		apDisplay.printColor("Averaging volumes with Affinity Propagation", "cyan")
		preffile = self.set_preferences(sim_matrix, self.params['preftype'])
		classes = self.run_affinity_propagation(simfile, preffile)
		
		### final model assessment
		euler_array = self.getEulerValuesForModels(alignparams)
		self.assess_3Dclass_quality(sim_matrix, classes, euler_array)

		### upload to database, if specified
		self.upload()

if __name__ == "__main__":

#	appiondata.sinedon.setConfig("appiondata", db="ap218")
	AAR = automatedAngularReconstitution()
	AAR.start()
	AAR.close()
	
	
