#!/usr/bin/env python
# Python script to upload a template to the database, and prepare images for import




	####	need to change mode to 755 of the batch file that is created
	####	how do I specify the filename from the pulldown menu?



import os
import shutil
import time
import apDB
import sys
import re
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
appiondb = apDB.apdb

#=====================
#=====================
class imagicReferenceFreeAlignmentScript(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage( "Usage: %prog --file=<name> --apix=<pixel> --outdir=<dir> "
			+"[options]")

		self.parser.add_option("--stackid", dest="stackid",
			help="ID of particle stack", metavar="int")
		self.parser.add_option("--lpfilt", dest="lpfilt", type="int",
			help="low-pass filter value (in angstroms)", metavar="INT")
		self.parser.add_option("--hpfilt", dest="hpfilt", type="int", 
			help="high-pass filter value (in angstroms)", metavar="INT")
		self.parser.add_option("--mask_radius", dest="mask_radius", type="float", default=1.0,
			help="radius of mask for MSA (in pixels or fraction of radius)", metavar="FLOAT")
                self.parser.add_option("--mask_dropoff", dest="mask_dropoff", type="float", 
                        help="dropoff (softness) of mask for MSA (in pixels or fraction of radius)", metavar="FLOAT")
		self.parser.add_option("--bin", dest="bin", type="int", default=1,
			help="binning of the image (power of 2)", metavar="INT")
		self.parser.add_option("--numiters", dest="numiters", type="int", default=50,
			help="number of iterations for MSA run", metavar="INT")
		self.parser.add_option("--overcorrection", dest="overcorrection", type="float",
			help="overcorrection factor for MSA program (determines its convergence speed)", metavar="FLOAT")
		self.parser.add_option("--MSAmethod", dest="MSAmethod", type="str",
			help="distance criteria that will be used in MSA", metavar="STR")
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
		if self.params['stackid'] is None:
			apDisplay.printError("There is no stack ID specified")
		if self.params['runId'] is None:
			apDisplay.printError("enter a run ID")
		if self.params['overcorrection'] is None:
			apDisplay.printError("enter value for the overcorrection factor")
		if self.params['MSAmethod'] is None:
			apDisplay.printError("enter distance criteria for MSA program (i.e. eulidean, chisquare, modulation)")
		
		return

	#=====================
	def setOutDir(self):

		# get reference-free classification and reclassification parameters
		if self.params['stackid'] is not None:
			stackdata = appiondb.direct_query(appionData.ApStackData, self.params['stackid'])
			path = stackdata['path']['path']
		else:
			apDisplay.printError("stack not in the database")

		uppath = os.path.abspath(os.path.join(path, "../.."))
		self.params['outdir'] = os.path.join(uppath, "norefImagic", self.params['runId'])


	def insertAlignment(self, imagicstack, insert=False):
#		alignrunq = appionData.ApAlignRunData()
#		alignrunq['runname'] = self.params['runId']
#		alignrunq['path'] = appionData.ApPathData(path=os.path.abspath(self.params['outdir']))
#		uniquerun = alignrunq.query(results=1)
#		if uniquerun:
#			apDisplay.printError("Run name '"+str(self.params['runId'])+"' and path already exist in database")
                
		### create norefParam object
		norefq = appionData.ApImagicNoRefRunData()
		norefq['runname'] = self.params['runId']
		norefq['mask_radius'] = self.params['mask_radius']
		norefq['mask_dropoff'] = self.params['mask_dropoff']
		norefq['numiters'] = self.params['numiters']
		norefq['overcorrection'] = self.params['overcorrection']
		norefq['MSAmethod'] = self.params['MSAmethod']

		### finish alignment run
		alignrunq = appionData.ApAlignRunData()
		alignrunq['runname'] = self.params['runId']
		alignrunq['path'] = appionData.ApPathData(path=os.path.abspath(self.params['outdir']))
		alignrunq['imagicnorefrun'] = norefq
		alignrunq['hidden'] = False
                alignrunq['bin'] = self.params['bin']
                alignrunq['hp_filt'] = self.params['hpfilt']
                alignrunq['lp_filt'] = self.params['lpfilt']
                alignrunq['description'] = self.params['description']
                alignrunq['project|projects|project'] = apProject.getProjectIdFromStackId(self.params['stackid'])

		# STOP RERENCE FREE PARAMETERS HERE

		### setup alignment stack	
		alignstackq = appionData.ApAlignStackData()
		alignstackq['alignrun'] = alignrunq
		alignstackq['imagicfile'] = os.path.basename(imagicstack)
		alignstackq['avgmrcfile'] = "average.mrc"
		alignstackq['iteration'] = 0
		alignstackq['path'] = appionData.ApPathData(path=os.path.abspath(self.params['outdir']))
		imagicfile = os.path.join(self.params['outdir'], alignstackq['imagicfile'])
                if not os.path.isfile(imagicfile):
                        apDisplay.printError("could not find stack file: "+imagicfile)
		alignstackq['stack'] = apStack.getOnlyStackData(self.params['stackid'])
		alignstackq['boxsize'] = self.params['boxsize']
		alignstackq['pixelsize'] = self.params['apix']
		alignstackq['description'] = self.params['description']
		alignstackq['hidden'] = False
		alignstackq['project|projects|project'] = apProject.getProjectIdFromStackId(self.params['stackid'])

		if insert is True:
			alignstackq.insert()

                ### create reference
                refq = appionData.ApAlignReferenceData()
                refq['refnum'] = 0
                refq['iteration'] = 0
                refq['mrcfile'] = "template.mrc"
                refq['path'] = appionData.ApPathData(path=os.path.abspath(self.params['outdir']))
                refq['alignrun'] = alignrunq

#		insert particle alignment (shift, rotate, etc.)
	
		return 


	#=====================
	def start(self):
				
		# get stack parameters
		if self.params['stackid'] is not None:
			stackdata = appiondb.direct_query(appionData.ApStackData, self.params['stackid'])
			stackpixelsize = apStack.getStackPixelSizeFromStackId(self.params['stackid'])
			stack_box_size = apStack.getStackBoxsize(self.params['stackid'])
			self.params['boxsize'] = stack_box_size / int(self.params['bin'])
			self.params['apix'] = stackpixelsize * int(self.params['bin'])
			orig_path = stackdata['path']['path']
			orig_file = stackdata['name']
			linkingfile = orig_path+"/"+orig_file
			linkingfile = linkingfile.replace(".hed", "")
		else:
			apDisplay.printError("stack not in the database")
		
		# copy stack file to working directory	
                if not os.path.isfile(linkingfile+".hed"):
                        apDisplay.printError("stackfile does not exist: "+linkingfile+".img")
                else:
                        shutil.copyfile(linkingfile+".img", str(self.params['outdir'])+"/start.img")
                        shutil.copyfile(linkingfile+".hed", str(self.params['outdir'])+"/start.hed")
	


		# EMAN command to filter input images and bin by specified number	
	#	emancmd  = "proc2d "
	#	emancmd += linkingfile+".img "
	#	emancmd += os.path.join(str(self.params['outdir']), "start.img")+" "
	#	orig_apix = float(self.params['apix']) / int(self.params['bin'])
	#	emancmd += "apix="+str(orig_apix)+" "
	#	if self.params['lpfilt'] > 0:
	#		emancmd += "lp="+str(self.params['lpfilt'])+" "
	#	if self.params['hpfilt'] > 0:
	#		emancmd += "hp="+str(self.params['hpfilt'])+" "
	#	if self.params['bin'] > 1:
	#		emancmd += "shrink="+str(self.params['bin'])+" "
	#	starttime = time.time()
	#	apDisplay.printColor("Running EMAN filtering", "cyan")
	#	apEMAN.executeEmanCmd(emancmd, verbose=True)
	#	apDisplay.printColor("finished eman in "+apDisplay.timeString(time.time()-starttime), "cyan")

                

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

	#	starttime=time.time()
		print self.params
		print "... stack pixel size: "+str(self.params['apix'])
		print "... stack box size: "+str(self.params['boxsize'])	
		apDisplay.printColor("Running IMAGIC .batch file: See imagicReferenceFreeAlignment.log for details", "cyan")
		
		# IMAGIC batch file creation	
		filename = "imagicReferenceFreeAlignment.batch"
		f = open(filename, 'w')
                f.write("#!/bin/csh -f\n")
                f.write("setenv IMAGIC_BATCH 1\n")
		if self.params['bin'] > 1:
			f.write("/usr/local/IMAGIC/stand/coarse.e <<EOF > imagicReferenceFreeAlignment.log\n")
			f.write("start\n")
			f.write("start_coarse\n")
			f.write(str(self.params['bin'])+"\n")
			f.write("EOF\n")
			f.write("/usr/local/IMAGIC/stand/im_rename.e <<EOF >> imagicReferenceFreeAlignment.log\n")
			f.write("start_coarse\n")
			f.write("start\n")
			f.write("EOF\n")
		if self.params['hpfilt_imagic'] and self.params['lpfilt_imagic'] is not None:
			f.write("/usr/local/IMAGIC/incore/incband.e OPT BAND-PASS <<EOF")
			if  os.path.isfile("imagicReferenceFreeAlignment.log"):
				f.write(" >> imagicReferenceFreeAlignment.log\n")
			else:
				f.write(" > imagicReferenceFreeAlignment.log\n")
			f.write("start\n")
			f.write("start_filt\n")
			f.write(str(self.params['hpfilt_imagic'])+"\n")
			f.write("0\n")
			f.write(str(self.params['lpfilt_imagic'])+"\n")
			f.write("NO\n")
			f.write("EOF\n")
                        f.write("/usr/local/IMAGIC/stand/im_rename.e <<EOF")
                	if  os.path.isfile("imagicReferenceFreeAlignment.log"):
                       		f.write(" >> imagicReferenceFreeAlignment.log\n")
                	else:
                        	f.write(" > imagicReferenceFreeAlignment.log\n")
                        f.write("start_filt\n")
                        f.write("start\n")
                        f.write("EOF\n")
		if self.params['mask_radius'] and self.params['mask_dropoff'] is not None:
			f.write("/usr/local/IMAGIC/stand/arithm.e <<EOF")
                	if  os.path.isfile("imagicReferenceFreeAlignment.log"):
                        	f.write(" >> imagicReferenceFreeAlignment.log\n")
                	else:
                        	f.write(" > imagicReferenceFreeAlignment.log\n")
			f.write("start\n")
			f.write("start_masked\n")
			f.write("SOFT\n")
			f.write(str(self.params['mask_radius'])+"\n")
			f.write(str(self.params['mask_dropoff'])+"\n")
			f.write("EOF\n")
                        f.write("/usr/local/IMAGIC/stand/im_rename.e <<EOF >> imagicReferenceFreeAlignment.log\n")
                        f.write("start_masked\n")
                        f.write("start\n")
                        f.write("EOF\n")
		f.write("/usr/local/IMAGIC/stand/testim.e <<EOF")
                if  os.path.isfile("imagicReferenceFreeAlignment.log"):
                        f.write(" >> imagicReferenceFreeAlignment.log\n")
                else:
                        f.write(" > imagicReferenceFreeAlignment.log\n")
		f.write("msamask\n")
		f.write(str(self.params['boxsize'])+","+str(self.params['boxsize'])+"\n")
		f.write("REAL\n")
		f.write("DISC\n")
		f.write(str(self.params['mask_radius'])+"\n")
		f.write("EOF\n")
		f.write("/usr/local/IMAGIC/msa/msa.e <<EOF >> imagicReferenceFreeAlignment.log\n")
		f.write("FRESH_MSA\n")
		f.write(str(self.params['MSAmethod'])+"\n")
		f.write("start\n")
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

		### execute batch file that was created
		aligntime = time.time()
		os.chdir(str(self.params['outdir']))
		os.system('chmod 755 imagicReferenceFreeAlignment.batch')
		os.system('./imagicReferenceFreeAlignment.batch')
		apDisplay.printColor("finished IMAGIC in "+apDisplay.timeString(time.time()-aligntime), "cyan")
		aligntime = time.time() - aligntime
	
		### upload alignment
		imagicstack = os.path.join(self.params['outdir'], "start.hed")
                inserttime = time.time()
                if self.params['commit'] is True:
                        self.insertAlignment(imagicstack, insert=True)
                else:
                        apDisplay.printWarning("not committing results to DB")
                inserttime = time.time() - inserttime

                apDisplay.printMsg("Alignment time: "+apDisplay.timeString(aligntime))
                apDisplay.printMsg("Database Insertion time: "+apDisplay.timeString(inserttime))

	
	
	
#=====================
#=====================
if __name__ == '__main__':
	imagicNoref = imagicReferenceFreeAlignmentScript()
	imagicNoref.start()
	imagicNoref.close()

	
