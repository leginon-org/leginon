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
import appionData

import apParam
import apChimera
import apDisplay
import apEMAN
import apIMAGIC
import apFile
import apSymmetry
import apDatabase
import apStack
import apProject
import apFile
import apVolume


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
		self.parser.add_option("--numiters", dest="numiters", type="int",
			help="total number of iterations", metavar="int")
		self.parser.add_option("--itn", dest="itn", type="int",
			help="number of this iteration", metavar="int")
		self.parser.add_option("--symmetry", dest="symmetry", type="int",
			help="symmetry of the object", metavar="INT")
		self.parser.add_option("--radius", dest="radius", type="int", default=0.7,
			help="particle radius (in pixels): this is used for MRA and MSA", metavar="INT")
			
		### MRA
		self.parser.add_option("--mrarefs_ang_inc", dest="mrarefs_ang_inc", type="int",	default=25,
			help="angular increment of reprojections for MRA", metavar="INT")
		self.parser.add_option("--max_shift_orig", dest="max_shift_orig", type="float", default=0.2,
			help="maximum radial shift during MRA", metavar="float")	
		self.parser.add_option("--max_shift_this", dest="max_shift_this", type="float", default=0.05,
			help="maximum radial shift during MRA for this iteration", metavar="float")
		self.parser.add_option("--samp_param", dest="samp_param", type="int", default=8,
			help="used to define precision of rotational alignment during MRA", metavar="int")
		
		### MSA
		self.parser.add_option("--ignore_images", dest="ignore_images", type="int", default=10,
			help="percentage of images to ignore when constructing classes", metavar="INT")
		self.parser.add_option("--ignore_members", dest="ignore_members", type="int", default=10,
			help="percentage of worst class members to ignore", metavar="INT")
		self.parser.add_option("--num_classes", dest="numclasses", type="int",
			help="total number of classes created with MSA classify", metavar="INT")
			
		### angular reconstitution
		self.parser.add_option("--forw_ang_inc", dest="forw_ang_inc", type="int", default=25,
			help="angular increment of reprojections for euler angle refinement", metavar="INT")
		self.parser.add_option("--euler_ang_inc", dest="euler_ang_inc", type="int", default=10,
			help="angular increment for euler angle search", metavar="INT")		
			
		### threed & automasking params
		self.parser.add_option("--ham_win", dest="ham_win", type="float", default=0.8,
			help="similar to lp-filtering parameter that determines detail in 3d map", metavar="float")
		self.parser.add_option("--object_size", dest="object_size", type="float", default=0.8,
			help="object size as fraction of image size", metavar="float")
		self.parser.add_option("--amask_dim", dest="amask_dim", type="float", default=0.04,
			help="automasking parameter determined by smallest object size", metavar="float")
		self.parser.add_option("--amask_lp", dest="amask_lp", type="float", default=0.15,
			help="automasking parameter for low-pass filtering", metavar="float")
		self.parser.add_option("--amask_sharp", dest="amask_sharp", type="float", default=0.15,
			help="automasking parameter that determines sharpness of mask", metavar="float")
		self.parser.add_option("--amask_thresh", dest="amask_thresh", type="float", default=15,
			help="automasking parameter that determines object thresholding", metavar="float")

		### parameters for keeping images
		self.parser.add_option("--keep_classes", dest="keep_classes", type="int", default=0.9,
			help="Fraction of classified images to keep (based on the overall quality of the class average)", metavar="INT")
		self.parser.add_option("--keep_ordered", dest="keep_ordered", type="int", default=0.9,
			help="Fraction of ordered images to keep (based on error in angular reconstitution)", metavar="INT")

		### mass specified for eman volume function
		self.parser.add_option("--mass", dest="mass", type="int",
			help="OPTIONAL: used for thresholding volume of a 3d map to 1 based on given mass", metavar="INT")
                        
		### chimera only, if the run is already completed
		self.parser.add_option("--chimera-only", dest="chimera-only", default=False,
			action="store_true", help="use only if you want to regenerate chimera slices from an already existing model: input rundir and runname")
		self.parser.add_option("--contour", dest="contour", type="float", default=1.0,
			help="threshold value for chimera volume", metavar="#")
		self.parser.add_option("--zoom", dest="zoom", type="float", default=1.0,
			help="threshold value for chimera volume", metavar="#")
		self.parser.add_option("--iterations", dest="iterations", type="str",
			help="list of iterations for which you would like chimera slices generated, separated by comma", metavar="1,2,5...")

		return 

	#=====================
	def checkConflicts(self):
	
		### chimera only
		if self.params['chimera-only'] is True:
			if self.params['rundir'] is None:
				apDisplay.printError("Please specify the directory in which your files are located")
			if self.params['iterations'] is None:
				apDisplay.printError("Please specify the iterations for which you need chimera slices generated (e.g. \"1,2,5\")")
			else:
				stringlist = self.params['iterations'].split(",")
				self.itlist = [int(v) for v in stringlist]
		
			return
		
		### otherwise go on with the reconstruction
		else:
	
			if self.params['itn'] is None:
				apDisplay.printError("enter iteration number")
			if self.params['symmetry'] is None:
				apDisplay.printError("enter object symmetry")
			if self.params['numclasses'] is None:
				apDisplay.printError("enter number of classes used for creating 3d0")

			if self.params['stackid'] is None:
				apDisplay.printError("enter a stack ID for the stack that will be used in the refinement")
			if self.params['imagic3d0id'] is None and self.params['modelid'] is None:
				apDisplay.printError("enter an imagic 3d0 id or model id for the refinement")
		
			return

	#=====================
	def setRunDir(self):
	
		if self.params['imagic3d0id'] is not None:
			modeldata = appionData.ApImagic3d0Data.direct_query(self.params['imagic3d0id'])
			path = os.path.join(modeldata['path']['path'], modeldata['runname'])
		elif self.params['modelid'] is not None:
			print "NEED TO SET RECON PATH ... NOT WORKING YET"
		else:
			apDisplay.printError("3d0 initial model not in database")

		self.params['rundir'] = os.path.join(path, self.params['runname'])

	#=======================
	def createImagicBatchFileHeaders(self):
		# this is for deleting header information that may interfere with the batch file
		filename = os.path.join(self.params['rundir'], "headers.batch")
		
		f = open(filename, 'w')	
		f.write("#!/bin/csh -f\n")	
		f.write("setenv IMAGIC_BATCH 1\n")
		f.write("cd "+str(self.params['rundir'])+"\n")
		f.write("rm -f ordered0.*\n") 		
		f.write("rm -f sino_ordered0.*\n")	
		f.write("/usr/local/IMAGIC/stand/headers.e <<EOF > imagic3dRefine_"+str(self.params['itn'])+".log\n")
		f.write("start\n")
		f.write("write\n")
		f.write("wipe\n")
		f.write("all\n")
		f.write("EOF\n")
		f.write("/usr/local/IMAGIC/stand/copyim.e <<EOF >> imagic3dRefine_"+str(self.params['itn'])+".log\n")
		f.write("start\n")
		f.write("start_originalsformra\n")
		f.write("EOF\n")
		f.write("/usr/local/IMAGIC/stand/headers.e <<EOF >> imagic3dRefine_"+str(self.params['itn'])+".log\n")
		f.write("start_originalsformra\n")
		f.write("write\n")
		f.write("wipe\n")
		f.write("shift\n")
		f.write("EOF\n")
		f.close()
		
		return filename

	def startFiles(self, modelfile):
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
		f.write("%.3f,%.3f,%.3f\n"% (self.params['apix'], self.params['apix'], self.params['apix']))
		f.write("YES\n")
		f.write("0\n")
		f.write("EOF\n")

		### forward project to create references for MRA
		f.write("/usr/local/IMAGIC/threed/forward.e SURF FORWARD <<EOF >> startFiles.log\n")
		f.write(basename[:-4]+"\n")
		f.write("-99999\n")
		f.write("PROJECTIONS\n")
		f.write("YES\n")
		f.write("mrarefs_masked_3d"+str(self.params['itn']-1)+"\n")
		f.write("ASYM_TRIANGLE\n")
		f.write(symmetry+"\n")		
		f.write("EQUIDIST\n")
		f.write("ZERO\n")
		f.write(str(self.params['mrarefs_ang_inc'])+"\n")		
		f.write("EOF\n")
		
		### forward project to create euler angle anchor set
		f.write("/usr/local/IMAGIC/threed/forward.e SURF FORWARD <<EOF >> startFiles.log\n")
		f.write(basename[:-4]+"\n")
		f.write("-99999\n")
		f.write("PROJECTIONS\n")
		f.write("YES\n")
		f.write("masked_3d"+str(self.params['itn']-1)+"_ordered"+str(self.params['itn']-1)+"_repaligned_forward\n")
		f.write("ASYM_TRIANGLE\n")
		f.write(symmetry+"\n")		
		f.write("EQUIDIST\n")
		f.write("ZERO\n")
		f.write(str(self.params['forw_ang_inc'])+"\n")		
		f.write("EOF\n\n")
	
		### make a mask for use in MSA	
		radius = float(self.params['radius']) / self.params['boxsize']
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
	def createImagicBatchFile(self):
		# IMAGIC batch file creation
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
			f.write("masked_3d"+str(self.params['itn']-1)+"_ordered"+str(self.params['itn']-1)+"_repaligned\n")
			f.write("-99999\n")
			f.write("PROJECTIONS\n")
			f.write("YES\n")
