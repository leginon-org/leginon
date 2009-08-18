#!/usr/bin/env python

"""
Kernel Probability Density Estimator Self-Organizing Map
applid to Rotational Spectra

This Script must run three independent programs

1)Find the centre-of-symmetry in the average of the aligned images
	xmipp_find_center2d -i images.med.xmp -x0 31.5 -y0 31.5 -r1 3 -r2 25 -low 27 -high 30
2)Calculate the rotational spectra for all individual particles.
	xmipp_make_spectra -i images.sel -o images.sim -x0 31.0 -y0 30.625 -r1 3 -r2 25
3) Calculate a self-organizing map of all rotational spectra.
	xmipp_classify_kerdensom -i images.sim -o kerd -xdim 7 -ydim 7 -reg0 1000 -reg1 200 -steps 5
===========
Show how a visualization program should be done able to
Inspect the self-organizing map, and identify distinct classes.

xmipp_show -spectsom kerd -din images.sim

The output is
	(1) a set of plots (spectra)
	(2) which images has been asigned to which plots

"""
# python
import re
import os
import sys
import glob
import time
import math
import pylab
import subprocess
# appion
import appionScript
import apXmipp
import apDisplay
import appionData
import apEMAN
import apFile
import apProject
import apFourier
import apImagicFile
import apImage
from pyami import mrc,spider
#basic logging,
import logging
LOG_FILENAME = './rotKerdenSOM.log'
logging.basicConfig(filename=LOG_FILENAME,level=logging.DEBUG,)


