#!/usr/bin/env python
# Python script to upload a template to the database, and prepare images for import




	####	need to change mode to 755 of the batch file that is created
	####	how do I specify the filename from the pulldown menu?



import os
import time
import sys
import re
import subprocess
import appionScript
import appiondata

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
		self.parser.add_option("--templateStackId", dest="templateStackId", type="int",
			help="template stack ID from either reprojections or class averages", metavar="INT")
		self.parser.add_option("--3_projections", dest="projections", type="str",
			help="3 initial projections for angular reconstitution", metavar="STR")
		self.parser.add_option("--symmetry", dest="symmetry", type="int",
			help="symmetry of the object", metavar="INT")
		self.parser.add_option("--euler_ang_inc", dest="euler_ang_inc", type="int", default=10,
			help="angular increment for euler angle search", metavar="INT")
		self.parser.add_option("--num_classums", dest="num_classums", type="int",
			help="number of sorted classums (based on angular reconstitution error) used for 3d0 construction", metavar="INT")
		self.parser.add_option("--ham_win", dest="ham_win", type="float", default=0.8,
			help="similar to lp-filtering parameter that determines detail in 3d map", metavar="float")
		self.parser.add_option("--object_size", dest="object_size", type="float", default=0.8,
			help="object size as fraction of image size", metavar="float")
		self.parser.add_option("--repalignments", dest="repalignments", type="int", default=1,
			help="number of alignments to reprojections", metavar="INT")
		self.parser.add_option("--amask_dim", dest="amask_dim", type="float", default=0.04,
			help="automasking parameter determined by smallest object size", metavar="float")
		self.parser.add_option("--amask_lp", dest="amask_lp", type="float", default=0.5,
			help="automasking parameter for low-pass filtering", metavar="float")
		self.parser.add_option("--amask_sharp", dest="amask_sharp", type="float", default=0.5,
			help="automasking parameter that determines sharpness of mask", metavar="float")
		self.parser.add_option("--amask_thresh", dest="amask_thresh", type="int", default=15,
			help="automasking parameter that determines object thresholding", metavar="INT")
		self.parser.add_option("--mrarefs_ang_inc", dest="mrarefs_ang_inc", type="int",	default=25,
			help="angular increment of reprojections for MRA", metavar="INT")
		self.parser.add_option("--forw_ang_inc", dest="forw_ang_inc", type="int", default=25,
			help="angular increment of reprojections for euler angle refinement", metavar="INT")

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

		return

	#=====================
	def checkConflicts(self):

		### chimera only
		if self.params['chimera-only'] is True:
			if self.params['rundir'] is None:
				apDisplay.printError("Please specify the directory in which your files are located")

			return
		else:

		### otherwise go on with the reconstruction

			if (self.params['reclassId'] is None and self.params['norefClassId'] is None and \
				self.params['clusterId'] is None and self.params['templateStackId'] is None):
				apDisplay.printError("There is no class average ID specified")
			if self.params['templateStackId'] is not None and (self.params['clusterId'] is not None or self.params['norefClassId'] is not None):
				apDisplay.printError("Please use only one class average stack")
			if self.params['clusterId'] is not None and (self.params['templateStackId'] is not None or self.params['norefClassId'] is not None):
				apDisplay.printError("Please use only one class average stack")
			if self.params['norefClassId'] is not None and (self.params['clusterId'] is not None or self.params['templateStackId'] is not None):
				apDisplay.printError("Please use only one class average stack")
			if self.params['projections'] is None:
				apDisplay.printError("enter 3 projections from which to begin angular reconstitution")
			if self.params['symmetry'] is None:
				apDisplay.printError("enter object symmetry")

			return

	#=====================
	def setRunDir(self):

		# get reference-free classification and reclassification parameters
		if self.params['norefClassId'] is not None:
			norefclassdata = appiondata.ApNoRefClassRunData.direct_query(self.params['norefClassId'])
			path = norefclassdata['norefRun']['path']['path']
		elif self.params['reclassId'] is not None:
			reclassdata = appiondata.ApImagicReclassifyData.direct_query(self.params['reclassId'])
			path = reclassdata['path']['path']
		elif self.params['clusterId'] is not None:
			clusterdata = appiondata.ApClusteringStackData.direct_query(self.params['clusterId'])
			path = clusterdata['path']['path']
		elif self.params['templateStackId'] is not None:
			tsdata = appiondata.ApTemplateStackData.direct_query(self.params['templateStackId'])
			path = tsdata['path']['path']
