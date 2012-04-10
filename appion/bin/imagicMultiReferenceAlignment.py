#!/usr/bin/env python
# Python script to align images based on a reference template stack

import os
import shutil
import time
import sys
import re
import subprocess
from appionlib import appionScript
from appionlib import appiondata
from appionlib import apImagicFile
from appionlib import apTemplate
from appionlib import apDisplay
from appionlib import apParam
from appionlib import apIMAGIC
from appionlib import apFile
from appionlib import apStack
from appionlib import apProject

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
		self.parser.add_option("--center", dest="center", default=False,
			action="store_true", help="center particles with respect to the total sum prior to multi-reference alignment")
		self.parser.add_option("--num_orientations", dest="num_orientations", type="int", default="17",
			help="number of different rotation directions desired", metavar="INT")
		self.parser.add_option("--max_shift_orig", dest="max_shift_orig", type="float", default="0.2",
			help="maximum radial shift during MRA", metavar="float")
		self.parser.add_option("--max_shift_this", dest="max_shift_this", type="float", default="0.2",
			help="maximum radial shift during MRA for this iteration", metavar="float")
		self.parser.add_option("--samp_param", dest="samp_param", type="int", default="12",
			help="used to define precision of rotational alignment during MRA", metavar="int")
		self.parser.add_option("--minrad", dest="minrad", type="float", default="0.0",
			help="minimum inner radius of the image to be included in rotational alignment", metavar="float")
		self.parser.add_option("--maxrad", dest="maxrad", type="float", default="0.8",
			help="maximum inner radius of the image to be included in rotational alignment", metavar="float")
		self.parser.add_option("--numiter", dest="numiter", type="int", default="5",
			help="number of alignment iterations to perform", metavar="int")

		### choices
		self.aligntypes = ('rotational', 'translational', 'horizontal', 'vertical', 'all', 'brute_force')
		self.parser.add_option("--alignment_type", dest="alignment_type", type="choice", choices=self.aligntypes, default="all",
			help="you can specify what kind of alignment to do. Currently the options are 'all', 'rotational', \
				'translational', 'horizontal', 'vertical', or 'brute_force'. If 'all' is specified, you also need to note which \
				alignment (rotational or translational) to perform first", metavar="CHOICE")	
		self.first_alignment = ('rotation_first', 'translation_first')	
		self.parser.add_option("--first_alignment", dest="first_alignment", type="choice", choices=self.first_alignment, 
			default="rotation_first", help="which alignment routine is performed first? \
				specify 'rotation_first' or 'translation_first'", metavar="CHOICE")

		self.parser.set_defaults(nproc=8)

		return 


	#=====================
	def checkConflicts(self):
		### check for IMAGIC installation
		self.imagicroot = apIMAGIC.checkImagicExecutablePath()	
	
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
			stackdata = appiondata.ApStackData.direct_query(self.params['stackId']) 
			Atackpath = stackdata['path']['path']
			uppath = os.path.abspath(os.path.join(stackpath, "../.."))
			self.params['rundir'] = os.path.join(uppath, "align", self.params['runname'])
		else:
			apDisplay.printError("stack not in the database")


	#=====================
	def createImagicBatchFileMRA(self):
		# IMAGIC batch file creation

		##### DELETE HEADERS!!!!!!!!!!
		
		apIMAGIC.copyFile(self.params['rundir'], "start.hed", headers=True)
		apIMAGIC.copyFile(self.params['rundir'], "references.hed", headers=True)		

		filename = os.path.join(self.params['rundir'], "imagicMRA.batch")
		f = open(filename, 'w')
		f.write("#!/bin/csh -f\n")
		f.write("setenv IMAGIC_BATCH 1\n")

		append_log = False ### log file for imagic MRA, appended only if options are given

		#### OPTION OF PREPARING MULTI-REFERENCE ALIGNMENT REFERENCES

		if (self.params['refs'] is True and self.params['thresh_refs'] is not None and self.params['maskrad_refs'] is not None):
			f.write(str(self.imagicroot)+"/align/alirefs.e <<EOF")
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
			if self.params['mirror'] is True:
				f.write("YES\n")
				f.write("NO\n")
				f.write("TANDEM\n")
			else:
				f.write("NO\n")
			f.write("5\n")
			f.write("NO\n")
			f.write("EOF\n")
			f.write(str(self.imagicroot)+"/stand/im_rename.e <<EOF >> multiReferenceAlignment.log\n")
			f.write("references_prep\n")
			f.write("references\n")
			f.write("EOF\n")
			append_log = True
			
		### if centering is specified, center particle in a reference-free translational alignment to the total sum
		if self.params['center'] is True:
			if self.params['nproc'] > 1:
				f.write(str(self.imagicroot)+"/openmpi/bin/mpirun -np "+str(self.params['nproc'])+\
					" -x IMAGIC_BATCH "+str(self.imagicroot)+"/align/alimass.e_mpi <<EOF")
				if append_log is True:
					f.write(" >> multiReferenceAlignment.log\n")
				else:
					f.write(" > multiReferenceAlignment.log\n")
				f.write("YES\n")
				f.write(str(self.params['nproc'])+"\n")
			else:
				f.write(str(self.imagicroot)+"/align/alimass.e <<EOF")
				if append_log is True:
					f.write(" >> multiReferenceAlignment.log\n")
				else:
					f.write(" > multiReferenceAlignment.log\n")
				f.write("NO\n")
				
			f.write("start\n")
			f.write("start_cent\n")
			f.write("TOTSUM\n")
			f.write("CCF\n")
			f.write(str(self.params['max_shift_orig'])+"\n")
			f.write("3\n")
			f.write("NO_FILTER\n")
			f.write("EOF\n")
