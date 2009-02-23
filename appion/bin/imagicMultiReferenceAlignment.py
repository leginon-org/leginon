#!/usr/bin/env python
# Python script to upload a template to the database, and prepare images for import




	####	need to change mode to 755 of the batch file that is created
	####	how do I specify the filename from the pulldown menu?



import os
import shutil
import time
import sys
import re
import appionScript
import appionData

import apParam
import apRecon
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
class imagicAlignmentScript(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage( "Usage: %prog --file=<name> --apix=<pixel> --outdir=<dir> "
			+"[options]")

		### stack, template, & particles to use
		self.parser.add_option("--stackId", dest="stackId", type="int",
			help="ID of stack for alignment", metavar="int")
		self.parser.add_option("--templateStackId", "--t", dest="templateStackId", type="int",
                        help="ID of template stack used as references", metavar="int")
		self.parser.add_option("-N", "--num-part", dest="numpart", type="int",
                        help="Number of particles to use", metavar="#")

		### filtering parameters
                self.parser.add_option("--clip", dest="clipsize", type="int",
                        help="Clip size in pixels (reduced box size)", metavar="#")
                self.parser.add_option("--lowpass", "--lp", dest="lowpass", type="int",
                        help="Low pass filter radius (in Angstroms)", metavar="#")
                self.parser.add_option("--highpass", "--hp", dest="highpass", type="int",
                        help="High pass filter radius (in Angstroms)", metavar="#")
                self.parser.add_option("--bin", dest="bin", type="int", default=1,
                        help="Bin images by factor", metavar="#")

		### imagic-specific parameters -- references
		self.parser.add_option("--refs", dest="refs", default=True,
			action="store_true", help="if this is marked, the references will be prepared")
		self.parser.add_option("--no-refs", dest="refs", default=True,
                        action="store_false", help="if this is marked, the references will NOT be prepared")
		self.parser.add_option("--lowpass_refs", "--lp_refs", dest="lowpass_refs", type="int", default="5",
                        help="Low pass filter radius (in Angstroms) of the reference stack", metavar="#")
		self.parser.add_option("--thresh_refs", dest="thresh_refs", type="int", default="-999",
                        help="thresholding pixel values of mrarefs (negative density values commonly represent stain)", metavar="#")
		self.parser.add_option("--maskrad_refs", dest="maskrad_refs", type="float", default="0.9",
                        help="radius of circular mask for references", metavar="float")

		### imagic-specific parameters -- multi-reference alignment
		self.parser.add_option("--mirror", "-M", dest="mirror", default=True,
                        action="store_true", help="use mirrors in alignment to capture different particle orientations")
		self.parser.add_option("--no-mirror", dest="mirror", default=True,
                        action="store_false", help="DO NOT use mirrors in alignment to capture different particle orientations")
		self.parser.add_option("--max_shift_orig", dest="max_shift_orig", type="float", default="0.2",
                        help="maximum radial shift during MRA", metavar="float")
#		self.parser.add_option("--max_shift_this", dest="max_shift_this", type="float",
#                        help="maximum radial shift during MRA for this iteration", metavar="float")
                self.parser.add_option("--samp_param", dest="samp_param", type="int", default="12",
                        help="used to define precision of rotational alignment during MRA", metavar="int")
		self.parser.add_option("--minrad", dest="minrad", type="float", default="0.0",
                        help="minimum inner radius of the image to be included in rotational alignment", metavar="float")
		self.parser.add_option("--maxrad", dest="maxrad", type="float", default="0.8",
                        help="maximum inner radius of the image to be included in rotational alignment", metavar="float")
		self.parser.add_option("--numiter", dest="numiter", type="int", default="5",
                        help="number of alignment iterations to perform", metavar="int")


		return 

	#=====================
	def checkConflicts(self):
		### run parameters
		if self.params['templateStackId'] is None:
			apDisplay.printError("enter template stack Id")
		if self.params['stackId'] is None:
			apDisplay.printError("enter a stack Id")

		### references
		if self.params['refs'] is True:
			if self.params['thresh_refs'] is None or self.params['maskrad_refs'] is None:
				apDisplay.printError("enter ALL parameters for preparing references")
		
		### Multi Reference Alignment params
		if self.params['mirror'] is None:
			apDisplay.printError("enter option of using mirrors")

		return

	#=====================
	def setRunDir(self):

		# get reference-free classification and reclassification parameters
		if self.params['stackId'] is not None:
			stackdata = appionData.ApStackData.direct_query(self.params['stackId']) 
			Atackpath = stackdata['path']['path']
			uppath = os.path.abspath(os.path.join(stackpath, "../.."))
			self.params['rundir'] = os.path.join(uppath, "align", self.params['runname'])
		else:
			apDisplay.printError("stack not in the database")


	#=====================
	def createImagicBatchFile(self):
		# IMAGIC batch file creation

		##### DELETE HEADERS!!!!!!!!!!
		
		apIMAGIC.copyFile(self.params['rundir'], "start.hed", headers=True)

		filename = os.path.join(self.params['rundir'], "imagicMRA.batch")
		f = open(filename, 'w')
                f.write("#!/bin/csh -f\n")
                f.write("setenv IMAGIC_BATCH 1\n")

		appendlog = False ### log file for imagic MRA, appended only if options are given

		#### Bin down stack, low-pass filter and high-pass filter images

		if self.params['bin'] > 1:
                        f.write("/usr/local/IMAGIC/stand/coarse.e <<EOF > multiReferenceAlignment.log\n")
                        f.write("start\n")
                        f.write("start_coarse\n")
                        f.write(str(self.params['bin'])+"\n")
                        f.write("EOF\n")
                        f.write("/usr/local/IMAGIC/stand/im_rename.e <<EOF >> multiReferenceAlignment.log\n")
                        f.write("start_coarse\n")
                        f.write("start\n")
                        f.write("EOF\n")
                        append_log = True
                if self.params['highpass'] is not None and self.params['lowpass'] is not None:
			
			### convert to IMAGIC-specific filtering parameters
			highpass, lowpass = apIMAGIC.convertFilteringParameters(self.params['highpass'], self.params['lowpass'], self.params['apix'])
                        f.write("/usr/local/IMAGIC/incore/incband.e OPT BAND-PASS <<EOF")
                        if append_log is True:
                                f.write(" >> multiReferenceAlignment.log\n")
                        else:
                                f.write(" > multiReferenceAlignment.log\n")
                        f.write("start\n")
                        f.write("start_filt\n")
                        f.write(str(highpass)+"\n")
                        f.write("0\n")
                        f.write(str(lowpass)+"\n")
                        f.write("NO\n")
                        f.write("EOF\n")
                        f.write("/usr/local/IMAGIC/stand/im_rename.e <<EOF >> multiReferenceAlignment.log\n")
                        f.write("start_filt\n")
                        f.write("start\n")
                        f.write("EOF\n")
                        append_log = True

		#### OPTION OF PREPARING MULTI-REFERENCE ALIGNMENT REFERENCES

		if (self.params['refs'] is True and self.params['thresh_refs'] is not None and self.params['maskrad_refs'] is not None):
			f.write("/usr/local/IMAGIC/align/alirefs.e <<EOF")
			if append_log is True:
				f.write(" >> multiReferenceAlignment.log\n")
			else:
				f.write(" > multiReferenceAlignment.log\n")
			f.write("ALL\n")
			f.write("CCF\n")
			f.write("references\n")
			f.write("NO\n")
			f.write(str(self.params['maskrad_refs'])+"\n")
			f.write("references_prep\n")
			f.write(str(self.params['thresh_refs'])+"\n")
			f.write("0.1\n")
			f.write("-180,180\n")
			f.write("NO\n")
			f.write("NO\n")
			f.write("EOF\n")
			f.write("/usr/local/IMAGIC/stand/im_rename.e <<EOF >> multiReferenceAlignment.log\n")
			f.write("references_prep\n")
			f.write("references\n")
			f.write("EOF\n")
			append_log = True

		### multi-reference alignment		

		f.write("/usr/local/IMAGIC/align/mralign.e <<EOF")
		if append_log is True:
			f.write(" >> multiReferenceAlignment.log\n")
		else:
			f.write(" > multiReferenceAlignment.log\n")
		f.write("NO\n")
		f.write("FRESH\n")
		f.write("ALL\n")
		f.write("ROTATION_FIRST\n")
		f.write("CCF\n")
		f.write("start\n")
		f.write("alignstack\n")
		f.write("start\n")
		f.write("references\n")
		if self.params['lowpass_refs'] is not None:
			hpfilt_imagic, lpfilt_imagic = apIMAGIC.convertFilteringParameters("", self.params['lowpass_refs'], self.params['apix'])
			f.write("LOWPASS\n")
			f.write(str(lpfilt_imagic)+"\n")
		else:
			f.write("NO\n")
		if self.params['mirror'] is not None:
			f.write("YES\n")
		else:
			f.write("NO\n")
		f.write(str(self.params['max_shift_orig'])+"\n")
		f.write("-180,180\n")
		f.write("INTERACTIVE\n")
		f.write(str(self.params['samp_param'])+"\n")
		f.write(str(self.params['minrad'])+","+str(self.params['maxrad'])+"\n")
		f.write(str(self.params['numiter'])+"\n")	
		f.write("NO\n")
		f.write("EOF\n")
		f.close()

		return filename

	def scaleTemplates(self):
		apDisplay.printError("need to get scaling to work ... not working yet!")
#		if self.params['boxsize'] < self.templatestack['boxsize']:
#			scale = self.templatestack['boxsize'] / self.params['boxsize']
#			
			### coarsen templates

#		elif self.params['boxsize'] > self.templatestack['boxsize']:
#			scale = self.params['boxsize'] / self.templatestack['boxsize']
			
			### blow up templates

	def createAverageMrc(self):
		apDisplay.printColor("now creating Average MRC file", "green")
		return 

	### ==========================	
        def getParticleData(self, partnum):
                partq = appionData.ApStackParticlesData()
                partq['stack'] = self.stackdata['stack']
                partq['particleNumber'] = partnum
                parts = partq.query(results=1)
		return parts[0]

	def getParticleParams(self):
		apDisplay.printColor("now getting particle parameters", "green")
		return ""

	def insertAlignmentRun(self, insert=False):               		

		### setup alignment run
                alignrunq = appionData.ApAlignRunData()
                alignrunq['runname'] = self.params['runname']
                alignrunq['path'] = appionData.ApPathData(path=os.path.abspath(self.params['rundir']))
                uniquerun = alignrunq.query(results=1)
                if uniquerun:
                        apDisplay.printError("Run name '"+self.params['runname']+"' and path already exist in database")
		
		### setup Reference preparation parameters, if given
		MRAq = appionData.ApMultiRefAlignRunData()
		if self.params['refs'] is True:
			MRAq['lowpass_refs'] = self.params['lowpass_refs']
			MRAq['thresh_refs'] = self.params['thresh_refs']
			MRAq['maskrad_refs'] = self.params['maskrad_refs']	
	
		### setup Multi Reference Alignment Run
		MRAq['mirror'] = self.params['mirror']
		MRAq['max_shift_orig'] = self.params['max_shift_orig']
#		MRAq['max_shift_this'] = self.params['max_shift_this']
		MRAq['samp_param'] = self.params['samp_param']
		MRAq['min_radius'] = self.params['minrad']
		MRAq['max_radius'] = self.params['minrad']
		MRAq['numiter'] = self.params['numiter']

		### finish alignment run
                alignrunq['imagicMRA'] = MRAq
                alignrunq['hidden'] = False
                alignrunq['description'] = self.params['description']
                alignrunq['lp_filt'] = self.params['lowpass']
                alignrunq['hp_filt'] = self.params['highpass']
                alignrunq['bin'] = self.params['bin']
                alignrunq['project|projects|project'] = apProject.getProjectIdFromStackId(self.params['stackId'])
	
		### setup alignment stack
                alignstackq = appionData.ApAlignStackData()
                alignstackq['imagicfile'] = "alignstack.hed"
#		alignstackq['avgmrcfile'] = "average.mrc"
                alignstackq['refstackfile'] = os.path.join(self.params['rundir'], "references.hed") 
                alignstackq['iteration'] = self.params['numiter']
                alignstackq['path'] = appionData.ApPathData(path=os.path.abspath(self.params['rundir']))
                alignstackq['alignrun'] = alignrunq	

		### check to make sure files exist
                imagicfile = os.path.join(self.params['rundir'], alignstackq['imagicfile'])
                if not os.path.isfile(imagicfile):
                        apDisplay.printError("could not find stack file: "+imagicfile)
#                avgmrcfile = os.path.join(self.params['rundir'], alignstackq['avgmrcfile'])
#                if not os.path.isfile(avgmrcfile):
#                        apDisplay.printError("could not find average mrc file: "+avgmrcfile)
                refstackfile = os.path.join(self.params['rundir'], alignstackq['refstackfile'])
                if not os.path.isfile(refstackfile):
                        apDisplay.printError("could not find reference stack file: "+refstackfile)
                alignstackq['stack'] = apStack.getOnlyStackData(self.params['stackId'])
                alignstackq['boxsize'] = self.params['boxsize']
                alignstackq['pixelsize'] = self.params['apix'] 
                alignstackq['description'] = self.params['description']
                alignstackq['hidden'] =  False
                alignstackq['num_particles'] = self.params['numpart']
                alignstackq['project|projects|project'] = apProject.getProjectIdFromStackId(self.params['stackId'])

		### insert
                if self.params['commit'] is True:
                        alignstackq.insert()
                self.alignstackdata = alignstackq

		return 

	def insertParticlesIntoDatabase(self, stackid, partlist, insert=False):
		apDisplay.printColor("now inserting particles into Database", "green")	
		return

	#=====================
	def start(self):
		### get stack parameteres
		self.stack = {}
                self.stack['data'] = apStack.getOnlyStackData(self.params['stackId'])
                self.stack['apix'] = apStack.getStackPixelSizeFromStackId(self.params['stackId'])
                self.stack['boxsize'] = apStack.getStackBoxsize(self.params['stackId'])
                self.stack['file'] = os.path.join(self.stack['data']['path']['path'], self.stack['data']['name'])

		### copy stack into working directory	
		if os.path.isfile(self.stack['file']):
			apDisplay.printColor("copying stack into running directoroy", "green")
			if self.stack['file'][-4:] == ".img" or self.stack['file'][-4:] == ".hed":
				strippedfile = self.stack['file'][:-4]
			else:
				strippedfile = self.stack['file']
			emancmd = "proc2d "+strippedfile+".hed "+os.path.join(self.params['rundir'], "start_copy.hed ")+"first=0 last="+str(self.params['numpart']-1)
			apEMAN.executeEmanCmd(emancmd)
			os.renames(os.path.join(self.params['rundir'], "start_copy.hed"), os.path.join(self.params['rundir'], "start.hed"))
			os.renames(os.path.join(self.params['rundir'], "start_copy.img"), os.path.join(self.params['rundir'], "start.img"))	
	
		### get template stack parameters
		self.templatestack = {}
		self.templatestack['data'] = appionData.ApTemplateStackData.direct_query(self.params['templateStackId'])
		self.templatestack['apix'] = self.templatestack['data']['apix']
		self.templatestack['boxsize'] = self.templatestack['data']['boxsize']	
		self.templatestack['file'] = os.path.join(self.templatestack['data']['path']['path'], self.templatestack['data']['templatename'])

		### copy templates into working directoryi
		if os.path.isfile(self.templatestack['file']):
			apDisplay.printColor("copying templates into running directoroy", "green")		
			if self.templatestack['file'][-4:] == ".img" or self.templatestack['file'][-4:] == ".hed":
				strippedfile = self.templatestack['file'][:-4]
			else:
				strippedfile = self.templatestack['file']
			shutil.copyfile(strippedfile+".hed", os.path.join(self.params['rundir'], "references.hed"))
			shutil.copyfile(strippedfile+".img", os.path.join(self.params['rundir'], "references.img"))

		### set new pixelsize and boxsize
		if self.params['bin'] is not None:
			self.params['apix'] = float(self.stack['apix']) * int(self.params['bin'])
			self.params['boxsize'] = int(self.stack['boxsize']) / int(self.params['bin'])

		### make sure template stack boxsize matches that of the input stack
		if self.params['boxsize'] != self.templatestack['boxsize']:
			self.scaleTemplates()

		starttime=time.time()
		print self.params
		print "... stack pixel size: "+str(self.params['apix'])
		print "... stack box size: "+str(self.params['boxsize'])	
		apDisplay.printColor("Running IMAGIC .batch file: See multiReferenceAlignment.log file for details", "cyan")
	
		### create IMAGIC batch file
		batchfile = self.createImagicBatchFile()

		### execute IMAGIC batch file
		aligntime0 = time.time()
		os.system("chmod 775 "+str(batchfile))
		os.chdir(self.params['rundir'])
#		apIMAGIC.copyFile(self.params['rundir'], "start.hed")  ### removes poorly formatted EMAN headers
#		apIMAGIC.executeImagicBatchFile(batchfile)
               	apDisplay.printColor("finished IMAGIC in "+apDisplay.timeString(time.time()-aligntime0), "cyan")

		### create Average MRC file
		self.createAverageMrc()		

		partlist = self.getParticleParams()

		### insert run into database
                self.insertAlignmentRun(insert=True)
		self.insertParticlesIntoDatabase(self.params['stackId'], partlist, insert=True)

	
	
#=====================
#=====================
if __name__ == '__main__':
	imagicalignment = imagicAlignmentScript()
	imagicalignment.start()
	imagicalignment.close()

	
