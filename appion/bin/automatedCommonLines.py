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
import glob
import shutil
import subprocess
import operator

#appion
from appionlib import appionScript
from appionlib import appiondata
from appionlib import apChimera
from appionlib import apEulerCalc
from appionlib import apImagicFile
from appionlib import apDisplay
from appionlib import apFile
from appionlib import apFourier
from appionlib import apRecon
from appionlib import apIMAGIC
from appionlib import apSymmetry
from appionlib import apParam
from appionlib import apThread
from appionlib import apXmipp
from appionlib import apXmippProtocolsProjMatchBasic as xp
from appionlib import apCommonLines

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
		self.parser.set_defaults(nproc=1)
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
		self.parser.add_option("--non_weighted_sequence", dest="non_weighted_sequence", default=False, action="store_true",
			help="if this is specified, then the sequence of addition into angular reconstitution will \
				be completely randomized, rather than weighted and randomized")
		self.parser.add_option("--asqfilter", dest="asqfilt", default=False, action="store_true",
				help="ASQ filtering means Amplitude-Square-Root and is described \
				in papers, like: Marin van Heel, Michael Schatz, and Elena Orlova, 'Correlation \
				Functions Revisited', Ultramicroscopy 46 (1992) 304-316. This filtering is important \
				if one does not want the sinogram (and a sine-correlation-function derived from it) \
				to be largely dominated by low-frequency information. The ASQ filter functions largely \
				as a high-pass filter but is based on a rather different philosophy (see paper).", metavar="BOOL")		
		self.parser.add_option("--linear_mask", dest="linmask", type="float", default=0,
			help="Radius of the linear mask (in Angstroms) to be imposed on the sinogram and within which the statistics will be calculated \
				for the normalization of the sinograms. For best results, this value should be exactly 1/2 * the diameter of your \
				particle. For example, for a particle of diameter 200 Angstroms, this value should be 100. For NO masking answer '0'", \
				metavar="FLOAT")
		self.parser.add_option("--first_image", dest="firstimage", type="int", default=None,
			help="specify the first image (numbering starts with 0) to be used during C1 startup, rather than randomizing", metavar="INT")
		self.parser.add_option("--symmetry", dest="symid", type="int", default=1,
			help="symmetry of the object (ID from Appion Database). This is automatically defaulted to the suggested C1 symmetry", metavar="INT")
		self.parser.add_option("--num_volumes", dest="num_volumes", type="int",
			help="number of volumes to create using angular reconstitution", metavar="INT")
		self.parser.add_option("--ang_inc", dest="ang_inc", type="int", default=2,
			help="angular increment for Euler search within the sinogram", metavar="INT")
		self.parser.add_option("--keep_ordered", dest="keep_ordered", type="int", default=90,
			help="percentage of the best class averages to keep for the actual 3D reconstruction. \
				This value is determined by the error in angular reconstitution for each input class average", metavar="INT")
			
		### 3D refinement
		self.parser.add_option("--mask_radius", dest="mask_radius", type="int",
			help="Radius of the mask for the refinement of the initial volume calculated by angular reconstitution (Angstroms). \
				For best results, this value should be slightly larger than the diameter of your particle (e.g. for a 200 \
				Angstrom particle, this value can be ~240/2 ~= 120 Angstroms). The default value is 'linear_mask' parameter * 1.2", \
				metavar="INT")
		self.parser.add_option("--inner_radius", dest="inner_radius", type="int", default=0,
			help="inner radius for the alignment search of volume refinement (Angstroms)", metavar="INT")
		self.parser.add_option("--outer_radius", dest="outer_radius", type="int",
			help="outer radius for the alignment search during volume refinement (Angstroms). \
				The default value is 'mask_radius'*0.8", metavar="INT")		
		self.parser.add_option("--mass", dest="mass", type="int", 
			help="mass of particle (in kDa). this is ONLY necessary for the chimera snapshots", metavar="INT")	
	
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
			help="number of 3D Eigenvectors (Eigenvolumes) to create during Principal Component Analysis for data reduction", metavar="INT")
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

		### Final model evaluation
		self.parser.add_option("--presumed_symid", dest="presumed_sym", type="str", default=1,
			help="presumed symmetry id of the particles. This is ONLY used in the calculation of Euler jumpers during \
				the evaluation of the final model and does not affect the volumes in any way. It's defaulted to c1, but \
				if your particles have high symmetry, then the Euler jumper angles will come out higher than what they should \
				be and may affect the selection of optimal models. IDs refer to database entries.", metavar="INT")
		
		### Miscellaneous
		self.parser.add_option("--do_not_remove", dest="do_not_remove", default=False, action="store_true",
			help="specify if you want to keep miscellaneous files associated with angular reconstitution (e.g. sinograms) \
				NOTE: keeping these files takes up huge amounts of diskspace")
		self.parser.add_option("--memory", dest="memory", default='2gb',
			help="This is only for the storage of the references, which is usually not necessary to modify for small stacks")
							
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

		### class average parameters
		if self.params['templatestackid'] is not None:
			self.stackdata = appiondata.ApTemplateStackData.direct_query(self.params['templatestackid'])
			self.clsname = self.stackdata['templatename']
			self.params['apix'] = self.stackdata['apix']
			self.params['boxsize'] = self.stackdata['boxsize']
		elif self.params['clusterid'] is not None:
			self.stackdata = appiondata.ApClusteringStackData.direct_query(self.params['clusterid'])
			self.clsname = self.stackdata['avg_imagicfile']
			self.params['apix'] = self.stackdata['clusterrun']['pixelsize']
			self.params['boxsize'] = self.stackdata['clusterrun']['boxsize']
		self.params['avgs'] = os.path.join(self.params['rundir'], os.path.basename(self.clsname))
		self.params['numpart'] = apFile.numImagesInStack(os.path.join(self.stackdata['path']['path'], self.clsname))
			
		### check for scaling
		self.params['refineapix'] = self.params['apix']
		self.params['refineboxsize'] = self.params['boxsize']		
		if self.params['scale'] is True:
			self.scalefactor = float(64.0 / self.params['boxsize'])
			self.params['apix'] = self.params['apix'] / self.scalefactor
			self.params['boxsize'] = 64	
		else:
			self.scalefactor = 1

		### check for basic input parameters
		if self.params['templatestackid'] is None and self.params['clusterid'] is None:
			apDisplay.printError("enter either a template stack ID or a cluster ID for the run")
		if self.params['templatestackid'] is not None and self.params['clusterid'] is not None:
			apDisplay.printError("please specify EITHER a template stack id OR a cluster id, not both")
		if self.params['num_volumes'] is None:
			apDisplay.printError("please specify the number of volumes that you wish to produce from the class averages")
			
		### angular reconstitution checks
		if self.params['keep_ordered'] < 1.0: 											### probably specified as a fraction
			self.params['keep_ordered'] = self.params['keep_ordered'] * 100	### convert to percentage
		self.params['keep_ordered_num'] = self.params['numpart'] * self.params['keep_ordered'] / 100
			
		### number of processors for threading ONLY works on a single node
		threadnproc = apParam.getNumProcessors()
		if self.params['nproc'] > threadnproc:
			self.params['threadnproc'] = threadnproc
		else:
			self.params['threadnproc'] = self.params['nproc']
			
		### refinement parameters
		if self.params['mask_radius'] is None and self.params['linmask'] != 0:
			self.params['mask_radius'] = self.params['linmask'] * 1.2
		elif self.params['mask_radius'] is None and self.params['linmask'] == 0:
			self.params['mask_radius'] = self.params['boxsize'] * self.params['refineapix']
		if self.params['outer_radius'] is None:
			self.params['outer_radius'] = self.params['mask_radius'] * 0.8

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

	def calculate_ccc_matrix_3d(self, volumedict):
		'''
		for each volume calculates a cross-correlation coefficient to each successive volume, then 
		returns a file corresponding to cross-correlation coefficients between the images. 
		'''
		
		apDisplay.printMsg("Creating cross-correlation similarity matrix for affinity propagation ...")		
			
		### create a similarity matrix using cross-correlation of aligned 3-D models
		self.params['rundir'] = os.getcwd()
		cc_matrix = numpy.ones((self.params['num_volumes'], self.params['num_volumes']))

		### create cross-correlation similarity matrix
		for i in range(len(volumedict)):
			for j in range(i+1, len(volumedict)):		
				model1 = mrc.read(volumedict[i+1])
				model2 = mrc.read(volumedict[j+1])
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
	
	def create_difference_matrix(self, ccc_matrix, norm=False):
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
	#=====================
	#=====================	

	def calculate_sequence_of_addition(self, avgs, ccc_matrix, first=None, normlist=False):
		''' 
		calculates a unique sequence of addition of class averages. function first initializes a random seed, then calculates
		the rest of the sequence based on the resulting weighted probability matrix generated from each successive addition
		NOTE: image numbering starts with 0!
		'''
			
		### initialize sequence (image queue) and weight matrix, which determines sequence calculation
		probability_list = numpy.zeros(self.params['numpart'])
		sequence = []
			
		### if completely random sequence is desired, do that here
		if self.params['non_weighted_sequence'] is True:
			apDisplay.printMsg("calculating random sequence of image addition")
			im_list = []
			for i in range(self.params['numpart']):
				im_list.append(i)		
			while im_list:
				r = numpy.random.randint(len(im_list))
				sequence.append(im_list[r]+1)
				del im_list[r]
			return sequence
			
		else:	
			apDisplay.printMsg("calculating weighted randomized sequence of image addition")
			### otherwise randomize first image selection and continue with weighted selection
			im_queue = []
			for i in range(self.params['numpart']):
				im_queue.append(i)
			if first != None and isinstance(first, int):
				im_init = first
			else:
				im_init = numpy.random.randint(low=0, high=self.params['numpart'])

			### create probability matrix from ccc matrix and append new image
			diff_matrix = self.create_difference_matrix(ccc_matrix, norm=False)
			probability_list = self.create_probability_list(im_init, probability_list, diff_matrix)
			sequence.append(im_init+1)

			### figure out the rest of the sequence, based on the first randomly selected image
			for image in range(len(im_queue)-1):
				next_choice = self.weighted_random_pick(im_queue, probability_list)
				probability_list = self.update_probability_list(next_choice, probability_list, diff_matrix)
				
				### check to make sure that the probability list does not contain all zeros (in which case there are duplicate images)
				break_weighted_randomization = False
				for item in probability_list:
					if sum(probability_list) == 0:
						break_weighted_randomization = True ### do not weight randomization, just add the remaining images
						for i in range(len(im_queue)):
							if i+1 not in sequence:
								sequence.append(i+1)
								
				if break_weighted_randomization is True:
					break
				if normlist is True:
					probability_list = self.normList(probability_list)
				sequence.append(next_choice+1)
				
			return sequence

	#=====================
	#=====================
	#=====================
		
	def create_probability_list(self, selection, probability_list, diff_matrix):
		''' creates the list that stores probability values used for weighted randomized selection '''
		
		for i in range(len(probability_list)):
			probability_list[i] += diff_matrix[i][selection]