#			f.write("WIDENING\n")
			f.write("mrarefs_masked_3d"+str(self.params['itn']-1)+"\n")
			f.write("ASYM_TRIANGLE\n")
			f.write(symmetry+"\n")		
			f.write("EQUIDIST\n")
			f.write("ZERO\n")
			f.write(str(self.params['mrarefs_ang_inc'])+"\n")		
			f.write("EOF\n")
			
			f.write("/usr/local/IMAGIC/threed/forward.e SURF FORWARD <<EOF >> imagic3dRefine_"+str(self.params['itn'])+".log\n")
			f.write("masked_3d"+str(self.params['itn']-1)+"_ordered"+str(self.params['itn']-1)+"_repaligned\n")
			f.write("-99999\n")
			f.write("PROJECTIONS\n")
			f.write("YES\n")
#			f.write("WIDENING\n")
			f.write("masked_3d"+str(self.params['itn']-1)+"_ordered"+str(self.params['itn']-1)+"_repaligned_forward\n")
			f.write("ASYM_TRIANGLE\n")
			f.write(symmetry+"\n")		
			f.write("EQUIDIST\n")
			f.write("ZERO\n")
			f.write(str(self.params['forw_ang_inc'])+"\n")		
			f.write("EOF\n\n")
		
		### first do a multi reference alignment of entire stack, using forward projections as references
		radius = float(self.params['radius']) / self.params['boxsize']
		if radius > 1:
			radius = 1
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
		f.write("mrarefs_masked_3d"+str(self.params['itn']-1)+"\n")
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
		f.write("0.0,"+str(radius)+"\n")			
		f.write("5\n")			
		f.write("NO\n")
		f.write("EOF\n")

		### Perform multivariate statistical analysis on aligned stack
		f.write("/usr/local/IMAGIC/msa/msa.e <<EOF >> imagic3dRefine_"+str(self.params['itn'])+".log\n")
		f.write("NO\n")
		f.write("FRESH_MSA\n")
		f.write("modulation\n")
		f.write("mra"+str(self.params['itn'])+"\n")
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
		f.write("69\n")
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
		f.write("DOWN\n")
		f.write(str(keep_classums)+"\n")
		f.write("EOF\n")
		f.write("/usr/local/IMAGIC/stand/im_rename.e <<EOF >> imagic3dRefine_"+str(self.params['itn'])+".log\n")
		f.write("classums_"+str(self.params['itn'])+"_sorted\n")
		f.write("classums_"+str(self.params['itn'])+"\n")
		f.write("EOF\n")
		
		### calculate euler angles, using anchor set for references
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
		f.write("masked_3d"+str(self.params['itn']-1)+"_ordered"+str(self.params['itn']-1)+"_repaligned_forward\n")
		f.write("arsino_masked_3d"+str(self.params['itn']-1)+"_ordered"+str(self.params['itn']-1)+"_repaligned_forward\n")
		f.write("my_sine\n")
		f.write("YES\n")
		f.write(str(self.params['euler_ang_inc'])+"\n")	
		f.write("YES\n")
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
		
		### build another 3d, this time from the orderes, sorted, and aligned class averages
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

		### automask the 3d, automasking is based on modulation analysis
		f.write("/usr/local/IMAGIC/threed/automask3d.e <<EOF >> imagic3dRefine_"+str(self.params['itn'])+".log\n")
		f.write("DO_IT_ALL\n")
		f.write("3d"+str(self.params['itn'])+"_ordered"+str(self.params['itn'])+"_repaligned\n")
		f.write("3d"+str(self.params['itn'])+"_ordered"+str(self.params['itn'])+"_repaligned_modvar\n")
		f.write("YES\n")
		f.write(str(self.params['amask_dim'])+","+str(self.params['amask_lp'])+"\n")		
		f.write(str(self.params['amask_sharp'])+"\n")			
		f.write("AUTOMATIC\n")
		f.write(str(self.params['amask_thresh'])+"\n")			
		f.write("mask_3d"+str(self.params['itn'])+"_ordered"+str(self.params['itn'])+"_repaligned\n")
		f.write("masked_3d"+str(self.params['itn'])+"_ordered"+str(self.params['itn'])+"_repaligned\n")
		f.write("EOF\n")
		
		### use EM2EM to convert 3d from IMAGIC to MRC format
		f.write("/usr/local/IMAGIC/stand/em2em.e <<EOF >> imagic3dRefine_"+str(self.params['itn'])+".log\n")
		f.write("IMAGIC\n")
		f.write("MRC\n")
		f.write("3D\n")
		f.write("masked_3d"+str(self.params['itn'])+"_ordered"+str(self.params['itn'])+"_repaligned\n")
		f.write("masked_3d"+str(self.params['itn'])+"_ordered"+str(self.params['itn'])+"_repaligned.mrc\n")
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
		f.write(str(self.params['boxsize'])+"\n")			
		f.write("EOF\n")
		
		f.close()
		
		return filename

	#======================
	def upload3dRunData(self):
		refineq = appionData.ApImagic3dRefineRunData()
		if self.params['stackid'] is not None:
			refineq['project|projects|project'] = apProject.getProjectIdFromStackId(self.params['stackid'])
		refineq['runname'] = self.params['runname']
		refineq['imagic3d0run'] = appionData.ApImagic3d0Data.direct_query(self.params['imagic3d0id'])
		refineq['description'] = self.params['description']
		refineq['pixelsize'] = self.params['apix']
		refineq['boxsize'] = self.params['boxsize']
		refineq['path'] = appionData.ApPathData(path=os.path.dirname(os.path.abspath(self.params['rundir'])))
		refineq['hidden'] = False
		if self.params['commit'] is True and self.params['itn'] == 1:
			refineq.insert()
		self.refinedata = refineq
		return 
		
		
	#======================	
	def upload3dIterationData(self):
		itnq = appionData.ApImagic3dRefineIterationData()
		itnq['refinement_run'] = self.refinedata
		itnq['iteration'] = self.params['itn']
		itnq['name'] = "masked_3d"+str(self.params['itn'])+"_ordered"+str(self.params['itn'])+"_repaligned.mrc"
		itnq['max_shift_orig'] = self.params['max_shift_orig']
		itnq['max_shift_this'] = self.params['max_shift_this']
		itnq['sampling_parameter'] = self.params['samp_param']
		itnq['euler_ang_inc'] = self.params['euler_ang_inc']
		itnq['ham_win'] = self.params['ham_win']
		itnq['obj_size'] = self.params['object_size']