#		elif self.params['imagicClusterId'] is not None:
#			clusterdata = appiondata.ApClusteringStackData.direct_query(self.params['imagicClusterId'])
#			path = clusterdata['path']['path']
		else:
			apDisplay.printError("class averages not in the database")

		uppath = os.path.abspath(os.path.join(path, "../.."))
		self.params['rundir'] = os.path.join(uppath, "init_models", self.params['runname'])

	#=====================
	def createImagicBatchFile(self, linkingfile):
		# IMAGIC batch file creation
		syminfo = apSymmetry.findSymmetry(self.params['symmetry'])
		symmetry = syminfo['eman_name']
		filename = os.path.join(self.params['rundir'], "imagicCreate3d0.batch")
		f = open(filename, 'w')
		f.write("#!/bin/csh -f\n")
		f.write("setenv IMAGIC_BATCH 1\n")
		f.write("cd "+str(self.params['rundir'])+"/\n")
		f.write("cp "+linkingfile+".img start_stack.img\n")
		f.write("cp "+linkingfile+".hed start_stack.hed\n")
		if self.params['norefClassId'] is not None or self.params['clusterId'] is not None or self.params['templateStackId'] is not None:
			# create compatible headers following EMAN processing
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
		f.write("1\n")
		f.write("30\n")
		f.write("no\n")
		f.write("EOF\n")

		### figure out which projections have already been used before proceeding
		repalignments = self.params['repalignments'] + 1
		numbers = self.params['projections'].split(";")
		integers = [int(x) for x in numbers]
		integers.sort()
		j = 1
		list = []
		while j <= self.params['numpart']:
			list.append(j)
			j += 1
		for item in integers:
			list.remove(item)
		j = 1
		proj = str(list[0])
		length = len(list)
		while j < length:
			if (list[j] != (list[(j-1)] + 1)):
				proj = proj+"-"+str(list[j-1])+";"+str(list[j])
			j += 1
			if j == length:
				proj = proj+"-"+str(list[j-1])

		### continue with the script creation
		f.write("/usr/local/IMAGIC/angrec/euler.e <<EOF >> imagicCreate3d0.log\n")
		f.write(symmetry+"\n")
		if lowercase != "c1":
			f.write("0\n")
		f.write("new\n")
		f.write("add\n")
		f.write("start_stack\n")
		f.write(str(proj)+"\n")
		f.write("ordered0\n")
		f.write("sino_ordered0\n")
		f.write("yes\n")
		f.write("0.9\n")
		f.write("my_sine\n")
		f.write(str(self.params['euler_ang_inc'])+"\n")
		f.write("yes\n")
		f.write("EOF\n")
		f.write("/usr/local/IMAGIC/incore/excopy.e <<EOF >> imagicCreate3d0.log\n")
		f.write("SORT\n")
		f.write("ordered0\n")
		f.write("ordered0_sort\n")
		f.write("ANGULAR_ERROR\n")
		f.write("UP\n")
		f.write(str(self.params['num_classums'])+"\n")
		f.write("EOF\n")
		f.write("/usr/local/IMAGIC/threed/true3d.e <<EOF >> imagicCreate3d0.log\n")
		f.write("no\n")
		f.write(symmetry+"\n")
		f.write("yes\n")
		f.write("ordered0_sort\n")
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
		f.write("ordered0_sort\n")
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
		f.write("while ($j<"+str(repalignments)+")\n")
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
#		f.write("/usr/local/IMAGIC/threed/automask3d.e <<EOF >> imagicCreate3d0.log\n")
#		f.write("DO_IT_ALL\n")
#		f.write("3d0_ordered0_repaligned\n")
#		f.write("3d0_ordered0_repaligned_modvar\n")
#		f.write("yes\n")
#		f.write(str(self.params['amask_dim'])+","+str(self.params['amask_lp'])+"\n")
#		f.write(str(self.params['amask_sharp'])+"\n")
#		f.write("AUTOMATIC\n")
#		f.write(str(self.params['amask_thresh'])+"\n")
#		f.write("mask_3d0_ordered0_repaligned\n")
#		f.write("masked_3d0_ordered0_repaligned\n")
#		f.write("EOF\n")
		### workaround for now
		f.write("/usr/local/IMAGIC/stand/copyim.e <<EOF >> imagicCreate3d0.log\n")
		f.write("3d0_ordered0_repaligned\n")
		f.write("masked_3d0_ordered0_repaligned\n")
		f.write("EOF\n")

		f.write("/usr/local/IMAGIC/stand/em2em.e <<EOF >> imagicCreate3d0.log\n")
		f.write("IMAGIC\n")
		f.write("MRC\n")
		f.write("3d\n")