#			if probability_list[i] == 0: ### slightly perturb to avoid identical selections in sequence
#				probability_list[i] = 0 + numpy.random.uniform(0,1) * 0.000001			
		return probability_list
		
	#=====================
	#=====================
	#=====================
		
	def update_probability_list(self, selection, probability_list, diff_matrix):
		''' updates the list that stores probability values used for weighted randomized selection '''

		for i in range(len(probability_list)):
			if probability_list[i] != 0:
				probability_list[i] *= diff_matrix[i][selection]
		probability_list[selection] = 0 ### don't use this selection anymore

		return probability_list

	#=====================
	#=====================
	#=====================

	def weighted_random_pick(self, im_queue, probability_list):
		''' 
		based on the given probabilities of the existing choices, this function determines what the next image will be. 
		It uses a weighted randomized decision-making strategy that takes into account how different the images are from each other
		'''
		
		weight_total = sum((p for p in probability_list))
		n = numpy.random.uniform(0, weight_total)
		cumulative_p = 0.0
		for image, image_probability in zip(im_queue, probability_list):
			cumulative_p += image_probability
			if n < cumulative_p: break
					
		return image
			
	def check_for_duplicates_in_sequence(self, sequence):
		### make sure that the sequence does not contain duplicate selections
		for j, s1 in enumerate(sequence):
			for k, s2 in enumerate(sequence):
				if j == k: pass
				else:
					if s1 == s2:
						apDisplay.printError("%d, %d, equivalent values in final sequence" % (s1, s2))
		return			
		
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
			
		### this is the actual alignment
		f.write(str(self.imagicroot)+"/align/alirefs.e <<EOF >> prealignClassAverages.log\n")
		f.write("ALL\n")
		f.write("CCF\n")
		f.write(str(os.path.basename(self.params['avgs'])[:-4])+"\n") 
		f.write("NO\n")
		f.write("0.99\n")
		f.write(str(os.path.basename(self.params['avgs'])[:-4])+"_aligned\n")
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
		if self.params['asqfilt'] is True:
			f.write("yes\n")
		else:
			f.write("no\n")
		f.write("%.3f\n" % (self.params['linmask'] / self.params['apix'] / self.params['boxsize'] * 2))
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
				if self.params['asqfilt'] is True:
					f.write("yes\n")
				else:
					f.write("no\n")
				f.write("%.3f\n" % (self.params['linmask'] / self.params['apix'] / self.params['boxsize'] * 2))
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
			if self.params['asqfilt'] is True:
				f.write("yes\n")
			else:
				f.write("no\n")
			f.write("%.3f\n" % (self.params['linmask'] / self.params['apix'] / self.params['boxsize'] * 2))
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
		f.write("%i\n" % (self.params['keep_ordered_num']))	
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
		f.write("ordered"+str(iteration)+"_Eulers.plt\n")
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
	
	def refine_volume(self, volnum):
		''' Xmipp projection-matching based refinement of volume generated by common lines '''
		
		basedir = os.path.abspath(os.getcwd())
		rundir = os.path.join(basedir, "refine_%d" % volnum)
		if not os.path.isdir(rundir):
			os.mkdir(rundir)
	
		### set projection-matching parameters
		SelFileName = "partlist.sel"
		ReferenceFileName = os.path.join(self.params['rundir'], "refinement", "%d.vol" % volnum)
		WorkingDir = os.path.basename(rundir)
		ProjectDir = os.getcwd()
		MaskRadius = self.params['mask_radius'] / self.params['refineapix']   # in pixels
		InnerRadius = self.params['inner_radius'] / self.params['refineapix'] # in pixels
		OuterRadius = self.params['outer_radius'] / self.params['refineapix'] # in pixels
		AvailableMemory = self.params['memory']
		ResolSam = self.params['refineapix']
		NumberOfMpiProcesses = self.params['nproc']

		### optional parameters
		NumberofIterations = 12
		AngSamplingRateDeg = '4x10 4x5 4x3 2x2 2x1'
		MaxChangeInAngles = '4x1000 4x20 4x9 2x6 2x3'
		MaxChangeOffset = '4x1000 4x10'
		Search5DShift = '4x5 1'
		Search5DStep = '4x2 1'
		FourierMaxFrequencyOfInterest = '0.35'
		ConstantToAddToFiltration = '0.35'

		### do projection-matching
		apDisplay.printColor("refining volume %d by projection-matching" % volnum, "cyan")

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
					_ConstantToAddToFiltration=ConstantToAddToFiltration
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
		self.refinement_quality_criteria(count)

		### link / summarize final files
		if not os.path.isfile(os.path.join(rundir, "3d%d_refined.vol" % volnum)):
			os.symlink(os.path.join("Iter_%d" % count, "Iter_%d_reconstruction.vol" % count), \
				os.path.join(rundir, "3d%d_refined.vol" % volnum))
		if not os.path.isfile(os.path.join(rundir, "3d%d_refined.frc" % volnum)):
			os.symlink(os.path.join("Iter_%d" % count, "reconstruction_2.vol.frc"), \
				os.path.join(rundir, "3d%d_refined.frc" % volnum))
		if not os.path.isfile(os.path.join(rundir, "3d%d_refined_projections.hed" % volnum)):
			os.symlink(os.path.join("Iter_%d" % count, "Iter_%d_projections_noflip.hed" % count), \
				os.path.join(rundir, "3d%d_refined_projections.hed" % volnum))
		if not os.path.isfile(os.path.join(rundir, "3d%d_refined_projections.img" % volnum)):
			os.symlink(os.path.join("Iter_%d" % count, "Iter_%d_projections_noflip.img" % count), \
				os.path.join(rundir, "3d%d_refined_projections.img" % volnum))
		apXmipp.removeMirrorFromDocfile(os.path.join(rundir, "Iter_%d" % count, "Iter_%d_current_angles.doc" % count), \
			os.path.join(rundir, "3d%d_refined_angles.doc" % volnum))
		avgs = apImagicFile.readImagic(self.params['refineavgs'])['images']
		repjs = apImagicFile.readImagic(os.path.join(rundir, "3d%d_refined_projections.hed" % volnum))['images']
		comparison = []
		for i in range(len(avgs)):
			comparison.append(avgs[i])
			comparison.append(repjs[i])
		apImagicFile.writeImagic(comparison, os.path.join(rundir, "clsavg_reprojection_comparison.hed"))
		
		os.chdir(basedir)
		
		return
	
	#=====================
	#=====================
	#=====================
	
	def refinement_quality_criteria(self, iteration):
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
		f.write("%d %d\n" % (self.params['refineboxsize'], self.params['refineboxsize']))
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
		apXmipp.gatherSingleFilesIntoStack("Iter_%d_projections_noflip.sel" % iteration, "Iter_%d_projections_noflip.hed" % iteration)

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
		
		time.sleep(5) # bugfix for not executing split command
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
			% (self.params['nproc'], iteration, self.params['nproc'])
		apParam.runCmd(reconcmd1, "Xmipp")
		reconcmd2 = "mpirun -np %d xmipp_mpi_reconstruct_fourier -i reconstruction_2.sel -o reconstruction_2.vol -sym c1 -doc Iter_%d_current_angles_2.doc -thr %d" \
			% (self.params['nproc'], iteration, self.params['nproc'])			
		apParam.runCmd(reconcmd2, "Xmipp")
		fsccmd = "xmipp_resolution_fsc -ref reconstruction_1.vol -i reconstruction_2.vol -sam %.3f" % self.params['refineapix']
		apParam.runCmd(fsccmd, "Xmipp")
