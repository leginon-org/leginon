#!/usr/bin/env python

import os
import sys
import math
import glob
import time
import random
import shutil
import optparse
import subprocess

from pyami import mrc
from pyami import imagic2mrc
from appionlib import apFile
from appionlib import apParam
from appionlib import apDisplay
from appionlib import basicScript
from appionlib import apImagicFile

####
# This is a low-level file with NO database connections
# Please keep it this way
####

class SetupFrealignJobs(basicScript.BasicScript):
	#============================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --options")
		
		####card 1
		self.parser.add_option("--fmag", dest="fmag", default=False,
			action="store_true", help="Refine the magnification")
		self.parser.add_option("--fdef", dest="fdef", default=False,
			action="store_true", help="Refine the defocus")
		self.parser.add_option("--fastig", dest="fastig", default=False,
			action="store_true", help="Refine the defocus astigmatism")
		self.parser.add_option("--fpart", dest="fpart", default=False,
			action="store_true", help="Refine the defocus per particle")
		self.parser.add_option("--iewald", dest="iewald", default=0,
			action="store", type='choice', choices=['0','1','2','-1','-2'], 
			help="Compensate for the Ewald sphere")
		self.parser.add_option("--fbeaut", dest="fbeaut", default=False,
			action="store_true", help="Final symmetrization of output map")
		self.parser.add_option("--ffilt", dest="ffilt", default=False,
			action="store_true", help="Apply single particle Wiener filter to reconstruction")
		self.parser.add_option("--fbfact", dest="fbfact", default=False,
			action="store_true", help="Calculate and apply B-factor to reconstruction")
		self.parser.add_option("--interp", dest="interp", default=0,
			action="store", type='choice', choices=['0','1'], help="Interpolation scheme")
		self.parser.add_option('--fcref', dest="fcref", default=False,
			action="store_true", help="apply FOM filter to final reconstruction")

		####card 2
		self.parser.add_option('--mask', dest="mask", type='float',
			help="mask from center of particle to outer edge in Angstroms")
		self.parser.add_option('--imask', dest="imask", default=0, type='float',
			help="inner mask radius in Angstroms")
		self.parser.add_option('--mw', dest="mw", default=0, type='float',
			help="Molecular weight of complex in kDa")
		self.parser.add_option('--wgh', '--ampcontrast', dest="wgh", type='float',
			help="amplitude contrast")
		self.parser.add_option('--xstd', dest="xstd", default=0.0, type='float',
			help="standard deviations above mean for masking of input model")
		self.parser.add_option('--pbc', dest="pbc", default=100.0, type='float',
			help="conversion constant for phase residual weighting of particles. 100 gives equal weighting")
		self.parser.add_option('--boff', dest="boff", default=65, type='int',
			help="average phase residual of all particles. used for weighting")
		self.parser.add_option('--dang', dest="dang", type='int', default=5, 
			help="step size if using modes 3 and 4")
		self.parser.add_option('--itmax', dest="itmax", default=10, type='int',
			help="number of iterations of randomization. used for modes 2 and 4")
		self.parser.add_option('--ipmax', dest="ipmax", default=10, type='int',
			help="number of potential matches in a search that should be tested further in local refinement")

		####card 5
		self.parser.add_option('--sym', dest="sym", 
			help="symmetry. Options are I, O, Dx (e.g. D7), Cx (e.g. C7), or H")
	
		####card 5b
		self.parser.add_option('--alpha', dest='alpha', type='float', 
			help='twist per helical subunit in degrees')
		self.parser.add_option('--rise', dest='rise', type='float', 
			help='rise per helical subunit in Angroms')
		self.parser.add_option('--nsubunits', dest='nsubunits', type='float', 
			help='The number of unique subunits per helical segment')
		self.parser.add_option('--nstarts', dest='nstarts', type='int', default=1, 
			help='helical starts')
		self.parser.add_option('--stiffness', dest='stiffness', type='float', default=20, 
			help='constrains Eulers from neighboring segments of the same filament. 1 is weak and 100 is very strong.')

		####card 6
		self.parser.add_option('--target', dest="target", default=10.0, type='float',
			help="target phase residual during refinement")
		self.parser.add_option('--thresh', dest="thresh", default=90.0, type='float',
			help="phase residual threshold cut-off")
		self.parser.add_option('--cs', dest="cs", type='float',
			help="spherical aberation")
		self.parser.add_option('--kv', dest="kv", type='float',
			help="accelerlating voltage")

		####card 7
		self.parser.add_option('--rrec', dest="rrec", type='float',  
			help="resolution to which to limit the reconstruction")
		self.parser.add_option('--hp', dest="hp", default=100.0, type='float',
			help="upper limit for low resolution signal")
		self.parser.add_option('--lp', dest="lp", default=4.0, type='float',
			help="lower limit for high resolution signal")
		self.parser.add_option('--rclass', dest="rclass", default=10.0, type='float',
			help="lower limit for high resolution to be included when classifying particles among multiple models")
		self.parser.add_option('--rbfact', dest="rbfact", default=0, type='float',
			help="rbfact to apply to particles before classification. 0.0 applies no rbfact.")

		####card 10
		self.parser.add_option('--inputparam', dest="inputparam",
			help="Input particle parameters.")
		
		#### Appion self.params
		self.parser.add_option('--ctf', dest='ctf', default=True, action='store_true',
			help="choose if frealign should perform ctf correction")
		self.parser.add_option('--noctf', dest='ctf', default=True, action='store_false',
			help="choose if frealign should NOT perform ctf correction")
		self.parser.add_option('--goldstd', dest='goldstd', default=True, action='store_true',
			help="use gold standard FSC method, divide data into two groups")
		self.parser.add_option('--nogoldstd', dest='goldstd', default=True, action='store_false',
			help="do NOT use gold standard FSC method")

		self.parser.add_option('--rundir', dest='rundir', default=os.getcwd(),
			help="directory in which to run job")
		self.parser.add_option('--apix', dest='apix', type='float',
			help="pixel size of the stack")
		self.parser.add_option('--inputstack', dest='inputstack',
			help="input MRC particle stack")	
		self.parser.add_option('--inputvol', dest='inputvol', 
			help="input MRC volume file name")
		self.parser.add_option('--totalprocs', dest='totalprocs', type='int',
			help='total processors per iteration, i.e., number of refinement jobs')
		self.parser.add_option('--wallclock', dest='wallclock', default=240, type='int',
			help='time limit for processing jobs in hours')
		self.parser.add_option('--reconproc', dest='reconproc', default=4, type='int',
			help='processors for reconstruction process on single node')
		self.parser.add_option('--reconnode', dest='reconnode', 
			help='node for reconstruction, e.g. --reconnode=pe1955-14 ')
		self.parser.add_option('--numiter', dest='numiter', default=10,
			help='number of iterations to create files for')
		self.parser.add_option('--frealignExe', dest='frealignExe', default="frealign.exe",
			help='executable file for frealign')
		self.parser.add_option('--frealignMP', dest='frealignMP', default="frealign_mp.exe",
			help='executable file for frealign with openMP')

	#============================
	def checkConflicts(self):
		if self.params['kv'] is None:
			apDisplay.printError("please enter voltage, --kv")
		if self.params['cs'] is None:
			apDisplay.printError("please enter spherical aberration, --cs")
		if self.params['apix'] is None:
			apDisplay.printError("please enter pixel size, --apix")		
		if self.params['inputvol'] is None:
			apDisplay.printError("please enter input volume, --inputvol")
		if self.params['inputstack'] is None:
			apDisplay.printError("please enter input stack, --inputstack")
		if self.params['inputparam'] is None:
			apDisplay.printError("please enter input particle parameters, --inputparam")				
		if self.params['totalprocs'] is None:
			apDisplay.printError("please enter total processes, --totalprocs")		
		if self.params['sym'] is None:
			apDisplay.printError("please enter symmetry, --sym; Options are I, O, Dx (e.g. D7), Cx (e.g. C7), or H")
		if not self.params['sym'][0] in ['I', 'O', 'D', 'C', 'H',]:
			apDisplay.printError("incorrect symmetry, --sym; Options are I, O, Dx (e.g. D7), Cx (e.g. C7), or H")
		if self.params['mask'] is None:
			apDisplay.printError("please enter mask size in Angstroms, --mask")	

		if self.params['ctf'] is False:
			 self.params['wgh'] = -1.0
		elif self.params['wgh'] is None:
			apDisplay.printError("please enter amplitude contrast, --wgh")
			
		if self.params['rrec'] is None:
			self.params['rrec'] = self.params['apix']*2.5

	#============================
	def bc(self, boolVal):
		""" Convert bool to single letter T or F """
		if boolVal is True:
			return "T"
		return "F"

	#============================
	def appendFrealignJobFile(self, 
			jobFile, inputParamFile, volFile, stackFile,
			firstPart, lastPart, prefix,
			recon=True):
	
		### hard coded parameters
		self.defaults = {
			'cform': 'M', #(I) use imagic, (M) use mrc, (S) use spider
			'fstat': False, # memory saving function, calculates many stats, such as SSNR
			'ifsc': 0, # memory saving function, usually false
			'fmatch': False, # make matching projection for each particle
			'iewald': 0.0, #  
			'fbeaut': True, # 
			'dfstd': 100,  # defocus standard deviation (in Angstroms), usually +/- 100 A, only for defocus refinement
			'beamtiltx': 0.0, #assume zero beam tilt
			'beamtilty': 0.0, #assume zero beam tilt
		}
		if recon is True:
			self.defaults['fstat'] = True
			iflag = 0
		else:
			iflag = 1

		f = open(jobFile, 'a')
		f.write('\n')
		f.write('# IFLAG %d\n'%(iflag))
		f.write('# PARTICLES %d THRU %d\n'%(firstPart, lastPart))
		f.write('# RECON %s\n'%(recon))
		if recon is True:
			f.write('rm -fv /tmp/frealign/%s\n'%(os.path.basename(volFile)))
		f.write('\n')
		f.write('### START FREALIGN ###\n')
		f.write("echo 'START FREALIGN...'\n")
		#f.write('frealign.exe << EOF\n')
		logFile = "frealign.%s.out"%(prefix)
		if recon is True:
			f.write('%s << EOF > %s\n'%(self.params['frealignExe'], logFile))
		else:
			f.write('%s << EOF > %s\n'%(self.params['frealignMP'], logFile))

		### CARD 1
		f.write('%s,%d, %s,%s,%s,%s, %d, %s,%s,%s, %d,%s,%d\n' % (
			self.defaults['cform'],
			iflag, 
			self.bc(self.params['fmag']), self.bc(self.params['fdef']), #T/F refinements
			self.bc(self.params['fastig']), self.bc(self.params['fpart']), #T/F refinements
			self.defaults['iewald'], 
			self.bc(self.defaults['fbeaut']), self.bc(self.params['fcref']), self.bc(self.defaults['fmatch']), 
			self.defaults['ifsc'],
			self.bc(self.defaults['fstat']), self.iblow))

		### CARD 2
		f.write('%d,%d,%.3f,%.3f,%.2f,%d,%d,%.2f,%d,%d\n' % (
			self.params['mask'], self.params['imask'], ### mask radii are in Angstroms
			self.params['apix'], self.params['wgh'], 
			self.params['xstd'], self.params['pbc'], 
			self.params['boff'], self.params['dang'], 
			self.params['itmax'], self.params['ipmax']))

		### CARD 3 fixing of an Euler angle or shift parameters, 1 = refine all
		f.write('%d,%d,%d,%d,%d\n' % (1,1,1,1,1))


		### CARD 4 -- particle limits
		f.write('%d, %d\n' % (firstPart, lastPart))

		### CARD 5
		if self.params['sym'].lower() == 'icos':
			f.write('I\n')
		else:
			f.write('%s\n' % (self.params['sym']))

		### CARD 6
		f.write('%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f\n' % (
			1.0, self.params['apix'], 
			self.params['target'], self.params['thresh'], 
			self.params['cs'], self.params['kv'], 
			self.defaults['beamtiltx'], self.defaults['beamtilty']))

		### CARD 7
		### lp should be ~25 A for iflag 3 and ~12 A for iflag 1
	 	f.write('%.2f,%.2f,%.2f,%.2f,%.2f\n' % (
			self.params['rrec'], self.params['hp'], 
			self.params['lp'], self.defaults['dfstd'], self.params['rbfact']))

		### CARD 8
		f.write('/tmp/frealign/%s\n'%(os.path.basename(stackFile)))
		f.write('/tmp/frealign/match.%s.mrc\n'%(prefix))
		f.write('%s\n'%(inputParamFile))
		f.write('outparams.%s.par\n'%(prefix))
		f.write('/tmp/frealign/shift.%s.par\n'%(prefix))

		if recon is False:
			# set relmag to -100, if no 3d reconstruction is desired for parallel mode
			reconrelmag = -100.0
		else:
			reconrelmag = 0.0
		f.write('%.1f,0.0,0.0,0.0,0.0,0.0,0.0,0.0\n' %reconrelmag)
		#f.write('%s\n'%(os.path.splitext(inputVolFile)[0]))
		f.write('/tmp/frealign/%s\n'%(os.path.basename(volFile)))
		f.write('/tmp/frealign/%s.weights\n'%(prefix))
		f.write('%s.odd.mrc\n'%(prefix))
		f.write('%s.even.mrc\n'%(prefix))
		f.write('/tmp/frealign/%s.phasediffs\n'%(prefix))
		f.write('/tmp/frealign/%s.pointspread\n'%(prefix))
		f.write('EOF\n\n')
		f.write('### END FREALIGN\n')
		f.write('echo "END FREALIGN"\n')
		
		f.close()
		os.chmod(jobFile, 0755)


	#===============
	def calcMemNeeded(self):
		### from frealign paper
		nn1 = self.boxsize
		nnbig = nn1 * self.iblow
		memneed = 24 * nn1**3 + 4 * nnbig**3 + 200e6

		## double it just in case
		memneed *= 2.0

		return memneed

	#===============
	def setIBLOW(self):
		"""
		IBLOW expands the volume in memory, 
		larger is faster, but needs more mem; 
		can be 1, 2 or 4
		"""
		self.iblow = 4
		if self.calcMemNeeded() > 4e9:
			self.iblow = 2
		if self.calcMemNeeded() > 4e9:
			self.iblow = 1
		### more than 40GB need then die
		if self.calcMemNeeded() > 40e9:
			apDisplay.printError("%s of memory is required which is too much, reduce box size or recons per processor"
				%(apDisplay.bytes(self.calcMemNeeded())))
		apDisplay.printMsg("IBLOW set to %d, requiring %s memory"
			%(self.iblow, apDisplay.bytes(self.calcMemNeeded())))

	#===============
	def createJobFiles(self):
		self.goldStandardResolution()
		for i in range(self.params['numiter']):
			for side in ('left', 'right'):
				apDisplay.printColor("iteration %02d, side %s"%(i+1,side), "cyan")
				stackFile = os.path.join("..", self.splitStacks[side])
				oldprefix = "%s.iter%02d"%(side, i)
				newprefix = "%s.iter%02d"%(side, i+1)
				
				self.createIterationJobRefineFiles(oldprefix, newprefix, stackFile)
				self.createReconstructionJobs(newprefix, stackFile)
			#sys.exit(1)	

	#===============
	def goldStandardResolution(self):
		jobfile = 'goldstandard.sh'
		f = open(jobfile, 'w')
		f.write("#!/bin/sh\n\n")		
		for iternum in range(1, self.params['numiter']+1):
			fscfile = 'sidetest.iter%02d.fsc'%(iternum)
			leftVol = 'threed.left.iter%02d.mrc'%(iternum)
			rightVol = 'threed.right.iter%02d.mrc'%(iternum)
			f.write('if [ -f %s ] && [ -f %s ]; then\n'%(leftVol, rightVol))
			f.write('  if [ -f %s ]; then\n'%(fscfile))
			f.write('    echo done')
			f.write('  else')
			f.write('    proc3d %s %s fsc=%s\n'
				%(leftVol, rightVol, fscfile))
			f.write('    getRes.py --fscfile=%s --boxsize=%d --apix=%.3f >> gold_resolution.txt\n'
				%(fscfile, self.boxsize, self.params['apix']))
			f.write('fi\n\n')
		f.close()
		os.chmod(jobfile, 0755)

	#===============
	def createReconstructionJobs(self, prefix, stackFile):
		"""
		combine all the parameter files & combine into 1
		then reconstruct the density
		"""
		combineparamfile = 'params.%s.par'%(prefix)
		combinevolfile = 'threed.%s.mrc'%(prefix)
		combinejobfile = '%s/recon.%s.sh'%(prefix, prefix)
		cmd = ("cat outparams.%s.*.par | egrep -v '^C' | sort -n > %s"%
			(prefix, combineparamfile))

		f = open(combinejobfile, 'w')
		f.write("#!/bin/sh\n\n")
		fullpath = os.path.join(self.params['rundir'], prefix)
		f.write('cd %s\n' % fullpath)
		f.write(cmd+"\n\n")
		f.write("wc -l %s \n"%(combineparamfile))
		f.write("/bin/rm -fv %s.mrc\n"%(prefix))
		f.write("/bin/rm -fv threed.%s.mrc\n"%(prefix))
		f.write("mkdir /tmp/frealign\n")
		f.write("rsync -vrtPhL %s /tmp/frealign/%s\n"%(stackFile, os.path.basename(stackFile)))	
		### environmental variable decide how many cpus for volume
		f.write('export NCPUS=%d\n'%(self.params['reconproc']))		
		
		time.sleep(0.05)
		f.close()

		self.appendFrealignJobFile(combinejobfile, combineparamfile, 
			combinevolfile, stackFile, 1, self.numpart, prefix,
			recon=True)

		f = open(combinejobfile, 'a')
		### calculate EMAN fsc curve
		f.write('proc3d %s.odd.mrc %s.even.mrc fsc=eotest.%s.fsc\n'%(prefix, prefix, prefix))
	
		f.write('getRes.py --fscfile=eotest.%s.fsc --boxsize=%d --apix=%.3f >> ../resolution.txt\n'
			%(prefix, self.boxsize, self.params['apix']))

		### move file down directory
		f.write('rsync -vrtPhL /tmp/frealign/threed.%s.mrc .\n'%(prefix))
		f.write('rsync -vrtPhL threed.%s.mrc ..\n'%(prefix))		
		f.write('/bin/cp -v %s ..\n'%(combineparamfile))
		time.sleep(0.05)
		f.close()

		return combinejobfile

	#===============
	def createIterationJobRefineFiles(self, oldprefix, newprefix, stackFile):
		"""
		Create multiple job files for frealign reconstruction
		using the mpiexec command
		"""

		### create individual mpi scripts
		particlePerProcess = float(self.numpart)/self.params['totalprocs'] - 1
		apDisplay.printColor("Using approx %.1f particles per process file, for a total of %d processes"
			%(particlePerProcess, self.params['totalprocs']), "purple")
		lastPart = 0
		procjobfiles = []
		
		for i in range(self.params['totalprocs']):
			procNum = i+1
			inputVolFile = "../threed.%s.mrc"%(oldprefix)
			firstPart = lastPart + 1
			lastPart = firstPart + particlePerProcess
			if lastPart > self.numpart-2:
				lastPart = self.numpart
			inputParamFile = "../params.%s.par"%(oldprefix)

			apParam.createDirectory(newprefix, warning=False)
			jobFile = "%s/refine.%s.proc%03d.sh"%(newprefix, newprefix, procNum)

			procPrefix = "%s.proc%03d"%(newprefix, procNum)

			f = open(jobFile, 'w')
			f.write("#!/bin/sh\n\n")
			fullpath = os.path.join(self.params['rundir'], newprefix)
			f.write('cd %s\n' % fullpath)
			f.write("/bin/rm -fv frealign.%s.out\n"%(procPrefix))
			f.write("/bin/rm -fv outparams.%s.par\n"%(procPrefix))
			f.write("/bin/rm -fv shift.%s.par\n"%(procPrefix))
			f.write("mkdir /tmp/frealign\n")
			f.write("rsync -vrtPhL %s /tmp/frealign/%s\n"%(inputVolFile, os.path.basename(inputVolFile)))
			f.write("rsync -vrtPhL %s /tmp/frealign/%s\n"%(stackFile, os.path.basename(stackFile)))
			f.close()
			
			#partDiff =  math.floor(lastPart) - math.floor(firstPart)
			#print "proc %d: %.1f->%.1f (%d)"%(procNum, firstPart, lastPart, partDiff)

			self.appendFrealignJobFile(jobFile, inputParamFile,
				inputVolFile, stackFile,
				math.floor(firstPart), math.floor(lastPart), procPrefix,
				recon=False)
		return

	#============================
	def checkAndCopyFiles(self):
		if not os.path.isfile(self.params['inputstack']):
			apDisplay.printError("Stack file %s does not exist"%(self.params['inputstack']))
		if not os.path.isfile(self.params['inputvol']):
			apDisplay.printError("Initial model file %s does not exist"%(self.params['inputvol']))
		if not os.path.isfile(self.params['inputparam']):
			apDisplay.printError("Initial parameter file %s does not exist"%(self.params['inputparam']))

		apParam.createDirectory(self.params['rundir'])

		firstVolFile = os.path.join(self.params['rundir'], "initial_volume.mrc")
		apDisplay.printColor("Linking initial model %s to recon folder %s"%
			(self.params['inputvol'], firstVolFile), "purple")
		if not os.path.exists(firstVolFile):
			os.symlink(self.params['inputvol'], firstVolFile)
			#shutil.copy(self.params['inputvol'], firstVolFile)

		firstParamFile = os.path.join(self.params['rundir'], "initial_params.par")		
		apDisplay.printColor("Copying initial parameters %s to recon folder %s"
			%(self.params['inputparam'], firstParamFile), "purple")
		apFile.removeFile(firstParamFile)
		time.sleep(0.1)			
		shutil.copy(self.params['inputparam'], firstParamFile)

		os.chdir(self.params['rundir'])

		for side in ('left', 'right'):
			prefix = "%s.iter%02d"%(side, 0)
			volFile = "threed.%s.mrc"%(prefix)
			if not os.path.islink(volFile):
				os.symlink(os.path.basename(firstVolFile), volFile)

		self.createSplitParamFiles(firstParamFile)

		return

	#============================
	def createSplitParamFiles(self, paramfile):
		apDisplay.printColor("Splitting parameter file for gold standard", "purple")
		origF = open(paramfile, "r")
		leftF = open("params.left.iter00.par", "w")
		rightF = open("params.right.iter00.par", "w")
		for line in origF:
			partNum = int(line[:7])
			data = line[7:].rstrip()
			if partNum % 2 == 0:
				newPartNum = partNum/2
			else:
				newPartNum = (partNum+1)/2
			newLine = "%s%s"%(apDisplay.leftPadString("%d"%(newPartNum), 7), data)
			if partNum % 2 == 0:
				rightF.write(newLine+'\n')
			else:
				leftF.write(newLine+'\n')		
		origF.close()
		rightF.close()
		leftF.close()
		return		
		
	#============================
	def createSplitStacks(self):
		self.splitStacks = {}
		self.splitStacks['left'] = "particles.left.mrc"
		self.splitStacks['right'] = "particles.right.mrc"
		if not os.path.isfile(self.splitStacks['left']):
			pass
		elif not os.path.isfile(self.splitStacks['right']):	
			pass
		elif apFile.fileSize(self.splitStacks['left']) < 100:	
			pass
		elif apFile.fileSize(self.splitStacks['right']) < 100:	
			pass
		else:
			apDisplay.printMsg("split stacks already exist, skipping this step")
			return	
							
		apDisplay.printColor("Step 1A: Splitting input stack %s into two parts"
			%(self.params['inputstack']), "purple")
		oddfile, evenfile = apImagicFile.splitStackEvenOdd(self.params['inputstack'], 
			rundir=self.params['rundir'], msg=True)

		apDisplay.printColor("Step 1B: Converting odd particles from %s into Left MRC stack %s"
			%(oddfile, self.splitStacks['left']), "purple")
		imagic2mrc.imagic_to_mrc(oddfile, self.splitStacks['left'])
		apFile.removeStack(oddfile)

		apDisplay.printColor("Step 1C: Converting even particles from %s into Right MRC stack %s"
			%(evenfile, self.splitStacks['right']), "purple")
		imagic2mrc.imagic_to_mrc(evenfile, self.splitStacks['right'])
		apFile.removeStack(evenfile)
		
		return
		
	#============================
	def checkNumberOfParticles(self):
		#determine number of particle in input stack
		header = mrc.readHeaderFromFile(self.splitStacks['right'])
		#print header['shape']
		rightnumpart = header['shape'][0]-1
		rightboxsize = max(header['shape'][1], header['shape'][2])
		apDisplay.printColor("Found %d particles in the right stack file with box size %d x %d"
			%(rightnumpart, header['shape'][1], header['shape'][2]), "green")
		#determine number of particle in input stack
		header = mrc.readHeaderFromFile(self.splitStacks['left'])
		#print header['shape']
		leftnumpart = header['shape'][0]-1
		leftboxsize = max(header['shape'][1], header['shape'][2])
		apDisplay.printColor("Found %d particles in the left stack file with box size %d x %d"
			%(leftnumpart, header['shape'][1], header['shape'][2]), "green")
			
		if leftboxsize != rightboxsize:
			apDisplay.printError("particles have different box size")
		self.boxsize = leftboxsize
			
		if leftnumpart != rightnumpart:
			apDisplay.printWarning("particles have different count")
		self.numpart = min(leftnumpart, rightnumpart)
			
		return
				
	#============================
	def start(self):
		###
		# gold standard FSC method
		# 2a. use same initial model at start
		# 2b. create separate models during refinement
		# 2c. separate models do NOT mix during refinement
		# 3a. rather than create a new stack, use single stack but divide particles into two groups
		# 3b. 500 particles, 6 processes, appox. 83 particles per proc
		# 3c. group A: 1-83,   167-250, 334-416
		# 3d. group B: 84-166, 251-333, 417-500
		###

		### make sure we have files we need
		apDisplay.printColor("Step 0: Check to make sure files exist", "purple")
		self.checkAndCopyFiles()
			
		### split stack into two parts
		apDisplay.printColor("Step 1: Process stack", "purple")
		self.createSplitStacks()
		self.checkNumberOfParticles()

		### determine reconstruction memory requirements
		self.setIBLOW()

		### create script files
		self.createJobFiles()
			
		sys.exit(1)


#============================
#============================
if __name__ == '__main__':
	setupFrealign = SetupFrealignJobs()
	setupFrealign.start()
	setupFrealign.close()