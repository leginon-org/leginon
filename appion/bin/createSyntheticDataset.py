#!/usr/bin/env python

### python imports
import os
import re
import subprocess
import numpy
import random
import math
import time

### appion imports
import apVolume
import apEMAN
import apDisplay
import apDatabase
import apFile
import apImage
import apImagicFile
import apIMAGIC
import apParam
import appionScript
import appionData
import apStackMeanPlot
from pyami import mrc, imagefun
from EMAN import *
from scipy import fftpack, ndimage

class createSyntheticDatasetScript(appionScript.AppionScript):

	#=====================
	def setupParserOptions(self):

		self.parser.set_usage("Usage: %prog --stack=ID [ --num-part=# ]")

		### necessary input values
		self.parser.add_option("--modelid", dest="modelid", type="int",
			help="model id from database", metavar="#")
		self.parser.add_option("-f", "--threedfile", dest="threedfile", type="str",
			help="name of the 3d .mrc file from which projections will be made", metavar="STR")
		self.parser.add_option("-b", "--boxsize", dest="box", type="int",
			help="boxsize that will be applied to the stack", metavar="INT")
		self.parser.add_option("--apix", dest="apix", type="float",
			help="pixelsize of the 3d model", metavar="FLOAT")
			
		### optional global parameters
		self.parser.add_option("--session", dest="sessionname", type="str",
			help="session name (e.g. 06jul12a), do not give experiment id", metavar="str")

		### default input parameters
		self.parser.add_option("--projcount", dest="projcount", type="int", default=10228,
			help="number of projections to be made from the input 3d .mrc file", metavar="INT")
		self.parser.add_option("--projstdev", dest="projstdev", type="float", default=5.0,
			help="standard deviation of projection angle for each preferred orientation", metavar="FLOAT")
		self.parser.add_option("--shiftrad", dest="shiftrad", type="int", default=5,
			help="radius of of random shift for each particle", metavar="INT")
		self.parser.add_option("--rotang", dest="rotang", type="int", default=360,
			help="angle of random rotation for each particle", metavar="INT")
		self.parser.add_option("--flip", dest="flip", default=True,
			action="store_true", help="randomly flip the projections along with shifts and rotations")
		self.parser.add_option("--no-flip", dest="flip", default=True,
			action="store_false", help="DO NOT randomly flip the projections along with shifts and rotations")
		self.parser.add_option("--kv", dest="kv", type="float", default=120,
			help="KV of the microscope, needed for envelope function", metavar="INT")
		self.parser.add_option("--cs", dest="cs", type="float", default=0.002,
			help="spherical aberration of the microscope", metavar="FLOAT")
		self.parser.add_option("--df1", dest="df1", type="float", default=-1.5,
			help="defocus value 1 (represented as the mean if --randomdef & --randomdef-std specified)", metavar="FLOAT")
		self.parser.add_option("--df2", dest="df2", type="float", default=-1.5,
			help="defocus value 2 (represented as the mean if --randomdef & --randomdef-std specified", metavar="FLOAT")
		self.parser.add_option("--randomdef", dest="randomdef", default=False,
			action="store_true", help="randomize defocus values when applying CTF (df1 and df2 would represent the mean)")
		self.parser.add_option("--randomdef-std", dest="randomdef_std", type="float", default=0.4,
			help="standard deviation (in microns) for the gaussian distribution of defoci randomizations about the mean", metavar="FLOAT")
		self.parser.add_option("--astigmatism", dest="astigmatism", type="float", default=0,
			help="only input if you want to apply an astigmatic ctf", metavar="FLOAT")
		self.parser.add_option("--snr1", dest="snr1", type="float", default=1.8,
			help="first level of noise, simulating beam damage & structural noise", metavar="FLOAT")
		self.parser.add_option("--snrtot", dest="snrtot", type="float", default=0.06,
			help="total signal-to-noise ratio, simulating beam damage, structural noise, & digitization", metavar="FLOAT")
		self.parser.add_option("--envelope", dest="envelope", type="string",
			help="you may apply any envelope function to the dataset, but it has to be a 2d .mrc file that represents envelope decay", metavar="STR")

		### optional parameters (ACE2 correct & filtering)
		self.parser.add_option("--ace2correct", dest="ace2correct", default=False,
			action="store_true", help="ace2correct images after applying CTF")
		self.parser.add_option("--ace2correct-rand", dest="ace2correct_rand", default=False,
			action="store_true", help="ace2correct images after applying CTF & slightly randomize / wiggle the defocus parameters")
		self.parser.add_option("--ace2correct-std", dest="ace2correct_std", type="float", default=0.05,
			help="used in conjunction with ace2correct-rand, specify the standard deviation in microns. The correction \
				defoci will be 'wiggled' about the actual applied defocus value with a gaussian distribution determined by the std. \
				This value should not be too high, otherwise severe artifacts will be introduced into the images", metavar="float")
				
		### optional ACE2 estimation parameters, used in conjunction with ace2correct
		self.parser.add_option("--ace2estimate", dest="ace2estimate", default=False,
			action="store_true", help="use ace2 when estimating the defocus that was applied to each image (simulates robustness of ACE2 algorithm)")
			
		self.parser.add_option("--lpfilt", dest="lpfilt", type="int",
			help="low-pass filter images after creation of the dataset", metavar="INT")
		self.parser.add_option("--hpfilt", dest="hpfilt", type="int",
			help="high-pass filter images after creation of the dataset", metavar="INT")
		self.parser.add_option("--norm", dest="norm", default=False,
			action="store_true", help="normalize images after creation of the dataset")

		return		
	
	
	#=====================
	def checkConflicts(self):

		### necessary input values
		if self.params['threedfile'] is None and self.params['modelid'] is None:
			apDisplay.printError('either threed .mrc file or modelid was not defined')
		if self.params['threedfile'] is not None and self.params['modelid'] is not None:
			apDisplay.printError('please specify a single .mrc file (i.e. threedfile or modelid)')
		if self.params['runname'] is None:
			runcount = 1
			while os.path.isdir(os.path.join(self.params['rundir'], "dataset"+str(runcount))):
				runcount += 1
			self.params['runname'] = "dataset"+str(runcount)
		if self.params['rundir'] is None:
			apDisplay.printError('run directory not specified')
		self.params['rundir'] = os.path.join(self.params['rundir'], self.params['runname'])
		if self.params['box'] is None and self.params['modelid'] is None:
			apDisplay.printError('boxsize of the output stack not specified')
		if self.params['apix'] is None and self.params['modelid'] is None:
			apDisplay.printError('angstroms per pixel of the input model not specified')
			
		### get session info
		if self.params['sessionname'] is None:
			split = self.params['rundir'].split("/")
			self.params['sessionname'] = split[4]

		### make sure that the defoci are negative and in microns
		self.params['df1'] *= 10**-6
		self.params['df2'] *= 10**-6
		if self.params['df1'] > 0:
			apDisplay.printError('defocus value is positive!')
		if self.params['df2'] > 0:
			apDisplay.printError('defocus value is positive!')