#		fsc = apRecon.getResolutionFromGenericFSCFile("reconstruction_2.vol.frc", self.params['boxsize'], self.params['apix'])
		
		os.chdir(basedir)
		return
	
	#=====================
	#=====================
	#=====================
	
	def xmipp_max_like_3d_align(self, volumedict):
		''' 3-D maximum likelihood alignment of all models resulting from iterative 3d0 creation '''
		
		### create necessary input .sel & .doc files
		selfile = open(os.path.join(self.params['rundir'], "volumes.sel"), "w")
		for v in sorted(volumedict):
			selfile.write("%s 1\n" % volumedict[v])
		selfile.close()
		docfile = open(os.path.join(self.params['rundir'], "volumes.doc"), "w")
		for v in sorted(volumedict):
			docfile.write(" ; %s\n" % volumedict[v])
			docfile.write(str(v)+" 10 0 0 0 0 0 0 0 0 0 0\n")
		docfile.close()
		
		### run 3-D maximum-likelihood alignment
		rundir = os.path.join(self.params['rundir'], "max_like_alignment")
		if not os.path.isdir(rundir):
			os.mkdir(rundir)
		if self.params['nproc'] > 1:
			xmippcmd1 = "mpirun -np %d xmipp_mpi_ml_tomo " % self.params['nproc']
		else:
			xmippcmd1 = "xmipp_ml_tomo "
		xmippcmd1+= "-i volumes.sel -o max_like_alignment/nref%d_15deg " % self.params['nref']
		xmippcmd1+= "-nref %d -doc volumes.doc -iter 5 -ang 15 -dim 32 -perturb" % self.params['nref']
		if self.params['threadnproc'] > 1:
			xmippcmd1 += " -thr "+str(self.params['threadnproc'])
		apParam.runCmd(xmippcmd1, package="Xmipp")
		'''
		if self.params['nproc'] > 1:
			xmippcmd2 = "mpirun -np %d xmipp_mpi_ml_tomo " % self.params['nproc']
		else:
			xmippcmd2 = "xmipp_ml_tomo "
		xmippcmd2+= "-i volumes.sel -o max_like_alignment/nref%d_10deg " % self.params['nref']
		xmippcmd2+= "-nref %d -doc max_like_alignment/nref%d_15deg_it000005.doc -keep_angles " % (self.params['nref'], self.params['nref']) 
		xmippcmd2+= "-iter 5 -ang 10 -ang_search 50 -maxres 0.35 -perturb"
		if self.params['threadnproc'] > 1:
			xmippcmd2 += " -thr "+str(self.params['threadnproc'])			
		apParam.runCmd(xmippcmd2, package="Xmipp")

		if self.params['nproc'] > 1:
			xmippcmd3 = "mpirun -np %d xmipp_mpi_ml_tomo " % self.params['nproc']
		else:
			xmippcmd3 = "xmipp_ml_tomo "
		xmippcmd3+= "-i volumes.sel -o max_like_alignment/nref%d_5deg " % self.params['nref']
		xmippcmd3+= "-nref %d -doc max_like_alignment/nref%d_10deg_it000005.doc -keep_angles " % (self.params['nref'], self.params['nref'])
		xmippcmd3+= "-iter 5 -ang 5 -ang_search 25 -maxres 0.35 -perturb"
		if self.params['threadnproc'] > 1:
			xmippcmd3 += " -thr "+str(self.params['threadnproc'])
		apParam.runCmd(xmippcmd3, package="Xmipp")
		'''
