#!/usr/bin/env python
# Python script to upload a template to the database, and prepare images for import




	####	need to change mode to 755 of the batch file that is created
	####	how do I specify the filename from the pulldown menu?



import os
import shutil
import time
import sys
import re
import subprocess
from appionlib import appionScript
from appionlib import appiondata
from appionlib import apImagicFile
from appionlib import apParam
from appionlib import apDisplay
from appionlib import apFile
from appionlib import apStack
from appionlib import apProject
from appionlib import apIMAGIC

#=====================
#=====================
class imagicMultivariateStatisticalAnalysisScript(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage( "Usage: %prog --file=<name> --apix=<pixel> --rundir=<dir> "
			+"[options]")

		### basic params
		self.parser.add_option("--nproc", dest="nproc", type="int", default=8,
			help="number of processors to use", metavar="int")
		self.parser.add_option("--alignid", dest="alignid",
			help="ID of particle stack", metavar="int")

		### filtering & binning params
		self.parser.add_option("--lpfilt", dest="lpfilt", type="int",
			help="low-pass filter value (in angstroms)", metavar="INT")
		self.parser.add_option("--hpfilt", dest="hpfilt", type="int",
			help="high-pass filter value (in angstroms)", metavar="INT")
		self.parser.add_option("--bin", dest="bin", type="int", default=1,
			help="binning of the image (power of 2)", metavar="INT")

		### masking & MSA params
		self.parser.add_option("--mask_radius", dest="mask_radius", type="float", default=1.0,
			help="radius of mask for MSA (in pixels or fraction of radius)", metavar="FLOAT")
		self.parser.add_option("--mask_dropoff", dest="mask_dropoff", type="float",
			help="dropoff (softness) of mask for MSA (in pixels or fraction of radius)", metavar="FLOAT")
		self.parser.add_option("--numiters", dest="numiters", type="int", default=50,
			help="number of iterations for MSA run", metavar="INT")
		self.parser.add_option("--overcorrection", dest="overcorrection", type="float", default=0.8,
			help="overcorrection factor for MSA program (determines its convergence speed)", metavar="FLOAT")
		self.parser.add_option("--MSAdistance", dest="MSAdistance", type="str",
			help="distance criteria that will be used in MSA", metavar="STR")

		return

	#=====================
	def checkConflicts(self):
		### check for IMAGIC installation
		self.imagicroot = apIMAGIC.checkImagicExecutablePath()	
	
		### check input parameters
		if self.params['alignid'] is None:
			apDisplay.printError("There is no stack ID specified")
		if self.params['runname'] is None:
			apDisplay.printError("enter a run ID")
		if self.params['MSAdistance'] is None:
			apDisplay.printError("enter distance criteria for MSA program (i.e. eulidean, chisquare, modulation)")

		return

	#=====================
	def setRunDir(self):
		# get reference-free classification and reclassification parameters
		if self.params['alignid'] is not None:
                	self.alignstackdata = appiondata.ApAlignStackData.direct_query(self.params['alignid'])
                	path = self.alignstackdata['path']['path']
                	uppath = os.path.abspath(os.path.join(path, "../.."))
                	self.params['rundir'] = os.path.join(uppath, "imagicmsa", self.params['runname'])

        #=====================
        def checkAnalysisRun(self):
                # create a norefParam object
                analysisrunq = appiondata.ApAlignAnalysisRunData()
                analysisrunq['runname'] = self.params['runname']
                analysisrunq['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
                # ... path makes the run unique:
                uniquerun = analysisrunq.query(results=1)
                if uniquerun:
                        apDisplay.printError("Run name '"+self.params['runname']+"' for stackid="+\
                                str(self.params['alignid'])+"\nis already in the database")

	#=====================
	def createImagicBatchFile(self):
		# IMAGIC batch file creation
		append_log = False
		filename = os.path.join(self.params['rundir'], "imagicMultivariateStatisticalAnalysis.batch")
		f = open(filename, 'w')
		f.write("#!/bin/csh -f\n")
		f.write("setenv IMAGIC_BATCH 1\n")

		### optional binning
		if self.params['bin'] > 1:
			f.write(str(self.imagicroot)+"/stand/coarse.e <<EOF > imagicMultivariateStatisticalAnalysis.log\n")
			f.write("start\n")
			f.write("start_coarse\n")
			f.write(str(self.params['bin'])+"\n")
			f.write("EOF\n")
			f.write(str(self.imagicroot)+"/stand/im_rename.e <<EOF >> imagicMultivariateStatisticalAnalysis.log\n")
			f.write("start_coarse\n")
			f.write("start\n")
			f.write("EOF\n")
			append_log = True

		### optional filtering
		if self.params['hpfilt_imagic'] and self.params['lpfilt_imagic'] is not None:
			f.write(str(self.imagicroot)+"/incore/incband.e OPT BAND-PASS <<EOF")
			if append_log is True:
				f.write(" >> imagicMultivariateStatisticalAnalysis.log\n")
			else:
				f.write(" > imagicMultivariateStatisticalAnalysis.log\n")
			f.write("start\n")
			f.write("start_filt\n")
			f.write(str(self.params['hpfilt_imagic'])+"\n")
			f.write("0\n")
			f.write(str(self.params['lpfilt_imagic'])+"\n")
			f.write("NO\n")
			f.write("EOF\n")
			f.write(str(self.imagicroot)+"/stand/im_rename.e <<EOF >> imagicMultivariateStatisticalAnalysis.log\n")
			f.write("start_filt\n")
			f.write("start\n")
			f.write("EOF\n")
			append_log = True

#		### make a mask for MSA
#		if self.params['mask_radius'] and self.params['mask_dropoff'] is not None:
#			f.write(str(self.imagicroot)+"/stand/arithm.e <<EOF")
#			if append_log is True:
#				f.write(" >> imagicMultivariateStatisticalAnalysis.log\n")
#			else:
#				f.write(" > imagicMultivariateStatisticalAnalysis.log\n")
#			f.write("start\n")
#			f.write("start_masked\n")
#			f.write("CIRC\n")
#			f.write(str(self.params['mask_radius'])+"\n")
#			f.write(str(self.params['mask_dropoff'])+"\n")
#			f.write("EOF\n")
#			f.write(str(self.imagicroot)+"/stand/im_rename.e <<EOF >> imagicMultivariateStatisticalAnalysis.log\n")
#			f.write("start_masked\n")
#			f.write("start\n")
#			f.write("EOF\n")
#			append_log = True
		f.write(str(self.imagicroot)+"/stand/testim.e <<EOF")
		if append_log is True:
			f.write(" >> imagicMultivariateStatisticalAnalysis.log\n")
		else:
			f.write(" > imagicMultivariateStatisticalAnalysis.log\n")
		f.write("msamask\n")
		f.write(str(self.params['boxsize'])+","+str(self.params['boxsize'])+"\n")
		f.write("REAL\n")
		f.write("DISC\n")
		f.write(str(self.params['mask_radius'])+"\n")
		f.write("EOF\n")

		### run MSA
		if self.params['nproc'] > 1:
			f.write(str(self.imagicroot)+"/openmpi/bin/mpirun -np "+str(self.params['nproc'])+\
				" -x IMAGIC_BATCH  "+str(self.imagicroot)+"/msa/msa.e_mpi <<EOF >> imagicMultivariateStatisticalAnalysis.log\n")
			f.write("YES\n")
			f.write(str(self.params['nproc'])+"\n")
		else:
			f.write(str(self.imagicroot)+"/msa/msa.e <<EOF >> imagicMultivariateStatisticalAnalysis.log\n")
			f.write("NO\n")
		f.write("FRESH_MSA\n")
		f.write(str(self.params['MSAdistance'])+"\n")
		f.write("start\n")
#		if self.params['nproc'] > 1:
#			f.write("NO\n")
		f.write("NO\n")
		f.write("msamask\n")
		f.write("eigenimages\n")
		f.write("pixcoos\n")
		f.write("eigenpixels\n")
		f.write(str(self.params['numiters'])+"\n")
		f.write("69\n")
		f.write(str(self.params['overcorrection'])+"\n")
		f.write("my_msa\n")
		f.write("EOF\n")
		f.close()

		return filename

	#=========================
	def insertAnalysis(self, imagicstack, runtime, insert=False):
		### create MSAParam object
		msaq = appiondata.ApImagicAlignAnalysisData()
		msaq['runname'] = self.params['runname']
		msaq['run_seconds'] = runtime
		msaq['bin'] = self.params['bin']
		msaq['highpass'] = self.params['hpfilt']
		msaq['lowpass'] = self.params['lpfilt']
		msaq['mask_radius'] = self.params['mask_radius']
		msaq['mask_dropoff'] = self.params['mask_dropoff']
		msaq['numiters'] = self.params['numiters']
		msaq['overcorrection'] = self.params['overcorrection']
		msaq['MSAdistance'] = self.params['MSAdistance']
		msaq['eigenimages'] = "eigenimages"

		### finish analysis run
		analysisrunq = appiondata.ApAlignAnalysisRunData()
		analysisrunq['runname'] = self.params['runname']
		analysisrunq['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
		analysisrunq['imagicMSArun'] = msaq
		analysisrunq['alignstack'] = self.alignstackdata
		analysisrunq['hidden'] = False
		analysisrunq['description'] = self.params['description']

		apDisplay.printMsg("inserting Align Analysis Run parameters into database")
		if insert is True:
			analysisrunq.insert()

		return

	#=====================
	def start(self):
		t0 = time.time()

		self.checkAnalysisRun()

		# get stack parameters
		if self.params['alignid'] is not None:
			self.alignstackdata = appiondata.ApAlignStackData.direct_query(self.params['alignid'])
			stackpixelsize = self.alignstackdata['pixelsize']
			stack_box_size = self.alignstackdata['boxsize']
			self.params['boxsize'] = stack_box_size / int(self.params['bin'])
			self.params['apix'] = stackpixelsize * int(self.params['bin'])
			orig_path = self.alignstackdata['path']['path']
			orig_file = self.alignstackdata['imagicfile']
			linkingfile = orig_path+"/"+orig_file
			linkingfile = linkingfile.replace(".hed", "")
		else:
			apDisplay.printError("stack not in the database")

		# link stack file to working directory
		if not os.path.isfile(linkingfile+".hed"):
			apDisplay.printError("stackfile does not exist: "+linkingfile+".img")
		else:
			if not os.path.isfile(os.path.join(str(self.params['rundir']), "start.img")):
				apDisplay.printMsg("copying aligned stack into working directory for operations with IMAGIC")
#				shutil.copyfile(linkingfile+".img", str(self.params['rundir'])+"/start.img")
#				shutil.copyfile(linkingfile+".hed", str(self.params['rundir'])+"/start.hed")
				lnkcmd1 = "ln -s "+linkingfile+".img "+os.path.join(self.params['rundir'], "start.img")
				lnkcmd2 = "ln -s "+linkingfile+".hed "+os.path.join(self.params['rundir'], "start.hed")
				proc = subprocess.Popen(lnkcmd1, shell=True)
				proc.wait()
				proc = subprocess.Popen(lnkcmd2, shell=True)
				proc.wait()
				### header bug
				apImagicFile.setMachineStampInImagicHeader(os.path.join(self.params['rundir'], "start.hed"))
			else:
				apDisplay.printColor("aligned stack already exists in working directory", "green")

		### NEED TO CONVERT FILTERING PARAMETERS TO IMAGIC FORMAT BETWEEN 0-1
		if self.params['lpfilt'] is not None:
			self.params['lpfilt_imagic'] = 2 * float(self.params['apix']) / int(self.params['lpfilt'])
		else:
			self.params['lpfilt_imagic'] = False
		if float(self.params['lpfilt_imagic']) > 1:
			self.params['lpfilt_imagic'] = 1	# imagic cannot perform job when lowpass > 1
		if self.params['hpfilt'] is not None:
			self.params['hpfilt_imagic'] = 2 * float(self.params['apix']) / int(self.params['hpfilt'])
		else:
			self.params['hpfilt_imagic'] = False

		print self.params
		print "... aligned stack pixel size: "+str(self.params['apix'])
		print "... aligned stack box size: "+str(self.params['boxsize'])
		apDisplay.printColor("Running IMAGIC .batch file: See imagicMultivariateStatisticalAnalysis.log for details", "cyan")

		### create imagic batch file
		filename = self.createImagicBatchFile()
		### execute batch file that was created
		aligntime = time.time()
		proc = subprocess.Popen('chmod 775 '+filename, shell=True)
		proc.wait()
		apIMAGIC.executeImagicBatchFile(filename)
		logfile = open(os.path.join(self.params['rundir'], "imagicMultivariateStatisticalAnalysis.log"))
		apIMAGIC.checkLogFileForErrors(os.path.join(self.params['rundir'], "imagicMultivariateStatisticalAnalysis.log"))
		if not os.path.isfile(os.path.join(self.params['rundir'], "eigenimages.hed")):
			apDisplay.printError("IMAGIC did not run and did not create eigenimages")
		aligntime = time.time() - aligntime

		### remove copied stack
#		while os.path.isfile(os.path.join(self.params['rundir'], "start.img")):
#		apFile.removeStack(os.path.join(self.params['rundir'], "start.img"))

		### normalize eigenimages
		eigenimages = os.path.join(self.params['rundir'], "eigenimages.img")
		emancmd = "proc2d "+str(eigenimages)+" "+str(eigenimages)+" inplace"
		apParam.runCmd(emancmd, package="EMAN")

		### upload alignment
		imagicstack = os.path.join(self.params['rundir'], "start.hed")
		inserttime = time.time()
		if self.params['commit'] is True:
			self.insertAnalysis(imagicstack, runtime=aligntime, insert=True)
		else:
			apDisplay.printWarning("not committing results to DB")
		inserttime = time.time() - inserttime

		apDisplay.printMsg("Alignment time: "+apDisplay.timeString(aligntime))
		apDisplay.printMsg("Database Insertion time: "+apDisplay.timeString(inserttime))




#=====================
#=====================
if __name__ == '__main__':
	imagicMSA = imagicMultivariateStatisticalAnalysisScript()
	imagicMSA.start()
	imagicMSA.close()