#		itnq['repalignments'] = self.params['repalignments']
		itnq['amask_dim'] = self.params['amask_dim']
		itnq['amask_lp'] = self.params['amask_lp']
		itnq['amask_sharp'] = self.params['amask_sharp']
		itnq['amask_thresh'] = self.params['amask_thresh']
		itnq['mra_ang_inc'] = self.params['mrarefs_ang_inc']
		itnq['forw_ang_inc'] = self.params['forw_ang_inc']
#		itnq['num_classums'] = self.params['num_classums']
		itnq['symmetry'] = apSymmetry.findSymmetry(self.params['symmetry'])
		if self.params['commit'] is True:
			itnq.insert()
		return

	#=====================
	def start(self):
	
		### chimera only
		if self.params['chimera-only'] is True:
			for item in self.itlist:
				mrcname = self.params['rundir']+"/masked_3d"+str(item)+"_ordered"+str(item)+"_repaligned.mrc"
				mrcnamerot = self.params['rundir']+"/masked_3d"+str(item)+"_ordered"+str(item)+"_repaligned.mrc.rot.mrc"
	
				### create chimera slices of densities
				apChimera.renderSnapshots(mrcname, contour=self.params['contour'], zoom=self.params['zoom'], sym='c1')
				apChimera.renderAnimation(mrcname, contour=self.params['contour'], zoom=self.params['zoom'], sym='c1')
				apChimera.renderSnapshots(mrcnamerot, contour=self.params['contour'], zoom=self.params['zoom'], sym='c1')

			return
		
		### otherwise go on with the reconstruction
		else:
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
				
				### figure out which model is being used (i.e. from 3d0 run or uploaded initial model)
				if self.params['imagic3d0id'] is not None:
					self.model = {}
					modeldata = appionData.ApImagic3d0Data.direct_query(self.params['imagic3d0id'])
					self.model['boxsize'] = modeldata['boxsize']
					self.model['apix'] = modeldata['pixelsize']			
					orig_path = os.path.join(modeldata['path']['path'], modeldata['runname'])
					modelfile = os.path.join(self.params['rundir'], "threed0.mrc")
					shutil.copyfile(os.path.join(orig_path, "masked_3d0_ordered0_repaligned.mrc"), modelfile)
				else:
					########## GET MODEL DATA #############
					if self.params['modelid'] is not None:
						self.model = {}
						modeldata = appionData.ApInitialModelData.direct_query(self.params['modelid'])
						self.model['apix'] = modeldata['pixelsize']
						self.model['box'] = modeldata['boxsize']
						origmodel = os.path.join(modeldata['path']['path'], modeldata['name'])
						modelfile = os.path.join(self.params['rundir'], "threed0.mrc")
					else:
						apDisplay.printError("Initial model not in the database")
					shutil.copyfile(origmodel, modelfile) 
					
				### scale model
				if self.params['apix'] != self.model['apix'] or self.params['boxsize'] != self.model['boxsize']:
					apVolume.rescaleModel(modelfile, modelfile, self.model['apix'], self.params['apix'], self.params['boxsize'])
				
				### create MRA and forward projections (anchor set)
				batchfile = self.startFiles(modelfile)
				proc = subprocess.Popen('chmod 755 '+batchfile, shell=True)
				proc.wait()
				apIMAGIC.executeImagicBatchFile(batchfile)
				logfile = open(os.path.join(self.params['rundir'], "startFiles.log"))
				loglines = logfile.readlines()
				for line in loglines:
					if re.search("ERROR in program", line):
						apDisplay.printError("ERROR IN IMAGIC SUBROUTINE, please check the logfile: startFiles.log")
				