#
#		ANGULAR INCREMENT SET TO 15
#
		### check for all iterations, just in case Xmipp ended early, sometimes it converges before 5th iteration
		i = 5
		while i > 0:
			vol_doc_file = os.path.join(rundir, "nref%d_15deg_it00000%d.doc") % (self.params['nref'], i)
			alignref = os.path.join(rundir, "nref%d_15deg_it00000%d_ref000001.vol") % (self.params['nref'], i)
			if os.path.isfile(vol_doc_file):
				return vol_doc_file, alignref
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
		
	def align_volumes(self, alignparams, alignref):
		''' align the volumes to the resulting reference from maximum-likelihood '''
		
		transcmds = []
		rotcmds = []
		emancmds = []
		for i in range(self.params['num_volumes']):
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
			emancmd = "proc3d "+str(alignparams[i][0])+" "+str(alignparams[i][0])[:-4]+".mrc apix="+str(self.params['apix'])
			emancmds.append(emancmd)
		apThread.threadCommands(transcmds, nproc=self.params['threadnproc'], pausetime=10)
		apThread.threadCommands(rotcmds, nproc=self.params['threadnproc'], pausetime=10)
		apThread.threadCommands(emancmds, nproc=self.params['threadnproc'], pausetime=10)
			
		return
		
	#=====================
	#=====================
	#=====================

	def runPrincipalComponentAnalysis(self, volumedict, recalculate=False):
		''' 
		runs principal component analysis to reduce dimensionality of dataset and returns the correlation file
		corresponding to the similarity of each point in factor space
		'''
		
		### default number of eigenvolumes
		self.params['rundir'] = os.getcwd()
		if self.params['num_volumes'] < 69:
			numeigens = self.params['num_volumes']
		else:
			numeigens = self.params['numeigens']
		apDisplay.printMsg("using %d Eigenvectors (Eigenvolumes) to reduce dimensionality of dataset and calculate volume similarities" % (numeigens))
			
		### create input array from all volumes 	
		volumes = numpy.empty([self.params['num_volumes'], self.params['boxsize'], self.params['boxsize'], self.params['boxsize']])
		for v in sorted(volumedict):
			vol = mrc.read(volumedict[v])
			volumes[(v-1)] += vol
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
#		sim_matrix = numpy.where(diff_matrix != 0, 1/diff_matrix, 1) ### this doesn't work very well
		max = diff_matrix.max()
		min = numpy.where(diff_matrix > 0, diff_matrix, max).min()
		norm_diff_matrix = numpy.where(diff_matrix > 0, (diff_matrix - (min))/(max-min), 0)
		sim_matrix = numpy.where(norm_diff_matrix >= 0, 1-norm_diff_matrix, 0)
					
		### write similarities (CCCs) to file 
		apDisplay.printMsg("writing similarities to file CCCs_3d.dat")
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
		preffile = os.path.join(self.params['rundir'], 'affinity_propagation_preferences.dat')
		apDisplay.printMsg("Dumping preference value to file")
		f = open(preffile, 'w')
		for i in range(0,self.params['num_volumes']):
			f.write('%.10f\n' % (prefvalue))
		f.close()
		
		return preffile
		
	#=====================
	#=====================
	#=====================
	
	def run_affinity_propagation(self, volumedict, simfile, preffile):
		''' Use Affinity Propagation to classify and average all aligned 3-D models '''
		
		apDisplay.printMsg("running Affinity Propagation on aligned 3-D models")

		### run Affinity Propagation
		apclusterexe = "apcluster.exe"
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
				avgclass += mrc.read(volumedict[member])