#		if self.params['df1'] < -1e-05:
#			apDisplay.printError('make sure defocus is in meters, i.e. for -2 microns, df=-2e-06!')
#		if self.params['df2'] < -1e-05:
#			apDisplay.printError('make sure defocus is in meters, i.e. for -2 microns, df=-2e-06!')

		### make sure that only one type of ace2correction is specified
		if self.params['ace2correct'] is True and self.params['ace2correct_rand'] is True:
			apDisplay.printError('Please specify only 1 type of ace2 correction')
		if self.params['ace2correct_std'] >= 0.5 or self.params['ace2correct_std'] <= 0:
			apDisplay.printError("Ace2correct standard deviation specified too high, please use value between 0 < std < 0.5")
		if self.params['ace2estimate'] is True and self.params['ace2correct'] is False:
			apDisplay.printError("ACE2 estimation should only be used if you're doing correction as well, please use both ace2correct and ace2estimate")

		### some defaults, and workarounds for now
		self.appiondir = apParam.getAppionDirectory()
		self.params['filesperdir'] = 2048
		self.params['projpergraph'] = 100 
		if self.params['filesperdir'] > self.params['projcount']:
			self.params['filesperdir'] = math.ceil(float(self.params['projcount']) / 2)
						
		### make sure amplitude correction file exists			
		if self.params['envelope'] is None:
			self.params['envelope'] = os.path.join(apParam.getAppionDirectory(), "lib/envelopeImage.mrc")


		return


	#=====================
	def center(self, image):
		half = numpy.asarray(image.shape)/2
		imagecent = ndimage.shift(image, half, mode='wrap', order=0)
		return imagecent


	#=====================
	def real_fft2d(self, image, *args, **kwargs):
		padshape = numpy.asarray(image.shape)*1
		padimage = apImage.frame_constant(image, padshape, image.mean())
		fft = fftpack.fft2(padimage, *args, **kwargs)
		return fft


	#=====================
	def inverse_real_fft2d(self, fft, *args, **kwargs):
		return fftpack.ifft2(fft, *args, **kwargs).real
	
	
	#=====================		
	def applyEnvelope(self, inimage, outimage, envelope, scaleFactor=1):
		"""
		input path to image and envelope, output amplitude-adjusted image
		"""
		
		apDisplay.printColor("now applying envelope function to: "+inimage, "cyan")
		
		### read images
		im = mrc.read(inimage)
		env = mrc.read(envelope)

		### scale envelope
		if scaleFactor != 1:
			env = ndimage.zoom(env, zoom=scaleFactor, mode='nearest')
		
		### fourier transform
		imfft = self.real_fft2d(im)

		### shift center of envelope to the edges
		envamp = self.center(env)

		### mutliply real envelope function by image fft
		envamp = (envamp - envamp.min()) / (envamp.max() - envamp.min())
		newfft = envamp * imfft

		### inverse transform
		newimg = self.inverse_real_fft2d(newfft)

		### normalize between 0 and 1
		newimg = (newimg-newimg.mean()) / newimg.std()

		### save image
		mrc.write(newimg, outimage)

		### workaround for now
		time.sleep(1)

	#=====================
	def setEulers(self):
		eulerlist = []
		eulerlist.append((0,0))
		eulerlist.append((90,0))
		eulerlist.append((90,90))
		
		return eulerlist


	#=====================
	def createProjections(self):
		timestamp = apParam.makeTimestamp()
		eulerlist = self.setEulers()
		while os.path.isfile(os.path.join(self.params['rundir'], "proj.hed")):
			apFile.removeStack(os.path.join(self.params['rundir'], "proj.hed"))
		eulerfile = os.path.join(self.params['rundir'], "eulers.lst")
		f = open(eulerfile, "w")
		projcount = numpy.zeros((len(eulerlist)), dtype=numpy.uint16)
		angsum = numpy.zeros((len(eulerlist),3), dtype=numpy.float32)
		t0 = time.time()
		for i in range(self.params['projcount']):
			projnum = int(random.random()*len(eulerlist))
			alt = random.gauss(eulerlist[projnum][0], self.params['projstdev'])
			az = random.gauss(eulerlist[projnum][1], self.params['projstdev'])
			phi = random.random()*360.0-180.0
			f.write("%.8f\t%.8f\t%.8f\n"%(alt,az,phi))

			### stats
			projcount[projnum] += 1
			angsum[projnum,0] += alt
			angsum[projnum,1] += az
			angsum[projnum,2] += phi
		apDisplay.printMsg("Finished random in %s, %.3f ns per iteration"
			%(apDisplay.timeString(time.time()-t0), 1.0e6 * (time.time()-t0)/float(self.params['projcount'])))
		f.close()
	
		print "projection count", projcount
		for i in range(len(eulerlist)):
			angavg = angsum[i,:]/projcount[i]
			print "angle average %d: %03.3f, %03.3f, %03.3f"%(i, angavg[0], angavg[1], angavg[2])
	
		### first get rid of projection artifacts from insufficient padding
		if self.params['threedfile'] is not None:
			origfile = self.params['threedfile']
		elif self.params['modelid'] is not None:
			self.modelparams = appionData.ApInitialModelData.direct_query(self.params['modelid'])
			origfile = os.path.join(self.modelparams['path']['path'], self.modelparams['name'])
			if self.params['apix'] is None:
				self.params['apix'] = self.modelparams['pixelsize']
			if self.params['box'] is None:
				self.params['box'] = self.modelparams['boxsize']
		clipped = os.path.join(self.params['rundir'], "clipped.mrc")
		newsize = self.params['box'] * 1.5
		emancmd = "proc3d "+origfile+" "+clipped+" clip="+str(int(newsize))+","+str(int(newsize))+","+str(int(newsize))+" edgenorm"
		apEMAN.executeEmanCmd(emancmd, showcmd=True, verbose=True)

		### project resized file
		filename = os.path.join(self.params['rundir'], 'proj.hed')
		emancmd = "project3d "+clipped+" out="+filename+" list="+eulerfile
		t0 = time.time()
		apEMAN.executeEmanCmd(emancmd, showcmd=True, verbose=True)
		apDisplay.printMsg("Finished project3d in %s, %.3f ms per iteration"
			%(apDisplay.timeString(time.time()-t0), 1.0e3 * (time.time()-t0)/float(self.params['projcount'])))
		
		return filename
	

	#=====================
	def readMRCStats(self, filename):
		### read mean and stdev parameters from original image
		data = EMData()
		data.readImage(filename) 
		mean = data.Mean()
		stdev = data.Sigma()

		return mean, stdev	


	#=====================
	def addNoise(self, filename, noiselevel, SNR):
		### create new image with modified SNR
		basename, extension = os.path.splitext(filename)
		formattedsnr = "%.2f" % (SNR)
		newname = basename+"_snr"+formattedsnr+".hed"
		while os.path.isfile(newname):
			apFile.removeStack(newname)
		emancmd = "proc2d "+filename+" "+newname+" addnoise="+str(noiselevel)
		apEMAN.executeEmanCmd(emancmd)

		return newname


	#=====================
	def breakupStackIntoSingleFiles(self, stackfile, partdir="partfiles", numpart=None):
		"""
		takes the stack file and creates single mrc files ready for processing
		"""
		os.chdir(self.params['rundir'])
		apDisplay.printColor("Breaking up IMAGIC into single files, this can take a while", "cyan")
		
		starttime = time.time()
		filesperdir = self.params['filesperdir']
		if numpart is None:
			numpart = apFile.numImagesInStack(stackfile)
		apParam.createDirectory(partdir)
		
		self.params['numdir'] = self.createSubFolders(partdir, numpart, filesperdir)
		apDisplay.printMsg("Splitting "+str(numpart)+" particles into "+str(self.params['numdir'])+" folders with "
			+str(filesperdir)+" particles per folder")
		subdir = 0

		if not os.path.isfile(stackfile):
			apDisplay.printError("stackfile does not exist: "+stackfile)

		### make particle files
		self.partlistdocfile = "partlist.doc"
		f = open(self.partlistdocfile, "w")
		i = 0
		j = 0

		curdir = os.path.join(partdir,str(subdir))
		numsubstacks = math.ceil(float(numpart) / float(filesperdir))

		t0 = time.time()
		stackimages = {}
		filesperdir = int(filesperdir)

		while i < numpart:
			if (i) % filesperdir == 0:
				subdir += 1
				curdir = os.path.join(partdir,str(subdir))
				esttime = (time.time()-t0)/float(i+1)*float(numpart-i)
				apDisplay.printMsg("new directory: '"+curdir+"' at particle "+str(i)+" of "+str(numpart)
					+", "+apDisplay.timeString(esttime)+" remain")

				### use EMAN to breakup large stack into substack
				path = os.path.dirname(stackfile)
				substack = os.path.join(path, "substack"+str(j))+".hed"
				emancmd = "proc2d "+stackfile+" "+substack+" first="+str(filesperdir * j)+" last="+str(filesperdir * (j+1) - 1)
				apEMAN.executeEmanCmd(emancmd)
				stackimages = apImagicFile.readImagic(substack)
				j += 1
			elif numpart < filesperdir:
				stackimages = apImagicFile.readImagic(stackfile)

			### Scott's imagic reader and Neil's mrc writer, 38 sec for 9000 particles
			partfile = os.path.join(partdir,str(subdir),"part%06d.mrc"%(i))
			k = i - (filesperdir * (j-1))
			partimg = stackimages['images'][k]
			mrc.write(partimg, partfile)
			f.write(os.path.abspath(partfile)+" 1\n")
			i += 1
				
		f.close()

		subdir = os.path.dirname(substack)
		syscmd = "rm -f "+subdir+"/substack*"
		subprocess.Popen(syscmd, shell=True)
		apDisplay.printColor("finished breaking stack in "+apDisplay.timeString(time.time()-starttime), "cyan")

		return self.partlistdocfile


	#=====================
	def createRawMicrographs(self, stack, noiselevel):
		### create micrograph directory
		apParam.makedirs(os.path.join(self.params['rundir'], "micrographs"))
		os.chdir(os.path.join(self.params['rundir'], "micrographs"))

		basenum = int(self.params['projcount']) / self.params['projpergraph'] ### can probably give as option later as well
		remainder = int(self.params['projcount']) % self.params['projpergraph']
	
		imgcount = 0
		mcount = 1
		micrographlist = []
		for item in range(basenum):
			partstack = os.path.join(self.params['rundir'], "micrographs", "stack"+str(mcount))+".hed"
			while os.path.isfile(partstack):
				apFile.removeStack(partstack)
			time.sleep(1) ### workaround for now, encountering problems between removing and creating stack
			emancmd = "proc2d "+stack+" "+partstack+" first="+str(imgcount)+" last="+str(imgcount+self.params['projpergraph']-1)+" norm"
			apEMAN.executeEmanCmd(emancmd)
			batchfile = self.createImagicBatchFile(mcount)
			apIMAGIC.copyFile(os.path.join(self.params['rundir'], "micrographs"), "stack"+str(mcount)+".hed", headers=True)
			apIMAGIC.executeImagicBatchFile(batchfile)
			logfile = open(os.path.join(self.params['rundir'], "micrographs", "createMicrograph.log"))
			loglines = logfile.readlines()
			for line in loglines:
				if re.search("ERROR in program", line):
					apDisplay.printError("ERROR IN IMAGIC SUBROUTINE, please check the logfile: createMicrograph.log")
		
			### add noise to micrographs
			micrograph = os.path.join(self.params['rundir'], "micrographs", "micrograph"+str(mcount)+".hed")
			noisygraph = micrograph+".noise.mrc"
			while os.path.isfile(noisygraph):
				apDisplay.printWarning("removing file "+noisygraph)
				apFile.removeFile(noisygraph)
			emancmd = "proc2d "+micrograph+" "+noisygraph+" addnoise="+str(noiselevel)
			apEMAN.executeEmanCmd(emancmd)
		
			imgcount += self.params['projpergraph']
			micrographlist.append(noisygraph)
			mcount += 1
		
		if remainder != 0:
			remstack = os.path.join(self.params['rundir'], "micrographs", "stack"+str(mcount))+".hed"
			emancmd = "proc2d "+stack+" "+remstack+" first="+str(imgcount)+" last="+str(imgcount+remainder-1)+" norm"
			while os.path.isfile(remstack):
				apFile.removeStack(remstack)
			apEMAN.executeEmanCmd(emancmd)
			
			batchfile = self.createImagicBatchFile(mcount)
			apIMAGIC.copyFile(os.path.join(self.params['rundir'], "micrographs"), "stack"+str(mcount)+".hed", headers=True)
			apIMAGIC.executeImagicBatchFile(batchfile)
			logfile = open(os.path.join(self.params['rundir'], "micrographs", "createMicrograph.log"))
			loglines = logfile.readlines()
			for line in loglines:
				if re.search("ERROR in program", line):
					apDisplay.printError("ERROR IN IMAGIC SUBROUTINE, please check the logfile: createMicrograph.log")
		
			### add noise to micrograph
			micrograph = os.path.join(self.params['rundir'], "micrographs", "micrograph"+str(mcount)+".hed")
			noisygraph = micrograph+".noise.mrc"
			while os.path.isfile(noisygraph):
				apDisplay.printWarning("removing file "+noisygraph)
				apFile.removeFile(noisygraph)
			emancmd = "proc2d "+micrograph+" "+noisygraph+" addnoise="+str(noiselevel)
			apEMAN.executeEmanCmd(emancmd)
			micrographlist.append(noisygraph)
		
		self.params['numgraphs'] = mcount
		
		### now do the rest: ctf application, envelope function, noise addition
		
		self.micrographlist = []
		for image in micrographlist:
		
			### run ace2 correction, set defocus parameters early, i.e. once for every micrograph
			if self.params['randomdef'] is True:
				randomfloat = random.gauss(0,self.params['randomdef_std'])
				df1 = self.params['df1'] + randomfloat * 1e-06
				df2 = self.params['df2'] + randomfloat * 1e-06
			else:
				df1 = self.params['df1']
				df2 = self.params['df2']
				
			ace2cmd = "ace2correct.exe -img "+image+" -kv "+str(self.params['kv'])+" -cs "+\
				str(self.params['cs'])+" -apix "+str(self.params['apix'])+" -df "+str(df1)+","+\
				str(df2)+","+str(self.params['astigmatism'])+" -apply -out="+self.params['rundir']
			self.executeAce2Cmd(ace2cmd)
			ctfappliedgraph = image+".corrected.mrc"
			for num in range(self.params['projpergraph']): ### write defocus for each projection
				self.defocuslist1.append(df1)
				self.defocuslist2.append(df2)
				self.astigmatismlist.append(self.params['astigmatism'])
		
			### apply envelope
			outimage = ctfappliedgraph+".ampcorrected.mrc"
			self.applyEnvelope(ctfappliedgraph, outimage, self.params['envelope'])
			
			### read MRC stats to figure out the second noise level addition
			graphmean, graphstdev = self.readMRCStats(outimage)

			### cascading of noise processes according to Frank and Al-Ali (1975)
			graphsnr2 = 1 / ((1+1/float(self.params['snrtot'])) / (1/float(self.params['snr1']) + 1) - 1)
			graphnoiselevel2 = float(graphstdev) / float(graphsnr2)
			
			noisygraph2 = outimage+".noise.mrc"
			emancmd = "proc2d "+outimage+" "+noisygraph2+" addnoise="+str(graphnoiselevel2)
			apEMAN.executeEmanCmd(emancmd)
			
			### optional ace2correction here
			if self.params['ace2correct'] is True and self.params['ace2estimate'] is True:
				### use ACE2 to estimate the defoci that were applied to the raw micrographs
				ace2cmd = "ace2.exe -i "+noisygraph2+" -a "+str(self.params['apix'])+" -c "+\
					str(self.params['cs'] * 1000 )+" -k "+str(self.params['kv'])+" -b 2"
				self.executeAce2Cmd(ace2cmd)
				ctfparamspath = noisygraph2+".ctf.txt"
				ctffile = open(ctfparamspath, 'r')
				lines = ctffile.readlines()
				ctffile.close()
				stripped = [line.strip() for line in lines]
				defparams = stripped[1]
				deflist = defparams.split(" ")
				df1c = deflist[2]
				df2c = deflist[3]
				astigmatismc = deflist[4]
				for num in range(self.params['projpergraph']):
					self.defocuslist1c.append(df1c)
					self.defocuslist2c.append(df2c)
					self.astigmatismlistc.append(astigmatismc)
				### and now correct
				ace2cmd = "ace2correct.exe -img "+noisygraph2+" -kv "+str(self.params['kv'])+" -cs "+\
					str(self.params['cs'])+" -apix "+str(self.params['apix'])+" -df "+str(df1c)+","+\
					str(df2c)+","+str(astigmatismc)+" -wiener 0.1"
				self.executeAce2Cmd(ace2cmd)
				correctedgraph = noisygraph2+".corrected.mrc"
				self.micrographlist.append(correctedgraph)
			elif self.params['ace2correct'] is True and self.params['ace2estimate'] is False:
				for num in range(self.params['projpergraph']):
					self.defocuslist1c.append(df1)
					self.defocuslist2c.append(df2)
					self.astigmatismlistc.append(self.params['astigmatism'])
				ace2cmd = "ace2correct.exe -img "+noisygraph2+" -kv "+str(self.params['kv'])+" -cs "+\
					str(self.params['cs'])+" -apix "+str(self.params['apix'])+" -df "+str(df1)+","+\
					str(df2)+","+str(self.params['astigmatism'])+" -wiener 0.1"
				self.executeAce2Cmd(ace2cmd)
				correctedgraph = noisygraph2+".corrected.mrc"
				self.micrographlist.append(correctedgraph)
			elif self.params['ace2correct_rand'] is True and self.params['ace2correct_std'] is not None:
				randomwiggle = random.gauss(0, self.params['ace2correct_std'])
				df1w = df1 + randomwiggle * 1e-06
				df2w = df2 + randomwiggle * 1e-06
				for num in range(self.params['projpergraph']):
					self.defocuslist1c.append(df1w)
					self.defocuslist2c.append(df2w)
					self.astigmatismlistc.append(self.params['astigmatism'])
				ace2cmd = "ace2correct.exe -img "+noisygraph2+" -kv "+str(self.params['kv'])+" -cs "+\
					str(self.params['cs'])+" -apix "+str(self.params['apix'])+" -df "+str(df1w)+","+\
					str(df2w)+","+str(self.params['astigmatism'])+" -wiener 0.1"
				self.executeAce2Cmd(ace2cmd)
				correctedgraph = noisygraph2+".corrected.mrc"
				self.micrographlist.append(correctedgraph)
			else:
				self.micrographlist.append(noisygraph2)
			
	#=====================
	def createImagicBatchFile(self, mcount):
		# IMAGIC batch file creation

		batchfile = os.path.join(self.params['rundir'], "micrographs", "createMicrograph.batch")
		f = open(batchfile, 'w')
		f.write("#!/bin/csh -f\n")
		f.write("setenv IMAGIC_BATCH 1\n")
		f.write("/usr/local/IMAGIC/stand/arithm.e MODE THRESHOLD <<EOF > createMicrograph.log\n")
		f.write("stack"+str(mcount)+"\n")
		f.write("stack"+str(mcount)+"_thresh\n")
		f.write("LOWER_THRESHOLD\n")
		f.write("FIXED_DENSITY\n")
		f.write("0\n")
		f.write("USE_THRESHOLD\n")
		f.write("EOF\n")

		f.write("/usr/local/IMAGIC/stand/im_rename.e <<EOF >> createMicrograph.log\n")
		f.write("stack"+str(mcount)+"_thresh\n")
		f.write("stack"+str(mcount)+"\n")
		f.write("EOF\n")
		
		f.write("/usr/local/IMAGIC/stand/model_micrograph.e <<EOF >> createMicrograph.log\n")
		f.write("stack"+str(mcount)+"\n")
		f.write("micrograph"+str(mcount)+"\n")
		f.write("ROTATE_RANDOMLY_TOO\n")
		f.write(str(self.params['projpergraph'])+"\n")
		f.write("micrograph"+str(mcount)+"\n")
		f.write("4096,4096\n")
		f.write("128\n")
		f.write("AVOID_OVERLAP\n")
		f.write("0.01\n")
		f.write("SEQUENTIAL\n")
		f.write("EOF\n")
		
		f.close()

		return batchfile
	
	
	#=====================
	def createSubFolders(self, partdir, numpart, filesperdir):
		i = 0
		dirnum = 0
		while i < numpart:
			dirnum += 1
			apParam.createDirectory(os.path.join(partdir, str(dirnum)))
			i += filesperdir

		return dirnum


	#=====================
	def applyEnvelopeAndCTF(self, noisystack):
		### apply envelope function to each mrc file
		numpart = apFile.numImagesInStack(noisystack)
		filesperdir = self.params['filesperdir']
		i = 0			### for number of particles
		j = 0			### for number of subdirectories
		basedir = self.params['rundir']	
		t0 = time.time()
		
		self.correctedpartlist = []
		while i < numpart:
		
			### do this only when a new directory is encountered
			if (i) % filesperdir == 0:
		
				### rundir gets changed several times in order to accomodate amplitude correction script
				self.params['rundir'] = basedir
				if not os.path.exists(os.path.join(self.params['rundir'], 'partfiles', str(j+1))):
					apDisplay.printError("inconsistency with number of subdirectories in /partfiles")
				else:
					self.params['rundir'] = os.path.join(self.params['rundir'], 'partfiles', str(j+1))
				esttime = (time.time()-t0)/float(i+1)*float(numpart-i)
				apDisplay.printMsg("new directory: '"+self.params['rundir']+"' at particle "+str(i)+" of "+str(numpart)
					+", "+apDisplay.timeString(esttime)+" remain")
				os.chdir(self.params['rundir'])	### ace2 workaround
				j += 1							
						
			### apply CTF using ACE2
			noisyimage = os.path.join(self.params['rundir'], "part%06d.mrc"%(i))			

			ace2cmd = "ace2correct.exe -img "+noisyimage+" -kv "+str(self.params['kv'])+" -cs "+\
				str(self.params['cs'])+" -apix "+str(self.params['apix'])+" -df "+str(self.defocuslist1[i])+","+\
				str(self.defocuslist2[i])+","+str(self.astigmatismlist[i])+" -apply"
			self.executeAce2Cmd(ace2cmd)
			ctfapplied = noisyimage+".corrected.mrc"
				
			### apply envelope function	
			ampcorrected = ctfapplied+".ampcorrected.mrc"
			scaleFactor =  self.params['box'] / float(4096)
			self.applyEnvelope(ctfapplied, ampcorrected, self.params['envelope'], scaleFactor=scaleFactor)			
			
			if self.params['ace2correct'] is True or self.params['ace2correct_rand'] is True:		
				### now correct CTF using estimated parameters from micrograph		
				ace2cmd = "ace2correct.exe -img "+ampcorrected+" -kv "+str(self.params['kv'])+" -cs "+\
						str(self.params['cs'])+" -apix "+str(self.params['apix'])+" -df "+str(self.defocuslist1c[i])+","+\
						str(self.defocuslist2c[i])+","+str(self.astigmatismlistc[i])+" -wiener 0.1"
				self.executeAce2Cmd(ace2cmd)
				ctfcorrected = ampcorrected+".corrected.mrc"
				self.correctedpartlist.append(ctfcorrected)
			else:
				self.correctedpartlist.append(ampcorrected)
				
			i += 1

		### exit while loops, change to basedir
		self.params['rundir'] = basedir
		
		### write defocus lists to file for ctf application 
		n = 0
		defocusfile = os.path.join(self.params['rundir'], "defocuslist_application.lst")
		f = open(defocusfile, "w")
		f.write("projection \t")
		f.write("defocus1 \t")
		f.write("defocus2 \t")
		f.write("astigmatism \t\n")
		while n < self.params['projcount']:
			f.write(str(n)+"\t")
			f.write(str(self.defocuslist1[n])+"\t")
			f.write(str(self.defocuslist2[n])+"\t")
			f.write(str(self.astigmatismlist[n])+"\t\n")
			n += 1
		f.close()

		### write defocus lists to file for ctf correction
		if self.params['ace2correct'] is True or self.params['ace2correct_rand'] is True:
			n = 0
			defocusfile = os.path.join(self.params['rundir'], "defocuslist_correction.lst")
			f = open(defocusfile, "w")
			f.write("projection \t")
			f.write("defocus1 \t")
			f.write("defocus2 \t")
			f.write("astigmatism \t\n")
			while n < self.params['projcount']:
				f.write(str(n)+"\t")
				f.write(str(self.defocuslist1c[n])+"\t")
				f.write(str(self.defocuslist2c[n])+"\t")
				f.write(str(self.astigmatismlistc[n])+"\t\n")
				n += 1
			f.close()

	#=====================
	def executeAce2Cmd(self, ace2cmd, verbose=False, showcmd=True, logfile=None):
		"""
		executes an EMAN command in a controlled fashion
		"""
		waited = False
		if showcmd is True:
			sys.stderr.write(apDisplay.colorString("ACE2: ","magenta")+ace2cmd+"\n")
		t0 = time.time()
		try:
			if logfile is not None:
				logf = open(logfile, 'a')
				ace2proc = subprocess.Popen(ace2cmd, shell=True, stdout=logf, stderr=logf)
			elif verbose is False:
				ace2proc = subprocess.Popen(ace2cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			else:
				ace2proc = subprocess.Popen(ace2cmd, shell=True)
			if verbose is True:
				ace2proc.wait()
			else:
				### continuous check
				waittime = 2.0
				while ace2proc.poll() is None:
					if waittime > 10:
						waited = True
						sys.stderr.write(".")
					waittime *= 1.1
					time.sleep(waittime)
		except:
			apDisplay.printWarning("could not run ace2 command: "+ace2cmd)
			raise
		tdiff = time.time() - t0
		if tdiff > 20:
			apDisplay.printMsg("completed in "+apDisplay.timeString(tdiff))
		elif waited is True:
			print ""


	#=====================
	def uploadData(self):
			
		sessiondata = apDatabase.getSessionDataFromSessionName(self.params['sessionname'])
		if self.params['projectid'] is not None:
			projectnum = self.params['projectid']
		else:
			projectnum = apProject.getProjectIdFromSessionName(self.params['sessionname'])

		### create synthetic stack object ... not saving global params like runname, session, project, description, etc. here; that's in ApStackData
		syntheticq = appionData.ApSyntheticStackParamsData()
		### get number of fakestack runs
		numentries = len(syntheticq)
		syntheticq['modelid'] = appionData.ApInitialModelData.direct_query(self.params['modelid'])
		syntheticq['boxsize'] = self.params['box']
		syntheticq['apix'] = self.params['apix']
		syntheticq['projcount'] = self.params['projcount']
		syntheticq['projstdev'] = self.params['projstdev']
		syntheticq['shiftrad'] = self.params['shiftrad']
		syntheticq['rotang'] = self.params['rotang']
		if self.params['flip'] is True:
			syntheticq['flip'] = 1
		else:
			syntheticq['flip'] = 0
		syntheticq['kilovolts'] = self.params['kv']
		syntheticq['spher_aber'] = self.params['cs']
		syntheticq['defocus_x'] = self.params['df1']
		syntheticq['defocus_y'] = self.params['df2']
		if self.params['randomdef'] is True:
			syntheticq['randomdef'] = 1
			syntheticq['randomdef_std'] = self.params['randomdef_std']
		else:
			syntheticq['randomdef'] = 0
		syntheticq['astigmatism'] = self.params['astigmatism']
		syntheticq['snr1'] = self.params['snr1']
		syntheticq['snrtot'] = self.params['snrtot']
		syntheticq['envelope'] = self.params['envelope']
		if self.params['ace2correct'] is True:
			syntheticq['ace2correct'] = 1
		else:
			syntheticq['ace2correct'] = 0
		if self.params['ace2correct_rand'] is True:
			syntheticq['ace2correct_rand'] = 1
			syntheticq['ace2correct_std'] = self.params['ace2correct_std']
		else:
			syntheticq['ace2correct_rand'] = 0
		if self.params['ace2estimate'] is True:
			syntheticq['ace2estimate'] = 1
		else:
			syntheticq['ace2estimate'] = 0
		syntheticq['lowpass'] = self.params['lpfilt']
		syntheticq['highpass'] = self.params['hpfilt']
		if self.params['norm'] is True:
			syntheticq['norm'] = 1
		else:
			syntheticq['norm'] = 0

		### fill stack parameters
		stparamq = appionData.ApStackParamsData()
		stparamq['boxSize'] = self.params['box']
		stparamq['bin'] = 1
		stparamq['fileType'] = "imagic"
		stparamq['defocpair'] = 0
		stparamq['lowpass'] = self.params['lpfilt']
		stparamq['highpass'] = self.params['hpfilt']
		stparamq['norejects'] = 1
		stparamq['inverted'] = 0
		if self.params['ace2correct'] is True or self.params['ace2correct_rand'] is True:
			stparamq['phaseFlipped'] = 1
			stparamq['fliptype'] = "ace2part"
		else:
			stparamq['phaseFlipped'] = 0
		if self.params['norm'] is True:
			stparamq['normalized'] = 1
		else:
			stparamq['normalized'] = 0
		
		paramslist = stparamq.query()

		### create a stack object
		stackq = appionData.ApStackData()
		stackq['path'] = appionData.ApPathData(path=os.path.abspath(self.params['rundir']))
		### see if stack already exists in the database (just checking path & name)
		uniqstackdatas = stackq.query(results=1)

		### create a stackRun object
		runq = appionData.ApStackRunData()
		runq['stackRunName'] = self.params['runname']
		runq['session'] = sessiondata
		### see if stack run already exists in the database (just checking runname & session)
		uniqrundatas = runq.query(results=1)
	
		### finish stack object
		stackq['name'] = self.params['finalstack']
		stackq['description'] = self.params['description']
		stackq['hidden'] = 0
		stackq['pixelsize'] = self.params['apix'] * 1e-10
		stackq['project|projects|project'] = projectnum
		self.stackdata = stackq

		### finish stackRun object
		runq['stackParams'] = stparamq
		runq['syntheticStackParams'] = syntheticq
		self.stackrundata = runq

		### create runinstack object
		rinstackq = appionData.ApRunsInStackData()
		rinstackq['stackRun'] = runq
		rinstackq['project|projects|project'] = projectnum
		
        	### if not in the database, make sure run doesn't already exist
		if not uniqstackdatas and not uniqrundatas:
			if self.params['commit'] is True:
				apDisplay.printColor("Inserting stack parameters into database", "cyan")
				rinstackq['stack'] = stackq
#				rinstackq.insert()
			else:
				apDisplay.printColor("NOT INSERTING stack parameters into database", "cyan")
				
		elif uniqrundatas and not uniqstackdatas:
			apDisplay.printError("Weird, run data without stack already in the database")
		else:

			rinstack = rinstackq.query(results=1)

			prevrinstackq = appionData.ApRunsInStackData()
			prevrinstackq['stackRun'] = uniqrundatas[0]
			prevrinstackq['stack'] = uniqstackdatas[0]
			prevrinstackq['project|projects|project'] = projectnum
			prevrinstack = prevrinstackq.query(results=1)

			## if no runinstack found, find out which parameters are wrong:
			if not rinstack:
				for i in uniqrundatas[0]:
					print "r =======",i,"========"
					if uniqrundatas[0][i] != runq[i]:
						apDisplay.printError("the value for parameter '"+str(i)+"' is different from before")
					else:
						print i,uniqrundatas[0][i],runq[i]
				for i in uniqrundatas[0]['stackParams']:
					print "p =======",i,"========"
					if uniqrundatas[0]['stackParams'][i] != stparamq[i]:
						apDisplay.printError("the value for parameter '"+str(i)+"' is different from before")
					else:
						print i, uniqrundatas[0]['stackParams'][i], stparamq[i]
				for i in uniqstackdatas[0]:
					print "s =======",i,"========"
					if uniqstackdatas[0][i] != stackq[i]:
						apDisplay.printError("the value for parameter '"+str(i)+"' is different from before")
					else:
						print i,uniqstackdatas[0][i],stackq[i]
				for i in prevrinstack[0]:
					print "rin =======",i,"========"
					if prevrinstack[0][i] != rinstackq[i]:
						print i,prevrinstack[0][i],rinstackq[i]
						apDisplay.printError("the value for parameter '"+str(i)+"' is different from before")
					else:
						print i,prevrinstack[0][i],rinstackq[i]
				apDisplay.printError("All parameters for a particular stack must be identical! \n"+\
											 "please check your parameter settings.")
			apDisplay.printWarning("Stack already exists in database! Will try and appending new particles to stack")

		### create a fake selection run
		selectq = appionData.ApSelectionRunData()
		selectq['session'] = sessiondata
		selectq['name'] = "fakerun"
		self.selectq = selectq
		if self.params['commit'] is True:
			apDisplay.printColor("Inserting fake selection parameters into the database", "cyan") 
#			selectq.insert()
		else:
			apDisplay.printColor("NOT INSERTING fake selection parameters into the database", "cyan")



		partNumber = 0
		### loop over the particles and insert
		if self.params['commit'] is True:
			apDisplay.printColor("inserting particle parameters into database", "cyan")
		else:
			apDisplay.printColor("NOT INSERTING particle parameters into database", "cyan")
		for i in range(len(self.correctedpartlist)):
			partNumber += 1
			partfile = self.correctedpartlist[i]
			partmeandict = self.partmeantree[i]
			
			partq = appionData.ApParticleData()
			partq['selectionrun'] = selectq
			partq['xcoord'] = partNumber

			stpartq = appionData.ApStackParticlesData()

			### check unique params
			stpartq['stack'] = self.stackdata
			stpartq['stackRun'] = self.stackrundata
			stpartq['particleNumber'] = partNumber
			stpartdata = stpartq.query(results=1)
			if stpartdata:
				apDisplay.printError("trying to insert a duplicate particle")

			stpartq['particle'] = partq
			stpartq['mean'] = partmeandict['mean']
			stpartq['stdev'] = partmeandict['stdev']
			if self.params['commit'] is True:
#				stpartq.insert()

		return


	#=====================
	def start(self):	

		### first create projections
		filename = self.createProjections()

		### shift & rotate randomly
		newname = filename[:-4]+"_rand.hed"
		if self.params['flip'] is not None:
			flip = ",flip"
		else: 
			flip = ""
		while os.path.isfile(newname):
			apFile.removeStack(newname)
		emancmd = "proc2d "+filename+" "+newname+" randomize="+str(self.params['shiftrad'])+","+\
			str(self.params['rotang'])+flip+" clip="+str(self.params['box'])+","+str(self.params['box'])+" edgenorm norm"
		apEMAN.executeEmanCmd(emancmd)

		### read MRC stats to figure out noise level addition
		mean1, stdev1 = self.readMRCStats(newname)

		### calculate noiselevel additions and add noise to an initial ratio of 1.8, simulating beak and structural damage
		noiselevel1 = float(stdev1) / float(self.params['snr1'])
		noisystack = self.addNoise(newname, noiselevel1, SNR=self.params['snr1'])
		
		### these are for application
		self.defocuslist1 = []
		self.defocuslist2 = []
		self.astigmatismlist = []
		
		### these are for correction
		self.defocuslist1c = []
		self.defocuslist2c = []
		self.astigmatismlistc = []
		
		### create raw micrographs from input stack (newname)
		self.createRawMicrographs(newname, noiselevel1)

		### breakup stack for applying envelope and ctf parameters
		self.partlistdocfile = self.breakupStackIntoSingleFiles(noisystack)

		### apply envelope and ctf to each .mrc file, then correct based on how well ace2 works on raw micrographs
		self.applyEnvelopeAndCTF(noisystack)

		### convert to single stack of corrected files
		partlist = []

		for file in self.correctedpartlist:
			a = mrc.read(file)
			partlist.append(a)
		ctfappliedstack = os.path.join(self.params['rundir'], "ctfstack.hed")
		apImagicFile.writeImagic(partlist, ctfappliedstack)

		### read MRC stats to figure out noise level addition
		mean2, stdev2 = self.readMRCStats(ctfappliedstack)

		### cascading of noise processes according to Frank and Al-Ali (1975)
		snr2 = 1 / ((1+1/float(self.params['snrtot'])) / (1/float(self.params['snr1']) + 1) - 1)
		noiselevel2 = float(stdev2) / float(snr2)

		### add a last layer of noise
		noisystack2 = self.addNoise(ctfappliedstack,noiselevel2, SNR=self.params['snrtot'])

		### low-pass / high-pass filter resulting stack, if specified
		if self.params['hpfilt'] is not None or self.params['lpfilt'] is not None:
			filtstack = noisystack2[:-4]
			filtstack = filtstack+"_filt.hed"
			emancmd = "proc2d "+noisystack2+" "+filtstack+" apix="+str(self.params['apix'])+" "
			if self.params['hpfilt'] is not None:
				emancmd = emancmd+"hp="+str(self.params['hpfilt'])+" "
			if self.params['lpfilt'] is not None:
				emancmd = emancmd+"lp="+str(self.params['lpfilt'])+" "
			if self.params['norm'] is True:
				emancmd = emancmd+"norm="+str(self.params['norm'])+" "
			while os.path.isfile(filtstack):
				apFile.removeStack(filtstack)
			apEMAN.executeEmanCmd(emancmd)
			self.params['finalstack'] = os.path.basename(filtstack)
			finalstack = filtstack
		else:
			self.params['finalstack'] = os.path.basename(noisystack2)
			finalstack = noisystack2
			
		### read mean and stdev
		self.partmeantree = []
		imagicdata = apImagicFile.readImagic(os.path.join(self.params['rundir'], self.params['finalstack']))
		apDisplay.printColor("Reading mean and standard deviation values for each particle", "cyan")
		### loop over the particles and read data
		for i in range(len(self.correctedpartlist)):
			partdata = self.correctedpartlist[i]
			partarray = imagicdata['images'][i]
			# take abs of mean, because ctf whole image may become negative
			partmeandict = {
				'partdata': partdata,
				'mean': abs(partarray.mean()),
				'stdev': partarray.std(),
				'min': partarray.min(),
				'max': partarray.max(),
			}
			if partmeandict['mean'] > 1.0e7:
				partmeandict['mean'] /= 1.0e7
			if partmeandict['stdev'] > 1.0e7:
				partmeandict['stdev'] /= 1.0e7
			if abs(partmeandict['stdev']) < 1.0e-6:
				apDisplay.printError("Standard deviation == 0 for particle %d in image %s"%(i,shortname))
			self.partmeantree.append(partmeandict)
		
		### upload if commit is checked
		micrographlist = self.micrographlist
		particlelist = self.correctedpartlist
		self.uploadData()

		### post-processing: create average file for viewing on webpages
		emancmd = "proc2d "+finalstack+" "+os.path.join(self.params['rundir'], "average.mrc")+" average"
		apEMAN.executeEmanCmd(emancmd)
		### post-processing: Create Stack Mean Plot
		if self.params['commit'] is True:
			stackid = apStack.getStackIdFromPath(finalstack)
			if stackid is not None:
				apStackMeanPlot.makeStackMeanPlot(stackid)


#=====================
if __name__ == "__main__":
	syntheticdataset = createSyntheticDatasetScript(True)
	syntheticdataset.start()
	syntheticdataset.close()
	


