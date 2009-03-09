#!/usr/bin/env python
# Python script to upload a template to the database, and prepare images for import




	####	need to change mode to 755 of the batch file that is created
	####	how do I specify the filename from the pulldown menu?



import os
import time
import sys
import re
import appionScript
import appionData

import apParam
import apChimera
import apDisplay
import apEMAN
import apIMAGIC
import apFile
import apUpload
import apDatabase
import apStack
import apProject


#=====================
#=====================
class imagic3d0Script(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage( "Usage: %prog --file=<name> --apix=<pixel> --rundir=<dir> "
			+"[options]")

		self.parser.add_option("--reclassId", dest="reclassId",
			help="ID for reclassification of reference-free alignment", metavar="int")
		self.parser.add_option("--norefId", dest="norefId",
			help="ID for reference-free alignment", metavar="int")
		self.parser.add_option("--norefClassId", dest="norefClassId", type="int",
			help="reference free class id", metavar="INT")
                self.parser.add_option("--clusterId", dest="clusterId", type="int",
                        help="new class average id from alignment pipeline", metavar="INT")
                self.parser.add_option("--imagicClusterId", dest="imagicClusterId", type="int",
                        help="new IMAGIC class average id from alignment pipeline", metavar="INT")
		self.parser.add_option("--3_projections", dest="projections", type="str",
			help="3 initial projections for angular reconstitution", metavar="STR")
		self.parser.add_option("--symmetry", dest="symmetry", type="int",
			help="symmetry of the object", metavar="INT")
		self.parser.add_option("--euler_ang_inc", dest="euler_ang_inc", type="int", #default=10,
			help="angular increment for euler angle search", metavar="INT")
		self.parser.add_option("--num_classums", dest="num_classums", type="int",
			help="total number of classums used for 3d0 construction", metavar="INT")	
		self.parser.add_option("--ham_win", dest="ham_win", type="float", 
			help="similar to lp-filtering parameter that determines detail in 3d map", metavar="float")
		self.parser.add_option("--object_size", dest="object_size", type="float", #default=0.8,
			help="object size as fraction of image size", metavar="float")	
		self.parser.add_option("--repalignments", dest="repalignments", type="int", default=2,
			help="number of alignments to reprojections", metavar="INT")
		self.parser.add_option("--amask_dim", dest="amask_dim", type="float",
			help="automasking parameter determined by smallest object size", metavar="float")
		self.parser.add_option("--amask_lp", dest="amask_lp", type="float",
			help="automasking parameter for low-pass filtering", metavar="float")
		self.parser.add_option("--amask_sharp", dest="amask_sharp", type="float",
			help="automasking parameter that determines sharpness of mask", metavar="float")
		self.parser.add_option("--amask_thresh", dest="amask_thresh", type="float",
			help="automasking parameter that determines object thresholding", metavar="float")
		self.parser.add_option("--mrarefs_ang_inc", dest="mrarefs_ang_inc", type="int",	#default=25,
			help="angular increment of reprojections for MRA", metavar="INT")
		self.parser.add_option("--forw_ang_inc", dest="forw_ang_inc", type="int", #default=25,
			help="angular increment of reprojections for euler angle refinement", metavar="INT")
		
		### mass specified for eman volume function
		self.parser.add_option("--mass", dest="mass", type="int",
                        help="OPTIONAL: used for thresholding volume of a 3d map to 1 based on given mass", metavar="INT")

		return 

	#=====================
	def checkConflicts(self):
		if (self.params['reclassId'] is None and self.params['norefClassId'] is None and self.params['clusterId'] is None and self.params['imagicClusterId'] is None) :
			apDisplay.printError("There is no class average ID specified")
		if self.params['projections'] is None:
			apDisplay.printError("enter 3 projections from which to begin angular reconstitution")
		if self.params['symmetry'] is None:
			apDisplay.printError("enter object symmetry")
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
	def setRunDir(self):

		# get reference-free classification and reclassification parameters
		if self.params['norefClassId'] is not None:
			norefclassdata = appionData.ApNoRefClassRunData.direct_query(self.params['norefClassId'])
			path = norefclassdata['norefRun']['path']['path']
		elif self.params['reclassId'] is not None:
			reclassdata = appionData.ApImagicReclassifyData.direct_query(self.params['reclassId'])
			path = reclassdata['path']['path']
		elif self.params['clusterId'] is not None:
			clusterdata = appionData.ApClusteringStackData.direct_query(self.params['clusterId'])
			path = clusterdata['path']['path']
		elif self.params['imagicClusterId'] is not None:
			clusterdata = appionData.ApClusteringStackData.direct_query(self.params['imagicClusterId'])
			path = clusterdata['path']['path']
		else:
			apDisplay.printError("class averages not in the database")

		uppath = os.path.abspath(os.path.join(path, "../.."))
		self.params['rundir'] = os.path.join(uppath, "init_models", self.params['runname'])

	#=====================
	def createImagicBatchFile(self, linkingfile):
		# IMAGIC batch file creation
		syminfo = apUpload.getSymmetryData(self.params['symmetry'])
		symmetry = syminfo['eman_name']
		filename = os.path.join(self.params['rundir'], "imagicCreate3d0.batch")
		f = open(filename, 'w')
		f.write("#!/bin/csh -f\n")
		f.write("setenv IMAGIC_BATCH 1\n")
		f.write("cd "+str(self.params['rundir'])+"/\n")
		f.write("cp "+linkingfile+".img start_stack.img\n") 
		f.write("cp "+linkingfile+".hed start_stack.hed\n")
		if self.params['norefClassId'] is not None or self.params['clusterId'] is not None:
			# THERE IS A REALLY STUPID IMAGIC ERROR WHERE IT DOESN'T READ IMAGIC FORMAT CREATED BY OTHER 
			# PROGRAMS, AND SO FAR THE ONLY WAY I CAN DEAL WITH IT IS BY WIPING OUT THE HEADERS!
			f.write("/usr/local/IMAGIC/stand/copyim.e <<EOF > imagicCreate3d0.log\n")
			f.write("start_stack\n")
			f.write("start_stack_copy\n")
			f.write("EOF\n")
			f.write("/usr/local/IMAGIC/stand/headers.e <<EOF >> imagicCreate3d0.log\n")
			f.write("start_stack_copy\n")
			f.write("write\n")
			f.write("wipe\n")
			f.write("all\n")
			f.write("EOF\n")
			f.write("rm start_stack.*\n")
			f.write("mv start_stack_copy.img start_stack.img\n") 
			f.write("mv start_stack_copy.hed start_stack.hed\n")
		f.write("/usr/local/IMAGIC/angrec/euler.e <<EOF > imagicCreate3d0.log\n")
		f.write(symmetry+"\n")
		lowercase = str(symmetry).lower()
		if lowercase != "c1":
			f.write("0\n")
		f.write("new\n")
		f.write("fresh\n")
		f.write("start_stack\n")
		f.write(str(self.params['projections'])+"\n")
		f.write("ordered0\n") 
		f.write("sino_ordered0\n")
		f.write("yes\n")
		f.write(".9\n")
		f.write("my_sine\n")
		f.write(str(self.params['euler_ang_inc'])+"\n")
		f.write("30\n")
		f.write("no\n")
		f.write("EOF\n")
		f.write("/usr/local/IMAGIC/angrec/euler.e <<EOF >> imagicCreate3d0.log\n")
		f.write(symmetry+"\n")
		if lowercase != "c1":
                        f.write("0\n")
		f.write("new\n")
		f.write("add\n")
		f.write("start_stack\n")
		f.write("1-"+str(self.params['num_classums'])+"\n")
		f.write("ordered0\n")
		f.write("sino_ordered0\n")
		f.write("yes\n")
		f.write("0.9\n")
		f.write("my_sine\n")
		f.write("5.0\n")
		f.write("yes\n")
		f.write("EOF\n")
		f.write("/usr/local/IMAGIC/threed/true3d.e <<EOF >> imagicCreate3d0.log\n")
		f.write("no\n")
		f.write(symmetry+"\n")
		f.write("yes\n")
		f.write("ordered0\n")
		f.write("ANGREC_HEADER_VALUES\n")
		f.write("3d0_ordered0\n")
		f.write("rep0_ordered0\n")
		f.write("err0_ordered0\n")
		f.write("no\n")
                f.write(str(self.params['ham_win'])+"\n")
                f.write(str(self.params['object_size'])+"\n")
		f.write("EOF\n")
		f.write("/usr/local/IMAGIC/align/alipara.e <<EOF >> imagicCreate3d0.log\n")
		f.write("all\n")
		f.write("ccf\n")
		f.write("ordered0\n")
		f.write("ordered0_repaligned\n")
		f.write("rep0_ordered0\n")
		f.write("0.2\n")
		f.write("-180,180\n")
		f.write("5\n")
		f.write("EOF\n")
		f.write("/usr/local/IMAGIC/threed/true3d.e <<EOF >> imagicCreate3d0.log\n")
		f.write("no\n")
		f.write(symmetry+"\n")
		f.write("yes\n")
		f.write("ordered0_repaligned\n")
		f.write("ANGREC_HEADER_VALUES\n")
		f.write("3d0_ordered0_repaligned\n")
		f.write("rep0_ordered0_repaligned\n")
		f.write("err0_ordered0_repaligned\n")
		f.write("no\n")
                f.write(str(self.params['ham_win'])+"\n")
                f.write(str(self.params['object_size'])+"\n")
		f.write("EOF\n\n")
		f.write("set j=1\n")
		f.write("while ($j<"+str(self.params['repalignments'])+")\n")
		f.write("/usr/local/IMAGIC/stand/im_rename.e <<EOF >> imagicCreate3d0.log\n")
		f.write("ordered0_repaligned\n")
		f.write("to_be_aligned\n")
		f.write("EOF\n")
		f.write("/usr/local/IMAGIC/align/alipara.e <<EOF >> imagicCreate3d0.log\n")
		f.write("all\n")
		f.write("ccf\n")
		f.write("to_be_aligned\n")
		f.write("ordered0_repaligned\n")
		f.write("rep0_ordered0_repaligned\n")
		f.write("0.2\n")
		f.write("-180,180\n")
		f.write("5\n")
		f.write("EOF\n")
		f.write("/usr/local/IMAGIC/threed/true3d.e <<EOF >> imagicCreate3d0.log\n")
		f.write("no\n")
		f.write(symmetry+"\n")
		f.write("yes\n")
		f.write("ordered0_repaligned\n")
		f.write("ANGREC_HEADER_VALUES\n")
		f.write("3d0_ordered0_repaligned\n")
		f.write("rep0_ordered0_repaligned\n")
		f.write("err0_ordered0_repaligned\n")
		f.write("no\n")
		f.write(str(self.params['ham_win'])+"\n")
		f.write(str(self.params['object_size'])+"\n")
		f.write("EOF\n")
		f.write("@ j++\n")
		f.write("end\n\n")
		f.write("/usr/local/IMAGIC/threed/automask3d.e <<EOF >> imagicCreate3d0.log\n")
		f.write("DO_IT_ALL\n")
		f.write("3d0_ordered0_repaligned\n")
		f.write("3d0_ordered0_repaligned_modvar\n")
		f.write("yes\n")
		f.write(str(self.params['amask_dim'])+","+str(self.params['amask_lp'])+"\n")
		f.write(str(self.params['amask_sharp'])+"\n")
		f.write("AUTOMATIC\n")
		f.write(str(self.params['amask_thresh'])+"\n")
		f.write("mask_3d0_ordered0_repaligned\n")
		f.write("masked_3d0_ordered0_repaligned\n")
		f.write("EOF\n")
		f.write("/usr/local/IMAGIC/stand/em2em.e <<EOF >> imagicCreate3d0.log\n")
		f.write("IMAGIC\n")
		f.write("MRC\n")
		f.write("3d\n")
		f.write("multiple\n")
		f.write("masked_3d0_ordered0_repaligned\n")
		f.write("masked_3d0_ordered0_repaligned.mrc\n")
		f.write("yes\n")
		f.write("EOF\n")
		f.write("/usr/local/IMAGIC/threed/forward.e <<EOF >> imagicCreate3d0.log\n")
		f.write("masked_3d0_ordered0_repaligned\n")
		f.write("-99999\n")
		f.write("projections\n")
		f.write("widening\n")
		f.write("mrarefs_masked_3d0\n")
		f.write("asym_triangle\n")
		f.write(symmetry+"\n")
		f.write("equidist\n")
		f.write("zero\n")
		f.write(str(self.params['mrarefs_ang_inc'])+"\n")
		f.write("EOF\n")
		f.write("/usr/local/IMAGIC/threed/forward.e <<EOF >> imagicCreate3d0.log\n")
		f.write("masked_3d0_ordered0_repaligned\n")
		f.write("-99999\n")
		f.write("projections\n")
		f.write("widening\n")
		f.write("masked_3d0_ordered0_repaligned_forward\n")
		f.write("asym_triangle\n")
		f.write(symmetry+"\n")
		f.write("equidist\n")
		f.write("zero\n")
		f.write(str(self.params['forw_ang_inc'])+"\n")
		f.write("EOF\n\n")
		f.write("rm to_be_aligned.*\n") 
		f.close()
		
		return filename

	#=====================
	def upload3d0(self):
		modelq = appionData.ApImagic3d0Data()
		modelq['project|projects|project'] = apProject.getProjectIdFromStackId(self.params['stackid'])
		modelq['name'] = "masked_3d0_ordered0_repaligned.mrc"
		modelq['runname'] = self.params['runname']
		if self.params['norefClassId'] is not None:
			modelq['norefclass'] = appionData.ApNoRefClassRunData.direct_query(self.params['norefClassId'])
		elif self.params['reclassId'] is not None:
			modelq['reclass'] = appionData.ApImagicReclassifyData.direct_query(self.params['reclassId'])
		elif self.params['clusterId'] is not None:
			modelq['clusterclass'] = appionData.ApClusteringStackData.direct_query(self.params['clusterId'])
                elif self.params['imagicClusterId'] is not None:
                        modelq['imagicclusterclass'] = appionData.ApClusteringStackData.direct_query(self.params['imagicClusterId'])
		modelq['projections'] = self.params['projections']
		modelq['euler_ang_inc'] = self.params['euler_ang_inc']
		modelq['ham_win'] = self.params['ham_win']
		modelq['obj_size'] = self.params['object_size']
		modelq['repalignments'] = self.params['repalignments']
		modelq['amask_dim'] = self.params['amask_dim']
		modelq['amask_lp'] = self.params['amask_lp']
		modelq['amask_sharp'] = self.params['amask_sharp']
		modelq['amask_thresh'] = self.params['amask_thresh']
		modelq['mra_ang_inc'] = self.params['mrarefs_ang_inc']
		modelq['forw_ang_inc'] = self.params['forw_ang_inc']
		modelq['description'] = self.params['description']
		modelq['num_classums'] = self.params['num_classums']
		modelq['pixelsize'] = self.params['apix']
		modelq['boxsize'] = self.params['boxsize']
		modelq['symmetry'] = appionData.ApSymmetryData.direct_query(self.params['symmetry'])
		modelq['path'] = appionData.ApPathData(path=os.path.dirname(os.path.abspath(self.params['rundir'])))
	
		modelq['hidden'] = False
		if self.params['commit'] is True:
			modelq.insert()
                else:
                        apDisplay.printWarning("not committing results to DB")
		return 


	#=====================
	def start(self):
		self.params['projections'] = self.params['projections'].replace(",", ";")
		print self.params
		
		# get reference-free classification and reclassification parameters
		if self.params['norefClassId'] is not None:
			norefclassdata = appionData.ApNoRefClassRunData.direct_query(self.params['norefClassId'])
			self.params['stackid'] = norefclassdata['norefRun']['stack'].dbid
			stackpixelsize = apStack.getStackPixelSizeFromStackId(self.params['stackid'])
			stack_box_size = apStack.getStackBoxsize(self.params['stackid'])
			binning = norefclassdata['norefRun']['norefParams']['bin']
			self.params['boxsize'] = stack_box_size / binning
			self.params['apix'] = stackpixelsize * binning
			orig_path = norefclassdata['norefRun']['path']['path']
			orig_file = norefclassdata['classFile']
			linkingfile = orig_path+"/"+orig_file
		elif self.params['reclassId'] is not None:
			reclassdata = appionData.ApImagicReclassifyData.direct_query(self.params['reclassId'])
			self.params['stackid'] = reclassdata['norefclass']['norefRun']['stack'].dbid
			stackpixelsize = apStack.getStackPixelSizeFromStackId(self.params['stackid'])
			stack_box_size = apStack.getStackBoxsize(self.params['stackid'])
			binning = reclassdata['norefclass']['norefRun']['norefParams']['bin']
			self.params['boxsize'] = stack_box_size / binning
			self.params['apix'] = stackpixelsize * binning
			orig_path = reclassdata['path']['path']
			orig_runname = reclassdata['runname']
			orig_file = "reclassified_classums_sorted"
			linkingfile = orig_path+"/"+orig_runname+"/"+orig_file
		elif self.params['clusterId'] is not None or self.params['imagicClusterId'] is not None:
			if self.params['clusterId'] is not None:
				clusterdata = appionData.ApClusteringStackData.direct_query(self.params['clusterId'])
            		elif self.params['imagicClusterId'] is not None:
                        	clusterdata = appionData.ApClusteringStackData.direct_query(self.params['imagicClusterId'])
			self.params['stackid'] = clusterdata['clusterrun']['alignstack']['stack'].dbid
			self.params['boxsize'] = clusterdata['clusterrun']['boxsize']
 			self.params['apix'] = clusterdata['clusterrun']['pixelsize']
			orig_path = clusterdata['path']['path']
			orig_file = clusterdata['avg_imagicfile']
			if orig_file[-4:] == ".img" or orig_file[-4:] == ".hed":
				orig_file = orig_file[:-4]
			linkingfile = os.path.join(orig_path, orig_file)
		else:
			apDisplay.printError("class averages not in the database")


		print "... class average stack pixel size: "+str(self.params['apix'])
		print "... class average stack box size: "+str(self.params['boxsize'])	
		apDisplay.printMsg("Running IMAGIC .batch file: See imagicCreate3d0.log for details")
	
		### create batch file for execution with IMAGIC
		filename = self.createImagicBatchFile(linkingfile)
		
		### these files interfere with IMAGIC program
                if os.path.isfile(str(self.params['rundir'])+"/ordered0.img") is True:
			os.remove(str(self.params['rundir'])+"/ordered0.img")
                if os.path.isfile(str(self.params['rundir'])+"/ordered0.hed") is True:
			os.remove(str(self.params['rundir'])+"/ordered0.hed")
                if os.path.isfile(str(self.params['rundir'])+"/sino_ordered0.img") is True:
                        os.remove(str(self.params['rundir'])+"/sino_ordered0.img")
		if os.path.isfile(str(self.params['rundir'])+"/sino_ordered0.hed") is True:
			os.remove(str(self.params['rundir'])+"/sino_ordered0.hed")

                ### execute batch file that was created
		time3d0 = time.time()
                os.system('chmod 755 '+filename)
                apIMAGIC.executeImagicBatchFile(filename)
                apDisplay.printColor("finished IMAGIC in "+apDisplay.timeString(time.time()-time3d0), "cyan")
                time3d0 = time.time() - time3d0

		mrcname = self.params['rundir']+"/masked_3d0_ordered0_repaligned.mrc"
		mrcnamerot = self.params['rundir']+"/masked_3d0_ordered0_repaligned.mrc.rot.mrc"

		### use EMAN to normalize density & rotate model azimuthaly by 90 degrees
		apEMAN.executeEmanCmd('proc3d %s %s apix=%f norm' % (mrcname, mrcname, self.params['apix']))
		apEMAN.executeEmanCmd('proc3d %s %s apix=%f rot=0,90,0 norm' % (mrcname, mrcnamerot, self.params['apix']))

		### optional thresholding based on specified size
		if self.params['mass'] is not None:
			volumecmd1 = "volume "+mrcname+" "+str(self.params['apix'])+" set="+str(self.params['mass'])
			volumecmd2 = "volume "+mrcnamerot+" "+str(self.params['apix'])+" set="+str(self.params['mass'])
			apEMAN.executeEmanCmd(volumecmd1)
			apEMAN.executeEmanCmd(volumecmd2)
		
		### create chimera slices of densities
		apChimera.renderSnapshots(mrcname, 30,
			1.0, 1.0, self.params['apix'], 'c1', self.params['boxsize'], False)
		apChimera.renderSnapshots(mrcnamerot, 30,
			1.0, 1.0, self.params['apix'], 'c1', self.params['boxsize'], False)

		### upload density
		self.upload3d0()

	
	
	
#=====================
#=====================
if __name__ == '__main__':
	imagic3d0 = imagic3d0Script()
	imagic3d0.start()
	imagic3d0.close()

	