#				avgclass += mrc.read(os.path.join(self.params['rundir'], "volumes", "3d"+str(member)+"_ordered"+str(member)+"_filt.mrc"))
			avgclass = avgclass / num_members
			mrc.write(avgclass, os.path.join(self.params['rundir'], (str(classnum)+".mrc")), header)
					
		return classes
		
	#=============================															===============================
	#=============================					EULER ANGLE FUNCTIONS					===============================
	#=============================															===============================
			
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
			eulerFile = open(os.path.join(self.params['rundir'], "angular_reconstitution", "ordered"+str(i+1)+"_Eulers.plt"))
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
	#=====================
	#=====================	
				
	def calculateMeanEulerJumpForModelClass(self, classes, euler_array_transformed):
		'''
		takes as input a dictionary of Euler values for each model along with a dictionary key for the model class containing
		separate 3D reconstructions. It then calculates, for each class average, the mean Euler angle difference (Euler jump),
		between all combinations of models within that class.  
		'''
		
		l = []
		if apSymmetry.findSymmetry(self.params['presumed_sym'])['symmetry'].lower() == "c1":
			symmetry = "c1"
		elif apSymmetry.findSymmetry(self.params['presumed_sym'])['symmetry'].lower() == "oct":
			symmetry = "oct"
		else:
			try:
				symmetry = apSymmetry.findSymmetry(self.params['presumed_sym'])['symmetry'].lower().split()[0]
			except:
				symmetry = "c1"

		for i in range(self.params['numpart']): ### for each class average
			for j in range(len(classes)):
				if len(classes) == 1:
					l.append(0)
				else:
					for k in range(j+1, len(classes)):
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
#							d = apEulerCalc.computeDistance(t1,t2)
							d = apEulerCalc.eulerCalculateDistance(e1, e2, inplane=True)
						else:
							d = apEulerCalc.eulerCalculateDistanceSym(e1, e2, sym=symmetry, inplane=True)
						l.append(d)
		meanjump = numpy.asarray(l).mean()
		
		return meanjump
						
	#=============================															===============================
	#=============================					3D CLASS ASSESSMENT				===============================
	#=============================															===============================	
			
	def avgCCCBetweenProjectionsAndReprojections(self, classes, ordered_file, reproj_file):
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
				ccc += self.calculate_ccs(orderedarray[i], reparray[i])[0]
			avgCCC = ccc / orderedarray.shape[0]
			CCCs.append(avgCCC)
		classCCC = sum(CCCs) / len(CCCs)

		return classCCC
	
	#=====================
	#=====================
	#=====================			
	
	def assess_3Dclass_quality(self, voldict, sim_matrix, classes, euler_array_transformed):
		''' assesses each model based on multiple criteria '''

		apDisplay.printColor("Parsing through resulting 3D classes to assess the quality of each 3D model", "yellow")
		
		### make ssnr directory
		if not os.path.isdir(os.path.join(self.params['rundir'], "ssnr_data")):
			os.mkdir(os.path.join(self.params['rundir'], "ssnr_data"))

		### calculate final model statistics using similarity array
		classnames = classes.keys()
		bestavg = 0
		mf = open(os.path.join(self.params['rundir'], "final_model_members.dat"), "w")
		vf = open(os.path.join(self.params['rundir'], "final_model_stats.dat"), "w")
		vf.write("%9s %5s %8s %8s %8s %8s %8s\n" \
			% ("MODEL", "NUM", "CCPR", "EJ", "CCC", "STDEV", "SSNR"))		
		for classnum in classnames:
			sims = []
			volarray = numpy.zeros((((len(classes[classnum]),self.params['boxsize'], self.params['boxsize'], self.params['boxsize']))))
			for i in range(len(classes[classnum])):
				for j in range(i+1, len(classes[classnum])):
					sim = sim_matrix[(classes[classnum][i]-1), (classes[classnum][j]-1)]
					sims.append(sim)
				if len(classes[classnum]) == 1:
					sims.append(1) ### when a single model is in a class, its self-similarity is 1
				volarray[i] += mrc.read(voldict[classes[classnum][i]])