#		f.write("multiple\n")
		f.write("masked_3d0_ordered0_repaligned\n")
		f.write("masked_3d0_ordered0_repaligned.mrc\n")
		f.write("yes\n")
		f.write("EOF\n")
		f.write("/usr/local/IMAGIC/threed/forward.e <<EOF >> imagicCreate3d0.log\n")
		f.write("masked_3d0_ordered0_repaligned\n")
		f.write("-99999\n")
		f.write("projections\n")
		f.write("YES\n")
		f.write("mrarefs_masked_3d0\n")
#		f.write("widening\n")
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
		f.write("YES\n")
#		f.write("widening\n")
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
		modelq = appiondata.ApImagic3d0Data()
		if self.params['stackid'] is not None:
			modelq['project|projects|project'] = apProject.getProjectIdFromStackId(self.params['stackid'])
		elif self.params['templateStackId'] is not None:
			tsdata = appiondata.ApTemplateStackData.direct_query(self.params['templateStackId'])
			modelq['project|projects|project'] = apProject.getProjectIdFromSessionId(tsdata['session'].dbid)
		modelq['name'] = "masked_3d0_ordered0_repaligned.mrc"
		modelq['runname'] = self.params['runname']
		if self.params['norefClassId'] is not None:
			modelq['norefclass'] = appiondata.ApNoRefClassRunData.direct_query(self.params['norefClassId'])
		elif self.params['reclassId'] is not None:
			modelq['reclass'] = appiondata.ApImagicReclassifyData.direct_query(self.params['reclassId'])
		elif self.params['clusterId'] is not None:
			modelq['clusterclass'] = appiondata.ApClusteringStackData.direct_query(self.params['clusterId'])