#======================
#======================
class rotKerdenSOMScript(appionScript.AppionScript):
	#======================
	def setupParserOptions(self):
		"""
		typical command line looks like:
			kerdenSOM.py --projectid=237 --rundir=/ami/data00/appion/09jul20b/align/kerden1
				--description="wqeqw" --runname=kerden1 --alignid=1 --maskrad=64
				--xdim=5 --ydim=4 --numpart=1327 --commit
		"""

		"""
		For the new version there are two extra parameters
		spectraInnerRadius, int
		# Outer radius for rotational harmonics calculation:
		spectraOuterRadius, int

		NOTES
		There is no regularization factor...
		sugest expert options for regularization factors
		default maps bigger
		SpectraInnerRadius=14
		# Outer radius for rotational harmonics calculation:
		SpectraOuterRadius=18

		"""
		self.spectraTemporalFiles='spectra_%02d_%02d'
		self.spectraTemporalFilesMask='spectra_??_??'
		self.parser.add_option("-a", "--alignid", dest="alignstackid", type="int",
			help="Alignment stack id", metavar="#")
		#self.parser.add_option("-m", "--maskrad", dest="maskrad", type="float",
		#	help="Mask radius in Angstroms", metavar="#")n
		self.parser.add_option("-x", "--xdim", dest="xdim", type="int", default=4,
			help="X dimension", metavar="#")
		self.parser.add_option("-y", "--ydim", dest="ydim", type="int", default=3,
			help="Y dimension", metavar="#")
		self.parser.add_option("--numpart", dest="numpart", type="int",
			help="Number of particles, default all in stack", metavar="#")
		#self.convergemodes = ( "normal", "fast", "slow" )
		#self.parser.add_option("--converge", dest="converge",
		#	help="Convergence criteria mode", metavar="MODE",
		#	type="choice", choices=self.convergemodes, default="normal" )
		#Regularization factors
		self.parser.add_option("-i", "--initregulfact", dest="initregulfact", type="float",
			help="Initial Regularization Factor", metavar="#", default=1000.)
		self.parser.add_option("-f", "--finalregulfact", dest="finalregulfact", type="float",
			help="Final Regularization Factor", metavar="#", default=200.)
		self.parser.add_option("-w", "--incrementregulfact", dest="incrementregulfact", type="int",
			help="Increment Regularization Factor", metavar="#", default=5)
		#Spetra radii
		self.parser.add_option("-s", "--spectrainnerradius", dest="spectrainnerradius", type="int",
			help="Increment Regularization Factor", metavar="#")
		self.parser.add_option("-S", "--spectraouterradius", dest="spectraouterradius", type="int",
			help="Increment Regularization Factor", metavar="#")
		#Spetra harmonic
		self.parser.add_option("-l", "--spectralowharmonic", dest="spectralowharmonic", type="int",
			help="Increment Regularization Factor", metavar="#", default=1)
		self.parser.add_option("-L", "--spectrahighharmonic", dest="spectrahighharmonic", type="int",
			help="Increment Regularization Factor", metavar="#", default=15)

	#======================
	def checkConflicts(self):
		if self.params['alignstackid'] is None:
			apDisplay.printError("Please enter an aligned stack id, e.g. --alignstackid=4")
		if self.params['numpart'] is None:
			alignstackdata = appionData.ApAlignStackData.direct_query(self.params['alignstackid'])
			self.params['numpart'] = alignstackdata['num_particles']
		#####NOTE
		#if self.params['xdim'] > 16 or self.params['xdim'] > 16:
		if self.params['xdim'] > 16 or self.params['ydim'] > 16:
			apDisplay.printError("Dimensions must be less than 15")

	#======================
	def setRunDir(self):
		self.alignstackdata = appionData.ApAlignStackData.direct_query(self.params['alignstackid'])
		path = self.alignstackdata['path']['path']
		uppath = os.path.abspath(os.path.join(path, ".."))
		self.params['rundir'] = os.path.join(uppath, self.params['runname'])

	#======================
	def insertRotKerDenSOM(self):
		inserttime = time.time()
		### Preliminary data
		projectid = apProject.getProjectIdFromAlignStackId(self.params['alignstackid'])
		alignstackdata = appionData.ApAlignStackData.direct_query(self.params['alignstackid'])
		numclass = self.params['xdim']*self.params['ydim']
		pathdata = appionData.ApPathData(path=os.path.abspath(self.params['rundir']))

		### rotKerDen SOM Params object
		rotkerdenson = appionData.ApRotKerDenSOMParamsData()
		#rotkerdenson['mask_diam'] = 2.0*self.params['maskrad']
		rotkerdenson['x_dimension'] = self.params['xdim']
		rotkerdenson['y_dimension'] = self.params['ydim']
		#rotkerdenson['convergence'] = self.params['converge']
		rotkerdenson['run_seconds'] = time.time()-self.t0
		rotkerdenson['initregulfact'] = self.params['initregulfact']
		rotkerdenson['finalregulfact'] = self.params['finalregulfact']
		rotkerdenson['incrementregulfact'] = self.params['incrementregulfact']
		rotkerdenson['spectrainnerradius'] = self.params['spectrainnerradius']
		rotkerdenson['spectraouterradius'] = self.params['spectraouterradius']
		rotkerdenson['spectralowharmonic'] = self.params['spectralowharmonic']
		rotkerdenson['spectrahighharmonic'] = self.params['spectrahighharmonic']

		### Analysis Run object
		analysisq = appionData.ApAlignAnalysisRunData()
		analysisq['runname'] = self.params['runname']
		analysisq['path'] = pathdata
		analysisq['description'] = self.params['description']
		analysisq['alignstack'] = alignstackdata
		analysisq['hidden'] = False
		analysisq['project|projects|project'] = projectid

		### Clustering Run object
		clusterrunq = appionData.ApClusteringRunData()
		clusterrunq['runname'] = self.params['runname']
		clusterrunq['description'] = self.params['description']
		clusterrunq['boxsize'] = alignstackdata['boxsize']
		clusterrunq['pixelsize'] = alignstackdata['pixelsize']
		clusterrunq['num_particles'] = self.params['numpart']
		clusterrunq['alignstack'] = alignstackdata
		clusterrunq['project|projects|project'] = projectid
		clusterrunq['analysisrun'] = analysisq
		clusterrunq['rotkerdenparams'] = rotkerdenson

		### Clustering Stack object
		#Stack with cluster averages??????
		template =os.path.join(self.params['rundir'],self.spectraTemporalFilesMask + ".png")
		files = glob.glob(template)
		imglist = []
		for listname in files:
			a=apImage.readPNG(listname)
			imglist.append(a)
		apImagicFile.writeImagic(imglist,"rotkerdenstack" +self.timestamp + ".hed")
		clusterstackq = appionData.ApClusteringStackData()
		clusterstackq['avg_imagicfile'] = "rotkerdenstack"+self.timestamp+".hed"
		clusterstackq['num_classes'] = numclass
		clusterstackq['clusterrun'] = clusterrunq
		clusterstackq['path'] = pathdata
		clusterstackq['hidden'] = False
		imagicfile = os.path.join(self.params['rundir'], clusterstackq['avg_imagicfile'])
		if not os.path.isfile(imagicfile):
			apDisplay.printError("could not find average stack file: "+imagicfile)

		### looping over clusters
		apDisplay.printColor("Inserting particle classification data, please wait", "cyan")
		numclass = self.params['xdim']*self.params['ydim']
		for i in range(numclass):
			classnum = i+1
			classroot = "%s.%d"% (self.timestamp, classnum-1)
			classdocfile = os.path.join(self.params['rundir'], classroot)
			partlist = self.readClassDocFile(classdocfile)
			### Clustering Particle object
			# MRC image for each code node but plot or image
			clusterrefq = appionData.ApClusteringReferenceData()
			clusterrefq['refnum'] = classnum
			clusterrefq['avg_mrcfile'] = classroot+".mrc"
			clusterrefq['clusterrun'] = clusterrunq
			clusterrefq['path'] = pathdata
			clusterrefq['num_particles'] = len(partlist)

			### looping over particles
			#which particles belong to which code node
			sys.stderr.write(".")
			for partnum in partlist:
				alignpartdata = self.getAlignParticleData(partnum, alignstackdata)

				### Clustering Particle objects
				clusterpartq = appionData.ApClusteringParticlesData()
				clusterpartq['clusterstack'] = clusterstackq
				clusterpartq['alignparticle'] = alignpartdata
				clusterpartq['partnum'] = partnum
				clusterpartq['refnum'] = classnum
				clusterpartq['clusterreference'] = clusterrefq

				### finally we can insert parameters
				if self.params['commit'] is True:
					clusterpartq.insert()
		sys.stderr.write("\n")
		apDisplay.printMsg("Insertion complete in %s"%(apDisplay.timeString(time.time()-inserttime)))

	#=====================
	def getAlignParticleData(self, partnum, alignstackdata):
		#logging.debug('Inside getAlignParticleData')
		alignpartq = appionData.ApAlignParticlesData()
		alignpartq['alignstack'] = alignstackdata
		alignpartq['partnum'] = partnum
		alignparts = alignpartq.query(results=1)
		return alignparts[0]

	#=====================
	def readClassDocFile(self, docfile):
		if not os.path.isfile(docfile):
			return []
		partlist = []
		f = open(docfile, 'r')
		for line in f:
			sline = line.strip()
			if re.match("[0-9]+", sline):
				# numbers start at zero
				partnum = int(sline)+1
				partlist.append(partnum)
		f.close()
		if not partlist:
			return []
		partlist.sort()
		return partlist

	#=====================
	def createKerdenSOMPlots(self):
		apFile.removeFilePattern(os.path.join(self.params['rundir'],self.spectraTemporalFilesMask + ".png"))

		logging.debug('Inside createKerdenSOMPlots')
		apDisplay.printMsg("Create Plots")
		codeVectorFileName = os.path.join(self.params['rundir'], self.timestamp+'.cod')
		f1=open(codeVectorFileName,'r')
		#Read first line, I need number of harmonic plus size
		line=f1.readline()
		splitline = line.split()
		numberHarmonic = int(splitline[0])
		xx = int(splitline[2])
		yy = int(splitline[3])
		numberCodevectors = xx * yy

		xmin = int(self.params['spectralowharmonic'])
		xmax = int(self.params['spectrahighharmonic'])
		#array with x and y values
		xvalues=[]
		#fill x array with harmonic number
		for colNo in pylab.arange(xmin,xmax+1):
			xvalues.append(colNo)

		#figure size in inches
		pylab.rcParams['figure.figsize'] = 1, 1
		pylab.rc("lines", linewidth=1.5)
		pylab.rc(('xtick','ytick','axes'), labelsize=4.0)#fontsize

		#read code vector
		#compute y maximum
		ymax = 0.
		ymin = 150.
		for rowNo in range(numberCodevectors):
			line=f1.readline()
			splitLine=line.split()
			for colNo in pylab.arange(numberHarmonic):
				yval = float(splitLine[colNo])
				if ymax < yval:
					ymax = yval
				if ymin > yval:
					ymin = yval
		f1.close()
		ymax = math.ceil(ymax)+1
		print "ymax ", ymax
		ymin = max(math.floor(ymin)-1,0)
		print "ymin ", ymin

		f1=open(codeVectorFileName,'r')
		#skip first line
		line=f1.readline()
		for rowNo in range(numberCodevectors):
			line=f1.readline()
			splitLine=line.split()
			#print line
			data = []
			for colNo in pylab.arange(numberHarmonic):
				data.append(splitLine[colNo])
			print xvalues
			print data
			#clear previous plot
			pylab.clf()
			lines = pylab.plot(xvalues, data)
			pylab.ylim(ymin, ymax)
			pylab.xlim(xmin, xmax)
			pylab.xlabel('fold symmetry')
			pylab.ylabel('likelihood')
			pylab.xticks(xvalues)
			basefilename = os.path.join(self.params['rundir'], self.spectraTemporalFiles%(int(rowNo/yy),rowNo%xx))
			pylab.savefig(basefilename+".png", dpi=256, format='png')

	#======================
	def runKerdenSOM(self, indata):
		"""
		From http://xmipp.cnb.csic.es/twiki/bin/view/Xmipp/KerDenSOM

		KerDenSOM stands for "Kernel Probability Density Estimator Self-Organizing Map".
		It maps a set of high dimensional input vectors into a two-dimensional grid.
		"""
		kerdentime = time.time()
		apDisplay.printMsg("Running KerDen SOM")
		outstamp = os.path.join(self.params['rundir'], self.timestamp)
		kerdencmd = ( "xmipp_classify_kerdensom -verb 1 -i %s \
			-o %s -xdim %d -ydim %d -saveclusters \
			-reg0 %f -reg1 %f \
			-steps %d"%
			(indata,
				 outstamp, self.params['xdim'], self.params['ydim'],
				 self.params['initregulfact'], self.params['finalregulfact'],
				 self.params['incrementregulfact']
			 )
		)
		### convergence criteria
		#if self.params['converge'] == "fast":
		#	kerdencmd += " -eps 1e-5 "
		#elif self.params['converge'] == "slow":
		#	kerdencmd += " -eps 1e-9 "
		#else:
		#	kerdencmd += " -eps 1e-7 "

		logging.debug(kerdencmd)
		apDisplay.printColor(kerdencmd, "cyan")
		proc = subprocess.Popen(kerdencmd, shell=True)
		proc.wait()
		time.sleep(1)
		#09jul23l52.cod
		inputSpecrtaFile=outstamp+'.cod'
		logging.debug('code vector file name ' + inputSpecrtaFile)
		apDisplay.printMsg("KerDen SOM complete in %s"%(apDisplay.timeString(time.time()-kerdentime)))
		self.createKerdenSOMPlots()
		return

	#======================
	def runFindCenter(self, indata, xSizeVoxel):
		"""
		From http://xmipp.cnb.csic.es/twiki/bin/view/Xmipp/FindCenter

		This program looks fo the position of the center of symmetry in an image.

		"""
		centertime = time.time()
		apDisplay.printMsg("Running find_center2d")
		#ROB
		apDisplay.printMsg(' starting runFindCenter ')
		ncolumns = xSizeVoxel
		row = xSizeVoxel
		spectraouterradius = int (self.params['spectraouterradius'])
		#mrc to spider conversion writes images in non native endian format
		#xmipp_reverse endian will fix that
		findcentercmd = ( "xmipp_reverse_endian -i %s ;xmipp_find_center2d \
				-img %s -x0 %d -y0 %d -r1 %d -r2 %d -low %d -high %d "%
				(indata,indata, (ncolumns-1)/2,(row-1)/2,
				self.params['spectrainnerradius'],
				self.params['spectraouterradius'],
				spectraouterradius+2,
				spectraouterradius+5
			)
		)

		logging.debug(findcentercmd)
		apDisplay.printColor(findcentercmd, "cyan")
		#ROB pipe from shell
		proc = subprocess.Popen(findcentercmd, shell=True,stdout=subprocess.PIPE)
		proc.wait()
		stdout_value = proc.communicate()[0]
		print stdout_value
		stdout_value=stdout_value.split()
		if len(stdout_value) > 11 and ',' in stdout_value[12]:
			aux = stdout_value[12].split(',')[0]
			#new variables with outdata
			self.xOffset = float (aux)
			self.yOffset = float (stdout_value[15])
		else:
			self.xOffset = 0
			self.yOffset = 0



		apDisplay.printMsg(' runFindCenter Xoffset Yoffset ' + str(self.xOffset) + " " + str(self.yOffset))
		time.sleep(1)
		apDisplay.printMsg("Find center complete in %s"%(apDisplay.timeString(time.time()-centertime)))
		return

	#======================
	def runMakeSpectra(self, indata):
		"""
		From http://xmipp.cnb.csic.es/twiki/bin/view/Xmipp/Makespectra

		This program generates a Fourier-Bessel decomposition of each image listed in
		a *.sel. Then creates a report ASCII file for each image, with the harmonic
		energy percentage as a function of the radius, with extension .SPT.

		"""
		spectratime = time.time()
		apDisplay.printMsg("Running make_spectra")
		logging.debug('Inside make_spectra')
		#ROB
		tempFileNameforSpectra="tempFileNameforSpectra.txt"
		tmpSelFile=apXmipp.breakupStackIntoSingleFiles(indata, numpart=self.params['numpart']);
		makespectracmd = ( "xmipp_make_spectra -i %s -o %s \
			-x0 %f -y0 %f -r1 %d -r2 %d -low %d -high %d "%
			(tmpSelFile,
				tempFileNameforSpectra,
				self.xOffset,
				self.yOffset,
				self.params['spectrainnerradius'],
				self.params['spectraouterradius'],
				self.params['spectralowharmonic'],
				self.params['spectrahighharmonic'],
			)
		)

		logging.debug(makespectracmd)
		apDisplay.printColor(makespectracmd, "cyan")
		proc = subprocess.Popen(makespectracmd, shell=True,stdout=subprocess.PIPE)
		proc.wait()

		apDisplay.printMsg("Spectra calculation complete in %s"%(apDisplay.timeString(time.time()-spectratime)))
		time.sleep(1)

		return tempFileNameforSpectra

	#======================
	def fileId(self, fname):
		ext = os.path.splitext(fname)[1]
		num = int(ext[1:])
		return num

	#======================
	def sortFile(self, a, b):
		if self.fileId(a) > self.fileId(b):
			return 1
		return -1

	#======================
	def readListFile(self, listfile):
		partlist = []
		f = open(listfile, "r")
		for line in f:
			sline = line.strip()
			if re.match("[0-9]+$", sline):
				partnum = int(sline)+1
				partlist.append(partnum)
		f.close()
		return partlist

	#======================
	def createMontageInMemory(self):

		apDisplay.printMsg("Converting files")
		logging.debug('Inside createMontageInMemory')

		montagepngs = []
		files = glob.glob('spectra_??_??.png')
		for pngfile in files:
			montagepngs.append(pngfile)

		### create montage
		apFile.removeFile("montage.png")
		montagecmd = "montage -geometry +4+4 -tile %dx%d "%(self.params['xdim'],self.params['ydim'])
		for monpng in montagepngs:
			montagecmd += monpng+" "
		montagecmd += "montage.png"
		logging.debug('montagecmd ' + montagecmd)
		proc = subprocess.Popen(montagecmd, shell=True)
		proc.wait()
		time.sleep(1)

	#======================
	def start(self):
		#get aligned stack id
		aligndata = appionData.ApAlignStackData.direct_query(self.params['alignstackid'])
		xSizeVoxel = aligndata['boxsize']
		#get averaged image
		avgmrc = os.path.join(aligndata['path']['path'], aligndata["avgmrcfile"])
		avg = mrc.read(avgmrc)
		tmpSpiderFile="average.xmp"
		spider.write(avg, tmpSpiderFile)
		self.runFindCenter(tmpSpiderFile,xSizeVoxel)
		#get aligned stack
		alignStack = os.path.join(aligndata['path']['path'], aligndata["imagicfile"])
		tempFileNameforSpectra=self.runMakeSpectra(alignStack)

		#kerdensom will work with spectra output
		self.runKerdenSOM(tempFileNameforSpectra)
		self.createMontageInMemory()
		self.insertRotKerDenSOM()

		#apFile.removeFile(outdata)
		apFile.removeFilePattern("*.cod")
		apFile.removeFilePattern("*.err")
		apFile.removeFilePattern("*.his")
		apFile.removeFilePattern("*.inf")
		apFile.removeFilePattern("*.vs")
		apFile.removeFilePattern("*.xmp")
		apFile.removeFile(tempFileNameforSpectra)

#======================
#======================
if __name__ == '__main__':

	#logging.debug('Main')
	rotKerdenSOM = rotKerdenSOMScript()
	rotKerdenSOM.start()
	rotKerdenSOM.close()