#				volarray[i] += mrc.read(os.path.join(self.params['rundir'], "volumes", "3d%d_ordered%d_filt.mrc" % (classes[classnum][i], classes[classnum][i])))
				
			### get SSNR of volume class
			if len(classes[classnum]) == 1:
				res = self.params['apix'] * 2
			else:
				res = apFourier.spectralSNR3d(volarray, self.params['apix'])	
				os.rename(os.path.join(self.params['rundir'], "ssnr.dat"), os.path.join(self.params['rundir'], "ssnr_data", "ssnr_model_%d.dat" % (classnum)))
			
			### assess quality of class by comparing the summed CCC between projections and reprojections
#			ordered_file = os.path.join(self.params['rundir'], "angular_reconstitution", "ordered%d_sort.hed" % (m))
#			reproj_file = os.path.join(self.params['rundir'], "angular_reconstitution", "rep%d_ordered%d.hed" % (m, m))
			ordered_file = self.params['avgs']
			reproj_file = os.path.join(
				self.params['rundir'], "angular_reconstitution", "refine_%d" % m, "3d%d_refined_projections.hed" % m
				)
			CCC = self.avgCCCBetweenProjectionsAndReprojections(classes[classnum], ordered_file, reproj_file)
				
			### assess Euler jumpers for class (mean value for ALL class averages)
			mj = self.calculateMeanEulerJumpForModelClass(classes[classnum], euler_array_transformed)
			
			### print and write to file
			normsims = self.normList(sims)
			print "volumes going into model %d.mrc: %s \n" % (classnum, classes[classnum])
			mf.write("%d.mrc: %s \n" % (classnum, classes[classnum]))
			print "model %d.mrc, %d members with average proj/reproj CCC %f, mean Euler jump %f, similarity %f, standard deviation %f, and resolution %f" \
				% (classnum, len(classes[classnum]), CCC, mj, numpy.asarray(normsims).mean(), numpy.asarray(normsims).std(), res)
			vf.write("%5d.mrc %5d %8.3f %8.3f %8.3f %8.3f %8.3f\n" \
				% (classnum, len(classes[classnum]), CCC, mj, numpy.asarray(normsims).mean(), numpy.asarray(normsims).std(), res))
		mf.close()
		vf.close()
			
		return

	#=====================
	#=====================
	#=====================			
	
	def assess_3Dclass_quality2(self, voldict, sim_matrix, classes, euler_array_transformed):
		''' assesses each model based on multiple criteria, refinement only '''

		apDisplay.printColor("Parsing through resulting 3D classes to assess the quality of each 3D model", "yellow")

		### calculate final model statistics using similarity array
		classnames = classes.keys()
		bestavg = 0
		mf = open(os.path.join(self.params['rundir'], "final_model_members.dat"), "w")
		vf = open(os.path.join(self.params['rundir'], "final_model_stats.dat"), "w")
		vf.write("%11s %5s %8s %8s %8s %8s %8s\n" \
			% ("MODEL", "NUM", "CCPR", "EJ", "CCC", "STDEV", "FSC"))		
		for classnum in classnames:
			sims = []
			volarray = numpy.zeros((((len(classes[classnum]),self.params['boxsize'], self.params['boxsize'], self.params['boxsize']))))
			for i in range(len(classes[classnum])):
				for j in range(i+1, len(classes[classnum])):
					sim = sim_matrix[(classes[classnum][i]-1), (classes[classnum][j]-1)]
					sims.append(sim)
				if len(classes[classnum]) == 1:
					sims.append(1) ### when a single model is in a class, its self-similarity is 1
				volarray[i] += mrc.read(voldict[classes[classnum][i]])
				
			### get FSC of volume class
			try:
				res = apRecon.getResolutionFromGenericFSCFile(					
					os.path.join(self.params['rundir'], "refinement", "refine_%d" % classnum, "3d%d_refined.frc" % classnum),
					self.params['refineboxsize'], 
					self.params['refineapix']
					)
			except:
				res = 2 * self.params['refineapix']
			
			### assess quality of class by comparing the summed CCC between projections and reprojections
			ordered_file = self.params['refineavgs']
			reproj_file = os.path.join(
				self.params['rundir'], "refinement", "refine_%d" % classnum, "3d%d_refined_projections.hed" % classnum
				)
			CCC = self.avgCCCBetweenProjectionsAndReprojections(classes[classnum], ordered_file, reproj_file)
				
			### assess Euler jumpers for class (mean value for ALL class averages)
			mj = self.calculateMeanEulerJumpForModelClass(classes[classnum], euler_array_transformed)
			
			### print and write to file
			normsims = self.normList(sims)
			print "volumes going into model %d_r.mrc: %s \n" % (classnum, classes[classnum])
			mf.write("%d_r.mrc: %s \n" % (classnum, classes[classnum]))
			print "model %d_r.mrc, %d members with average proj/reproj CCC %f, mean Euler jump %f, similarity %f, standard deviation %f, and resolution %f" \
				% (classnum, len(classes[classnum]), CCC, mj, numpy.asarray(normsims).mean(), numpy.asarray(normsims).std(), res)
			vf.write("%5d_r.mrc %5d %8.3f %8.3f %8.3f %8.3f %8.3f\n" \
				% (classnum, len(classes[classnum]), CCC, mj, numpy.asarray(normsims).mean(), numpy.asarray(normsims).std(), res))
		mf.close()
		vf.close()
			
		return
					
	#=====================
	#=====================
	#=====================	
	
	def upload(self):
		''' insert into database, if commit is checked '''
		
		### path object
		pathq = appiondata.ApPathData()
		pathq['path'] = self.params['rundir']

		### acl run object
		aclq = appiondata.ApAutomatedCommonLinesRunData()
		aclq['path'] = pathq
		aclq['runname'] = self.params['runname']
		### check unique run
		uniquerun = aclq.query(results=1)
		if uniquerun:
			apDisplay.printError("runname already exists in the database")
		
		### acl params object
		aclparamq = appiondata.ApAutomatedCommonLinesParamsData()
		aclparamq['num_averages'] = self.params['numpart']
		aclparamq['num_volumes'] = self.params['num_volumes']
		aclparamq['symmetry'] = appiondata.ApSymmetryData.direct_query(self.params['symid'])
		aclparamq['num_alignment_refs'] = self.params['nref']
		aclparamq['angular_increment'] = self.params['ang_inc']
		aclparamq['keep_ordered'] = self.params['keep_ordered']
		aclparamq['threed_lpfilt'] = self.params['3d_lpfilt']
		aclparamq['hamming_window'] = self.params['ham_win']
		aclparamq['non_weighted_sequence'] = self.params['non_weighted_sequence']
		aclparamq['PCA'] = self.params['PCA']
		aclparamq['numeigens'] = self.params['numeigens']
		aclparamq['prealign_avgs'] = self.params['prealign']
		aclparamq['scale'] = self.params['scale']
		aclparamq['recalculate_volumes'] = self.params['recalculate']
		aclparamq['preference_type'] = self.params['preftype']
