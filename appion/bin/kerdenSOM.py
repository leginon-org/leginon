#!/usr/bin/env python

"""
Kernel Probability Density Estimator Self-Organizing Map
"""
# python
import re
import os
import sys
import subprocess
import glob
import time
import shutil
# appion
import appionScript
import apXmipp
import apDisplay
import appionData
import apEMAN
import apFile
import apProject


#======================
#======================
class kerdenSOMScript(appionScript.AppionScript):
	#======================
	def setupParserOptions(self):
		self.parser.add_option("-a", "--alignid", dest="alignstackid", type="int", 
			help="Alignment stack id", metavar="#")
		self.parser.add_option("-m", "--maskrad", dest="maskrad", type="float", 
			help="Mask radius in Angstroms", metavar="#")
		self.parser.add_option("-x", "--xdim", dest="xdim", type="int", default=4, 
			help="X dimension", metavar="#")
		self.parser.add_option("-y", "--ydim", dest="ydim", type="int", default=3,
			help="Y dimension", metavar="#")
		self.parser.add_option("--numpart", dest="numpart", type="int", 
			help="Number of particles, default all in stack", metavar="#")
		self.convergemodes = ( "normal", "fast", "slow" )
		self.parser.add_option("--converge", dest="converge",
			help="Convergence criteria mode", metavar="MODE", 
			type="choice", choices=self.convergemodes, default="normal" )

	#======================
	def checkConflicts(self):
		if self.params['alignstackid'] is None:
			apDisplay.printError("Please enter an aligned stack id, e.g. --alignstackid=4")
		if self.params['numpart'] is None:
			alignstackdata = appionData.ApAlignStackData.direct_query(self.params['alignstackid'])
			self.params['numpart'] = alignstackdata['num_particles']
		if self.params['xdim'] > 16 or self.params['xdim'] > 16:
			apDisplay.printError("Dimensions must be less than 15")

	#======================
	def setRunDir(self):
		self.params['rundir'] = os.getcwd()

	#======================
	def insertKerDenSOM(self):
		### Preliminary data
		projectid = apProject.getProjectIdFromAlignStackId(self.params['alignstackid'])
		alignstackdata = appionData.ApAlignStackData.direct_query(self.params['alignstackid'])
		numclass = self.params['xdim']*self.params['ydim']
		pathdata = appionData.ApPathData(path=os.path.abspath(self.params['rundir']))

		### KerDen SOM Params object
		kerdenq = appionData.ApKerDenSOMParamsData()
		kerdenq['mask_diam'] = 2.0*self.params['maskrad']
		kerdenq['x_dimension'] = self.params['xdim']
		kerdenq['y_dimension'] = self.params['ydim']
		kerdenq['convergence'] = self.params['converge']
		kerdenq['run_seconds'] = time.time()-self.t0

		### Align Analysis Run object
		analysisq = appionData.ApAlignAnalysisRunData()
		analysisq['runname'] = self.params['runname']
		analysisq['path'] = pathdata
		analysisq['description'] = self.params['description']
		analysisq['alignstack'] = alignstackdata
		analysisq['hidden'] = False
		analysisq['project|projects|project'] = projectid
		#analysisq['kerdenparams'] = kerdenq

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
		clusterrunq['kerdenparams'] = kerdenq

		### Clustering Stack object
		clusterstackq = appionData.ApClusteringStackData()
		clusterstackq['avg_imagicfile'] = "kerdenstack"+self.timestamp+".hed"
		clusterstackq['num_classes'] = numclass
		clusterstackq['clusterrun'] = clusterrunq
		clusterstackq['path'] = pathdata
		clusterstackq['hidden'] = False
		imagicfile = os.path.join(self.params['rundir'], clusterstackq['avg_imagicfile'])
		if not os.path.isfile(imagicfile):
			apDisplay.printError("could not find average stack file: "+imagicfile)

		### looping over clusters
		apDisplay.printColor("Inserting particle classification data, please wait", "cyan")
		for i in range(numclass):
			classnum = i+1
			classroot = "%s.%d"% (self.timestamp, classnum-1)
			classdocfile = os.path.join(self.params['rundir'], classroot)
			partlist = self.readClassDocFile(classdocfile)

			### Clustering Particle object
			clusterrefq = appionData.ApClusteringReferenceData()
			clusterrefq['refnum'] = classnum
			clusterrefq['avg_mrcfile'] = classroot+".mrc"
			clusterrefq['clusterrun'] = clusterrunq
			clusterrefq['path'] = pathdata
			clusterrefq['num_particles'] = len(partlist)

			### looping over particles
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

	#=====================
	def getAlignParticleData(self, partnum, alignstackdata):
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

	#======================
	def runKerdenSOM(self, indata):
		"""
		From http://xmipp.cnb.csic.es/twiki/bin/view/Xmipp/KerDenSOM

		KerDenSOM stands for "Kernel Probability Density Estimator Self-Organizing Map".
		It maps a set of high dimensional input vectors into a two-dimensional grid.
		"""
		apDisplay.printMsg("Running KerDen SOM")
		outstamp = os.path.join(self.params['rundir'], self.timestamp)
		kerdencmd = ( "xmipp_classify_kerdensom -verb 1 -i %s -o %s -xdim %d -ydim %d -saveclusters "%
			(indata, outstamp, self.params['xdim'], self.params['ydim'])
		)
		### convergence criteria
		if self.params['converge'] == "fast":
			kerdencmd += " -eps 1e-5 "
		elif self.params['converge'] == "slow":
			kerdencmd += " -eps 1e-9 "
		else:
			kerdencmd += " -eps 1e-7 "

		apDisplay.printColor(kerdencmd, "cyan")
		proc = subprocess.Popen(kerdencmd, shell=True)
		proc.wait()
		time.sleep(1)
		return

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
	def convertfiles(self):
		apDisplay.printMsg("Converting files")

		### create crappy files
		emancmd = ( "proc2d "+self.instack+" crap.mrc first=0 last=0 mask=1" )
		apEMAN.executeEmanCmd(emancmd, showcmd=False, verbose=False)
		emancmd = ( "proc2d crap.mrc crap.png" )
		apEMAN.executeEmanCmd(emancmd, showcmd=False, verbose=False)

		files = glob.glob(self.timestamp+".[0-9]*")
		files.sort(self.sortFile)
		montagecmd = ("montage -geometry +4+4 -tile %dx%d "%(self.params['xdim'], self.params['ydim']))
		stackname = "kerdenstack"+self.timestamp+".hed"
		count = 0
		numclass = self.params['xdim']*self.params['ydim']
		for listname in files:
			#listname = self.timestamp+str(i)
			if not os.path.isfile(listname) or apFile.fileSize(listname) < 1:
				### create a ghost particle
				emancmd = ( "proc2d crap.mrc "+stackname+" " )
				sys.stderr.write("skipping "+listname+"\n")
				apEMAN.executeEmanCmd(emancmd, showcmd=False, verbose=False)
				### create png
				shutil.copy("crap.png", listname+".png")
			else:
				### average particles
				emancmd = ("proc2d %s %s list=%s average"%
					(self.instack, stackname, listname))
				apEMAN.executeEmanCmd(emancmd, showcmd=True, verbose=False)
				### create mrc
				emancmd = ("proc2d %s %s first=%d last=%d"%
					(stackname, listname+".mrc", count, count))
				apEMAN.executeEmanCmd(emancmd, showcmd=False, verbose=False)
				### create png
				emancmd = ("proc2d %s %s"%
					(listname+".mrc", listname+".png"))
				apEMAN.executeEmanCmd(emancmd, showcmd=False, verbose=False)
			montagecmd += listname+".png "
			count +=1
		montagecmd += "montage.png"
		apEMAN.executeEmanCmd(montagecmd, showcmd=True, verbose=False)
		time.sleep(1)
		apFile.removeFile("crap.mrc")
		apFile.removeFile("crap.png")
		apFile.removeFilePattern(self.timestamp+".*.png")

	#======================
	def start(self):
		aligndata = appionData.ApAlignStackData.direct_query(self.params['alignstackid'])
		boxsize = aligndata['boxsize']
		apix = aligndata['pixelsize']
		maskpixrad = self.params['maskrad']/apix
		if maskpixrad*2 > boxsize-2:
			apDisplay.printError("Mask radius is too big for boxsize: %d > %d"%(maskpixrad*2,boxsize-2))
		apDisplay.printMsg("Mask radius and boxsize: %.1f < %d"%(maskpixrad*2,boxsize-2))
		self.instack = os.path.join(aligndata['path']['path'], aligndata['imagicfile'])
		outdata = "stack.data"

		apXmipp.convertStackToXmippData(self.instack, outdata, maskpixrad, 
			boxsize, numpart=self.params['numpart'])


		self.runKerdenSOM(outdata)
		self.convertfiles()
		self.insertKerDenSOM()

		apFile.removeFile(outdata)
		apFile.removeFilePattern("*.cod")

#======================
#======================
if __name__ == '__main__':
	kerdenSOM = kerdenSOMScript()
	kerdenSOM.start()
	kerdenSOM.close()