#		elif self.params['imagicClusterId'] is not None:
#			modelq['imagicclusterclass'] = appiondata.ApClusteringStackData.direct_query(self.params['imagicClusterId'])
		elif self.params['templateStackId'] is not None:
			modelq['templatestack'] = appiondata.ApTemplateStackData.direct_query(self.params['templateStackId'])

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
		modelq['numpart'] = self.params['numpart']
		modelq['num_classums'] = self.params['num_classums']
		modelq['pixelsize'] = self.params['apix']
		modelq['boxsize'] = self.params['boxsize']
		modelq['symmetry'] = apSymmetry.findSymmetry(self.params['symmetry'])
		modelq['path'] = appiondata.ApPathData(path=os.path.dirname(os.path.abspath(self.params['rundir'])))

		modelq['hidden'] = False
		if self.params['commit'] is True:
			modelq.insert()
		else:
			apDisplay.printWarning("not committing results to DB")
		return


	#=====================
	def start(self):

		### chimera only
		if self.params['chimera-only'] is True:
			mrcname = self.params['rundir']+"/masked_3d0_ordered0_repaligned.mrc"
			mrcnamerot = self.params['rundir']+"/masked_3d0_ordered0_repaligned.mrc.rot.mrc"

			### create chimera slices of densities
			apChimera.renderSnapshots(mrcname, contour=self.params['contour'], zoom=self.params['zoom'], sym='c1')
			apChimera.renderAnimation(mrcname, contour=self.params['contour'], zoom=self.params['zoom'], sym='c1')
			apChimera.renderSnapshots(mrcnamerot, contour=self.params['contour'], zoom=self.params['zoom'], sym='c1')

			return

		### otherwise go on with the reconstruction
		else:
			self.params['projections'] = self.params['projections'].replace(",", ";")

			# get reference-free classification and reclassification parameters
			if self.params['norefClassId'] is not None:
				norefclassdata = appiondata.ApNoRefClassRunData.direct_query(self.params['norefClassId'])
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
				reclassdata = appiondata.ApImagicReclassifyData.direct_query(self.params['reclassId'])
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
					clusterdata = appiondata.ApClusteringStackData.direct_query(self.params['clusterId'])
		    		elif self.params['imagicClusterId'] is not None:
					clusterdata = appiondata.ApClusteringStackData.direct_query(self.params['imagicClusterId'])
				self.params['stackid'] = clusterdata['clusterrun']['alignstack']['stack'].dbid
				self.params['boxsize'] = clusterdata['clusterrun']['boxsize']
	 			self.params['apix'] = clusterdata['clusterrun']['pixelsize']
				orig_path = clusterdata['path']['path']
				orig_file = clusterdata['avg_imagicfile']
				if orig_file[-4:] == ".img" or orig_file[-4:] == ".hed":
					orig_file = orig_file[:-4]
				linkingfile = os.path.join(orig_path, orig_file)
			elif self.params['templateStackId'] is not None:
				tsdata = appiondata.ApTemplateStackData.direct_query(self.params['templateStackId'])
				if tsdata['clusterstack'] is not None:
					clusterdata = tsdata['clusterstack']
					self.params['stackid'] = clusterdata['clusterrun']['alignstack']['stack'].dbid
				else:
					self.params['stackid'] = None
				self.params['stackid'] = 0
				self.params['boxsize'] = tsdata['boxsize']
				self.params['apix'] = tsdata['apix']
				orig_path = tsdata['path']['path']
				orig_file = tsdata['templatename']
				if orig_file[-4:] == ".img" or orig_file[-4:] == ".hed":
					orig_file = orig_file[:-4]
				linkingfile = os.path.join(orig_path, orig_file)
			else:
				apDisplay.printError("class averages not in the database")

			### check conflicts with number of particles
			self.params['numpart'] = apFile.numImagesInStack(linkingfile+".hed")
			if self.params['num_classums'] is None:
				self.params['num_classums'] = self.params['numpart']
			if self.params['num_classums'] > self.params['numpart']:
				apDisplay.printError("number of class averages greater than number of particles in stack")

			print self.params
			print "**********************"
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
			proc = subprocess.Popen('chmod 755 '+filename, shell=True)
			proc.wait()
			apIMAGIC.executeImagicBatchFile(filename)
			logfile = open(os.path.join(self.params['rundir'], "imagicCreate3d0.log"))
			loglines = logfile.readlines()
			for line in loglines:
				if re.search("ERROR in program", line):
					apDisplay.printError("ERROR IN IMAGIC SUBROUTINE, please check the logfile: imagicCreate3d0.log")
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
			apChimera.renderSnapshots(mrcname, contour=self.params['contour'], zoom=self.params['zoom'], sym='c1')
			apChimera.renderAnimation(mrcname, contour=self.params['contour'], zoom=self.params['zoom'], sym='c1')
			apChimera.renderSnapshots(mrcnamerot, contour=self.params['contour'], zoom=self.params['zoom'], sym='c1')

			### upload density
			self.upload3d0()

			return



#=====================
#=====================
if __name__ == '__main__':
	imagic3d0 = imagic3d0Script()
	imagic3d0.start()
	imagic3d0.close()