#			f.write(str(self.imagicroot)+"/stand/im_rename.e <<EOF >> multiReferenceAlignment.log\n")
#			f.write("start_cent\n")
#			f.write("start\n")
#			f.write("EOF\n")
			append_log = True
			
		### multi-reference alignment		
		if self.params['nproc'] > 1:
			f.write(str(self.imagicroot)+"/openmpi/bin/mpirun -np "+str(self.params['nproc'])+\
				" -x IMAGIC_BATCH "+str(self.imagicroot)+"/align/mralign.e_mpi <<EOF")
			### there is a bug in IMAGIC that makes the logfile tremendously big
#			if append_log is True:
#				f.write(" >> multiReferenceAlignment.log\n")
#			else:
#				f.write(" > multiReferenceAlignment.log\n")

			f.write("\n")

			f.write("YES\n")
			f.write(str(self.params['nproc'])+"\n")
		else:
			f.write(str(self.imagicroot)+"/align/mralign.e <<EOF")
			### there is a bug in IMAGIC that makes the logfile tremendously big
#			if append_log is True:
#				f.write(" >> multiReferenceAlignment.log\n")
#			else:
#				f.write(" > multiReferenceAlignment.log\n")

			f.write("\n")

			f.write("NO\n")
			
		f.write("FRESH\n")
		f.write("ALL_REFERENCES\n")
		f.write("ALIGNMENT\n")
		f.write("%s\n" % (self.params['alignment_type']))
		if self.params['alignment_type'].lower() == "all":
			f.write("%s\n" % (self.params['first_alignment']))
		if self.params['alignment_type'].lower() == "brute_force":
			f.write("%d\n" % (self.params['num_orientations']))
		f.write("CCF\n")
		if self.params['center'] is True:
			f.write("start_cent\n")
		else:
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
		f.write("NO\n")
		f.write(str(self.params['max_shift_orig'])+"\n")
		if self.params['center'] is True:
			f.write(str(self.params['max_shift_this'])+"\n")
		f.write("-180,180\n")
		if self.params['center'] is True:
			f.write("-180,180\n")
		f.write("INTERACTIVE\n")
		f.write(str(self.params['samp_param'])+"\n")
		f.write(str(self.params['minrad'])+","+str(self.params['maxrad'])+"\n")
		f.write(str(self.params['numiter'])+"\n")	
		f.write("NO\n")
		f.write("EOF\n")
		
		### write out alignment parameters to file
		f.write(str(self.imagicroot)+"/stand/headers.e <<EOF >> multiReferenceAlignment.log\n")
		f.write("PLT\n")
		f.write("INDEX\n")
		f.write("NUMBER_OF_INDEX\n")
		f.write("100;112;113;104;107\n") ### rotation, shiftx, shifty, ccc, reference num
