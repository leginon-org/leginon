#!/usr/bin/env python
# Python script to upload a template to the database, and prepare images for import




	####	need to change mode to 755 of the batch file that is created
	####	how do I specify the filename from the pulldown menu?



import os
import sys
import re
import appionScript
import appionData
import apParam
import apDisplay
import apEMAN
import apFile
import apDatabase
import apStack
import apProject

#=====================
#=====================
class reclassifyScript(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage( "Usage: %prog --file=<name> --apix=<pixel> --rundir=<dir> "
			+"[options]")

		self.parser.add_option("--oldstack", dest="oldstack",
			help="Filename of the old class averages", metavar="STR")
		self.parser.add_option("--file_new", dest="file_new",
			help="Filename of the new class averages", metavar="FILE")
		self.parser.add_option("--lp", dest="lp", type="float",
			help="Low pass filter value (in Angstroms)", metavar="FLOAT")
		self.parser.add_option("--hp", dest="hp", type="float",
			help="High pass filter value (in Angstroms)", metavar="FLOAT")
		self.parser.add_option("--mask", dest="mask", type="float", default=0.8,
			help="Radius of mask (fraction of image radius)", metavar="FLOAT")
		self.parser.add_option("--mask_dropoff", dest="mask_d", type="float", default=0,
			help="Width of soft edge by which mask is smoothed", metavar="FLOAT")	
		self.parser.add_option("--niter", dest="niter", type="int", default=5,
			help="number of translational alignment iterations", metavar="INT")
		self.parser.add_option("--numaverages", dest="numaverages", type="int",
			help="number of new class averages", metavar="INT")
		self.parser.add_option("--norefclassid", dest="classid", type="int",
			help="reference free class id", metavar="INT")	

		return 

	#=====================
	def checkConflicts(self):
		if self.params['classid'] is None:
			apDisplay.printError("enter a class ID")
		if self.params['oldstack'] is None:
			apDisplay.printError("no reference free classification specified")
		if self.params['lp'] is None:
			apDisplay.printError("enter low-pass filtering parameter")
		if self.params['hp'] is None:
			apDisplay.printError("enter high-pass filtering parameter")
		if self.params['mask'] is None:
			apDisplay.printError("enter mask radius")
		if self.params['mask_d'] is None:
			apDisplay.printError("enter mask drop-off")
		if self.params['niter'] is None:
			apDisplay.printError("enter number of translational alignment iterations")
		if self.params['numaverages'] is None:
			apDisplay.printError("enter number of new class averages")
		return

	#=====================
	def setRunDir(self):
	
		norefclassdata = appionData.ApNoRefClassRunData.direct_query(self.params['classid'])
		if norefclassdata is None: 
			apDisplay.printError("class ID not in the database")
		path = norefclassdata['norefRun']['path']['path']
		uppath = os.path.abspath(os.path.join(path, "../.."))
		self.params['rundir'] = os.path.join(uppath, "clsavgstacks", self.params['runname'])
		return



	def uploadreclassification(self):
		reclassq = appionData.ApImagicReclassifyData()
		reclassq['project|projects|project'] = apProject.getProjectIdFromStackId(self.params['stackid'])
		reclassq['runname'] = self.params['runname']
		reclassq['norefclass'] = appionData.ApNoRefClassRunData.direct_query(self.params['classid'])
		reclassq['lowpass'] = self.params['lp']
		reclassq['highpass'] = self.params['hp']
		reclassq['maskradius'] = self.params['mask']
		reclassq['maskdropoff'] = self.params['mask_d']
		reclassq['numiter'] = self.params['niter']
		reclassq['numaverages'] = self.params['numaverages']
		reclassq['path'] = appionData.ApPathData(path=os.path.dirname(os.path.abspath(self.params['rundir'])))
		reclassq['description'] = self.params['description']
		reclassq['hidden'] = False
		if self.params['commit'] is True:
			reclassq.insert()
		return 



	#=====================
	def start(self):
		print self.params
		norefclassdata = appionData.ApNoRefClassRunData.direct_query(self.params['classid'])
		if norefclassdata is None: 
			apDisplay.printError("class ID not in the database")
		self.params['stackid'] = norefclassdata['norefRun']['stack'].dbid
		stack_pixel_size = apStack.getStackPixelSizeFromStackId(self.params['stackid'])
		stack_box_size = apStack.getStackBoxsize(self.params['stackid'])
		binning = norefclassdata['norefRun']['norefParams']['bin']
		if binning is None:
			binning = 1
		self.params['apix'] = stack_pixel_size * binning
		self.params['boxsize'] = stack_box_size / binning

		### NEED TO CONVERT FILTERING PARAMETERS TO IMAGIC FORMAT BETWEEN 0-1
		self.params['lp'] = 2 * float(self.params['apix']) / int(self.params['lp'])
		if float(self.params['lp']) > 1:
			self.params['lp'] = 1
		self.params['hp'] = 2 * float(self.params['apix']) / int(self.params['hp'])

		
		print "... class average stack pixel size: "+str(self.params['apix'])
		print "... class average stack box size: "+str(self.params['boxsize'])	
		apDisplay.printMsg("Running IMAGIC .batch file: See imagicCreateNewClassums.log for details")

		filename = "imagicCreateNewClassums.batch"
		f = open(filename, 'w')
		
		
		f.write("#!/bin/csh -f\n")
		f.write("setenv IMAGIC_BATCH 1\n")
		f.write("cd "+str(self.params['rundir'])+"/\n")
		f.write("ln -s "+str(self.params['oldstack'])+".img start_stack.img\n")
		f.write("ln -s "+str(self.params['oldstack'])+".hed start_stack.hed\n")
		f.write("/usr/local/IMAGIC/stand/copyim.e <<EOF > imagicCreateNewClassums.log\n")
		f.write("start_stack\n")
		f.write("classums\n")
		f.write("EOF\n")
		f.write("/usr/local/IMAGIC/stand/headers.e <<EOF >> imagicCreateNewClassums.log\n")
		f.write("classums\n")
		f.write("write\n")
		f.write("wipe\n")
		f.write("all\n")
		f.write("EOF\n")
		f.write("/usr/local/IMAGIC/incore/incprep.e <<EOF >> imagicCreateNewClassums.log\n") 
		f.write("NO\n")
		f.write("classums\n")
		f.write("classums_filt\n")
		f.write(str(self.params['hp'])+"\n")
		f.write("0.0\n")
		f.write(str(self.params['lp'])+"\n")
		f.write(str(self.params['mask'])+","+str(self.params['mask_d'])+"\n")
		f.write("10.0\n")
		f.write("NO\n")
		f.write("EOF\n")
		f.write("/usr/local/IMAGIC/align/alimass.e <<EOF >> imagicCreateNewClassums.log\n") 
		f.write("NO\n")
		f.write("classums_filt\n")
		f.write("classums_filt_cent\n")
		f.write("TOTSUM\n")
		f.write("CCF\n")
		f.write("0.2\n")
		f.write(str(self.params['niter'])+"\n")
		f.write("EOF\n")
		f.write("/usr/local/IMAGIC/stand/testim.e <<EOF >> imagicCreateNewClassums.log\n")
		f.write("msamask\n")
		f.write(str(self.params['boxsize'])+","+str(self.params['boxsize'])+"\n")
		f.write("Real\n")
		f.write("disc\n")
		f.write(str(self.params['mask'])+"\n")
		f.write("EOF\n")
		f.write("/usr/local/IMAGIC/msa/msa.e <<EOF >> imagicCreateNewClassums.log\n")
		f.write("fresh_msa\n")
		f.write("modulation\n")
		f.write("classums_filt_cent\n")
		f.write("NO\n")
		f.write("msamask\n")
		f.write("eigenimages\n")
		f.write("pixel_coordinates\n")
		f.write("eigen_pixels\n")
		f.write("50\n")
		f.write("69\n")
		f.write("0.8\n")
		f.write("msa\n")
		f.write("EOF\n")
		f.write("/usr/local/IMAGIC/msa/classify.e <<EOF >> imagicCreateNewClassums.log\n")
		f.write("images/volumes\n")
		f.write("classums_filt_cent\n")
		f.write("0\n")
		f.write("69\n")
		f.write("yes\n")
		f.write(str(self.params['numaverages'])+"\n")
		f.write("classification\n")
		f.write("EOF\n")
		f.write("/usr/local/IMAGIC/msa/classum.e <<EOF >> imagicCreateNewClassums.log\n")
		f.write("classums_filt_cent\n")
		f.write("classification\n")
		f.write("reclassified_classums\n")
		f.write("no\n")
		f.write("none\n")
		f.write("0\n")
		f.write("EOF\n")
		f.write("/usr/local/IMAGIC/incore/excopy.e <<EOF >> imagicCreateNewClassums.log\n")
		f.write("sort\n")
		f.write("reclassified_classums\n")
		f.write("reclassified_classums_sorted\n")
		f.write("index\n")
		f.write("114\n")
		f.write("down\n")
		f.write("0\n")
		f.write("EOF\n\n")
		f.write("rm reclassified_classums.*\n")
		#f.write("rm classums.*\n")
		f.close()
		os.chdir(str(self.params['rundir']))
		os.system('chmod 755 imagicCreateNewClassums.batch')
		os.system('./imagicCreateNewClassums.batch')

		reclassified_classums = str(self.params['rundir'])+"/reclassified_classums.img"
		# upload it
		self.uploadreclassification()

	
	
	
#=====================
#=====================
if __name__ == '__main__':
	reclassify = reclassifyScript()
	reclassify.start()
	reclassify.close()

	