#				### delete headers
#				apIMAGIC.copyFile(self.params['rundir'], "start.hed", headers=True)


			### CONTINUE WITH CONSECUTIVE ITERATIONS ###
		
			print "... stack pixel size: "+str(self.params['apix'])
			print "... stack box size: "+str(self.params['boxsize'])	
			apDisplay.printMsg("Running IMAGIC .batch file: See imagic3dRefine_"+str(self.params['itn'])+".log for details")
		
			### create batch file for execution with IMAGIC
			batchfile = self.createImagicBatchFile()
			
			### execute batch file that was created
			time3dRefine = time.time()
			proc = subprocess.Popen('chmod 755 '+batchfile, shell=True)
			proc.wait()
			apIMAGIC.executeImagicBatchFile(batchfile)
			logfile = open(os.path.join(self.params['rundir'], "imagic3dRefine_"+str(self.params['itn'])+".log"))
			loglines = logfile.readlines()
			for line in loglines:
				if re.search("ERROR in program", line):
					apDisplay.printError("ERROR IN IMAGIC SUBROUTINE, please check the logfile: imagic3dRefine_"+str(self.params['itn'])+".log")
			apDisplay.printColor("finished IMAGIC in "+apDisplay.timeString(time.time()-time3dRefine), "cyan")
			time3dRefine = time.time() - time3dRefine

			mrcname = self.params['rundir']+"/masked_3d"+str(self.params['itn'])+"_ordered"+str(self.params['itn'])+"_repaligned.mrc"
			mrcnamerot = self.params['rundir']+"/masked_3d"+str(self.params['itn'])+"_ordered"+str(self.params['itn'])+"_repaligned.mrc.rot.mrc"

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
#			apFile.removeFile(os.path.join(self.params['rundir'], "chimera.log"))
#			apChimera.renderSnapshots(mrcname, contour=self.params['contour'], zoom=self.params['zoom'], sym='c1')
#			apFile.removeFile(os.path.join(self.params['rundir'], "chimera.log"))
#			apChimera.renderSnapshots(mrcnamerot, contour=self.params['contour'], zoom=self.params['zoom'], sym='c1')
#			apFile.removeFile(os.path.join(self.params['rundir'], "chimera.log"))
#			apChimera.renderAnimation(mrcname, contour=self.params['contour'], zoom=self.params['zoom'], sym='c1')

			### remove unwanted files
			prevmra = os.path.join(self.params['rundir'], "mra"+str(self.params['itn']-1)+".img")
			while os.path.isfile(prevmra):
				apFile.removeStack(prevmra)

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
		
