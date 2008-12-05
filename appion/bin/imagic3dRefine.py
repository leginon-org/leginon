#!/usr/bin/env python
# Python script to upload a template to the database, and prepare images for import




#####
######
######
#####			GET NUMBER OF CLASSUMS FROM REFERENCE FREE CLASSIFICATION 
#####
#####



import os

import sys
import re
import shutil
import appionScript
import appionData

import apParam
import apRecon
import apDisplay
import apEMAN
import apFile
import apUpload
import apDatabase
import apStack
import apProject


#=====================
#=====================
class imagic3dRefineScript(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage( "Usage: %prog --file=<name> --apix=<pixel> --outdir=<dir> "
			+"[options]")

		self.parser.add_option("--imagic3d0Id", dest="imagic3d0Id",
			help="ID of 3d0 used to initiate refinement", metavar="int")
		self.parser.add_option("--norefClassId", dest="norefClassId",
			help="ID of noref class averages used in refinement", metavar="int")	
		self.parser.add_option("--numiters", dest="numiters", type="int",
			help="total number of iterations", metavar="int")
		self.parser.add_option("--itn", dest="itn", type="int",
			help="number of this iteration", metavar="int")
		self.parser.add_option("--symmetry", dest="symmetry", type="str",
			help="symmetry of the object", metavar="STR")
		self.parser.add_option("--max_shift_orig", dest="max_shift_orig", type="float",
			help="maximum radial shift during MRA", metavar="float")	
		self.parser.add_option("--max_shift_this", dest="max_shift_this", type="float",
			help="maximum radial shift during MRA for this iteration", metavar="float")
		self.parser.add_option("--samp_param", dest="samp_param", type="int",
			help="used to define precision of rotational alignment during MRA", metavar="int")
		self.parser.add_option("--euler_ang_inc", dest="euler_ang_inc", type="int", #default=10,
			help="angular increment for euler angle search", metavar="INT")
		self.parser.add_option("--num_classums", dest="num_classums", type="int",
			help="total number of classums used for 3d0 construction", metavar="INT")	
		self.parser.add_option("--ham_win", dest="ham_win", type="float", 
			help="similar to lp-filtering parameter that determines detail in 3d map", metavar="float")
		self.parser.add_option("--object_size", dest="object_size", type="float", #default=0.8
			help="object size as fraction of image size", metavar="float")	
		self.parser.add_option("--repalignments", dest="repalignments", type="int",
			help="number of alignments to reprojections", metavar="INT")
		self.parser.add_option("--amask_dim", dest="amask_dim", type="float",
			help="automasking parameter determined by smallest object size", metavar="float")
		self.parser.add_option("--amask_lp", dest="amask_lp", type="float",
			help="automasking parameter for low-pass filtering", metavar="float")
		self.parser.add_option("--amask_sharp", dest="amask_sharp", type="float",
			help="automasking parameter that determines sharpness of mask", metavar="float")
		self.parser.add_option("--amask_thresh", dest="amask_thresh", type="float",
			help="automasking parameter that determines object thresholding", metavar="float")
		self.parser.add_option("--mrarefs_ang_inc", dest="mrarefs_ang_inc", type="int",	#default=25
			help="angular increment of reprojections for MRA", metavar="INT")
		self.parser.add_option("--forw_ang_inc", dest="forw_ang_inc", type="int",	#default=25
			help="angular increment of reprojections for euler angle refinement", metavar="INT")
		self.parser.add_option("-o", "--outdir", dest="outdir",
			help="Location to which output file will be saved", metavar="PATH")
		self.parser.add_option("-r", "--runid", dest="runId",
			help="Name assigned to this reclassification", metavar="TEXT")
		self.parser.add_option("--description", dest="description", type="str",
			help="description of run", metavar="STR")
		self.parser.add_option("-C", "--commit", dest="commit", default=True,
			action="store_true", help="Commit template to database")
		self.parser.add_option("--no-commit", dest="commit", default=True,
			action="store_false", help="Do not commit template to database")

		return 

	#=====================
	def checkConflicts(self):
		if self.params['runId'] is None:
			apDisplay.printError("enter a run ID")
		if self.params['itn'] is None:
			apDisplay.printError("enter iteration number")
		if self.params['symmetry'] is None:
			apDisplay.printError("enter object symmetry")
		if self.params['max_shift_orig'] is None:
			apDisplay.printError("enter maximum radial shift during MRA")
		if self.params['max_shift_this'] is None:
			apDisplay.printError("enter maximum radial shift during MRA for this iteration")
		if self.params['samp_param'] is None:
			apDisplay.printError("enter sampling parameter for MRA")
		if self.params['euler_ang_inc'] is None:
			apDisplay.printError("enter euler angle increment")
		if self.params['num_classums'] is None:
			apDisplay.printError("enter number of classums used for creating 3d0")
		if self.params['ham_win'] is None:
			apDisplay.printError("enter value for hamming window")
		if self.params['object_size'] is None:
			apDisplay.printError("enter value for object size as fraction of image size")
		if self.params['repalignments'] is None:
			apDisplay.printError("enter number of alignments to reprojections")
		if self.params['amask_dim'] is None:
			apDisplay.printError("enter automask parameter amask_dim")
		if self.params['amask_lp'] is None:
			apDisplay.printError("enter automask parameter amask_lp")
		if self.params['amask_sharp'] is None:
			apDisplay.printError("enter automask parameter amask_sharp")
		if self.params['amask_thresh'] is None:
			apDisplay.printError("enter automask parameter amask_thresh")
		if self.params['mrarefs_ang_inc'] is None:
			apDisplay.printError("enter angular increment of forward projections for MRA")
		if self.params['forw_ang_inc'] is None:
			apDisplay.printError("enter angular increment of forward projections for euler angle refinement")
		
		return

	#=====================
	def setOutDir(self):
	
		if self.params['imagic3d0Id'] is not None:
			modeldata = appionData.ApImagic3d0Data.direct_query(self.params['imagic3d0Id'])
			path = os.path.join(modeldata['path']['path'], modeldata['runname'])
		else:
			apDisplay.printError("3d0 initial model not in database")

		self.params['outdir'] = os.path.join(path, self.params['runid'])


	def upload3dRunData(self):
		refineq = appionData.ApImagic3dRefineRunData()
		refineq['project|projects|project'] = apProject.getProjectIdFromStackId(self.params['stackid'])
		refineq['runname'] = self.params['runId']
		refineq['norefclass'] = appionData.ApNoRefClassRunData.direct_query(self.params['norefClassId'])
		refineq['imagic3d0run'] = appionData.ApImagic3d0Data.direct_query(self.params['imagic3d0Id'])
		refineq['description'] = self.params['description']
		refineq['pixelsize'] = self.params['apix']
		refineq['boxsize'] = self.params['boxsize']
		refineq['path'] = appionData.ApPathData(path=os.path.dirname(os.path.abspath(self.params['outdir'])))
		refineq['hidden'] = False
		if self.params['commit'] is True and self.params['itn'] == 1:
			refineq.insert()
		self.refinedata = refineq
		return 

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
		itnq['repalignments'] = self.params['repalignments']
		itnq['amask_dim'] = self.params['amask_dim']
		itnq['amask_lp'] = self.params['amask_lp']
		itnq['amask_sharp'] = self.params['amask_sharp']
		itnq['amask_thresh'] = self.params['amask_thresh']
		itnq['mra_ang_inc'] = self.params['mrarefs_ang_inc']
		itnq['forw_ang_inc'] = self.params['forw_ang_inc']
		itnq['num_classums'] = self.params['num_classums']
		itnq['symmetry'] = appionData.ApSymmetryData.direct_query(self.params['symmetry'])
		if self.params['commit'] is True:
			itnq.insert()
		return

	#=====================

	def start(self):
		print self.params
		
		if self.params['imagic3d0Id'] is not None:
			modeldata = appionData.ApImagic3d0Data.direct_query(self.params['imagic3d0Id'])
			self.params['boxsize'] = modeldata['boxsize']
			self.params['apix'] = modeldata['pixelsize']
		else: 
			apDisplay.printError("3d0 initial model not in the database")
		
		
		# refinement is set to proceed against reference-free class averages, not reclassifications, so get norefid	
		if modeldata['norefclass'] is not None:
			norefclassdata = modeldata['norefclass']
			self.params['stackid'] = norefclassdata['norefRun']['stack'].dbid
		elif modeldata['reclass'] is not None:
			reclassid = modeldata['reclass'].dbid
			reclassdata = appionData.ApImagicReclassifyData.direct_query(reclassid)
			norefclassdata = reclassdata['norefclass']
			self.params['stackid'] = norefclassdata['norefRun']['stack'].dbid			
		else:
			apDisplay.printError("no class averages associated with model in the database")
		
		norefpath = norefclassdata['norefRun']['path']['path']
		clsavgfile = norefpath+"/"+norefclassdata['classFile']
		
		
################ 		NEED TO SPECIFY THE NUMBER OF CLASS AVERAGES IN ORIGINAL NOREF FILE 	###################
		
		

# need to copy files from initial model directory to working directory
		orig_path = os.path.join(modeldata['path']['path'], modeldata['runname'])
		mrarefsimg = "mrarefs_masked_3d0.img"
		mrarefshed = "mrarefs_masked_3d0.hed"
		forwimg = "masked_3d0_ordered0_repaligned_forward.img"
		forwhed = "masked_3d0_ordered0_repaligned_forward.hed"
		if os.path.isfile(str(self.params['outdir'])+"/start_stack.img") is False:
			shutil.copyfile(clsavgfile+".img", str(self.params['outdir'])+"/start_stack.img")
		if os.path.isfile(str(self.params['outdir'])+"/start_stack.hed") is False:
			shutil.copyfile(clsavgfile+".hed", str(self.params['outdir'])+"/start_stack.hed")
		if os.path.isfile(str(self.params['outdir'])+"/mrarefs_masked_3d.img") is False:
			shutil.copyfile(orig_path+"/"+mrarefsimg, str(self.params['outdir'])+"/mrarefs_masked_3d.img")
		if os.path.isfile(str(self.params['outdir'])+"/mrarefs_masked_3d.hed") is False:
			shutil.copyfile(orig_path+"/"+mrarefshed, str(self.params['outdir'])+"/mrarefs_masked_3d.hed")
		if os.path.isfile(str(self.params['outdir'])+"/masked_3d_ordered_repaligned_forward.img") is False:
			shutil.copyfile(orig_path+"/"+forwimg, str(self.params['outdir'])+"/masked_3d_ordered_repaligned_forward.img")
		if os.path.isfile(str(self.params['outdir'])+"/masked_3d_ordered_repaligned_forward.hed") is False:
			shutil.copyfile(orig_path+"/"+forwhed, str(self.params['outdir'])+"/masked_3d_ordered_repaligned_forward.hed")
	


		print "... class average pixel size: "+str(self.params['apix'])
		print "... class average box size: "+str(self.params['boxsize'])	
		apDisplay.printMsg("Running IMAGIC .batch file: See imagic3dRefine_"+str(self.params['itn'])+".log for details")
	
		filename = "imagicCreate3dRefine_"+str(self.params['itn'])+".batch"
		f = open(filename, 'w')
		
		
		
		
		
		
		f.write("#!/bin/csh -f\n")	
		f.write("setenv IMAGIC_BATCH 1\n")
		f.write("cd "+str(self.params['outdir'])+"\n")
		f.write("rm -f ordered0.*\n") 		
		f.write("rm -f sino_ordered0.*\n")	
		f.write("/usr/local/IMAGIC/stand/headers.e <<EOF > imagic3dRefine_"+str(self.params['itn'])+".log\n")
		f.write("start_stack\n")
		f.write("write\n")
		f.write("wipe\n")
		f.write("all\n")
		f.write("EOF\n")
		f.write("/usr/local/IMAGIC/stand/copyim.e <<EOF >> imagic3dRefine_"+str(self.params['itn'])+".log\n")
		f.write("start_stack\n")
		f.write("start_stack_originalsformra\n")
		f.write("EOF\n")
		f.write("/usr/local/IMAGIC/stand/headers.e <<EOF >> imagic3dRefine_"+str(self.params['itn'])+".log\n")
		f.write("start_stack_originalsformra\n")
		f.write("write\n")
		f.write("wipe\n")
		f.write("shift\n")
		f.write("EOF\n")
		f.write("/usr/local/IMAGIC/align/mralign.e <<EOF >> imagic3dRefine_"+str(self.params['itn'])+".log\n")
		f.write("NO\n")
		f.write("FRESH\n")
		f.write("ALL\n")
		f.write("ROTATION_FIRST\n")
		f.write("CCF\n")
		f.write("start_stack\n")
		f.write("mra_start_stack\n")
		f.write("start_stack_originalsformra\n")
		f.write("mrarefs_masked_3d\n")
		f.write("no\n")
		f.write("yes\n")
		f.write(str(self.params['max_shift_orig'])+"\n")		
		f.write(str(self.params['max_shift_this'])+"\n")		
		f.write("-180,180\n")
		f.write("-180,180\n")
		f.write("INTERACTIVE\n")
		f.write(str(self.params['samp_param'])+"\n") 		
		f.write("0.0,0.7\n")			
		f.write("5\n")			
		f.write("NO\n")
		f.write("EOF\n")
		f.write("/usr/local/IMAGIC/angrec/euler.e <<EOF >> imagic3dRefine_"+str(self.params['itn'])+".log\n")
		f.write(str(self.params['symmetry'])+"\n")
		lowercase = self.params['symmetry'].lower()
		if lowercase != "c1": 
			f.write("0\n")
		f.write("ANCHOR\n")
		f.write("FRESH\n")
		f.write("IMAGES\n")
		f.write("mra_start_stack\n")
		f.write("sino_mra_start_stack\n")
		f.write("YES\n")
		f.write("0.9\n")
		f.write("IMAGES\n")
		f.write("masked_3d_ordered_repaligned_forward\n")
		f.write("arsino_masked_3d_ordered_repaligned_forward\n")
		f.write("my_sine\n")
		f.write("YES\n")
		f.write(str(self.params['euler_ang_inc'])+"\n")	
		f.write("YES\n")
		f.write("NO\n")
		f.write("YES\n")
		f.write("EOF\n")
		f.write("/usr/local/IMAGIC/incore/excopy.e <<EOF >> imagic3dRefine_"+str(self.params['itn'])+".log\n")
		f.write("SORT\n")
		f.write("mra_start_stack\n")
		f.write("ordered\n")
		f.write("ANGULAR_ERROR\n")
		f.write("UP\n")
		f.write(str(self.params['num_classums'])+"\n")		
		f.write("EOF\n")
		f.write("/usr/local/IMAGIC/threed/true3d.e <<EOF >> imagic3dRefine_"+str(self.params['itn'])+".log\n")
		f.write("NO\n")
		f.write(str(self.params['symmetry'])+"\n") 		
		f.write("YES\n")
		f.write("ordered\n")
		f.write("ANGREC_HEADER_VALUES\n")
		f.write("3d_ordered\n")
		f.write("rep_ordered\n")
		f.write("err_ordered\n")
		f.write("NO\n")
		f.write(str(self.params['ham_win'])+"\n")		
		f.write(str(self.params['object_size'])+"\n")		
		f.write("EOF\n")
		f.write("/usr/local/IMAGIC/align/alipara.e <<EOF >> imagic3dRefine_"+str(self.params['itn'])+".log\n")
		f.write("ALL\n")
		f.write("CCF\n")
		f.write("ordered\n")
		f.write("ordered_repaligned\n")
		f.write("rep_ordered\n")
		f.write("0.2\n")			
		f.write("-180,180\n")
		f.write("5\n")
		f.write("EOF\n")
		f.write("/usr/local/IMAGIC/threed/true3d.e <<EOF >> imagic3dRefine_"+str(self.params['itn'])+".log\n")
		f.write("NO\n")
		f.write(str(self.params['symmetry'])+"\n") 		
		f.write("YES\n")
		f.write("ordered_repaligned\n")
		f.write("ANGREC_HEADER_VALUES\n")
		f.write("3d_ordered_repaligned\n")
		f.write("rep_ordered_repaligned\n")
		f.write("err_ordered_repaligned\n")
		f.write("NO\n")
		f.write(str(self.params['ham_win'])+"\n")		
		f.write(str(self.params['object_size'])+"\n")		
		f.write("EOF\n\n")
		f.write("set j=1\n")
		f.write("while ($j<"+str(self.params['repalignments'])+")\n")
		f.write("/usr/local/IMAGIC/stand/copyim.e <<EOF >> imagic3dRefine_"+str(self.params['itn'])+".log\n")
		f.write("ordered_repaligned\n")
		f.write("to_be_aligned\n")
		f.write("EOF\n")
		f.write("/usr/local/IMAGIC/align/alipara.e <<EOF >> imagic3dRefine_"+str(self.params['itn'])+".log\n")
		f.write("ALL\n")
		f.write("CCF\n")
		f.write("to_be_aligned\n")
		f.write("ordered_repaligned\n")
		f.write("rep_ordered_repaligned\n")
		f.write("0.2\n")			
		f.write("-180,180\n")
		f.write("5\n")
		f.write("EOF\n")
		f.write("/usr/local/IMAGIC/threed/true3d.e <<EOF >> imagic3dRefine_"+str(self.params['itn'])+".log\n")
		f.write("NO\n")
		f.write(str(self.params['symmetry'])+"\n")		
		f.write("YES\n")
		f.write("ordered_repaligned\n")
		f.write("ANGREC_HEADER_VALUES\n")
		f.write("3d_ordered_repaligned\n")
		f.write("rep_ordered_repaligned\n")
		f.write("err_ordered_repaligned\n")
		f.write("NO\n")
		f.write(str(self.params['ham_win'])+"\n")		
		f.write(str(self.params['object_size'])+"\n")	
		f.write("EOF\n")
		f.write("@ j++\n")
		f.write("end\n\n")
		f.write("/usr/local/IMAGIC/threed/automask3d.e <<EOF >> imagic3dRefine_"+str(self.params['itn'])+".log\n")
		f.write("DO_IT_ALL\n")
		f.write("3d_ordered_repaligned\n")
		f.write("3d_ordered_repaligned_modvar\n")
		f.write("YES\n")
		f.write(str(self.params['amask_dim'])+","+str(self.params['amask_lp'])+"\n")		
		f.write(str(self.params['amask_sharp'])+"\n")			
		f.write("AUTOMATIC\n")
		f.write(str(self.params['amask_thresh'])+"\n")			
		f.write("mask_3d_ordered_repaligned\n")
		f.write("masked_3d_ordered_repaligned\n")
		f.write("EOF\n")
		f.write("/usr/local/IMAGIC/stand/em2em.e <<EOF >> imagic3dRefine_"+str(self.params['itn'])+".log\n")
		f.write("IMAGIC\n")
		f.write("MRC\n")
		f.write("3D\n")
		f.write("MULTIPLE\n")
		f.write("masked_3d_ordered_repaligned\n")
		f.write("masked_3d_ordered_repaligned.mrc\n")
		f.write("YES\n")
		f.write("EOF\n")
		f.write("/usr/local/IMAGIC/incore/excopy.e <<EOF >> imagic3dRefine_"+str(self.params['itn'])+".log\n")
		f.write("EXTRACT\n")
		f.write("ordered_repaligned\n")
		f.write("ordered_repaligned_odd\n")
		f.write("INTERACTIVE\n")
		f.write("1-"+str(self.params['num_classums'])+"\n")		
		f.write("ODD\n")
		f.write("EOF\n")
		f.write("/usr/local/IMAGIC/incore/excopy.e <<EOF >> imagic3dRefine_"+str(self.params['itn'])+".log\n")
		f.write("EXTRACT\n")
		f.write("ordered_repaligned\n")
		f.write("ordered_repaligned_even\n")
		f.write("INTERACTIVE\n")
		f.write("1-"+str(self.params['num_classums'])+"\n") 		
		f.write("EVEN\n")
		f.write("EOF\n")
		f.write("/usr/local/IMAGIC/threed/true3d.e <<EOF >> imagic3dRefine_"+str(self.params['itn'])+".log\n")
		f.write("NO\n")
		f.write(str(self.params['symmetry'])+"\n") 		
		f.write("YES\n")
		f.write("ordered_repaligned_odd\n")
		f.write("ANGREC_HEAD\n")
		f.write("3d_ordered_repaligned_odd\n")
		f.write("fsc_rep\n")
		f.write("fsc_err\n")
		f.write("NO\n")
		f.write(str(self.params['ham_win'])+"\n")		
		f.write(str(self.params['object_size'])+"\n")	
		f.write("EOF\n")
		f.write("/usr/local/IMAGIC/threed/true3d.e <<EOF >> imagic3dRefine_"+str(self.params['itn'])+".log\n")
		f.write("NO\n")
		f.write(str(self.params['symmetry'])+"\n")		
		f.write("YES\n")
		f.write("ordered_repaligned_even\n")
		f.write("ANGREC_HEAD\n")
		f.write("3d_ordered_repaligned_even\n")
		f.write("fsc_rep\n")
		f.write("fsc_err\n")
		f.write("NO\n")
		f.write(str(self.params['ham_win'])+"\n")		
		f.write(str(self.params['object_size'])+"\n")		
		f.write("EOF\n")
		f.write("/usr/local/IMAGIC/threed/foushell.e MODE FSC <<EOF >> imagic3dRefine_"+str(self.params['itn'])+".log\n")
		f.write("3d_ordered_repaligned_odd\n")
		f.write("3d_ordered_repaligned_even\n")
		f.write("3d_fsc\n")
		f.write("3.\n")
		f.write(str(self.params['symmetry'])+"\n")		
		f.write(".66\n")			
		f.write(str(self.params['boxsize'])+"\n")			
		f.write("EOF\n")
		f.write("/usr/local/IMAGIC/threed/forward.e SURF FORWARD <<EOF >> imagic3dRefine_"+str(self.params['itn'])+".log\n")
		f.write("masked_3d_ordered_repaligned\n")
		f.write("-99999\n")
		f.write("PROJECTIONS\n")
		f.write("WIDENING\n")
		f.write("mrarefs_masked_3d\n")
		f.write("ASYM_TRIANGLE\n")
		f.write(str(self.params['symmetry'])+"\n")		
		f.write("EQUIDIST\n")
		f.write("ZERO\n")
		f.write(str(self.params['mrarefs_ang_inc'])+"\n")		
		f.write("EOF\n")
		f.write("/usr/local/IMAGIC/threed/forward.e SURF FORWARD <<EOF >> imagic3dRefine_"+str(self.params['itn'])+".log\n")
		f.write("masked_3d_ordered_repaligned\n")
		f.write("-99999\n")
		f.write("PROJECTIONS\n")
		f.write("WIDENING\n")
		f.write("masked_3d_ordered_repaligned_forward\n")
		f.write("ASYM_TRIANGLE\n")
		f.write(str(self.params['symmetry'])+"\n")		
		f.write("EQUIDIST\n")
		f.write("ZERO\n")
		f.write(str(self.params['forw_ang_inc'])+"\n")		
		f.write("EOF\n\n")
		
		f.write("mv arsino_masked_3d_ordered_repaligned_forward.img arsino_masked_3d"+str(self.params['itn'])+"_ordered"+str(self.params['itn'])+"_repaligned_forward.img\n")
		f.write("mv arsino_masked_3d_ordered_repaligned_forward.hed arsino_masked_3d"+str(self.params['itn'])+"_ordered"+str(self.params['itn'])+"_repaligned_forward.hed\n")
		f.write("mv ordered.img ordered"+str(self.params['itn'])+".img\n")
		f.write("mv ordered.hed ordered"+str(self.params['itn'])+".hed\n")
		f.write("mv 3d_ordered.img 3d"+str(self.params['itn'])+"_ordered"+str(self.params['itn'])+".img\n")
		f.write("mv 3d_ordered.hed 3d"+str(self.params['itn'])+"_ordered"+str(self.params['itn'])+".hed\n")
		f.write("mv rep_ordered.img rep"+str(self.params['itn'])+"_ordered"+str(self.params['itn'])+".img\n")
		f.write("mv rep_ordered.hed rep"+str(self.params['itn'])+"_ordered"+str(self.params['itn'])+".hed\n")
		f.write("mv err_ordered.img err"+str(self.params['itn'])+"_ordered"+str(self.params['itn'])+".img\n")
		f.write("mv err_ordered.hed err"+str(self.params['itn'])+"_ordered"+str(self.params['itn'])+".hed\n")
		f.write("mv ordered_repaligned.img ordered"+str(self.params['itn'])+"_repaligned.img\n")
		f.write("mv ordered_repaligned.hed ordered"+str(self.params['itn'])+"_repaligned.hed\n")
		f.write("mv 3d_ordered_repaligned.img 3d"+str(self.params['itn'])+"_ordered"+str(self.params['itn'])+"_repaligned.img\n")
		f.write("mv 3d_ordered_repaligned.hed 3d"+str(self.params['itn'])+"_ordered"+str(self.params['itn'])+"_repaligned.hed\n")
		f.write("mv rep_ordered_repaligned.img rep"+str(self.params['itn'])+"_ordered"+str(self.params['itn'])+"_repaligned.img\n")
		f.write("mv rep_ordered_repaligned.hed rep"+str(self.params['itn'])+"_ordered"+str(self.params['itn'])+"_repaligned.hed\n")
		f.write("mv err_ordered_repaligned.img err"+str(self.params['itn'])+"_ordered"+str(self.params['itn'])+"_repaligned.img\n")
		f.write("mv err_ordered_repaligned.hed err"+str(self.params['itn'])+"_ordered"+str(self.params['itn'])+"_repaligned.hed\n")
		f.write("mv 3d_ordered_repaligned_modvar.img 3d"+str(self.params['itn'])+"_ordered"+str(self.params['itn'])+"_repaligned_modvar.img\n")
		f.write("mv 3d_ordered_repaligned_modvar.hed 3d"+str(self.params['itn'])+"_ordered"+str(self.params['itn'])+"_repaligned_modvar.hed\n")
		f.write("mv mask_3d_ordered_repaligned.img mask_3d"+str(self.params['itn'])+"_ordered"+str(self.params['itn'])+"_repaligned.img\n")
		f.write("mv mask_3d_ordered_repaligned.hed mask_3d"+str(self.params['itn'])+"_ordered"+str(self.params['itn'])+"_repaligned.hed\n")
		f.write("mv masked_3d_ordered_repaligned.img masked_3d"+str(self.params['itn'])+"_ordered"+str(self.params['itn'])+"_repaligned.img\n")
		f.write("mv masked_3d_ordered_repaligned.hed masked_3d"+str(self.params['itn'])+"_ordered"+str(self.params['itn'])+"_repaligned.hed\n")
		f.write("mv masked_3d_ordered_repaligned.mrc masked_3d"+str(self.params['itn'])+"_ordered"+str(self.params['itn'])+"_repaligned.mrc\n")
		f.write("mv ordered_repaligned_odd.img ordered"+str(self.params['itn'])+"_repaligned_odd.img\n")
		f.write("mv ordered_repaligned_odd.hed ordered"+str(self.params['itn'])+"_repaligned_odd.hed\n")
		f.write("mv 3d_ordered_repaligned_odd.img 3d"+str(self.params['itn'])+"_ordered"+str(self.params['itn'])+"_repaligned_odd.img\n")
		f.write("mv 3d_ordered_repaligned_odd.hed 3d"+str(self.params['itn'])+"_ordered"+str(self.params['itn'])+"_repaligned_odd.hed\n")
		f.write("mv ordered_repaligned_even.img ordered"+str(self.params['itn'])+"_repaligned_even.img\n")
		f.write("mv ordered_repaligned_even.hed ordered"+str(self.params['itn'])+"_repaligned_even.hed\n")
		f.write("mv 3d_ordered_repaligned_even.img 3d"+str(self.params['itn'])+"_ordered"+str(self.params['itn'])+"_repaligned_even.img\n")
		f.write("mv 3d_ordered_repaligned_even.hed 3d"+str(self.params['itn'])+"_ordered"+str(self.params['itn'])+"_repaligned_even.hed\n")
		f.write("mv 3d_fsc.plt 3d"+str(self.params['itn'])+"_fsc.plt\n")
		f.write("mv 3d_ordered_lis.plt 3d"+str(self.params['itn'])+"_ordered"+str(self.params['itn'])+"_lis.plt\n")
		f.write("mv 3d_ordered_repaligned_lis.plt 3d"+str(self.params['itn'])+"_ordered"+str(self.params['itn'])+"_repaligned_lis.plt\n")
		f.write("mv 3d_ordered_repaligned_even_lis.plt 3d"+str(self.params['itn'])+"_ordered"+str(self.params['itn'])+"_repaligned_even_lis.plt\n")
		f.write("mv 3d_ordered_repaligned_odd_lis.plt 3d"+str(self.params['itn'])+"_ordered"+str(self.params['itn'])+"_repaligned_odd_lis.plt\n")
		f.write("mv 3d_ordered.lis 3d"+str(self.params['itn'])+"_ordered"+str(self.params['itn'])+".lis\n")
		f.write("mv 3d_ordered_repaligned.lis 3d"+str(self.params['itn'])+"_ordered"+str(self.params['itn'])+"_repaligned.lis\n")
		f.write("mv 3d_ordered_repaligned_odd.lis 3d"+str(self.params['itn'])+"_ordered"+str(self.params['itn'])+"_repaligned_odd.lis\n")
		f.write("mv 3d_ordered_repaligned_even.lis 3d"+str(self.params['itn'])+"_ordered"+str(self.params['itn'])+"_repaligned_even.lis\n")
		f.write("cp mrarefs_masked_3d.img mrarefs_masked_3d"+str(self.params['itn'])+".img\n")
		f.write("cp mrarefs_masked_3d.hed mrarefs_masked_3d"+str(self.params['itn'])+".hed\n")
		f.write("cp masked_3d_ordered_repaligned_forward.img masked_3d"+str(self.params['itn'])+"_ordered"+str(self.params['itn'])+"_repaligned_forward.img\n")
		f.write("cp masked_3d_ordered_repaligned_forward.hed masked_3d"+str(self.params['itn'])+"_ordered"+str(self.params['itn'])+"_repaligned_forward.hed\n")
		f.write("rm to_be_aligned.*\n")
		f.write("rm fsc_rep.*\n")
		f.write("rm fsc_err.*\n") 
		f.close()

		os.chdir(str(self.params['outdir']))
		os.system("chmod 755 "+str(self.params['outdir'])+"/imagicCreate3dRefine_"+str(self.params['itn'])+".batch")
		os.system(str(self.params['outdir'])+"/imagicCreate3dRefine_"+str(self.params['itn'])+".batch")

		mrcname = self.params['outdir']+"/masked_3d"+str(self.params['itn'])+"_ordered"+str(self.params['itn'])+"_repaligned.mrc"
		mrcnamerot = self.params['outdir']+"/masked_3d"+str(self.params['itn'])+"_ordered"+str(self.params['itn'])+"_repaligned.mrc.rot.mrc"

		### use EMAN to normalize density & rotate model azimuthaly by 90 degrees
		apEMAN.executeEmanCmd('proc3d %s %s apix=%f norm' % (mrcname, mrcname, self.params['apix']))
		apEMAN.executeEmanCmd('proc3d %s %s apix=%f rot=0,90,0 norm' % (mrcname, mrcnamerot, self.params['apix']))

		### create chimera slices of densities ******* .log file has caused problems if not removed
		if os.path.isfile(str(self.params['outdir'])+"/chimera.log") is not False:
			os.remove(str(self.params['outdir'])+"/chimera.log")
		apRecon.renderSnapshots(mrcname, 30, None, 
			3.0, 1.0, self.params['apix'], 'c1', self.params['boxsize'], False)

		if os.path.isfile(str(self.params['outdir'])+"/chimera.log") is not False:
			os.remove(str(self.params['outdir'])+"/chimera.log")
		apRecon.renderSnapshots(mrcnamerot, 30, None, 
			3.0, 1.0, self.params['apix'], 'c1', self.params['boxsize'], False)

		### upload density
		#if self.params['itn'] == 1:		
		self.upload3dRunData()

		self.upload3dIterationData()

		apDisplay.printMsg("IMAGIC .batch run for iteration "+str(self.params['itn'])+" is complete")

	
	
	
#=====================
#=====================
if __name__ == '__main__':
	imagic3dRefine = imagic3dRefineScript()
	imagic3dRefine.start()
	imagic3dRefine.close()
		
