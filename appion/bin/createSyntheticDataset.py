#!/usr/bin/env python

### python imports
import os
import re
import sys
import math
import time
import numpy
import random
import subprocess

### appion imports
from appionlib import appionScript
from appionlib import apEMAN
from appionlib import apDisplay
from appionlib import apDatabase
from appionlib import apFile
from appionlib import apImage
from appionlib import apImagicFile
from appionlib import apParam
from appionlib import appiondata
from appionlib import apStack
from appionlib import apXmipp
from appionlib import apStackMeanPlot
from appionlib import apThread
from appionlib.apSpider import operations
from pyami import mrc, imagefun
from scipy import fftpack, ndimage, arange

class createSyntheticDatasetScript(appionScript.AppionScript):

	#=====================
	def onInit(self):
		### initialize variables that are expected to exist
		self.envamp = None
		self.deflist1 = []

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
		self.parser.add_option("--projcount", dest="projcount", type="int", default=10000,
			help="number of projections to be made from the input 3d .mrc file", metavar="INT")
		self.parser.add_option("--projinc", dest="projinc", type="int", default=8,
			help="angular increment of projections as in EMAN project3d, prop=[projinc]", metavar="INT")
		self.parser.add_option("--preforient", dest="preforient", default=False,
			action="store_true", help="create projections with a preferred orientation at the 3 axes")
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
			help="kV of the microscope, needed for envelope function", metavar="INT")
		self.parser.add_option("--cs", dest="cs", type="float", default=2.0,
			help="spherical aberration of the microscope (in mm)", metavar="FLOAT")
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
		self.parser.add_option("--envelope", dest="envelopefile", type="string",
			help="apply any envelope decay function from a 1d spider file ", metavar="STR")

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

		self.appiondir = apParam.getAppionDirectory()

		### necessary input values
		if self.params['threedfile'] is None and self.params['modelid'] is None:
			apDisplay.printError('either threed .mrc file or modelid was not defined')
		if self.params['threedfile'] is not None and self.params['modelid'] is not None:
			apDisplay.printError('please specify a single .mrc file (i.e. threedfile or modelid)')
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

		### make sure amplitude correction file exists
		if self.params['envelopefile'] is None:
			self.params['envelopefile'] = os.path.join(apParam.getAppionDirectory(), "appionlib/data/radial-envelope.spi")
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
	def prepareEnvelope(self, scaleFactor=1.0):
		"""
		Original envelop mrc pixel size was 0.98 Angstroms, but may be better to say 1.04 Angstroms

		Now converts a 1D array into the 2D spectra
		"""
		apDisplay.printMsg("Creating 2D envelop from 1D array")
		envelope = self.params['envelopefile']
		if envelope is None:
			return
		spi = open(envelope, 'r')
		radialdata = []
		for line in spi:
			sline = line.strip()
			if not sline or sline[0] == ";":
				continue
			spidict = operations.spiderInLine(line)
			# second float column
			radialvalue = spidict['floatlist'][1]
			radialdata.append(radialvalue)
		spi.close()

		### create envelop in 2D
		xdata = numpy.arange(0, len(radialdata), 1.0, dtype=numpy.float32)
		rdata = numpy.array(radialdata, dtype=numpy.float32)
		def funcrad(r, xdata=None, rdata=None):
			return numpy.interp(r, xdata, rdata)
		envshape = (4096, 4096)
		envcalc = imagefun.fromRadialFunction(funcrad, envshape, xdata=xdata, rdata=rdata)

		### scale envelope
		if abs(scaleFactor - 1.0) > 0.01:
			print "scaling envelope by", scaleFactor
			envcalc = ndimage.zoom(envcalc, zoom=scaleFactor, mode='nearest')
		### shift center of envelope to the edges
		envamp = self.center(envcalc)
		### mutliply real envelope function by image fft
		self.envamp = (envamp - envamp.min()) / (envamp.max() - envamp.min())
		apDisplay.printMsg("Successfully created 2D envelop from 1D array")


	#=====================
	def applyEnvelope(self, inimage, outimage, scaleFactor=1, msg=False):
		"""
		input path to image and envelope, output amplitude-adjusted image
		"""

		if msg is True:
			apDisplay.printColor("now applying envelope function to: "+inimage, "cyan")

		if self.envamp is None:
			self.prepareEnvelope(scaleFactor)

		### read image
		im = mrc.read(inimage)

		### fourier transform
		imfft = self.real_fft2d(im)

		### mutliply real envelope function by image fft
		newfft = self.envamp * imfft

		### inverse transform
		newimg = self.inverse_real_fft2d(newfft)

		### normalize between 0 and 1
		newimg = (newimg-newimg.mean()) / newimg.std()

		### save image
		mrc.write(newimg, outimage)

		### workaround for now
		time.sleep(0.1)

		return

	#=====================
	def setEulers(self):
		eulerlist = []
		eulerlist.append((0,0))
		eulerlist.append((90,0))
		eulerlist.append((90,90))

		return eulerlist

	#=====================
	def numProj(self, ang=5, sym='d7', with_mirror=False):
		csym = abs(float(sym[1:]))
		ang = abs(float(ang))
		if ang == 0.0:
			return 0
		angrad = ang*math.pi/180.0
		maxalt = math.pi/2.0 + angrad/1.99
		maxaz = 2.0*math.pi/csym
		if sym[0].lower() == 'd':
			maxaz /= 2.0
		numproj = 0
		for alt in arange(0.0, maxalt, angrad):
			if alt < 1.0e-6:
				### only one for top projection
				numproj+=1
				continue
			### calculate number of steps
			numsteps = math.floor(360.0/(ang*1.1547));
			numsteps = math.floor(numsteps * math.sin(alt) + 0.5)
			if numsteps < 1.0e-3:
				### only valid for c1, d1, c2 and d2
				numsteps = 1.0
			numsteps = csym * math.floor(numsteps/csym + 0.5) + 1.0e-6
			### calculate azimuthal step size
			azstep = 2.0*math.pi/numsteps
			if (maxaz/azstep) < 2.8:
				### if less than 2.8 steps, use 2 steps
				azstep = maxaz/2.1
			for az in arange(0.0, maxaz-azstep/4.0, azstep):
				if not with_mirror and az > math.pi-1.0e-3 and abs(alt-math.pi/2.0) < 1.0e-3:
					### ignore half of the equator
					continue
				numproj+=1

		return numproj

	#=====================
	def createProjections(self):
		timestamp = apParam.makeTimestamp()
		eulerlist = self.setEulers()
		eulerfile = os.path.join(self.params['rundir'], "eulers.lst")
		f = open(eulerfile, "w")
		projcount = numpy.zeros((len(eulerlist)), dtype=numpy.uint16)
		angsum = numpy.zeros((len(eulerlist),3), dtype=numpy.float32)
		t0 = time.time()
		for i in range(self.params['projcount']):
			projnum = int(random.random()*len(eulerlist))
			alt = random.gauss(eulerlist[projnum][0], self.params['projstdev'])
			az = random.gauss(eulerlist[projnum][1], self.params['projstdev'])
			#phi = random.random()*360.0-180.0
			#phi = random.random()*360.0
			phi = 0.0
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
			self.modelparams = appiondata.ApInitialModelData.direct_query(self.params['modelid'])
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
		filename = os.path.join(self.params['rundir'], 'proj.img')
		apFile.removeStack(filename)
		emancmd = "project3d "+clipped+" out="+filename+" list="+eulerfile
		t0 = time.time()
		apEMAN.executeEmanCmd(emancmd, showcmd=True, verbose=True)
		apDisplay.printMsg("Finished project3d in %s, %.3f ms per iteration"
			%(apDisplay.timeString(time.time()-t0), 1.0e3 * (time.time()-t0)/float(self.params['projcount'])))

		return filename

	#=====================
	def createProjectionsEmanProp(self):

		### first get rid of projection artifacts from insufficient padding
		if self.params['threedfile'] is not None:
			origfile = self.params['threedfile']
		elif self.params['modelid'] is not None:
			self.modelparams = appiondata.ApInitialModelData.direct_query(self.params['modelid'])
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
		eulerfile = os.path.join(self.params['rundir'], "eulers.lst")
		tempeulerfile = os.path.join(self.params['rundir'], "tmpeulers.lst")
		filename = os.path.join(self.params['rundir'], "proj.img")
		temp = os.path.join(self.params['rundir'], "temp.img")

		emancmd = "project3d "+clipped+" out="+temp+" sym=c1 prop="+str(self.params['projinc'])+" > "+tempeulerfile
		apEMAN.executeEmanCmd(emancmd, showcmd=True, verbose=True)

		### update projection count & write eulerlist file
		f = open(tempeulerfile, "r")
		lines = f.readlines()
		f.close()
		apFile.removeStack(temp)
		apFile.removeFile(tempeulerfile)
		strip = [line.strip() for line in lines[2:]]   ### first two lines are EMAN commands
		iters = int(math.ceil(float(self.params['projcount']) / len(strip)))
		self.params['projcount'] = iters * len(strip)
		while os.path.isfile(eulerfile):
			apFile.removeFile(eulerfile)
		f = open(eulerfile, "a")
		n = 1
		for i in range(iters):
			for j in range(len(strip)):
				split = strip[j].split()
				f.write(str(n)+"\t")
				f.write(str(split[1])+"\t")
				f.write(str(split[2])+"\t")
				f.write(str(split[3])+"\t\n")
				n += 1
		f.close()

		### create actual projections
		apFile.removeStack(filename)
		t0 = time.time()
		emancmd = "project3d "+clipped+" out="+filename+" list="+eulerfile
		apEMAN.executeEmanCmd(emancmd, showcmd=True, verbose=True)
		apDisplay.printMsg("Finished project3d in %s, %.3f ms per iteration"
			%(apDisplay.timeString(time.time()-t0), 1.0e3 * (time.time()-t0)/float(self.params['projcount'])))

