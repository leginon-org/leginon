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
import apFile
import apImagicFile
import apParam
import appionScript
from pyami import spider
from pyami import mrc
from EMAN import *

class createSyntheticDatasetScript(appionScript.AppionScript):

	#=====================
	def setupParserOptions(self):

		self.parser.set_usage("Usage: %prog --stack=ID [ --num-part=# ]")

		### necessary input values
		self.parser.add_option("-f", "--threedfile", dest="threedfile", type="str",
			help="name of the 3d .mrc file from which projections will be made", metavar="STR")
		self.parser.add_option("-b", "--boxsize", dest="box", type="int",
			help="boxsize that will be applied to the stack", metavar="INT")
		self.parser.add_option("--apix", dest="apix", type="float",
			help="pixelsize of the 3d model", metavar="FLOAT")

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
		self.parser.add_option("--maxfilt", dest="maxfilt", type="float", default=3.2,
			help="maximum value for low-pass filter applied to the aplitude-corrected stack", metavar="FLOAT")
		self.parser.add_option("--ampfile", dest="ampfile",
			help="amplitude correction file that will be applied to the stack", metavar="STR")
		self.parser.add_option("--kv", dest="kv", type="float", default=120,
			help="KV of the microscope, needed for envelope function", metavar="INT")
		self.parser.add_option("--cs", dest="cs", type="float", default=0.002,
			help="spherical aberration of the microscope", metavar="FLOAT")
		self.parser.add_option("--df1", dest="df1", type="float", default=-1.0e-06,
			help="defocus value 1", metavar="FLOAT")
		self.parser.add_option("--df2", dest="df2", type="float", default=-1.0e-06,
			help="defocus value 2", metavar="FLOAT")
		self.parser.add_option("--randomdef", dest="randomdef", default=True,
			action="store_true", help="randomize defocus values when applying CTF (df1 and df2 would represent upper bounds)")
		self.parser.add_option("--no-randomdef", dest="randomdef", default=True,
			action="store_false", help="DO NOT randomize defocus values when applying CTF")
		self.parser.add_option("--astigmatism", dest="astigmatism", type="float", default=0,
			help="only input if you want to apply an astigmatic ctf", metavar="FLOAT")
		self.parser.add_option("--snr1", dest="snr1", type="float", default=1.8,
			help="first level of noise, simulating beam damage & structural noise", metavar="FLOAT")
		self.parser.add_option("--snrtot", dest="snrtot", type="float", default=0.06,
			help="total signal-to-noise ratio, simulating beam damage, structural noise, & digitization", metavar="FLOAT")
		self.parser.add_option("--filesperdir", dest="filesperdir", type="int", default=4096,
			help="workaround for now ... if you want less than 4096 projections, decrease this number", metavar="INT")

		return		
	
	#=====================
	def checkConflicts(self):

		### necessary input values
		if self.params['threedfile'] is None:
			apDisplay.printError('threed .mrc file was not defined')
		if self.params['rundir'] is None:
			apDisplay.printError('working directory not specified')
		if self.params['box'] is None:
			apDisplay.printError('boxsize of the output stack not specified')
		if self.params['apix'] is None:
			apDisplay.printError('angstroms per pixel of the input model not specified')

		### make sure that the defoci are negative and in microns
		if self.params['df1'] > 0:
			apDisplay.printError('defocus value is positive!')
		if self.params['df2'] > 0:
			apDisplay.printError('defocus value is positive!')
		if self.params['df1'] < -1e-05:
			apDisplay.printError('make sure defocus is in meters, i.e. for -2 microns, df=-2e-06!')
		if self.params['df2'] < -1e-05:
			apDisplay.printError('make sure defocus is in meters, i.e. for -2 microns, df=-2e-06!')

		### workaround for now
		if self.params['filesperdir'] > self.params['projcount']:
			self.params['filesperdir'] = self.params['projcount'] / 2	
		if self.params['ampfile'] is None:
			self.params['ampfile'] = os.path.join(apParam.getAppionDirectory(), "lib/ampcor_power.spi")


		return

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
		if os.path.isfile(os.path.join(self.params['rundir'], "proj.hed")):
			apFile.removeStack("proj.hed")
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
		origfile = os.path.join(self.params['rundir'], self.params['threedfile'])
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
	def runAmpCorrect (self, start_name, end_name, params):
		tmpfile = apVolume.createAmpcorBatchFile(start_name, params)
		apVolume.runAmpcor()

		### convert back to mrc or img/hed
		if os.path.isfile(end_name):
			os.remove(end_name)
			apDisplay.printColor("removing file "+str(end_name), 'green')

		emancmd = "proc2d "+tmpfile+" "+str(end_name)
		apEMAN.executeEmanCmd(emancmd)

		return


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
		newname = basename+"_snr"+str(SNR)+".hed"
		if os.path.isfile(newname):
			apDisplay.printColor("removing file "+newname, 'green')
			apFile.removeStack(newname)
		emancmd = "proc2d "+filename+" "+newname+" addnoise="+str(noiselevel)
		apEMAN.executeEmanCmd(emancmd)

		return newname


	#=====================
	def breakupStackIntoSingleFiles(self, stackfile, partdir="partfiles", numpart=None):
		"""
		takes the stack file and creates single spider files ready for processing
		"""
		apDisplay.printColor("Breaking up spider stack into single files, this can take a while", "cyan")
		
		starttime = time.time()
		filesperdir = self.params['filesperdir']
		if numpart is None:
			numpart = apFile.numImagesInStack(stackfile)
		apParam.createDirectory(partdir)
		
		if numpart > filesperdir:
			self.params['numdir'] = self.createSubFolders(partdir, numpart, filesperdir)
			apDisplay.printMsg("Splitting "+str(numpart)+" particles into "+str(self.params['numdir'])+" folders with "
				+str(filesperdir)+" particles per folder")
			subdir = 0
		else:
			subdir = "."

		if not os.path.isfile(stackfile):
			apDisplay.printError("stackfile does not exist: "+stackfile)

		### make particle files
		partlistdocfile = "partlist.doc"
		f = open(partlistdocfile, "w")
		i = 0
		j = 0

		curdir = os.path.join(partdir,str(subdir))
		numsubstacks = math.ceil(float(numpart) / float(filesperdir))

		t0 = time.time()
		newrun = True
		stackimages = {}

		while i < numpart:
			if (i) % filesperdir == 0 or newrun is True:
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
				newrun = False
			elif numpart < filesperdir: 
	   			stackimages = apImagicFile.readImagic(stackfile)

			### Scott's imagic reader and Neil's spidersingle writer, 38 sec for 9000 particles
			partfile = os.path.join(partdir,str(subdir),"part%06d.spi"%(i))
			k = i - (filesperdir * (j-1))
			partimg = stackimages['images'][k]
			spider.write(partimg, partfile)
			f.write(os.path.abspath(partfile)+" 1\n")
			i += 1
				
		f.close()

		apDisplay.printColor("now removing all substacks", "green")	
		subdir = os.path.dirname(substack)
		syscmd = "rm -f "+subdir+"/substack*"
		os.system(syscmd)
		apDisplay.printColor("finished breaking stack in "+apDisplay.timeString(time.time()-starttime), "cyan")

		return partlistdocfile


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
	def start(self):	

		### first create projections
		filename = self.createProjections()

		### shift & rotate randomly
		newname = filename[:-4]+"_rand.hed"
		if self.params['flip'] is not None:
			flip = ",flip"
		else: 
			flip = ""
		if os.path.isfile(newname):
			apFile.removeStack(newname)
		emancmd = "proc2d "+filename+" "+newname+" randomize="+str(self.params['shiftrad'])+","+\
			str(self.params['rotang'])+flip+" clip="+str(self.params['box'])+","+str(self.params['box'])+" edgenorm norm"
		apEMAN.executeEmanCmd(emancmd)

		### read MRC stats to figure out noise level addition
		mean1, stdev1 = self.readMRCStats(newname)

		### calculate noiselevel additions and add noise to an initial ratio of 1.8, simulating beak and structural damage
		noiselevel1 = float(stdev1) / float(self.params['snr1'])
		noisystack = self.addNoise(newname, noiselevel1, SNR=self.params['snr1'])

		### breakup stack for applying envelope and ctf parameters
		partlistdocfile = self.breakupStackIntoSingleFiles(noisystack)

		### apply envelope function to each mrc file
		numpart = apFile.numImagesInStack(noisystack)
		filesperdir = self.params['filesperdir']
		i = 0
		j = 0
		newrun = True
		basedir = self.params['rundir']	
		t0 = time.time()
		defocuslist1 = []
		defocuslist2 = []

		while i < numpart:
			### do this only when a new directory is encountered with 4096 particles
			if (i) % filesperdir == 0 or newrun is True:
		
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
				newrun = False
				j += 1
						
			### run amplitude correction
			noisyimage = os.path.join(self.params['rundir'], "part%06d.spi"%(i))			
			ampcorrected = os.path.join(self.params['rundir'], "part%06d.ampcorrected.mrc"%(i))
			self.runAmpCorrect(noisyimage, ampcorrected, self.params)
			
			### apply CTF using ACE2
			if self.params['randomdef'] is True:
				randomfloat = random.random()
				df1 = self.params['df1'] * randomfloat
				df2 = self.params['df2'] * randomfloat
				defocuslist1.append(df1)
				defocuslist2.append(df2)
				ace2cmd = "ace2correct.exe -img "+ampcorrected+" -kv "+str(self.params['kv'])+" -cs "+\
					str(self.params['cs'])+" -apix "+str(self.params['apix'])+" -df "+str(df1)+","+\
					str(df2)+","+str(self.params['astigmatism'])+" -apply"
				self.executeAce2Cmd(ace2cmd)
			else:
				ace2cmd = "ace2correct.exe -img "+ampcorrected+" -kv "+str(self.params['kv'])+" -cs "+\
					str(self.params['cs'])+" -apix "+str(self.params['apix'])+" -df "+str(self.params['df1'])+","+\
					str(self.params['df2'])+","+str(self.params['astigmatism'])+" -apply"
				self.executeAce2Cmd(ace2cmd)
			i += 1

		self.params['rundir'] = basedir
		
		### if randomdef selected, write defocus lists to file
		if self.params['randomdef'] is True:
			n = 0
			defocusfile = os.path.join(self.params['rundir'], "defocuslist.lst")
			f = open(defocusfile, "w")
			f.write("projection \t")
			f.write("defocus1 \t")
			f.write("defocus2 \t")
			f.write("astigmatism \t\n")
			while n < self.params['projcount']:
				f.write(str(n)+"\t")
				f.write(str(defocuslist1[n])+"\t")
				f.write(str(defocuslist2[n])+"\t")
				f.write(str(self.params['astigmatism'])+"\t\n")
				n += 1
			f.close()

		### convert to single stack of .corrected files
		filelist = []
		partlist = []
		l = 1

		while l <= self.params['numdir']:
			curdir = os.path.join(self.params['rundir'], "partfiles", str(l))
			for file in os.listdir(curdir):
				if os.path.isfile(curdir+"/"+file) and re.search("ampcorrected.mrc.corrected.mrc", file):
					filelist.append(curdir+"/"+file)
					a = mrc.read(curdir+"/"+file)
					partlist.append(a)
			os.system("rm -rf "+curdir+"/*.spi")
			l += 1

		ctfappliedstack = os.path.join(self.params['rundir'], "ctfstack.hed")
		apImagicFile.writeImagic(partlist, ctfappliedstack)			

		### read MRC stats to figure out noise level addition
		mean2, stdev2 = self.readMRCStats(ctfappliedstack)

		### cascading of noise processes according to Frank and Al-Ali (1975)
		snr2 = 1 / ((1+1/float(self.params['snrtot'])) / (1/float(self.params['snr1']) + 1) - 1)
		noiselevel2 = float(stdev2) / float(snr2)

		### add a last layer of noise
		noisystack2 = self.addNoise(ctfappliedstack,noiselevel2, SNR=self.params['snrtot'])


#=====================
if __name__ == "__main__":
	syntheticdataset = createSyntheticDatasetScript(True)
	syntheticdataset.start()
	syntheticdataset.close()