#		f.write("NO\n")
		f.write("alignstack\n")
		f.write("outparams.plt\n")
		f.write("EOF\n")

		f.close()

		return filename


	### ==========================	
	
	def createImagicBatchFileScaling(self):
		# IMAGIC batch file creation

		filename = os.path.join(self.params['rundir'], "prepareStack.batch")
		f = open(filename, 'w')
		f.write("#!/bin/csh -f\n")
		f.write("setenv IMAGIC_BATCH 1\n")

		append_log = False ### log file for imagic MRA, appended only if options are given

		#### Bin down stack, low-pass filter and high-pass filter images

		if self.params['bin'] > 1:
			f.write(str(self.imagicroot)+"/stand/coarse.e <<EOF > prepareStack.log\n")
			f.write("start\n")
			f.write("start_coarse\n")
			f.write(str(self.params['bin'])+"\n")
			f.write("EOF\n")
			f.write(str(self.imagicroot)+"/stand/im_rename.e <<EOF >> prepareStack.log\n")
			f.write("start_coarse\n")
			f.write("start\n")
			f.write("EOF\n")
			append_log = True
		if self.params['highpass'] is not None and self.params['lowpass'] is not None:	
			### convert to IMAGIC-specific filtering parameters
			highpass, lowpass = apIMAGIC.convertFilteringParameters(self.params['highpass'], self.params['lowpass'], self.params['apix'])
			f.write(str(self.imagicroot)+"/incore/incband.e OPT BAND-PASS <<EOF")
			if append_log is True:
				f.write(" >> prepareStack.log\n")
			else:
				f.write(" > prepareStack.log\n")
			f.write("start\n")
			f.write("start_filt\n")
			f.write(str(highpass)+"\n")
			f.write("0\n")
			f.write(str(lowpass)+"\n")
			f.write("NO\n")
			f.write("EOF\n")
			f.write(str(self.imagicroot)+"/stand/im_rename.e <<EOF >> prepareStack.log\n")
			f.write("start_filt\n")
			f.write("start\n")
			f.write("EOF\n")
			append_log = True

		f.close()

		return filename


	### ==========================
	def scaleTemplates(self):
		reffile = os.path.join(self.params['rundir'], "references.hed")
		if self.params['apix'] != self.templatestack['apix']:
			scalefactor = float(self.templatestack['apix']) / self.params['apix']
			templates = apImagicFile.readImagic(reffile)
			scaledtemplates = []
			for templatearray in templates['images']:
				newarray = apTemplate.scaleTemplate(templatearray, scalefactor)
				scaledtemplates.append(newarray)
			apImagicFile.writeImagic(scaledtemplates, reffile)

		refbox = apFile.getBoxSize(reffile)[0]		
		stbox = self.params['boxsize']		
	
		### now clip the references to get identical boxsizes
		if stbox != refbox:
			while os.path.isfile(reffile+".new.img"):
				apFile.removeStack(reffile+".new.img")
			emancmd = "proc2d "+reffile+" "+reffile+".new.hed clip="+str(stbox)+" edgenorm"
			apParam.runCmd(emancmd, "EMAN")
			os.rename(reffile+".new.hed", reffile)
			os.rename(reffile+".new.img", reffile[:-4]+".img")
			
		return


	### ==========================	
	def getParticleParams(self):
		apDisplay.printColor("now getting particle shift / rotation / correlation parameters", "cyan")
		
		f = open(os.path.join(self.params['rundir'], "outparams.plt"), "r")
		lines = f.readlines()
		strip = [line.strip() for line in lines]
		split = [params.split() for params in strip]
		params = []
		for list in split:
			numberlist = [eval(p) for p in list]
			### figure out if the particle is mirrored, based on which reference it belongs to
			numrefs = apFile.numImagesInStack(os.path.join(self.params['rundir'], "references.hed"))
			half = numrefs / 2
			if numberlist[4] > half and self.params['mirror'] is True:
				mirror = 1
			else:
				mirror = 0
			numberlist.append(mirror)
			params.append(numberlist)	
			
		return params
		
		
	### ==========================
	def insertAlignmentRun(self, insert=False):               		

		### setup alignment run
		alignrunq = appiondata.ApAlignRunData()
		alignrunq['runname'] = self.params['runname']
		alignrunq['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
		uniquerun = alignrunq.query(results=1)
		if uniquerun:
			apDisplay.printError("Run name '"+self.params['runname']+"' and path already exist in database")
		
		### setup Reference preparation parameters, if given
		MRAq = appiondata.ApMultiRefAlignRunData()
		if self.params['refs'] is True:
			MRAq['lowpass_refs'] = self.params['lowpass_refs']
			MRAq['thresh_refs'] = self.params['thresh_refs']
			MRAq['maskrad_refs'] = self.params['maskrad_refs']	
	
		### setup Multi Reference Alignment Run
		MRAq['mirror'] = self.params['mirror']
		MRAq['center'] = self.params['center']
		MRAq['alignment_type'] = self.params['alignment_type']
		if self.params['alignment_type'].lower() == "all":
			MRAq['first_alignment'] = self.params['first_alignment']
		if self.params['alignment_type'].lower() == "brute_force":
			MRAq['num_orientations'] = self.params['num_orientations']
		MRAq['max_shift_orig'] = self.params['max_shift_orig']
		if self.params['center'] is True:
			MRAq['max_shift_this'] = self.params['max_shift_this']
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
	
		### setup alignment stack
		alignstackq = appiondata.ApAlignStackData()
		alignstackq['imagicfile'] = "alignstack.hed"
		alignstackq['avgmrcfile'] = "average.mrc"
		alignstackq['refstackfile'] = "references.hed"
		alignstackq['iteration'] = self.params['numiter']
		alignstackq['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
		alignstackq['alignrun'] = alignrunq	

		### check to make sure files exist
		imagicfile = os.path.join(self.params['rundir'], alignstackq['imagicfile'])
		if not os.path.isfile(imagicfile):
			apDisplay.printError("could not find stack file: "+imagicfile)
		refstackfile = os.path.join(self.params['rundir'], alignstackq['refstackfile'])
		if not os.path.isfile(refstackfile):
			apDisplay.printError("could not find reference stack file: "+refstackfile)
		alignstackq['stack'] = apStack.getOnlyStackData(self.params['stackId'])
		alignstackq['boxsize'] = self.params['boxsize']
		alignstackq['pixelsize'] = self.params['apix'] 
		alignstackq['description'] = self.params['description']
		alignstackq['hidden'] =  False
		alignstackq['num_particles'] = self.params['numpart']

		### insert
		if self.params['commit'] is True:
			alignstackq.insert()
		self.alignstackdata = alignstackq

		return 

	def insertParticlesIntoDatabase(self, partlist, insert=False):
		count = 0
		inserted = 0
		t0 = time.time()
		apDisplay.printColor("Inserting particle alignment data, please wait", "cyan")
		for particle in partlist:
			count += 1
			
			### get all particle parameters
			partnum = count
			rotation = particle[0] * -1 ### in spider negative rotation is clockwise
			shiftx = particle[1]
			shifty = particle[2]
			ccc = particle[3]
			refnum = int(particle[4])
			mirror = particle[5]
			
			if count % 100 == 0:
				sys.stderr.write(".")

			### setup reference
			refq = appiondata.ApAlignReferenceData()
			refq['refnum'] = refnum
			refq['iteration'] = self.params['numiter']
			refq['imagicfile'] = "references.hed"
			refq['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
			refq['alignrun'] = self.alignstackdata['alignrun']
			refq['templatestack'] = appiondata.ApTemplateStackData.direct_query(self.params['templateStackId'])
			reffile = os.path.join(self.params['rundir'], refq['imagicfile'])
			if not os.path.isfile(reffile):
				apDisplay.printError("could not find reference file: "+reffile)

			### setup particle
			alignpartq = appiondata.ApAlignParticleData()
			alignpartq['partnum'] = partnum
			alignpartq['alignstack'] = self.alignstackdata
			stackpartdata = apStack.getStackParticle(self.params['stackId'], partnum)
			alignpartq['stackpart'] = stackpartdata
			alignpartq['xshift'] = shiftx
			alignpartq['yshift'] = shifty
			alignpartq['rotation'] = rotation
			alignpartq['mirror'] = mirror
			alignpartq['ref'] = refq
			alignpartq['correlation'] = ccc

			### insert
			if self.params['commit'] is True:
				inserted += 1
				alignpartq.insert()

		apDisplay.printColor("\ninserted "+str(inserted)+" of "+str(count)+" particles into the database in "
			+apDisplay.timeString(time.time()-t0), "cyan")

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
			apDisplay.printColor("copying stack into running directoroy", "cyan")
			if self.stack['file'][-4:] == ".img" or self.stack['file'][-4:] == ".hed":
				strippedfile = self.stack['file'][:-4]
			else:
				strippedfile = self.stack['file']
			while os.path.isfile(os.path.join(self.params['rundir'], "start.img")):
				apFile.removeStack(os.path.join(self.params['rundir'], "start.img"))
			emancmd = "proc2d "+strippedfile+".hed "+os.path.join(self.params['rundir'], "start.hed ")+\
				"first=0 last="+str(self.params['numpart']-1)
			apParam.runCmd(emancmd, "EMAN")
		else:
			apDisplay.printError("stack not found in database")
	
		### get template stack parameters
		self.templatestack = {}
		self.templatestack['data'] = appiondata.ApTemplateStackData.direct_query(self.params['templateStackId'])
		self.templatestack['apix'] = self.templatestack['data']['apix']
		self.templatestack['boxsize'] = self.templatestack['data']['boxsize']	
		self.templatestack['file'] = os.path.join(self.templatestack['data']['path']['path'], self.templatestack['data']['templatename'])
		self.templatestack['numimages'] = self.templatestack['data']['numimages']

		### copy templates into working directory
		if os.path.isfile(self.templatestack['file']):
			apDisplay.printColor("copying templates into running directoroy", "cyan")
			ts = os.path.join(self.params['rundir'], "references.img")		
			while os.path.isfile(ts):
				apFile.removeStack(ts)
			if self.templatestack['file'][-4:] == ".img" or self.templatestack['file'][-4:] == ".hed":
				strippedfile = self.templatestack['file'][:-4]
			else:
				strippedfile = self.templatestack['file']
			emancmd = "proc2d "+strippedfile+".img "+ts
			apParam.runCmd(emancmd, "EMAN")
		else:
			apDisplay.printError("template stack not found in database")

		### set new pixelsize
		if self.params['bin'] is not None and self.params['bin'] != 0:
			self.params['apix'] = float(self.stack['apix']) * int(self.params['bin'])
		else:
			self.params['apix'] = self.stack['apix']

		### scale, low-pass, and high-pass filter stack ... do this with imagic, because it determines the appropriate boxsizes
		scalingbatchfile = self.createImagicBatchFileScaling()
		preptime = time.time()
		proc = subprocess.Popen("chmod 775 "+str(scalingbatchfile), shell=True)
		proc.wait()
		os.chdir(self.params['rundir'])
		apParam.runCmd(scalingbatchfile, "IMAGIC")
		apIMAGIC.checkLogFileForErrors(os.path.join(self.params['rundir'], "prepareStack.log"))
               	apDisplay.printColor("finished IMAGIC in "+apDisplay.timeString(time.time()-preptime), "cyan")

		### set new boxsize, done only after scaling is complete
		if self.params['bin'] is not None:
			self.params['boxsize'] = apFile.getBoxSize(os.path.join(self.params['rundir'], "start.hed"))[0]
		else:
			self.params['boxsize'] = self.stack['boxsize']

		### make sure template stack boxsize matches that of the input stack
		if self.params['apix'] != self.templatestack['apix'] or self.params['boxsize'] != self.templatestack['boxsize']:
			self.scaleTemplates()

		starttime=time.time()
		print self.params
		print "... stack pixel size: "+str(self.params['apix'])
		print "... stack box size: "+str(self.params['boxsize'])	
		apDisplay.printColor("Running IMAGIC .batch file: See multiReferenceAlignment.log file for details", "cyan")
	
		### create IMAGIC batch file
		batchfile = self.createImagicBatchFileMRA()

		### execute IMAGIC batch file
		aligntime0 = time.time()
		proc = subprocess.Popen("chmod 775 "+str(batchfile), shell=True)
		proc.wait()
		os.chdir(self.params['rundir'])
		apParam.runCmd(batchfile, "IMAGIC")
		apIMAGIC.checkLogFileForErrors(os.path.join(self.params['rundir'], "multiReferenceAlignment.log"))
               	apDisplay.printColor("finished IMAGIC in "+apDisplay.timeString(time.time()-aligntime0), "cyan")

		### get particle parameters (shift, rotate, refnum, mirror, ccc)
		partparams = self.getParticleParams()

		### average stack
		alignstack = os.path.join(self.params['rundir'], "alignstack.hed")
		apStack.averageStack(alignstack)	

		### normalize particles (otherwise found problems in viewing with stackviewer)
		emancmd = "proc2d "+alignstack+" "+alignstack+".norm.hed norm"
		while os.path.isfile(alignstack+".norm.img"):
			apFile.removeStack(alignstack+".norm.img")
		apParam.runCmd(emancmd, "EMAN")
		os.rename(alignstack+".norm.hed", alignstack)
		os.rename(alignstack+".norm.img", alignstack[:-4]+".img")

		### normalize references
		emancmd = "proc2d "+ts+" "+ts+".norm.hed norm"
		while os.path.isfile(ts+".norm.img"):
			apFile.removeStack(ts+".norm.img")
		apParam.runCmd(emancmd, "EMAN")
		os.rename(ts+".norm.hed", ts)
		os.rename(ts+".norm.img", ts[:-4]+".img")

		### remove copied stack
		while os.path.isfile(os.path.join(self.params['rundir'], "start.img")):
			apFile.removeStack(os.path.join(self.params['rundir'], "start.img"))

		### insert run into database
		self.insertAlignmentRun(insert=True)
		self.insertParticlesIntoDatabase(partparams, insert=True)

	
	
#=====================
#=====================
if __name__ == '__main__':
	imagicalignment = imagicAlignmentScript()
	imagicalignment.start()
	imagicalignment.close()

	