#		aclparamq['do_not_remove'] = self.params['do_not_remove']

		### finish acl run object	
		aclq['acl_params'] = aclparamq
		aclq['pixelsize'] = self.params['apix']
		aclq['boxsize'] = self.params['boxsize']
		if self.params['templatestackid'] is not None:
			aclq['templatestackid'] = appiondata.ApTemplateStackData.direct_query(self.params['templatestackid'])
		else:
			aclq['clusterid'] = appiondata.ApClusteringStackData.direct_query(self.params['clusterid'])
		aclq['description'] = self.params['description']
		aclq['REF|projectdata|projects|project'] = self.params['projectid']
		aclq['hidden'] = False
		
		if self.params['commit'] is True:
			aclq.insert()
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
		
		##############################################		copy to working directory	##############################################
		refine = True
		### get initial parameters and copy class averages into working directory
		shutil.copyfile(os.path.join(self.stackdata['path']['path'], self.clsname[:-4]+".hed"), self.params['avgs'][:-4]+".hed")
		shutil.copyfile(os.path.join(self.stackdata['path']['path'], self.clsname[:-4]+".img"), self.params['avgs'][:-4]+".img")
#		apIMAGIC.copyFile(self.params['rundir'], self.clsname, headers=True)
		apIMAGIC.takeoverHeaders(self.params['avgs'], self.params['numpart'], self.params['refineboxsize'])
		
		###################################		scale & prealign class averages, if specified	 #####################################

		### scale class averages to 64x64, if scaling is specified
		self.params['refineavgs'] = self.params['avgs']
		if self.params['scale'] is True:
			emancmd = "proc2d %s %s_scaled.img scale=%.3f clip=%i,%i edgenorm" \
				% (self.params['avgs'], self.params['avgs'][:-4], self.scalefactor, 64, 64)
			self.params['avgs'] = self.params['avgs'][:-4]+"_scaled.img"
			while os.path.isfile(self.params['avgs']):
				apFile.removeStack(self.params['avgs'])
			apParam.runCmd(emancmd, "EMAN")
			apIMAGIC.copyFile(self.params['rundir'], os.path.basename(self.params['avgs']), headers=True)
			apIMAGIC.takeoverHeaders(self.params['avgs'], self.params['numpart'], self.params['boxsize'])
			
		if self.params['prealign'] is True:
			self.params['avgs'] = self.prealignClassAverages()
			apIMAGIC.checkLogFileForErrors(os.path.join(self.params['rundir'], "prealignClassAverages.log"))
		
		##############################################		create multiple 3d0s		##############################################
#		'''
		apDisplay.printColor("Calculating similarity matrix", "cyan")
		ccc_matrix = self.calculate_ccc_matrix_2d(self.params['avgs'])
		angrecondir = os.path.join(self.params['rundir'], "angular_reconstitution")
		clsavgs = os.path.split(self.params['avgs'])[1][:-4]
		if not os.path.isdir(angrecondir):
			os.mkdir(angrecondir)
		if not os.path.isfile(os.path.join(angrecondir, clsavgs+".hed")):
			os.symlink(os.path.join(self.params['rundir'], clsavgs+".hed"), os.path.join(angrecondir, clsavgs+".hed"))
		if not os.path.isfile(os.path.join(angrecondir, clsavgs+".img")):
			os.symlink(os.path.join(self.params['rundir'], clsavgs+".img"), os.path.join(angrecondir, clsavgs+".img"))
		
		cmdlist = []
		seqfile = open(os.path.join(self.params['rundir'], "sequences_for_angular_reconstitution.dat"), "w")
		apDisplay.printColor("Running multiple IMAGIC 3d0 creations", "cyan")
		for i in range(self.params['num_volumes']):
			sequence = self.calculate_sequence_of_addition(self.params['avgs'], ccc_matrix, first=self.params['firstimage'])
			self.check_for_duplicates_in_sequence(sequence)
			seqfile.write(str(sequence)+"\n")
			### create IMAGIC batch file for each model construction & append them to be threaded
			batchfile = self.imagic_batch_file(sequence, i+1)
			proc = subprocess.Popen('chmod 755 '+batchfile, shell=True)
			proc.wait()
			cmdlist.append(batchfile)
			os.chdir(self.params['rundir'])
		seqfile.close()
		apThread.threadCommands(cmdlist, nproc=self.params['threadnproc'], pausetime=10)
			
		### check for errors after execution
		for i in range(self.params['num_volumes']):
			apIMAGIC.checkLogFileForErrors(os.path.join(self.params['rundir'], "angular_reconstitution", "3d"+str(i+1)+".log"))
		
		#####################################   convert 3-D models to SPIDER format for Xmipp   ######################################
				
		### create volume directory
		volumedir = os.path.join(self.params['rundir'], "volumes")
		if not os.path.isdir(volumedir):
			os.mkdir(volumedir)

		### move volumes into volume directory		
		apDisplay.printColor("moving volumes for Xmipp 3-D Maximum Likelihood", "cyan")	
		volumes = {}
		cmds = []
		for i in range(self.params['num_volumes']):
			volume1 = os.path.join(self.params['rundir'], "angular_reconstitution", "3d%d_ordered%d_filt.vol" % (i+1,i+1))
			volume2 = os.path.join(volumedir, "3d%d.vol" % (i+1))
			cmds.append("proc3d %s %s spidersingle" % (volume1, volume2))
			volumes[(i+1)] = volume2
		apThread.threadCommands(cmds, nproc=self.params['threadnproc'])
							
		##############################################			align 3-D models		##############################################
								
		### run Maximum Likelihood 3-D alignment & align resulting volumes
		apDisplay.printColor("Running Xmipp maximum likelihood 3-D alignment", "cyan")
		vol_doc_file, alignref = self.xmipp_max_like_3d_align(volumes)
		alignparams = self.read_vol_doc_file(vol_doc_file)
		apDisplay.printColor("Aligning volumes based on 3-D ML parameters", "cyan")
		self.align_volumes(alignparams, alignref)
