#!/usr/bin/env python
# Python script to run automated refinement of an input stack and model using IMAGIC angular reconstitution
# This can be done with or without a previous imagic 3d0 run

import os
import sys
import re
import time
import shutil
import subprocess
import appionScript
import appiondata

import apParam
import apChimera
import apDisplay
import apEMAN
import apIMAGIC
import apFile
import apImagicFile
import apSymmetry
import apDatabase
import apStack
import apProject
import apFile
import apVolume
import spyder


#=====================
#=====================
class imagic3dRefineScript(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage( "Usage: %prog --file=<name> --apix=<pixel> --rundir=<dir> "
			+"[options]")

		### input stack and model from database
		self.parser.add_option("--stackid", dest="stackid",
			help="ID of stack used for refinement", metavar="int")
		self.parser.add_option("--modelid", dest="modelid",
			help="ID of 3d model used for refinement", metavar="int")
		self.parser.add_option("--imagic3d0id", dest="imagic3d0id",
			help="ID of 3d0 used to initiate refinement", metavar="int")

		### basic params
		self.parser.add_option("--nproc", dest="nproc", type="int",
			help="number of processors to use", metavar="int")
		self.parser.add_option("--numiters", dest="numiters", type="int",
			help="total number of iterations", metavar="int")
		self.parser.add_option("--itn", dest="itn", type="int",
			help="number of this iteration", metavar="int")
		self.parser.add_option("--symmetry", dest="symmetry", type="int",
			help="symmetry of the object", metavar="INT")
			
		### stack parameters (filtering and masking)
		self.parser.add_option("--filt_stack", dest="filt_stack", default=False,
			action="store_true", help="filter input stack for each iteration prior to alignment and classification")
		self.parser.add_option("--hp_filt", dest="hp_filt", type="int",
			help="high-pass filter input stack to this value prior to initial MRA (specified with --filt_stack option)", metavar="INT")
		self.parser.add_option("--lp_filt", dest="lp_filt", type="int",
			help="low-pass filter input stack to this value prior to initial MRA (specified with --filt_stack option)", metavar="INT")
		self.parser.add_option("--auto_filt_stack", dest="auto_filt_stack", default=False,
			action="store_true", help="auto filter input realigned stack for each iteration prior to the next alignment and \
				classification. The value is a fraction of the FSC for the model from the previous iteration, whereby the \
				specific number can be adjusted by the --auto_lp_filt_fraction parameter.")
		self.parser.add_option("--auto_lp_filt_fraction", dest="auto_lp_filt_fraction", type="int", default=25,
			help="This value specifies the fraction of the FSC to which the stack is automatically low-pass filtered prior to each \
				iteration of multi-reference alignment. For example, if the model from iteration 3 is resolved at 20 Angstroms by FSC 0.5 \
				a value of 0.75 here will low-pass filter the input stack for iteration 4 (i.e. mra3.hed) to 15 Angstroms. \
				Only then will the fourth multi-reference alignment proceed, creating mra4.hed from the filtered stack", metavar="INT")
		self.parser.add_option("--mask_val", dest="mask_val", type="int",
			help="circular mask radius (in pixels) applied to the stack (used for MRA and MSA)", metavar="INT")

		### MRA (IMAGIC)
		self.parser.add_option("--mrarefs_ang_inc", dest="mrarefs_ang_inc", type="int",	default=25,
			help="angular increment of reprojections for MRA", metavar="INT")
		self.parser.add_option("--mirror_refs", dest="mirror_refs", default=False, 
			action="store_true", help="also mirror projections for multi-reference alignment")
		self.parser.add_option("--cent_stack", dest="cent_stack", default=False, 
			action="store_true", help="also mirror projections for multi-reference alignment")		
		self.parser.add_option("--max_shift_orig", dest="max_shift_orig", type="float", default=0.2,
			help="maximum radial shift during MRA", metavar="float")
		self.parser.add_option("--max_shift_this", dest="max_shift_this", type="float", default=0.05,
			help="maximum radial shift during MRA for this iteration", metavar="float")
		self.parser.add_option("--samp_param", dest="samp_param", type="int", default=12,
			help="used to define precision of rotational alignment during MRA", metavar="int")
		self.parser.add_option("--minrad", dest="minrad", type="int", default=0,
			help="minimum radius (in pixels) used for MRA search", metavar="int")
		self.parser.add_option("--maxrad", dest="maxrad", type="int",
			help="maximum radius (in pixels) used for MRA search (defaulted to 0.8 * masksize)", metavar="int")

		### MRA (SPIDER)
		self.parser.add_option("--spider_align", dest="spider_align", default=False, 
			action="store_true", help="use SPIDER AP SH for multi-reference iterative 2-D alignment")
		self.parser.add_option("--xy_search", dest="xy_search", type="int",	default=5,
			help="translational search range in pixels", metavar="#")
		self.parser.add_option("--xy_step", dest="xy_step", type="int",	default=1,
			help="translational search step size in pixels", metavar="#")
		self.parser.add_option("--minrad_spi", dest="minrad_spi", type="int", default=1,
			help="minimum radius (in pixels) used for SPIDER MRA search", metavar="int")
		self.parser.add_option("--maxrad_spi", dest="maxrad_spi", type="int",
			help="maximum radius (in pixels) used for SPIDER MRA search (defaulted to 0.8 * masksize)", metavar="int")
		self.parser.add_option("--angle_change", dest="angle_change", type="int", default=0,
			help="maximum range of change for the Euler angles corresponding to each particle \
				speeds up later alignment iterations", metavar="int")

		### MSA
		self.parser.add_option("--ignore_images", dest="ignore_images", type="int", default=10,
			help="percentage of images to ignore when constructing classes", metavar="INT")
		self.parser.add_option("--ignore_members", dest="ignore_members", type="int", default=10,
			help="percentage of worst class members to ignore", metavar="INT")
		self.parser.add_option("--num_classes", dest="numclasses", type="int",
			help="total number of classes created with MSA classify", metavar="INT")
		self.parser.add_option("--num_eigenimages", dest="num_eigenimages", type="int", default=69,
			help="number of factors (Eigenimages) to use for the classification and summing", metavar="INT")

		### angular reconstitution
		self.parser.add_option("--forw_ang_inc", dest="forw_ang_inc", type="int", default=25,
			help="angular increment of reprojections for euler angle refinement", metavar="INT")
		self.parser.add_option("--euler_ang_inc", dest="euler_ang_inc", type="int", default=10,
			help="angular increment for euler angle search", metavar="INT")

		### threed reconstruction, filtering, & automasking params
		self.parser.add_option("--ham_win", dest="ham_win", type="float", default=0.99,
			help="similar to lp-filtering parameter, smooths out the filter used in 3d reconstruction", metavar="float")
		self.parser.add_option("--object_size", dest="object_size", type="float", default=0.8,
			help="object size as fraction of image size", metavar="float")
		self.parser.add_option("--3d_lpfilt", dest="threedfilt", type="int",
			help="low-pass filter the reconstructed 3-D model to specified resolution (Angstroms) prior to masking", metavar="INT")		
		self.parser.add_option("--amask_dim", dest="amask_dim", type="float", default=0.04,
			help="automasking parameter determined by smallest object size", metavar="float")
		self.parser.add_option("--amask_lp", dest="amask_lp", type="float", default=0.15,
			help="automasking parameter for low-pass filtering", metavar="float")
		self.parser.add_option("--amask_sharp", dest="amask_sharp", type="float", default=0.15,
			help="automasking parameter that determines sharpness of mask", metavar="float")
		self.parser.add_option("--amask_thresh", dest="amask_thresh", type="float", default=15,
			help="automasking parameter that determines object thresholding", metavar="float")

		### parameters for keeping images
		self.parser.add_option("--keep_classes", dest="keep_classes", type="float", default=0.9,
			help="Fraction of classified images to keep (based on the overall quality of the class average)", metavar="INT")
		self.parser.add_option("--keep_ordered", dest="keep_ordered", type="float", default=0.9,
			help="Fraction of ordered images to keep (based on error in angular reconstitution)", metavar="INT")

		### mass specified for eman volume function
		self.parser.add_option("--mass", dest="mass", type="int",
			help="OPTIONAL: used for thresholding volume of a 3d map to 1 based on given mass", metavar="INT")
		self.parser.add_option("--contour", dest="contour", type="int", default=1,
			help="OPTIONAL: Chimera thresholding value, set to 1 when density is thresholded with EMAN's 'volume' command", metavar="INT")
		self.parser.add_option("--zoom", dest="zoom", type="int", default=1,
			help="OPTIONAL: Chimera zoom value for creating snapshots", metavar="INT")

	#=====================
	def checkConflicts(self):

		if self.params['itn'] is None:
			apDisplay.printError("enter iteration number")
		if self.params['symmetry'] is None:
			apDisplay.printError("enter object symmetry")
		if self.params['numclasses'] is None:
			apDisplay.printError("enter number of classes used for creating 3d0")

		if self.params['stackid'] is None:
			apDisplay.printError("enter a stack ID for the stack that will be used in the refinement")
		if self.params['modelid'] is None:
			apDisplay.printError("enter a model id for the refinement")
			
		if self.params['maxrad'] > self.params['mask_val'] or self.params['maxrad'] <= 0 or self.params['maxrad'] is None:
			self.params['maxrad'] = self.params['mask_val'] * 0.8
		if self.params['minrad'] > self.params['mask_val'] or self.params['minrad'] < 0:
			self.params['minrad'] = 0
		
		if self.params['spider_align'] is True:
			if self.params['maxrad_spi'] > self.params['mask_val'] or self.params['maxrad_spi'] <= 0 or self.params['maxrad_spi'] is None:
				self.params['maxrad_spi'] = self.params['mask_val_spi'] * 0.8
			if self.params['minrad_spi'] > self.params['mask_val'] or self.params['minrad_spi'] < 1:
				self.params['minrad_spi'] = 1

	#=====================
	def setRunDir(self):

		self.stackdata = apStack.getOnlyStackData(self.params['stackid'], msg=False)
		path = self.stackdata['path']['path']
		uppath = os.path.abspath(os.path.join(path, "../.."))
		self.params['rundir'] = os.path.join(uppath,'recon',self.params['runname'])

	#=======================
	def startFiles(self, modelfile):
		"""
		initialization: conversions, projections, masking, etc.
		"""
		
		### first create IMAGIC batch file
		basename = os.path.basename(modelfile)
		batchfile = os.path.join(self.params['rundir'], "startFiles.batch")
		syminfo = apSymmetry.findSymmetry(self.params['symmetry'])
		symmetry = syminfo['eman_name']
		f = open(batchfile, "w")
		f.write("#!/bin/csh -f\n")
		f.write("setenv IMAGIC_BATCH 1\n")
		f.write("cd "+str(self.params['rundir'])+"\n")

		### convert to IMAGIC format
		f.write("/usr/local/IMAGIC/stand/em2em.e <<EOF >> startFiles.log\n")
		f.write("MRC\n")
		f.write("MRC\n")
		f.write("IMAGIC\n")
		f.write("3D_VOLUME\n")
		f.write(basename+"\n")
		f.write(basename[:-4]+"\n")
		f.write("%.3f,%.3f,%.3f\n" % (self.params['apix'], self.params['apix'], self.params['apix']))
		f.write("YES\n")
		f.write("0\n")
		f.write("EOF\n")

		### forward project to create references for MRA
		f.write("/usr/local/IMAGIC/threed/forward.e SURF FORWARD <<EOF >> startFiles.log\n")
		f.write(basename[:-4]+"\n")
		f.write("-99999\n")
		f.write("PROJECTIONS\n")
		f.write("YES\n")
#		f.write("mrarefs_masked_3d"+str(self.params['itn']-1)+"\n")
		f.write("mrarefs_3d"+str(self.params['itn']-1)+"\n")
		f.write("ASYM_TRIANGLE\n")
		f.write(symmetry+"\n")
		f.write("EQUIDIST\n")
		f.write("ZERO\n")
		f.write(str(self.params['mrarefs_ang_inc'])+"\n")
		f.write("EOF\n")
		
		if self.params['mirror_refs'] is True:
			### mirror projections for MRA
			f.write("/usr/local/IMAGIC/stand/arithm.e MODE MIRROR <<EOF >> startFiles.log\n")
#			f.write("mrarefs_masked_3d"+str(self.params['itn']-1)+"\n")
			f.write("mrarefs_3d"+str(self.params['itn']-1)+"\n")
			f.write("mirror\n")
			f.write("EOF\n")
			f.write("/usr/local/IMAGIC/stand/append.e <<EOF >> startFiles.log\n")
			f.write("mirror\n")
#			f.write("mrarefs_masked_3d"+str(self.params['itn']-1)+"\n")
			f.write("mrarefs_3d"+str(self.params['itn']-1)+"\n")
			f.write("EOF\n")
			f.write("/usr/local/IMAGIC/stand/imdel.e <<EOF >> startFiles.log\n")
			f.write("mirror\n")
			f.write("EOF\n")

		### forward project to create euler angle anchor set
		f.write("/usr/local/IMAGIC/threed/forward.e SURF FORWARD <<EOF >> startFiles.log\n")
		f.write(basename[:-4]+"\n")
		f.write("-99999\n")
		f.write("PROJECTIONS\n")
		f.write("YES\n")
#		f.write("masked_3d"+str(self.params['itn']-1)+"_ordered"+str(self.params['itn']-1)+"_repaligned_forward\n")
		f.write("3d"+str(self.params['itn']-1)+"_ordered"+str(self.params['itn']-1)+"_repaligned_forward\n")
		f.write("ASYM_TRIANGLE\n")
		f.write(symmetry+"\n")
		f.write("EQUIDIST\n")
		f.write("ZERO\n")
		f.write(str(self.params['forw_ang_inc'])+"\n")
		f.write("EOF\n\n")

		### make a mask for use in MSA
		radius = float(self.params['mask_val']) / (self.params['boxsize'] / 2)
		if radius > 1:
			radius = 1
		f.write("/usr/local/IMAGIC/stand/testim.e <<EOF >> startFiles.log\n")
		f.write("msamask\n")
		f.write(str(self.params['boxsize'])+","+str(self.params['boxsize'])+"\n")
		f.write("REAL\n")
		f.write("DISC\n")
		f.write(str(radius)+"\n")
		f.write("EOF\n")
		f.close()

		return batchfile

	#=======================
	def createImagicBatchFile_1(self):
		"""
		batch file for everything prior to multi-reference alignment
		"""
		
		syminfo = apSymmetry.findSymmetry(self.params['symmetry'])
		symmetry = syminfo['eman_name']
		
		filename = os.path.join(self.params['rundir'], "imagicCreate3dRefine_"+str(self.params['itn'])+".batch")
		f = open(filename, 'w')
		f.write("#!/bin/csh -f\n")
		f.write("setenv IMAGIC_BATCH 1\n")
		f.write("cd "+str(self.params['rundir'])+"\n")

		### if not first iteration, create forward projections from previous model
		f.write("echo 'start' > imagic3dRefine_"+str(self.params['itn'])+".log\n")
		if self.params['itn'] > 1:
			f.write("/usr/local/IMAGIC/threed/forward.e SURF FORWARD <<EOF >> imagic3dRefine_"+str(self.params['itn'])+".log\n")
#			f.write("masked_3d"+str(self.params['itn']-1)+"_ordered"+str(self.params['itn']-1)+"_repaligned\n")
			f.write("3d"+str(self.params['itn']-1)+"_ordered"+str(self.params['itn']-1)+"_repaligned\n")
			f.write("-99999\n")
			f.write("PROJECTIONS\n")
			f.write("YES\n")
#			f.write("WIDENING\n")
#			f.write("mrarefs_masked_3d"+str(self.params['itn']-1)+"\n")
			f.write("mrarefs_3d"+str(self.params['itn']-1)+"\n")
			f.write("ASYM_TRIANGLE\n")
			f.write(symmetry+"\n")
			f.write("EQUIDIST\n")
			f.write("ZERO\n")
			f.write(str(self.params['mrarefs_ang_inc'])+"\n")
			f.write("EOF\n")

			if self.params['mirror_refs'] is True:
				### mirror projections for MRA
				f.write("/usr/local/IMAGIC/stand/arithm.e MODE MIRROR <<EOF >> imagic3dRefine_"+str(self.params['itn'])+".log\n")
#				f.write("mrarefs_masked_3d"+str(self.params['itn']-1)+"\n")
				f.write("mrarefs_3d"+str(self.params['itn']-1)+"\n")
				f.write("mirror\n")
				f.write("EOF\n")
				f.write("/usr/local/IMAGIC/stand/append.e <<EOF >> imagic3dRefine_"+str(self.params['itn'])+".log\n")
				f.write("mirror\n")
#				f.write("mrarefs_masked_3d"+str(self.params['itn']-1)+"\n")
				f.write("mrarefs_3d"+str(self.params['itn']-1)+"\n")
				f.write("EOF\n")
				f.write("/usr/local/IMAGIC/stand/imdel.e <<EOF >> imagic3dRefine_"+str(self.params['itn'])+".log\n")
				f.write("mirror\n")
				f.write("EOF\n")

			f.write("/usr/local/IMAGIC/threed/forward.e SURF FORWARD <<EOF >> imagic3dRefine_"+str(self.params['itn'])+".log\n")
#			f.write("masked_3d"+str(self.params['itn']-1)+"_ordered"+str(self.params['itn']-1)+"_repaligned\n")
			f.write("3d"+str(self.params['itn']-1)+"_ordered"+str(self.params['itn']-1)+"_repaligned\n")
			f.write("-99999\n")
			f.write("PROJECTIONS\n")
			f.write("YES\n")
#			f.write("WIDENING\n")
#			f.write("masked_3d"+str(self.params['itn']-1)+"_ordered"+str(self.params['itn']-1)+"_repaligned_forward\n")
			f.write("3d"+str(self.params['itn']-1)+"_ordered"+str(self.params['itn']-1)+"_repaligned_forward\n")
			f.write("ASYM_TRIANGLE\n")
			f.write(symmetry+"\n")
			f.write("EQUIDIST\n")
			f.write("ZERO\n")
			f.write(str(self.params['forw_ang_inc'])+"\n")
			f.write("EOF\n\n")
			
		### provide an option of filtering the stack (for first iteration this is done on start.hed, for subsequent iterations on mra"itr".hed)
		if self.params['filt_stack'] is True:
			hpfilt, lpfilt = apIMAGIC.convertFilteringParameters(self.params['hp_filt'], self.params['lp_filt'], self.params['apix'])
			if self.params['itn'] == 1:
				f.write("/usr/local/IMAGIC/fft/filt_all.e <<EOF >> imagic3dRefine_"+str(self.params['itn'])+".log\n")
				f.write("start\n")
				f.write("start_filt\n")
				f.write("BANDPASS\n")
				f.write(str(hpfilt)+"\n")
				f.write(".001\n")
				f.write(str(lpfilt)+"\n")
				f.write("NO\n")
				f.write("EOF\n")
				f.write("/usr/local/IMAGIC/stand/im_rename.e <<EOF >> imagic3dRefine_"+str(self.params['itn'])+".log\n")
				f.write("start_filt\n")
				f.write("start\n")
				f.write("EOF\n")
			else:
				f.write("/usr/local/IMAGIC/fft/filt_all.e <<EOF >> imagic3dRefine_"+str(self.params['itn'])+".log\n")
				f.write("mra"+str(self.params['itn']-1)+"\n")
				f.write("mra_filt"+str(self.params['itn']-1)+"\n")
				f.write("BANDPASS\n")
				f.write(str(hpfilt)+"\n")
				f.write(".001\n")
				f.write(str(lpfilt)+"\n")
				f.write("NO\n")
				f.write("EOF\n")
				f.write("/usr/local/IMAGIC/stand/im_rename.e <<EOF >> imagic3dRefine_"+str(self.params['itn'])+".log\n")
				f.write("mra_filt"+str(self.params['itn']-1)+"\n")
				f.write("mra"+str(self.params['itn']-1)+"\n")
				f.write("EOF\n")
			
		### mask the stack (for first iteration this is done on start.hed, for subsequent iterations on mra"itr".hed)
		radius = float(self.params['mask_val']) / (self.params['boxsize'] / 2)
		if radius > 1:
			radius = 1
		if self.params['itn'] == 1:
			f.write("/usr/local/IMAGIC/stand/arithm.e <<EOF >> imagic3dRefine_"+str(self.params['itn'])+".log\n")
			f.write("start\n")
			f.write("start_mask\n")
			f.write("CIRC_MASK\n")
			f.write(str(radius)+"\n")
			f.write("EOF\n")
			f.write("/usr/local/IMAGIC/stand/im_rename.e <<EOF >> imagic3dRefine_"+str(self.params['itn'])+".log\n")
			f.write("start_mask\n")
			f.write("start\n")
			f.write("EOF\n")
		else:
			f.write("/usr/local/IMAGIC/stand/arithm.e <<EOF >> imagic3dRefine_"+str(self.params['itn'])+".log\n")
			f.write("mra"+str(self.params['itn']-1)+"\n")
			f.write("mra_masked"+str(self.params['itn']-1)+"\n")
			f.write("CIRC_MASK\n")
			f.write(str(radius)+"\n")
			f.write("EOF\n")
			f.write("/usr/local/IMAGIC/stand/im_rename.e <<EOF >> imagic3dRefine_"+str(self.params['itn'])+".log\n")
			f.write("mra_masked"+str(self.params['itn']-1)+"\n")
			f.write("mra"+str(self.params['itn']-1)+"\n")
			f.write("EOF\n")
			
		### if the first iteration, do a centering operation, i.e. reference-free translational alignment
		if self.params['itn'] == 1 and self.params['cent_stack'] is True:
			if self.params['nproc'] > 1:
				f.write("/usr/local/IMAGIC/openmpi/bin/mpirun -np "+str(self.params['nproc'])+\
					" -x IMAGIC_BATCH  /usr/local/IMAGIC/align/alimass.e_mpi <<EOF >> imagic3dRefine_"+str(self.params['itn'])+".log\n")
				f.write("YES\n")
				f.write(str(self.params['nproc'])+"\n")
			else:
				f.write("/usr/local/IMAGIC/align/alimass.e <<EOF >> imagic3dRefine_"+str(self.params['itn'])+".log\n")
				f.write("NO\n")
			f.write("start\n")
			f.write("start_cent\n")
			f.write("TOTSUM\n")
			f.write("CCF\n")
			f.write(str(self.params['max_shift_orig'])+"\n")
			f.write("3\n")
			f.write("EOF\n")
			f.write("/usr/local/IMAGIC/stand/im_rename.e <<EOF >> imagic3dRefine_"+str(self.params['itn'])+".log\n")
			f.write("start_cent\n")
			f.write("start\n")
			f.write("EOF\n")
			f.close()
		
		return filename
			
	#=======================			
	def runAlignment(self):
		"""
		batch file & execution of multi-reference alignment, using either SPIDER or IMAGIC
		"""
		
		if self.params['spider_align'] is True:
			### define input and output stack
			if self.params['itn'] == 1:
				instack = os.path.join(self.params['rundir'], "start.spi")
			else:
				instack = os.path.join(self.params['rundir'], "mra"+str(self.params['itn']-1)+".spi")
			outstack = os.path.join(self.params['rundir'], "mra"+str(self.params['itn'])+".spi")
			templatestack = os.path.join(self.params['rundir'], "mrarefs_3d"+str(self.params['itn']-1)+".spi")

			### setup and write SPIDER batch file
			localbatch = self.setupSpiderBatch(instack, outstack, templatestack)
			
			### run the alignment, removing any unecessary files
			self.runSpiderAlignment(instack, outstack, templatestack, localbatch)
			
		else:
			### set minimum & maximum radii for MRA, corresponding to IMAGIC values
			radmin = int(round(float(self.params['minrad']) / (self.params['boxsize'] / 2)))
			radmax = int(round(float(self.params['maxrad']) / (self.params['boxsize'] / 2)))
			
			### setup IMAGIC multi reference alignment batch file
			
			filename = os.path.join(self.params['rundir'], "imagicCreate3dRefine_"+str(self.params['itn'])+".batch")
			f = open(filename, 'w')
			f.write("#!/bin/csh -f\n")
			f.write("setenv IMAGIC_BATCH 1\n")
			f.write("cd "+str(self.params['rundir'])+"\n")
		
			if self.params['nproc'] > 1:
				f.write("/usr/local/IMAGIC/openmpi/bin/mpirun -np "+str(self.params['nproc'])+\
					" -x IMAGIC_BATCH  /usr/local/IMAGIC/align/mralign.e_mpi <<EOF >> imagic3dRefine_"+str(self.params['itn'])+".log\n")
				f.write("YES\n")
				f.write(str(self.params['nproc'])+"\n")
			else:
				f.write("/usr/local/IMAGIC/align/mralign.e <<EOF >> imagic3dRefine_"+str(self.params['itn'])+".log\n")
				f.write("NO\n")
			f.write("FRESH\n")
			f.write("ALIGNMENT\n")
			f.write("ALL\n")
			f.write("ROTATION_FIRST\n")
			f.write("CCF\n")
			if self.params['itn'] == 1:
				f.write("start\n")
				f.write("mra"+str(self.params['itn'])+"\n")
				f.write("start\n")
			else:
				f.write("mra"+str(self.params['itn']-1)+"\n")
				f.write("mra"+str(self.params['itn'])+"\n")
				f.write("start\n")
	#		f.write("mrarefs_masked_3d"+str(self.params['itn']-1)+"\n")
			f.write("mrarefs_3d"+str(self.params['itn']-1)+"\n")
			f.write("no\n")
			f.write("yes\n")
			f.write(str(self.params['max_shift_orig'])+"\n")
			if self.params['itn'] > 1:
				f.write(str(self.params['max_shift_this'])+"\n")
			f.write("-180,180\n")
			if self.params['itn'] > 1:
				f.write("-180,180\n")
			f.write("INTERACTIVE\n")
			f.write(str(self.params['samp_param'])+"\n")
			f.write(str(radmin)+","+str(radmax)+"\n")
			f.write("3\n")
			f.write("NO\n")
			f.write("EOF\n")
			f.close
			
			### run alignment
			proc = subprocess.Popen('chmod 755 '+filename, shell=True)
			proc.wait()
			apParam.runCmd(filename, "IMAGIC")
					
	#=======================			
	def createImagicBatchFile_2(self):
		"""
		batch file for everythin after multi-reference alignment
		"""

		syminfo = apSymmetry.findSymmetry(self.params['symmetry'])
		symmetry = syminfo['eman_name']

		filename = os.path.join(self.params['rundir'], "imagicCreate3dRefine_"+str(self.params['itn'])+".batch")
		f = open(filename, 'w')
		f.write("#!/bin/csh -f\n")
		f.write("setenv IMAGIC_BATCH 1\n")
		f.write("cd "+str(self.params['rundir'])+"\n")

		### Perform multivariate statistical analysis on aligned stack
		if self.params['nproc'] > 1:
			f.write("/usr/local/IMAGIC/openmpi/bin/mpirun -np "+str(self.params['nproc'])+\
				" -x IMAGIC_BATCH  /usr/local/IMAGIC/msa/msa.e_mpi <<EOF >> imagic3dRefine_"+str(self.params['itn'])+".log\n")
			f.write("YES\n")
			f.write(str(self.params['nproc'])+"\n")
		else:
			f.write("/usr/local/IMAGIC/msa/msa.e <<EOF >> imagic3dRefine_"+str(self.params['itn'])+".log\n")
			f.write("NO\n")
		f.write("FRESH_MSA\n")
		f.write("modulation\n")
		f.write("mra"+str(self.params['itn'])+"\n")
		f.write("NO\n")
		f.write("NO\n")
		f.write("msamask\n")
		f.write("eigenimages"+str(self.params['itn'])+"\n")
		f.write("pixcoos"+str(self.params['itn'])+"\n")
		f.write("eigenpixels"+str(self.params['itn'])+"\n")
		f.write("50\n")
		f.write("69\n") 
		f.write("0.8\n")
		f.write("my_msa\n")
		f.write("EOF\n")

		### classify the aligned particles into new classes
		f.write("/usr/local/IMAGIC/msa/classify.e <<EOF >> imagic3dRefine_"+str(self.params['itn'])+".log\n")
		f.write("IMAGES/VOLUMES\n")
		f.write("mra"+str(self.params['itn'])+"\n")
		f.write(str(self.params['ignore_images'])+"\n")
		f.write(str(self.params['num_eigenimages'])+"\n") 
		f.write("YES\n")
		f.write(str(self.params['numclasses'])+"\n")
		f.write("classes_"+str(self.params['itn'])+"\n")
		f.write("EOF\n")
		f.write("/usr/local/IMAGIC/msa/classum.e <<EOF >> imagic3dRefine_"+str(self.params['itn'])+".log\n")
		f.write("mra"+str(self.params['itn'])+"\n")
		f.write("classes_"+str(self.params['itn'])+"\n")
		f.write("classums_"+str(self.params['itn'])+"\n")
		f.write("YES\n")
		f.write("NONE\n")
		f.write(str(self.params['ignore_members'])+"\n")
		f.write("EOF\n")

		### sort the classums, keeping only the best ones
		keep_classums = self.params['keep_classes'] * self.params['numclasses']
		f.write("/usr/local/IMAGIC/incore/excopy.e <<EOF >> imagic3dRefine_"+str(self.params['itn'])+".log\n")
		f.write("SORT\n")
		f.write("classums_"+str(self.params['itn'])+"\n")
		f.write("classums_"+str(self.params['itn'])+"_sorted\n")
		f.write("OVERALL\n")
		f.write("UP\n")
		f.write(str(keep_classums)+"\n")
		f.write("EOF\n")
		f.write("/usr/local/IMAGIC/stand/im_rename.e <<EOF >> imagic3dRefine_"+str(self.params['itn'])+".log\n")
		f.write("classums_"+str(self.params['itn'])+"_sorted\n")
		f.write("classums_"+str(self.params['itn'])+"\n")
		f.write("EOF\n")

		### calculate euler angles, using anchor set for references
		if self.params['nproc'] > 1:
			f.write("/usr/local/IMAGIC/openmpi/bin/mpirun -np "+str(self.params['nproc'])+\
				" -x IMAGIC_BATCH  /usr/local/IMAGIC/angrec/euler.e_mpi <<EOF >> imagic3dRefine_"+str(self.params['itn'])+".log\n")
		else:
			f.write("/usr/local/IMAGIC/angrec/euler.e <<EOF >> imagic3dRefine_"+str(self.params['itn'])+".log\n")
		f.write(symmetry+"\n")
		lowercase = symmetry.lower()
		if lowercase != "c1":
			f.write("0\n")
		f.write("ANCHOR\n")
		f.write("FRESH\n")
		f.write("IMAGES\n")
		f.write("classums_"+str(self.params['itn'])+"\n")
		f.write("sino_classums_"+str(self.params['itn'])+"\n")
		f.write("YES\n")
		f.write("0.9\n")
		f.write("IMAGES\n")
#		f.write("masked_3d"+str(self.params['itn']-1)+"_ordered"+str(self.params['itn']-1)+"_repaligned_forward\n")
#		f.write("arsino_masked_3d"+str(self.params['itn']-1)+"_ordered"+str(self.params['itn']-1)+"_repaligned_forward\n")
		f.write("3d"+str(self.params['itn']-1)+"_ordered"+str(self.params['itn']-1)+"_repaligned_forward\n")
		f.write("arsino_3d"+str(self.params['itn']-1)+"_ordered"+str(self.params['itn']-1)+"_repaligned_forward\n")
		f.write("my_sine\n")
		f.write("YES\n")
		f.write(str(self.params['euler_ang_inc'])+"\n")
		f.write("YES\n")
		if self.params['nproc'] > 1:
			f.write("YES\n")
			f.write(str(self.params['nproc'])+"\n")
		else:
			f.write("NO\n")
		f.write("YES\n")
		f.write("EOF\n")

		### sort based on error in angular reconstitution
		keep_ordered = self.params['keep_ordered'] * keep_classums
		f.write("/usr/local/IMAGIC/incore/excopy.e <<EOF >> imagic3dRefine_"+str(self.params['itn'])+".log\n")
		f.write("SORT\n")
		f.write("classums_"+str(self.params['itn'])+"\n")
		f.write("ordered"+str(self.params['itn'])+"\n")
		f.write("ANGULAR_ERROR\n")
		f.write("UP\n")
		f.write(str(keep_ordered)+"\n")
		f.write("EOF\n")

		### build a 3d model from the ordered, sorted class averages
		if self.params['nproc'] > 1:
			f.write("/usr/local/IMAGIC/openmpi/bin/mpirun -np "+str(self.params['nproc'])+\
				" -x IMAGIC_BATCH  /usr/local/IMAGIC/threed/true3d.e_mpi <<EOF >> imagic3dRefine_"+str(self.params['itn'])+".log\n")
			f.write("YES\n")
			f.write(str(self.params['nproc'])+"\n")
		else:
			f.write("/usr/local/IMAGIC/threed/true3d.e <<EOF >> imagic3dRefine_"+str(self.params['itn'])+".log\n")
			f.write("NO\n")
		f.write(symmetry+"\n")
		f.write("YES\n")
		f.write("ordered"+str(self.params['itn'])+"\n")
		f.write("ANGREC_HEADER_VALUES\n")
		f.write("3d"+str(self.params['itn'])+"_ordered"+str(self.params['itn'])+"\n")
		f.write("rep"+str(self.params['itn'])+"_ordered"+str(self.params['itn'])+"\n")
		f.write("err"+str(self.params['itn'])+"_ordered"+str(self.params['itn'])+"\n")
		f.write("NO\n")
		f.write(str(self.params['ham_win'])+"\n")
		f.write(str(self.params['object_size'])+"\n")
		f.write("EOF\n")

		### align the ordered class averages to reprojections from the model
		f.write("/usr/local/IMAGIC/align/alipara.e <<EOF >> imagic3dRefine_"+str(self.params['itn'])+".log\n")
		f.write("ALL\n")
		f.write("CCF\n")
		f.write("ordered"+str(self.params['itn'])+"\n")
		f.write("ordered"+str(self.params['itn'])+"_repaligned\n")
		f.write("rep"+str(self.params['itn'])+"_ordered"+str(self.params['itn'])+"\n")
		f.write("0.2\n")
		f.write("-180,180\n")
		f.write("5\n")
		f.write("EOF\n")

		### build another 3d, this time from the ordered, sorted, and aligned class averages
		if self.params['nproc'] > 1:
			f.write("/usr/local/IMAGIC/openmpi/bin/mpirun -np "+str(self.params['nproc'])+\
				" -x IMAGIC_BATCH  /usr/local/IMAGIC/threed/true3d.e_mpi <<EOF >> imagic3dRefine_"+str(self.params['itn'])+".log\n")
			f.write("YES\n")
			f.write(str(self.params['nproc'])+"\n")
		else:
			f.write("/usr/local/IMAGIC/threed/true3d.e <<EOF >> imagic3dRefine_"+str(self.params['itn'])+".log\n")
			f.write("NO\n")
		f.write(symmetry+"\n")
		f.write("YES\n")
		f.write("ordered"+str(self.params['itn'])+"_repaligned\n")
		f.write("ANGREC_HEADER_VALUES\n")
		f.write("3d"+str(self.params['itn'])+"_ordered"+str(self.params['itn'])+"_repaligned\n")
		f.write("rep"+str(self.params['itn'])+"_ordered"+str(self.params['itn'])+"_repaligned\n")
		f.write("err"+str(self.params['itn'])+"_ordered"+str(self.params['itn'])+"_repaligned\n")
		f.write("NO\n")
		f.write(str(self.params['ham_win'])+"\n")
		f.write(str(self.params['object_size'])+"\n")
		f.write("EOF\n\n")
		
		### optional filtering of the 3d
		if self.params['threedfilt'] is not None:
			filtval = 2 * self.params['apix'] / self.params['threedfilt']
			if filtval > 1:
				filtval = 1
			f.write("/usr/local/IMAGIC/threed/fft3d.e FORW FILTER <<EOF >> imagic3dRefine_"+str(self.params['itn'])+".log\n")
			f.write("3d"+str(self.params['itn'])+"_ordered"+str(self.params['itn'])+"_repaligned\n")
			f.write("3d"+str(self.params['itn'])+"_ordered"+str(self.params['itn'])+"_repaligned_filt\n")
			f.write("GAUSSIAN\n")
			f.write(str(filtval)+"\n")
			f.write("EOF\n")
			### rename
			f.write("/usr/local/IMAGIC/stand/im_rename.e <<EOF >> imagic3dRefine_"+str(self.params['itn'])+".log\n")
			f.write("3d"+str(self.params['itn'])+"_ordered"+str(self.params['itn'])+"_repaligned_filt\n")
			f.write("3d"+str(self.params['itn'])+"_ordered"+str(self.params['itn'])+"_repaligned\n")
			f.write("EOF\n")

#		### automask the 3d, automasking is based on modulation analysis
#		f.write("/usr/local/IMAGIC/threed/automask3d.e <<EOF >> imagic3dRefine_"+str(self.params['itn'])+".log\n")
#		f.write("DO_IT_ALL\n")
#		f.write("3d"+str(self.params['itn'])+"_ordered"+str(self.params['itn'])+"_repaligned\n")
#		f.write("3d"+str(self.params['itn'])+"_ordered"+str(self.params['itn'])+"_repaligned_modvar\n")
#		f.write("YES\n")
#		f.write(str(self.params['amask_dim'])+","+str(self.params['amask_lp'])+"\n")
#		f.write(str(self.params['amask_sharp'])+"\n")
#		f.write("AUTOMATIC\n")
#		f.write(str(self.params['amask_thresh'])+"\n")
#		f.write("mask_3d"+str(self.params['itn'])+"_ordered"+str(self.params['itn'])+"_repaligned\n")
#		f.write("masked_3d"+str(self.params['itn'])+"_ordered"+str(self.params['itn'])+"_repaligned\n")
#		f.write("EOF\n")

		### use EM2EM to convert 3d from IMAGIC to MRC format
		f.write("/usr/local/IMAGIC/stand/em2em.e <<EOF >> imagic3dRefine_"+str(self.params['itn'])+".log\n")
		f.write("IMAGIC\n")
		f.write("MRC\n")
		f.write("3D\n")
#		f.write("masked_3d"+str(self.params['itn'])+"_ordered"+str(self.params['itn'])+"_repaligned\n")
#		f.write("masked_3d"+str(self.params['itn'])+"_ordered"+str(self.params['itn'])+"_repaligned.mrc\n")
		f.write("3d"+str(self.params['itn'])+"_ordered"+str(self.params['itn'])+"_repaligned\n")
		f.write("3d"+str(self.params['itn'])+"_ordered"+str(self.params['itn'])+"_repaligned.mrc\n")
		f.write("YES\n")
		f.write("EOF\n")

		### extract odd images for FSC analysis
		f.write("/usr/local/IMAGIC/incore/excopy.e <<EOF >> imagic3dRefine_"+str(self.params['itn'])+".log\n")
		f.write("EXTRACT\n")
		f.write("ordered"+str(self.params['itn'])+"_repaligned\n")
		f.write("ordered"+str(self.params['itn'])+"_repaligned_odd\n")
		f.write("INTERACTIVE\n")
		f.write("1-"+str(keep_ordered)+"\n")
		f.write("ODD\n")
		f.write("EOF\n")

		### extract even images for FSC analysis
		f.write("/usr/local/IMAGIC/incore/excopy.e <<EOF >> imagic3dRefine_"+str(self.params['itn'])+".log\n")
		f.write("EXTRACT\n")
		f.write("ordered"+str(self.params['itn'])+"_repaligned\n")
		f.write("ordered"+str(self.params['itn'])+"_repaligned_even\n")
		f.write("INTERACTIVE\n")
		f.write("1-"+str(keep_ordered)+"\n")
		f.write("EVEN\n")
		f.write("EOF\n")

		### build 3d from odd images
		if self.params['nproc'] > 1:
			f.write("/usr/local/IMAGIC/openmpi/bin/mpirun -np "+str(self.params['nproc'])+\
				" -x IMAGIC_BATCH  /usr/local/IMAGIC/threed/true3d.e_mpi <<EOF >> imagic3dRefine_"+str(self.params['itn'])+".log\n")
			f.write("YES\n")
			f.write(str(self.params['nproc'])+"\n")
		else:
			f.write("/usr/local/IMAGIC/threed/true3d.e <<EOF >> imagic3dRefine_"+str(self.params['itn'])+".log\n")
			f.write("NO\n")
		f.write(symmetry+"\n")
		f.write("YES\n")
		f.write("ordered"+str(self.params['itn'])+"_repaligned_odd\n")
		f.write("ANGREC_HEAD\n")
		f.write("3d"+str(self.params['itn'])+"_ordered"+str(self.params['itn'])+"_repaligned_odd\n")
		f.write("fsc_rep\n")
		f.write("fsc_err\n")
		f.write("NO\n")
		f.write(str(self.params['ham_win'])+"\n")
		f.write(str(self.params['object_size'])+"\n")
		f.write("EOF\n")

		### build 3d from even images
		if self.params['nproc'] > 1:
			f.write("/usr/local/IMAGIC/openmpi/bin/mpirun -np "+str(self.params['nproc'])+\
				" -x IMAGIC_BATCH  /usr/local/IMAGIC/threed/true3d.e_mpi <<EOF >> imagic3dRefine_"+str(self.params['itn'])+".log\n")
			f.write("YES\n")
			f.write(str(self.params['nproc'])+"\n")
		else:
			f.write("/usr/local/IMAGIC/threed/true3d.e <<EOF >> imagic3dRefine_"+str(self.params['itn'])+".log\n")
			f.write("NO\n")
		f.write(symmetry+"\n")
		f.write("YES\n")
		f.write("ordered"+str(self.params['itn'])+"_repaligned_even\n")
		f.write("ANGREC_HEAD\n")
		f.write("3d"+str(self.params['itn'])+"_ordered"+str(self.params['itn'])+"_repaligned_even\n")
		f.write("fsc_rep\n")
		f.write("fsc_err\n")
		f.write("NO\n")
		f.write(str(self.params['ham_win'])+"\n")
		f.write(str(self.params['object_size'])+"\n")
		f.write("EOF\n")

		### perform fourier shell correlation (FSC) between odd and even 3d
		f.write("/usr/local/IMAGIC/threed/foushell.e MODE FSC <<EOF >> imagic3dRefine_"+str(self.params['itn'])+".log\n")
		f.write("3d"+str(self.params['itn'])+"_ordered"+str(self.params['itn'])+"_repaligned_odd\n")
		f.write("3d"+str(self.params['itn'])+"_ordered"+str(self.params['itn'])+"_repaligned_even\n")
		f.write("3d"+str(self.params['itn'])+"_fsc\n")
		f.write("3.\n")
		f.write(symmetry+"\n")
		f.write(".66\n")
		f.write(str(self.params['apix'])+"\n")
		f.write("EOF\n")
		f.close()

		return filename

	#======================
	def convertSpiderFormat(self, infile, outfile, spider_to_imagic=False):
		"""
		use EM2EM to convert to or from SPIDER format
		"""
		
		### setup EM2EM batch file to convert from IMAGIC to SPIDER format
		batchfile = os.path.join(self.params['rundir'], "EM2EM.batch")
		f = open(batchfile, 'w')
		f.write("#!/bin/csh -f\n")
		f.write("setenv IMAGIC_BATCH 1\n")
		f.write("cd "+str(self.params['rundir'])+"\n")
		f.write("/usr/local/IMAGIC/stand/em2em.e <<EOF > EM2EM.log\n")
		if spider_to_imagic is True:
			f.write("SPIDER\n")
			f.write("SINGLE_FILE\n")
			f.write("IMAGIC\n")
			f.write("2D\n")
			f.write(infile+"\n")
			f.write("spi\n")
			f.write(outfile+"\n")
			f.write("%.3f,%.3f,%.3f\n" % (self.params['apix'], self.params['apix'], self.params['apix']))
			f.write("0\n")
			f.write("EOF\n")
		else:
			f.write("IMAGIC\n")
			f.write("SPIDER\n")
			f.write("SINGLE_FILE\n")
			f.write("2D\n")
			f.write(infile+"\n")
			f.write(outfile+"\n")
			f.write("spi\n")
			f.write("LINUX\n")
			f.write("EOF\n")
		f.close()
		
		### execute batch file
		proc = subprocess.Popen('chmod 755 '+batchfile, shell=True)
		proc.wait()
		apParam.runCmd(batchfile, "IMAGIC")
		apIMAGIC.checkLogFileForErrors(os.path.join(self.params['rundir'], "EM2EM.log"))
		
	#======================
	def setupSpiderBatch(self, instack, outstack, templatestack):
		"""
		sets up iterative alignment batch script for each iteration
		"""
		
		### parameters and filenames for this iteration
		cur_apshdoc = os.path.join(self.params['rundir'], "apshdoc"+str(self.params['itn']))
		if self.params['itn'] == 1:
			prev_apshdoc = "*"
		else:
			prev_apshdoc = os.path.join(self.params['rundir'], "apshdoc"+str(self.params['itn']-1))
		numref = apFile.numImagesInStack(templatestack[:-4]+".hed", self.params['boxsize'])
		numimg = apFile.numImagesInStack(instack[:-4]+".hed", self.params['boxsize'])
	
		### read / write batch file
		globalbatch = os.path.join(apParam.getAppionDirectory(), "spiderbatch/apsh.spi")
		localbatch =  os.path.join(self.params['rundir'], "apsh%.2d.spi") % (self.params['itn'])
		gf = open(globalbatch, "r")
		lf = open(localbatch, "w")
		modify = True
		for line in gf:
			if modify is True:
				if re.match("\<priordoc\>", line): 
					### prior apsh documentation file with Euler angles
					lf.write("<priordoc>"+prev_apshdoc+"\n")
				elif re.match("\<currentdoc\>", line): 
					### current apsh documentation file with Euler angles
					lf.write("<currentdoc>"+cur_apshdoc+"\n")
				elif re.match("\<pjstack\>", line):
					### stack of templates / projections for alignment
					lf.write("<pjstack>"+templatestack[:-4]+"\n")
				elif re.match("x33", line):
					### number of templates
					lf.write("x33="+str(numref)+" ; number of templates\n")
				elif re.match("\<imgstack\>", line):
					### input stack for MRA
					lf.write("<imgstack>"+instack[:-4]+"\n")
				elif re.match("x32", line):
					### number of raw images
					lf.write("x32="+str(numimg)+" ; number of images\n")
				elif re.match("\<outstack\>", line):
					### output multi-reference aligned stack
					lf.write("<outstack>"+outstack[:-4]+"\n")
				elif re.match("x34", line):
					### translational search range
					lf.write("x34="+str(self.params['xy_search'])+" ;search range\n")
				elif re.match("x35", line):
					### translational search step size
					lf.write("x35="+str(self.params['xy_step'])+" ;search step size\n")
				elif re.match("x36", line):
					### rotational search inner radius
					lf.write("x36="+str(self.params['minrad_spi'])+" ;inner radius\n")
				elif re.match("x37", line):
					### rotational search outer radius
					lf.write("x37="+str(self.params['maxrad_spi'])+" ;outer radius\n")
				elif re.match("x38", line):
					### limit angular search to this range within the Euler angles for the particle (in degrees)
					lf.write("x38="+str(self.params['angle_change'])+" ;angle change (delta)\n")
				elif re.match("x99", line):
					### number of processors
					lf.write("x99=%d ;number of processors\n"%(self.params['nproc']))
					modify = False
				else:
					lf.write(line)
			else:
				lf.write(line)
	
		gf.close()
		lf.close()
			
		return localbatch

	#======================
	def runSpiderAlignment(self, instack, outstack, templatestack, localbatch):
		"""
		if specified, runs a SPIDER instead of IMAGIC alignment for each iteration
		"""
		
		### convert to SPIDER format
		self.convertSpiderFormat(instack[:-4], instack[:-4])
		self.convertSpiderFormat(templatestack[:-4], templatestack[:-4])
		
		### set SPPROC_DIR environment variable
		spiprocdir = self.params['rundir']

		### run Alignment for this iteration
		mySpider = spyder.SpiderSession(logo=True, spiderprocdir=spiprocdir, projext=".spi", term=True, verbose=True)
		batchheadname = localbatch.split('.')[0]
		mySpider.toSpider("@%s" % batchheadname)
		mySpider.close()
		
		### convert back to IMAGIC format
		self.convertSpiderFormat(outstack[:-4], outstack[:-4], spider_to_imagic=True)
				
	#======================
	def upload3dRunData(self):
		"""
		uploads the general data for this refinement
		"""
		
		refineq = appiondata.ApImagic3dRefineRunData()
		if self.params['stackid'] is not None:
			refineq['project|projects|project'] = apProject.getProjectIdFromStackId(self.params['stackid'])
		refineq['runname'] = self.params['runname']
		refineq['initialModel'] = appiondata.ApInitialModelData.direct_query(self.params['modelid'])
		refineq['description'] = self.params['description']
		refineq['pixelsize'] = self.params['apix']
		refineq['boxsize'] = self.params['boxsize']
		refineq['path'] = appiondata.ApPathData(path=os.path.dirname(os.path.abspath(self.params['rundir'])))
		refineq['hidden'] = False
		if self.params['commit'] is True and self.params['itn'] == 1:
			refineq.insert()
		self.refinedata = refineq
		return


	#======================
	def upload3dIterationData(self):
		"""
		uploads the data for each iteration
		"""
		
		itnq = appiondata.ApImagic3dRefineIterationData()
		itnq['refinement_run'] = self.refinedata
		itnq['iteration'] = self.params['itn']
#		itnq['name'] = "masked_3d"+str(self.params['itn'])+"_ordered"+str(self.params['itn'])+"_repaligned.mrc"
		itnq['name'] = "3d"+str(self.params['itn'])+"_ordered"+str(self.params['itn'])+"_repaligned.mrc"
		itnq['filt_stack'] = self.params['filt_stack']
		itnq['hp_filt'] = self.params['hp_filt']
		itnq['lp_filt'] = self.params['lp_filt']
		itnq['auto_filt_stack'] = self.params['auto_filt_stack']
		itnq['auto_lp_filt_fraction'] = self.params['auto_lp_filt_fraction']
		itnq['mask_val'] = self.params['mask_val']
		itnq['mirror_refs'] = self.params['mirror_refs']
		itnq['cent_stack'] = self.params['cent_stack']
		itnq['max_shift_orig'] = self.params['max_shift_orig']
		itnq['max_shift_this'] = self.params['max_shift_this']
		itnq['sampling_parameter'] = self.params['samp_param']
		itnq['minrad'] = self.params['minrad']
		itnq['maxrad'] = self.params['maxrad']
		itnq['spider_align'] = self.params['spider_align']
		itnq['xy_search'] = self.params['xy_search']
		itnq['xy_step'] = self.params['xy_step']
		itnq['minrad_spi'] = self.params['minrad_spi']
		itnq['maxrad_spi'] = self.params['maxrad_spi']
		itnq['angle_change'] = self.params['angle_change']
		itnq['ignore_images'] = self.params['ignore_images']
		itnq['ignore_members'] = self.params['ignore_members']
		itnq['keep_classes'] = self.params['keep_classes']
		itnq['num_classums'] = self.params['numclasses']
		itnq['num_factors'] = self.params['num_eigenimages']
		itnq['euler_ang_inc'] = self.params['euler_ang_inc']
		itnq['keep_ordered'] = self.params['keep_ordered']
		itnq['ham_win'] = self.params['ham_win']
		itnq['obj_size'] = self.params['object_size']
		itnq['3d_lpfilt'] = self.params['threedfilt']
		itnq['amask_dim'] = self.params['amask_dim']
		itnq['amask_lp'] = self.params['amask_lp']
		itnq['amask_sharp'] = self.params['amask_sharp']
		itnq['amask_thresh'] = self.params['amask_thresh']
		itnq['mra_ang_inc'] = self.params['mrarefs_ang_inc']
		itnq['forw_ang_inc'] = self.params['forw_ang_inc']
		itnq['symmetry'] = apSymmetry.findSymmetry(self.params['symmetry'])
		if self.params['commit'] is True:
			itnq.insert()
		return

	#=====================
	def start(self):
		"""
		main portion of the program called by appionScript
		"""

		### get stack data
		self.stack = {}
		self.stack['data'] = apStack.getOnlyStackData(self.params['stackid'])
		self.stack['apix'] = apStack.getStackPixelSizeFromStackId(self.params['stackid'])
		self.stack['boxsize'] = apStack.getStackBoxsize(self.params['stackid'])
		self.stack['file'] = os.path.join(self.stack['data']['path']['path'], self.stack['data']['name'])
		stackhedfile = self.stack['file']
		stackimgfile = self.stack['file'][:-4]+".img"
		self.params['apix'] = self.stack['apix']
		self.params['boxsize'] = self.stack['boxsize']

		### ONLY FOR THE FIRST ITERATION
		if self.params['itn'] == 1:
			# copy stack from initial model directory to working directory
			cmd1 = "ln -s "+stackimgfile+" "+os.path.join(self.params['rundir'], "start.img")
			proc = subprocess.Popen(cmd1, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			proc.wait()
			cmd2 = "ln -s "+stackhedfile+" "+os.path.join(self.params['rundir'], "start.hed")
			proc = subprocess.Popen(cmd2, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			proc.wait()
			
			### set machine stamp in headers to avoid IMAGIC errors
			apImagicFile.setMachineStampInImagicHeader(os.path.join(self.params['rundir'], "start.hed"))

			### get initial model data & copy to working directory
			self.model = {}
			modeldata = appiondata.ApInitialModelData.direct_query(self.params['modelid'])
			self.model['apix'] = modeldata['pixelsize']
			self.model['box'] = modeldata['boxsize']
			origmodel = os.path.join(modeldata['path']['path'], modeldata['name'])
			modelfile = os.path.join(self.params['rundir'], "threed0.mrc")
			shutil.copyfile(origmodel, modelfile)

			### scale model
			if self.params['apix'] != self.model['apix'] or self.params['boxsize'] != self.model['boxsize']:
				apVolume.rescaleModel(modelfile, modelfile, self.model['apix'], self.params['apix'], self.params['boxsize'])

			### create forward projections for MRA and Angular Reconstitution (anchor set)
			batchfile = self.startFiles(modelfile)
			proc = subprocess.Popen('chmod 755 '+batchfile, shell=True)
			proc.wait()
			apParam.runCmd(batchfile, "IMAGIC")
			apIMAGIC.checkLogFileForErrors(os.path.join(self.params['rundir'], "startFiles.log"))

		### CONTINUE WITH CONSECUTIVE ITERATIONS ###

		print "... stack pixel size: "+str(self.params['apix'])
		print "... stack box size: "+str(self.params['boxsize'])

		time3dRefine = time.time()

		### create & execute batch file for IMAGIC prior to MRA
		batchfile = self.createImagicBatchFile_1()
		proc = subprocess.Popen('chmod 755 '+batchfile, shell=True)
		proc.wait()
		apDisplay.printMsg("Running IMAGIC .batch file: See imagic3dRefine_"+str(self.params['itn'])+".log for details")
		apParam.runCmd(batchfile, "IMAGIC")
		
		### run MRA, using either SPIDER or IMAGIC
		apDisplay.printMsg("running alignment")
		self.runAlignment()
		
		### create & execute batch file for IMAGIC after MRA
		batchfile = self.createImagicBatchFile_2()
		proc = subprocess.Popen('chmod 755 '+batchfile, shell=True)
		proc.wait()
		apDisplay.printMsg("Running IMAGIC .batch file: See imagic3dRefine_"+str(self.params['itn'])+".log for details")
		apParam.runCmd(batchfile, "IMAGIC")
		
		### check for any errors in any of the subroutines
		logfile = os.path.join(self.params['rundir'], "imagic3dRefine_"+str(self.params['itn'])+".log")
		apIMAGIC.checkLogFileForErrors(logfile)

		time3dRefine = time.time() - time3dRefine
		apDisplay.printColor("finished IMAGIC in "+apDisplay.timeString(time.time()-time3dRefine), "cyan")

		### define resulting 3-D densities
#		mrcname = self.params['rundir']+"/masked_3d"+str(self.params['itn'])+"_ordered"+str(self.params['itn'])+"_repaligned.mrc"
#		mrcnamerot = self.params['rundir']+"/masked_3d"+str(self.params['itn'])+"_ordered"+str(self.params['itn'])+"_repaligned.mrc.rot.mrc"
		mrcname = self.params['rundir']+"/3d"+str(self.params['itn'])+"_ordered"+str(self.params['itn'])+"_repaligned.mrc"
		mrcnamerot = self.params['rundir']+"/3d"+str(self.params['itn'])+"_ordered"+str(self.params['itn'])+"_repaligned.mrc.rot.mrc"

		### use EMAN to normalize density & rotate model azimuthaly by 90 degrees
		apEMAN.executeEmanCmd('proc3d %s %s apix=%f norm' % (mrcname, mrcname, self.params['apix']))
		apEMAN.executeEmanCmd('proc3d %s %s apix=%f rot=0,90,0 norm' % (mrcname, mrcnamerot, self.params['apix']))

		### optional thresholding based on specified size
		if self.params['mass'] is not None:
			volumecmd1 = "volume "+mrcname+" "+str(self.params['apix'])+" set="+str(self.params['mass'])
			volumecmd2 = "volume "+mrcnamerot+" "+str(self.params['apix'])+" set="+str(self.params['mass'])
			apEMAN.executeEmanCmd(volumecmd1)
			apEMAN.executeEmanCmd(volumecmd2)

		### create chimera slices of densities ******* .log file has caused problems if not removed
		apFile.removeFile(os.path.join(self.params['rundir'], "chimera.log"))
		apChimera.renderSnapshots(mrcname, contour=self.params['contour'], zoom=self.params['zoom'], sym='c1')
		apFile.removeFile(os.path.join(self.params['rundir'], "chimera.log"))
		apChimera.renderSnapshots(mrcnamerot, contour=self.params['contour'], zoom=self.params['zoom'], sym='c1')
#			apFile.removeFile(os.path.join(self.params['rundir'], "chimera.log"))
#			apChimera.renderAnimation(mrcname, contour=self.params['contour'], zoom=self.params['zoom'], sym='c1')

		### remove unwanted files
		prevmra = os.path.join(self.params['rundir'], "mra"+str(self.params['itn']-1)+".img")
		prevmra_spider = os.path.join(self.params['rundir'], "mra"+str(self.params['itn']-1)+".spi")
		prevtemp_spider = os.path.join(self.params['rundir'], "mrarefs_3d"+str(self.params['itn']-1)+".spi") 
		while os.path.isfile(prevmra):
			apFile.removeStack(prevmra)
			if self.params['spider_align'] is True:
				while os.path.isfile(prevmra_spider):
					apFile.removeFile(prevmra_spider)
				while os.path.isfile(prevtemp_spider):
					apFile.removeFile(prevtemp_spider)
#			if self.params['itn'] == self.params['numiters']:
#				startstack = os.path.join(self.params['rundir'], "start.img")
#				mrastack = os.path.join(self.params['rundir'], "mra"+str(self.params['itn'])+".img")
#				while os.path.isfile(startstack):
#					apFile.removeStack(startstack)
#				while os.path.isfile(mrastack):
#					apFile.removeStack(mrastack)

		### upload density
		self.upload3dRunData()

		self.upload3dIterationData()

		apDisplay.printMsg("IMAGIC .batch run for iteration "+str(self.params['itn'])+" is complete")

		return




#=====================
#=====================
if __name__ == '__main__':
	imagic3dRefine = imagic3dRefineScript()
	imagic3dRefine.start()
	imagic3dRefine.close()