#		self.params['projcount'] = int(split[-1][0]) ### last row, first value is last projection
#		self.params['projcount'] = self.numProj(ang=self.params['projinc'], sym='c1')  ### for some reasons did not work for prop=20
#		numpart = apFile.numImagesInStack(stackfile)

		return filename

	#=====================
	def shiftAndRotate(self, filename):
		### random shifts and rotations to a stack
		shiftstackname = filename[:-4]+"_rand.hed"
		apFile.removeStack(shiftstackname)
		shiftfile = os.path.join(self.params['rundir'], "shift_rotate.lst")
		if os.path.isfile(shiftfile):
			apFile.removeFile(shiftfile)
		f = open(shiftfile, "a")
		apDisplay.printMsg("Now randomly shifting and rotating particles")
		for i in range(self.params['projcount']):
			randrot = random.uniform(-1*self.params['rotang'], self.params['rotang'])
			randx = random.uniform(-1*self.params['shiftrad'], self.params['shiftrad'])
			randy = random.uniform(-1*self.params['shiftrad'], self.params['shiftrad'])
			if self.params['flip'] is not None:
				flip = random.choice([0,1])
			else:
				flip = 0
			emancmd = "proc2d "+filename+" "+shiftstackname+" first="+str(i)+" last="+str(i)+" rot="+str(randrot)+" trans="+str(randx)+","+str(randy)
			if flip == 0:
				emancmd = emancmd+" clip="+str(self.params['box'])+","+str(self.params['box'])+" edgenorm"
			else:
				emancmd = emancmd+" flip clip="+str(self.params['box'])+","+str(self.params['box'])+" edgenorm"
			apEMAN.executeEmanCmd(emancmd, showcmd=False)
			f.write("%.3f,"%(randrot))
			f.write("%.3f,"%(randx))
			f.write("%.3f,"%(randy))
			f.write(str(flip)+"\n")
		f.close()

		return shiftstackname

	#=====================
	def readFileStats(self, filename):
		if filename[-4:] == ".mrc":
			### mrc
			data = mrc.read(filename)
			mean = data.mean()
			stdev = data.std()
		elif filename[-4:] == ".hed" or filename[-4:] == ".img":
			### imagic
			last = min(256,self.params['filesperdir'])
			data = apImagicFile.readImagic(filename, last=last)['images']
			mean = data.mean()
			stdev = data.std()

		"""
		### read mean and stdev parameters from original image
		data = EMAN.EMData()
		data.readImage(filename)
		mean = data.Mean()
		stdev = data.Sigma()
		"""

		return mean, stdev

	#=====================
	def addNoise(self, oldstack, noiselevel, SNR):
		### create new image with modified SNR
		basename, extension = os.path.splitext(oldstack)
		formattedsnr = "%.2f" % (SNR)
		newstack = basename+"_snr"+formattedsnr+".hed"
		apFile.removeStack(newstack)
		emancmd = "proc2d "+oldstack+" "+newstack+" addnoise="+str(noiselevel)
		apEMAN.executeEmanCmd(emancmd)

		return newstack

	#=====================
	def getListOfDefocuses(self, numpart):
		"""
		same as createRawMicrographs with creating micrographs
		"""
		### these are for application
		self.deflist1 = []
		self.deflist2 = []

		### these are for correction
		self.deflist1c = []
		self.deflist2c = []

		### loop over particles
		for partnum in range(numpart):
			### run ace2 correction, set defocus parameters early, i.e. once for every micrograph
			if self.params['randomdef'] is True:
				randomfloat = random.gauss(0,self.params['randomdef_std'])
				df1 = self.params['df1'] + randomfloat * 1e-06
				df2 = self.params['df2'] + randomfloat * 1e-06
			else:
				df1 = self.params['df1']
				df2 = self.params['df2']
			self.deflist1.append(df1)
			self.deflist2.append(df2)

			if self.params['ace2correct_rand'] is True and self.params['ace2correct_std'] is not None:
				randomwiggle = random.gauss(0, self.params['ace2correct_std'])
				df1w = df1 + randomwiggle * 1e-06
				df2w = df2 + randomwiggle * 1e-06
				self.deflist1c.append(df1)
				self.deflist2c.append(df2)
			elif self.params['ace2correct'] is True :
				self.deflist1c.append(df1)
				self.deflist2c.append(df2)

		### write defocus lists to file for ctf application
		applydefocusfile = os.path.join(self.params['rundir'], "defocuslist_application.lst")
		correctdefocusfile = os.path.join(self.params['rundir'], "defocuslist_correction.lst")
		af = open(applydefocusfile, "w")
		cf = open(correctdefocusfile, "w")
		af.write("projection\tdefocus1\tdefocus2\tastigmatism\n")
		cf.write("projection\tdefocus1\tdefocus2\tastigmatism\n")
		n = 0
		while n < numpart:
			af.write("%d\t%.9f\t%.9f\t%.3f\n"
				%(n, self.deflist1[n], self.deflist2[n], self.params['astigmatism']))
			if self.params['ace2correct'] is True or self.params['ace2correct_rand'] is True:
				cf.write("%d\t%.9f\t%.9f\t%.3f\n"
					%(n, self.deflist1c[n], self.deflist2c[n], self.params['astigmatism']))
			n += 1
		af.close()
		cf.close()

		return

	#======================
	def getACE2Path(self):
		exename = 'ace2correct.exe'
		ace2exe = subprocess.Popen("which "+exename, shell=True, stdout=subprocess.PIPE).stdout.read().strip()
		if not os.path.isfile(ace2exe):
			ace2exe = os.path.join(apParam.getAppionDirectory(), 'bin', exename)
		if not os.path.isfile(ace2exe):
			apDisplay.printError(exename+" was not found at: "+apParam.getAppionDirectory())
		return ace2exe

	#=====================
	def applyCTFToDocFile(self, indocfile):
		apDisplay.printMsg("Applying CTF to particles")

		inf = open(indocfile, 'r')
		cmdlist = []
		partnum = 0
		for line in inf:
			### get filename
			partnum += 1
			filename = line.strip().split()[0]

			### apply CTF using ACE2
			ace2cmd = (self.ace2correct+" -img %s -kv %d -cs %.1f -apix %.3f -df %.9f,%.9f,%.3f -apply"
				%(filename, self.params['kv'], self.params['cs'], self.params['apix'],
				self.deflist1[partnum-1], self.deflist2[partnum-1], self.params['astigmatism']))
			cmdlist.append(ace2cmd)
		numpart = partnum
		inf.close()

		### thread the commands
		t0 = time.time()
		apThread.threadCommands(cmdlist)
		timeper = (time.time()-t0)/float(numpart)
		apDisplay.printColor("Total time %s"%(apDisplay.timeString(time.time()-t0)), "green")
		apDisplay.printColor("Time per particle %s"%(apDisplay.timeString(timeper)), "green")

		### check for the files, write to doc file
		inf = open(indocfile, 'r')
		outdocfile = os.path.splitext(indocfile)[0]+".apply.lst"
		outf = open(outdocfile, 'w')
		for line in inf:
			### get filename
			filename = line.strip().split()[0]
			newfile = filename+".corrected.mrc"
			if not os.path.isfile(newfile):
				apDisplay.printError("Ace 2 failed")
			outf.write(newfile+"\t1\n")
		inf.close()
		outf.close()

		return outdocfile

	#=====================
	def applyEnvelopToDocFile(self, indocfile):
		apDisplay.printMsg("Applying CTF to particles")

		inf = open(indocfile, 'r')
		outdocfile = os.path.splitext(indocfile)[0]+".envelop.lst"
		outf = open(outdocfile, 'w')
		cmdlist = []
		partnum = 0
		scaleFactor =  float(self.params['box']) / 4096.0
		t0 = time.time()
		for line in inf:
			### get filename
			partnum += 1
			filename = line.strip().split()[0]
			newfile = os.path.splitext(filename)[0]+".envelop.mrc"

			self.applyEnvelope(filename, newfile, scaleFactor=scaleFactor, msg=False)

			if not os.path.isfile(newfile):
				apDisplay.printError("Ace 2 failed")
			outf.write(newfile+"\t1\n")
		numpart = partnum
		inf.close()
		outf.close()
		timeper = (time.time()-t0)/float(numpart)
		apDisplay.printColor("Total time %s"%(apDisplay.timeString(time.time()-t0)), "green")
		apDisplay.printColor("Time per particle %s"%(apDisplay.timeString(timeper)), "green")


		return outdocfile

	#=====================
	def correctCTFToDocFile(self, indocfile):
		apDisplay.printMsg("Applying CTF to particles")

		inf = open(indocfile, 'r')
		cmdlist = []
		partnum = 0
		for line in inf:
			### get filename
			partnum += 1
			sline = line.strip()
			if not sline:
				continue
			filename = sline.split()[0]

			### correct CTF using ACE2
			ace2cmd = (self.ace2correct+" -img %s -kv %d -cs %.1f -apix %.3f -df %.9f,%.9f,%.3f -wiener 0.1"
				%(filename, self.params['kv'], self.params['cs'], self.params['apix'],
				self.deflist1c[partnum-1], self.deflist2c[partnum-1], self.params['astigmatism']))
			cmdlist.append(ace2cmd)

		numpart = partnum
		inf.close()

		### thread the commands
		t0 = time.time()
		apThread.threadCommands(cmdlist)
		timeper = (time.time()-t0)/float(numpart)
		apDisplay.printColor("Total time %s"%(apDisplay.timeString(time.time()-t0)), "green")
		apDisplay.printColor("Time per particle %s"%(apDisplay.timeString(timeper)), "green")

		### check for the files, write to doc file
		inf = open(indocfile, 'r')
		outdocfile = os.path.splitext(indocfile)[0]+".correct.lst"
		outf = open(outdocfile, 'w')
		for line in inf:
			### get filename
			filename = line.strip().split()[0]
			newfile = filename+".corrected.mrc"
			if not os.path.isfile(newfile):
				apDisplay.printError("Ace 2 failed")
			outf.write(newfile+"\t1\n")
		inf.close()
		outf.close()

		return outdocfile

	#=====================
	def applyEnvelopeAndCTF(self, stack):
		### get defocus lists
		numpart = self.params['projcount']
		cut = int(numpart/80.0)+1
		apDisplay.printMsg("%d particles per dot"%(cut))

		if len(self.deflist1) == 0:
			self.getListOfDefocuses(numpart)

		### break up particles
		partlistdocfile = apXmipp.breakupStackIntoSingleFiles(stack, filetype="mrc")

		t0 = time.time()
		apDisplay.printMsg("Applying CTF and Envelop to particles")

		### apply CTF using ACE2
		ctfapplydocfile = self.applyCTFToDocFile(partlistdocfile)

		### apply Envelop using ACE2
		envelopdocfile = self.applyEnvelopToDocFile(ctfapplydocfile)

		### correct CTF using ACE2
		if self.params['ace2correct'] is True or self.params['ace2correct_rand'] is True:
			ctfcorrectdocfile = self.correctCTFToDocFile(envelopdocfile)
		else:
			ctfcorrectdocfile = envelopdocfile

		timeper = (time.time()-t0)/float(numpart)
		apDisplay.printColor("Total time %s"%(apDisplay.timeString(time.time()-t0)), "green")
		apDisplay.printColor("Time per particle %s"%(apDisplay.timeString(timeper)), "green")

		### write corrected particle list to doc file
		ctfpartlist = []
		ctfpartlistfile = os.path.join(self.params['rundir'], "ctfpartlist.lst")
		inf = open(ctfcorrectdocfile, 'r')
		outf = open(ctfpartlistfile, "w")
		for line in inf:
			### get filename
			filename = line.strip().split()[0]
			if not os.path.isfile(filename):
				apDisplay.printError("CTF and envelop apply failed")
			ctfpartlist.append(filename)
			outf.write(filename+"\t1\n")
		inf.close()
		outf.close()

		### merge individual files into a common stack
		ctfstack = os.path.join(self.params['rundir'], "ctfstack.hed")
		apXmipp.gatherSingleFilesIntoStack(ctfpartlistfile, ctfstack, filetype="mrc")

		return ctfstack, ctfpartlist

	#=====================
	def executeAce2Cmd(self, ace2cmd, verbose=False, showcmd=True, logfile=None):
		"""
		executes an EMAN command in a controlled fashion
		"""
		waited = False
		if showcmd is True:
			os.sys.stderr.write(apDisplay.colorString("ACE2: ","magenta")+ace2cmd+"\n")
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
						os.sys.stderr.write(".")
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
	def uploadData(self, ctfpartlist):

		### read mean /stdev for uploading
		self.getPartMeanTree(os.path.join(self.params['rundir'], self.params['finalstack']), ctfpartlist)

		sessiondata = apDatabase.getSessionDataFromSessionName(self.params['sessionname'])
		if self.params['projectid'] is not None:
			projectnum = self.params['projectid']
		else:
			projectnum = apProject.getProjectIdFromSessionName(self.params['sessionname'])

		### create synthetic stack object ... not saving global params like runname, session, project, description, etc. here; that's in ApStackData
		syntheticq = appiondata.ApSyntheticStackParamsData()
		### get number of fakestack runs
		numentries = len(syntheticq)
		syntheticq['modelid'] = appiondata.ApInitialModelData.direct_query(self.params['modelid'])
		syntheticq['boxsize'] = self.params['box']
		syntheticq['apix'] = self.params['apix']
		syntheticq['projcount'] = self.params['projcount']
		syntheticq['projstdev'] = self.params['projstdev']
		syntheticq['shiftrad'] = self.params['shiftrad']
		syntheticq['rotang'] = self.params['rotang']
		syntheticq['flip'] = self.params['flip']
		syntheticq['kilovolts'] = self.params['kv']
		syntheticq['spher_aber'] = self.params['cs']
		syntheticq['defocus_x'] = self.params['df1']
		syntheticq['defocus_y'] = self.params['df2']
		syntheticq['randomdef'] = self.params['randomdef']
		if self.params['randomdef'] is True:
			syntheticq['randomdef_std'] = self.params['randomdef_std']
		syntheticq['astigmatism'] = self.params['astigmatism']
		syntheticq['snr1'] = self.params['snr1']
		syntheticq['snrtot'] = self.params['snrtot']
		syntheticq['envelope'] = os.path.basename(self.params['envelopefile'])
		syntheticq['ace2correct'] = self.params['ace2correct']
		syntheticq['ace2correct_rand'] = self.params['ace2correct_rand']
		if self.params['ace2correct_rand'] is True:
			syntheticq['ace2correct_std'] = self.params['ace2correct_std']
		syntheticq['ace2estimate'] = self.params['ace2estimate']
		syntheticq['lowpass'] = self.params['lpfilt']
		syntheticq['highpass'] = self.params['hpfilt']
		syntheticq['norm'] = self.params['norm']

		### fill stack parameters
		stparamq = appiondata.ApStackParamsData()
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
		stparamq['normalized'] = self.params['norm']

		paramslist = stparamq.query()

		### create a stack object
		stackq = appiondata.ApStackData()
		stackq['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
		### see if stack already exists in the database (just checking path & name)
		uniqstackdatas = stackq.query(results=1)

		### create a stackRun object
		runq = appiondata.ApStackRunData()
		runq['stackRunName'] = self.params['runname']
		runq['session'] = sessiondata
		### see if stack run already exists in the database (just checking runname & session)
		uniqrundatas = runq.query(results=1)

		### finish stack object
		stackq['name'] = self.params['finalstack']
		stackq['description'] = self.params['description']
		stackq['hidden'] = 0
		stackq['pixelsize'] = self.params['apix'] * 1e-10
		stackq['boxsize'] = self.params['box']
		self.stackdata = stackq

		### finish stackRun object
		runq['stackParams'] = stparamq
		runq['syntheticStackParams'] = syntheticq
		self.stackrundata = runq

		### create runinstack object
		rinstackq = appiondata.ApRunsInStackData()
		rinstackq['stackRun'] = runq

        	### if not in the database, make sure run doesn't already exist
		if not uniqstackdatas and not uniqrundatas:
			if self.params['commit'] is True:
				apDisplay.printColor("Inserting stack parameters into database", "cyan")
				rinstackq['stack'] = stackq
				rinstackq.insert()
			else:
				apDisplay.printWarning("NOT INSERTING stack parameters into database")

		elif uniqrundatas and not uniqstackdatas:
			apDisplay.printError("Weird, run data without stack already in the database")
		else:

			rinstack = rinstackq.query(results=1)

			prevrinstackq = appiondata.ApRunsInStackData()
			prevrinstackq['stackRun'] = uniqrundatas[0]
			prevrinstackq['stack'] = uniqstackdatas[0]
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
#		selectq = appiondata.ApSelectionRunData()
#		selectq['session'] = sessiondata
#		selectq['name'] = "fakerun"
#		self.selectq = selectq
		if self.params['commit'] is True:
			apDisplay.printColor("Inserting fake selection parameters into the database", "cyan")
#			selectq.insert()
		else:
			apDisplay.printWarning("NOT INSERTING fake selection parameters into the database")

		partNumber = 0
		### loop over the particles and insert
		if self.params['commit'] is True:
			apDisplay.printColor("inserting particle parameters into database", "cyan")
		else:
			apDisplay.printWarning("NOT INSERTING particle parameters into database")
		for i in range(len(ctfpartlist)):
			partNumber += 1
			partfile = ctfpartlist[i]
			partmeandict = self.partmeantree[i]

			partq = appiondata.ApParticleData()
#			partq['selectionrun'] = selectq
			partq['xcoord'] = partNumber

			stpartq = appiondata.ApStackParticleData()

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
				stpartq.insert()

		return

	#=====================
	def recoverLists(self):
		if len(self.deflist1) > 0:
			recoveryfile = os.path.join(self.params['rundir'], "defocuslist_application.lst")
			f = open(recoveryfile, "r")
			lines = f.readlines()
			lines = lines[1:]   ### first line has names
			f.close()
			split = [line.split() for line in lines]
			if self.deflist1 is None:
				for params in split:
					self.deflist1.append(params[1])
			if self.deflist2 is None:
				for params in split:
					self.deflist2.append(params[2])
			if self.astigist is None:
				for params in split:
					self.astigist.append(params[3])
		if len(self.deflist1c) > 0 and self.params['ace2correct'] is True:
			recoveryfile = os.path.join(self.params['rundir'], "defocuslist_correction.lst")
			f = open(recoveryfile, "r")
			lines = f.readlines()
			lines = lines[1:]   ### first line has names
			f.close()
			split = [line.split() for line in lines]
			if self.deflist1c is None:
				for params in split:
					self.deflist1c.append(params[1])
			if self.deflist2c is None:
				for params in split:
					self.deflist2c.append(params[2])
			if self.astigistc is None:
				for params in split:
					self.astigistc.append(params[3])

	#=====================
	def getPartMeanTree(self, stackfile, ctfpartlist):
		### read mean and stdev
		self.partmeantree = []
		imgnum = 0
		while imgnum < self.params['projcount']:
			apDisplay.printColor("Reading mean and standard deviation values for each particle", "cyan")
			### loop over the particles and read data
			first = imgnum
			last = first + self.params['filesperdir']
			if last >= self.params['projcount']:
				last = self.params['projcount']
			imagicdata = apImagicFile.readImagic(stackfile, first=first+1, last=last)
			for i in range(last - first):
				partdata = ctfpartlist[imgnum]
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
				imgnum += 1

	#=====================
	def start(self):
		self.ace2correct = self.getACE2Path()

		### determine amount of memory needed for entire stack
		memorylimit = 0.3
		bytelimit = memorylimit*(1024**3)
		writeiters = 1
		partbytes = 4*self.params['box']*self.params['box']
		if partbytes*self.params['projcount'] > bytelimit:
			writeiters = int(math.ceil(float(partbytes)*self.params['projcount'] / bytelimit))
		partsperiter = int(float(self.params['projcount']) / writeiters) ### number of particles read each time

		### some defaults, and workarounds for now
		self.params['projpergraph'] = 100
		self.params['filesperdir'] = partsperiter
		if self.params['filesperdir'] > 2048:
			self.params['filesperdir'] = 2048

		### first create projections
		if self.params['preforient'] is True:
			filename = self.createProjections()
		else:
			filename = self.createProjectionsEmanProp()

		### shift & rotate randomly
		shiftstackname = self.shiftAndRotate(filename)

		### read MRC stats to figure out noise level addition
		mean1, stdev1 = self.readFileStats(shiftstackname)

		### calculate noiselevel additions and add noise to an initial ratio of 1.8, simulating beam and structural damage
		noiselevel1 = float(stdev1) / float(self.params['snr1'])
		noisystack = self.addNoise(shiftstackname, noiselevel1, SNR=self.params['snr1'])

		### get list of defocus values
		self.getListOfDefocuses(self.params['projcount'])

		### apply envelope and ctf to each .mrc file, then correct based on how well ace2 works on raw micrographs
		ctfstack, ctfpartlist = self.applyEnvelopeAndCTF(noisystack)

		#recoverlists = self.recoverLists()

		### read IMAGIC stats to figure out noise level addition
		mean2, stdev2 = self.readFileStats(ctfstack)

		### cascading of noise processes according to Frank and Al-Ali (1975)
		snr2 = 1 / ((1+1/float(self.params['snrtot'])) / (1/float(self.params['snr1']) + 1) - 1)
		noiselevel2 = float(stdev2) / float(snr2)

		### add a last layer of noise
		noisystack2 = self.addNoise(ctfstack, noiselevel2, SNR=self.params['snrtot'])

		### low-pass / high-pass filter resulting stack, if specified
		if self.params['hpfilt'] is not None or self.params['lpfilt'] is not None or self.params['norm'] is True:
			filtstack = noisystack2[:-4]
			filtstack = filtstack+"_filt.hed"
			apFile.removeStack(filtstack)
			emancmd = "proc2d "+noisystack2+" "+filtstack+" apix="+str(self.params['apix'])+" "
			if self.params['hpfilt'] is not None:
				emancmd = emancmd+"hp="+str(self.params['hpfilt'])+" "
			if self.params['lpfilt'] is not None:
				emancmd = emancmd+"lp="+str(self.params['lpfilt'])+" "
			if self.params['norm'] is True:
				emancmd = emancmd+"norm="+str(self.params['norm'])+" "
			apEMAN.executeEmanCmd(emancmd)
			self.params['finalstack'] = os.path.basename(filtstack)
			finalstack = filtstack
		else:
			self.params['finalstack'] = os.path.basename(noisystack2)
			finalstack = noisystack2

		### post-processing: create average file for viewing on webpages
		apStack.averageStack(finalstack)

		### upload if commit is checked
		self.uploadData(ctfpartlist)

		### post-processing: Create Stack Mean Plot
		if self.params['commit'] is True:
			stackid = apStack.getStackIdFromPath(finalstack)
			if stackid is not None:
				apStackMeanPlot.makeStackMeanPlot(stackid, gridpoints=8)

#=====================
if __name__ == "__main__":
	syntheticdataset = createSyntheticDatasetScript(True)
	syntheticdataset.start()
	syntheticdataset.close()