#		'''
#		vol_doc_file = '/ami/data00/appion/09nov05a/angrecon/test2/max_like_alignment/nref1_15deg_it000005.doc'
#		alignparams = self.read_vol_doc_file(vol_doc_file)
		##############################################    Principal Component Analysis   #############################################

		apDisplay.printColor("Calculating inter-volume similarity", "cyan")
		aligned_volumes = {}
		for i in range(self.params['num_volumes']):
			aligned_volumes[(i+1)] = os.path.join(self.params['rundir'], "volumes", "3d%d.mrc" % (i+1))
		if self.params['PCA'] is True:
			simfile, sim_matrix = self.runPrincipalComponentAnalysis(aligned_volumes, recalculate=self.params['recalculate'])
		else:
			simfile, sim_matrix = self.calculate_ccc_matrix_3d(aligned_volumes)
				
		##############################################    3-D affinity propagation		##############################################

		### 3-D Affinity Propagation
		apDisplay.printColor("Averaging volumes with Affinity Propagation", "cyan")
		preffile = self.set_preferences(sim_matrix, self.params['preftype'])
		classes = self.run_affinity_propagation(aligned_volumes, simfile, preffile)

		#####################################	refine volumes using Xmipp projection matching	######################################
			
		if refine is True:
			if not os.path.isdir("refinement"):
				os.mkdir("refinement")
			os.chdir("refinement")
			apXmipp.breakupStackIntoSingleFiles(self.params['refineavgs'])
			xmippcmd = "xmipp_normalize -i partlist.sel -method OldXmipp"
			apParam.runCmd(xmippcmd, "Xmipp")
			for i in classes.keys():
				emancmd = "proc3d %s %s scale=%.3f clip=%d,%d,%d mask=%s spidersingle" \
					% (os.path.join(self.params['rundir'], "%d.mrc" % i), "%d.vol" % i, (1/self.scalefactor), \
						self.params['refineboxsize'], self.params['refineboxsize'], self.params['refineboxsize'], \
						(self.params['mask_radius'] / self.params['refineapix']))
				apParam.runCmd(emancmd, "EMAN")
				self.refine_volume((i))
				emancmd = "proc3d %s %s apix=%.3f" \
					% (os.path.join("refine_%d" % i, "3d%d_refined.vol" % i), os.path.join(self.params['rundir'], "%d_r.mrc" % i), \
						self.params['refineapix'])
				apParam.runCmd(emancmd, "EMAN")
			os.chdir(self.params['rundir'])
		
		##############################################		   model evaluation	    	##############################################
		
		### final model assessment
		euler_array = self.getEulerValuesForModels(alignparams)
		if refine is True:
			self.assess_3Dclass_quality2(aligned_volumes, sim_matrix, classes, euler_array)
		else:
			self.assess_3Dclass_quality(aligned_volumes, sim_matrix, classes, euler_array)
		apCommonLines.combineMetrics("final_model_stats.dat", "final_model_stats_sorted_by_Rcrit.dat", **{"CCPR":(1,1)})

		### upload to database, if specified
		self.upload()
		
		### make chimera snapshots
		if refine is True:
			for i in classes.keys():
				if self.params['mass'] is not None:
					apChimera.filterAndChimera(os.path.join(self.params['rundir'], "%d_r.mrc" % i), res=self.params['3d_lpfilt'], \
						apix=self.params['refineapix'], box=self.params['refineboxsize'], chimtype="snapshot", contour=2, \
						zoom=1, sym="c1", color="gold", mass=self.params['mass'])
	
		### cleanup
		snapshots = glob.glob("*.png")
		mtlfiles = glob.glob("*.mtl")
		objfiles = glob.glob("*.obj")
		pyfiles = glob.glob("*mrc.py")
		for file in mtlfiles:
			os.remove(file)
		for file in objfiles:
			os.remove(file)
		for file in pyfiles:
			os.remove(file)
		if not os.path.isdir("snapshots"):
			os.mkdir("snapshots")
		for s in snapshots:
			shutil.move(s, os.path.join("snapshots", s))
			

if __name__ == "__main__":

#	appiondata.sinedon.setConfig("appiondata", db="ap218")
	AAR = automatedAngularReconstitution()
	AAR.start()
	AAR.close()
	
	
