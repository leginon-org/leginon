#!/usr/bin/env python
import os
import sys
import math
import time
import shutil
import subprocess
#appion
from appionlib import apParam
from appionlib import apStack
from appionlib import apModel
from appionlib import apCtf
from appionlib import apImagicFile
from appionlib import appionScript
from appionlib import apProject
from appionlib import apDisplay
from appionlib import apFrealign
from appionlib import apSymmetry
from appionlib import apEMAN
from appionlib import apFile
from appionlib import apThread
from appionlib import apImagicFile
from appionlib import apStackFormat
from appionlib import appiondata
from appionlib import apInstrument
from appionlib import apPrepRefine
#other myami
from pyami import mrc

#================
#================
class frealignJob(apPrepRefine.Prep3DRefinement):
	#================
	def setupParserOptions(self):
		super(frealignJob,self).setupParserOptions()

		self.ctfestopts = ('ace2', 'ctffind')

		self.parser.set_usage("Usage: %prog -options")

		#self.parser.add_option("--commit", dest="commit", default=True,
		#	action="store_true", help="Commit processing run to database")

		####card 1
		self.parser.add_option("--fmag", dest="fmag", default=False,
			action="store_true", help="Refine the magnification")
		self.parser.add_option("--fdef", dest="fdef", default=False,
			action="store_true", help="Refine the defocus")
		self.parser.add_option("--fastig", dest="fastig", default=False,
			action="store_true", help="Refine the defocus astigmatism")
		self.parser.add_option("--fpart", dest="fpart", default=False,
			action="store_true", help="Refine the defocus per particle")
		self.parser.add_option('--fcref', dest="fcref", default=False,
			action="store_true", help="apply FOM filter to final reconstruction")
	
		####card 2
		self.parser.add_option('--wgh', dest="wgh", default=0.07, type='float',
			help="amplitude contrast")
		self.parser.add_option('--xstd', dest="xstd", default=0.0, type='float',
			help="standard deviations above mean for masking of input model")
		self.parser.add_option('--pbc', dest="pbc", default=100.0, type='float',
			help="conversion constant for phase residual weighting of particles. 100 gives equal weighting")
		self.parser.add_option('--boff', dest="boff", default=75, type='int',
			help="average phase residual of all particles. used for weighting")
		self.parser.add_option('--dang', dest="dang", type='int', default=5, 
			help="step size if using modes 3 and 4")
		self.parser.add_option('--itmax', dest="itmax", default=10, type='int',
			help="number of iterations of randomization. used for modes 2 and 4")
		self.parser.add_option('--ipmax', dest="ipmax", default=0, type='int',
			help="number of potential matches in a search that should be tested further in local refinement")
		
		####card 4
		''' last particle defined in the base class'''
	
		####card 5
		''' symmetry defined in the base class'''

		####card 6
		self.parser.add_option('--target', dest="target", default=10.0, type='float',
			help="target phase residual during refinement")
		self.parser.add_option('--thresh', dest="thresh", default=90.0, type='float',
			help="phase residual threshold cut-off")
		self.parser.add_option('--kv', dest="kv", default=120.0, type='float',
			help="accelerlating voltage")
	
		####card 7
		self.parser.add_option('--rrec', dest="rrec", default=10.0, type='float',  
			help="resolution to which to limit the reconstruction")
		self.parser.add_option('--hp', dest="hp", default=100.0, type='float',
			help="upper limit for low resolution signal")
		self.parser.add_option('--lp', dest="lp", default=10.0, type='float',
			help="lower limit for high resolution signal")
		self.parser.add_option('--rbfact', dest="rbfact", default=0, type='float',
			help="rbfact to apply to particles before classification. 0.0 applies no rbfact.")

		#### Appion params
		self.parser.add_option('--reconstackid', dest='reconstackid', type='int',
			help="recon stack id from database")
		self.parser.add_option('--reconiterid', dest='reconiterid', type='int',
			help="id for specific iteration from a refinement, used for retrieving particle orientations")
		self.parser.add_option("--cluster", dest="cluster", default=True,
			action="store_true", help="Make script for running on a cluster")
		self.parser.add_option("--no-cluster", dest="cluster", default=True,
			action="store_false", help="Run script interactively on current machine")

		self.parser.add_option('--noctf', dest='noctf', default=False, action='store_true',
			help="choose if frealign should not perform ctf correction")
		self.parser.add_option('--ctfmethod', dest='ctfmethod',
			help="Only use ctf values coming from this method of estimation", metavar="TYPE",
			type="choice", choices=self.ctfestopts)

	#=====================
	def checkPackageConflicts(self):
		if self.params['reconstackid'] is not None:	
			reconboxsize = apStack.getStackBoxsize(self.params['reconstackid'], msg=False)
			reconapix = apStack.getStackPixelSizeFromStackId(self.params['reconstackid'])
			refinenumpart = apStack.getNumberStackParticlesFromId(self.params['stackid'])
			reconnumpart = apStack.getNumberStackParticlesFromId(self.params['reconstackid'])
			if reconboxsize != self.boxsize:
				apDisplay.printError("Boxsize do not match for stacks")
			if reconapix != self.apix:
				apDisplay.printError("Pixelsize do not match for stacks")
			if refinenumpart != reconnumpart:
				apDisplay.printError("Number of particles do not match for stacks")
		if self.params['noctf'] is True:
			apDisplay.printWarning("Using no CTF method")
			self.params['wgh'] = -1.0

		"""
		Fake multiple job here for prep
		"""
		self.params['nproc']=1
		self.params['rpn']=1
		self.params['ppn']=1

	def setIterationParamList(self):
		self.iterparams = ['mask','imask', 'fmag','fdef','fastig','fpart','fcref','wgh', 'xstd', 'pbc', 'boff', 'dang', 'itmax', 'ipmax',  'target', 'thresh', 'rrec' ,'hp', 'lp', 'rbfact']
	def convertSymmetryNameForPackage(self):
		if not self.symmdata:
			# This is to handle T, I1, I2, and N that is not defined in eman
			return self.params['sym'].upper()
		eman_symm_name = self.symmdata['eman_name']
		if eman_symm_name[0] in ('c','d'):
			symm_name = eman_symm_name.upper()
		elif eman_symm_name == 'oct':
			symm_name = 'O'
		elif eman_symm_name == 'icos':
			symm_name = 'I'
		else:
			apDisplay.printError("unknown symmetry name conversion")
		return symm_name

	#===============
	def getStackParticleEulersForIteration(self, pnum):
		"""
		find the eulers assigned to a stack particle
		during a refinement.  This function will first
		find the particle id for the given stack particle,
		then find its position in the reference stack, and
		will get the eulers for that particle in the recon
		"""

		# get stack particle id
		stackp = apStack.getStackParticle(self.params['stackid'], pnum)
		particleid = stackp['particle'].dbid

		# find particle in reference stack
		refstackp = apStack.getStackParticleFromParticleId(particleid, self.oldreconstackid, nodie=True)
		if not refstackp:
			percentnoeuler = 100*self.noeulers/float(self.params['last'])
			apDisplay.printWarning('No eulers for particle %d (%.1f%%)' % (pnum, percentnoeuler))
			self.noeulers += 1
			if percentnoeuler > 10:
				apDisplay.printError('More than 10% of the particles have no euler, use a different reference reconstruction')
			pclass={
				'euler1': 0.0,
				'euler2': 0.0,
				'euler3': 0.0,
				'mirror': False,
				'shiftx': 0.0,
				'shifty': 0.0,
			}
		else:
			pclassq = appiondata.ApRefineParticleData()
			pclassq['particle'] = refstackp
			pclassq['refineIter'] = appiondata.ApRefineIterData.direct_query(self.params['reconiterid'])
			pclasses = pclassq.query(results=1)
			pclass = pclasses[0]

		try:
			emaneuler={
				'alt':    pclass['euler1'],
				'az':     pclass['euler2'],
				'phi':    pclass['euler3'],
				'mirror': pclass['mirror'],
				'shiftx': pclass['shiftx'],
				'shifty': pclass['shifty'],
			}
		except:
			print pclass
			emaneuler={
				'alt':    pclass['euler1'],
				'az':     pclass['euler2'],
				'phi':    pclass['euler3'],
				'mirror': pclass['mirror'],
				'shiftx': pclass['shiftx'],
				'shifty': pclass['shifty'],
			}

		return emaneuler

	#===============
	def generateParticleParams(self):
		paramfile = os.path.join(self.params['rundir'], 'params.iter000.par')
		apDisplay.printMsg("Creating parameter file: "+paramfile)

		numpart = apStack.getNumberStackParticlesFromId(self.params['stackid'])
		if os.path.isfile(paramfile):
			f = open(paramfile, 'r')
			numparam = len(f.readlines())
			if numparam > self.params['last']:
				apDisplay.printMsg("Param file exists")
				return paramfile
			else:
				apDisplay.printWarning("Param file exists with too few particles: %d vs %d"%(numparam,numpart))

		stackdata = apStack.getStackParticlesFromId(self.params['stackid'])
		particleparams={}

		f = open(paramfile, 'w')
		f.write("C           PSI   THETA     PHI     SHX     SHY    MAG   FILM      DF1      DF2  ANGAST  PRESA\n")
		apDisplay.printMsg("Writing out particle parameters")
		count = 0
		t0 = time.time()
		self.noeulers = 0
		for particle in stackdata:
			count += 1
			if (count % 200 == 0):
				estime = (time.time() - t0) * (numpart-count) / float(count)
				apDisplay.printMsg("particle %d -- %s remain"%(count, apDisplay.timeString(estime)))
			if count > self.params['last']:
				break
			# defaults
			## Niko says that if the defocus is negative it will not perform CTF correction
			## But it will also not correct the amplitudes
			particleparams = {
				'ptclnum': particle['particleNumber'],
				'psi': 0.0,
				'theta': 0.0,
				'phi': 0.0,
				'df1': -1.0, # workaround if no ctf correction
				'df2': -1.0, # set defocus to -1.0 Angstroms
				'angast': 0.0,
				'mag': 10000, # workaround to get around dstep
				'shx': 0.0,
				'shy': 0.0,
				'film': 1,
				'presa': 0.0,
				'dpres': 0.0,
			}
			imagedata = particle['particle']['image']
			if self.params['noctf'] is False:
				ctfdata, confidence = apCtf.getBestCtfValueForImage(imagedata, msg=False, method=self.params['ctfmethod'])
				if ctfdata is not None:
					### use defocus and astigmatism values
					particleparams['df1'] = abs(ctfdata['defocus1']*1e10)
					particleparams['df2'] = abs(ctfdata['defocus2']*1e10)
					particleparams['angast'] = -ctfdata['angle_astigmatism']
			# if using parameters from previous reconstruction
			if self.params['reconiterid'] is not None:
				emaneuler = self.getStackParticleEulersForIteration(particle['particleNumber'])
				frealigneulers = apFrealign.convertEmanEulersToFrealign(emaneuler, sym=self.params['sym'])
				particleparams['psi'] = frealigneulers['psi']
				particleparams['theta'] = frealigneulers['theta']
				particleparams['phi'] = frealigneulers['phi']
				particleparams['shx'] = emaneuler['shiftx']*self.params['sp_bin']
				particleparams['shy'] = emaneuler['shifty']*self.params['sp_bin']
				if emaneuler['mirror'] is True:
					particleparams['shx'] *= -1
			self.writeParticleParamLine(particleparams,f)
		f.close()
		return paramfile

	#===============
	def writeParticleParamLine(self, p, f):
		f.write( ("%7d"+"%8.2f%8.2f%8.2f"+"%8.2f%8.2f"+"%7d.%6d"+"%9.1f%9.1f%8.2f"+"%7.2f%8.2f\n") %
		(p['ptclnum'], #part num
			p['psi'],p['theta'],p['phi'], #Eulers
			p['shx'],p['shy'], #shifts
			p['mag'],p['film'], #scope
			p['df1'],p['df2'],p['angast'], #defocus
			p['presa'],p['dpres'], #phase residual, change in phase residual from previous run
		))

	#===============
	def setupParticleParams(self):
		if self.params['reconiterid'] is not None:
			### use parameters from previous reconstruction
			self.iflag = 1
			self.oldreconstackid = apStack.getStackIdFromIterationId(self.params['reconiterid'])
		elif self.params['dang'] is not None:
			### use slow projection matching search to determine initial Eulers
			self.iflag = 3

		"""
		if self.params['inpar'] is not None and os.path.isfile(self.params['inpar']):
			### use specified parameter file
			paramfile = self.params['inpar']
			apDisplay.printMsg("Using parameter file: "+paramfile)		
			return paramfile
		"""

		paramfile = self.generateParticleParams()
		return paramfile

	#===============
	def setupInitialModel(self):
		modeldata = self.model['data']
		modelfile = self.model['file']
		modelsym = modeldata['symmetry']['symmetry']

		apDisplay.printMsg("Current symmetry: %s"%(modeldata['symmetry']['description']))

		# if icosahedral recon, rotate volume to 3DEM standard orientation
		if modelsym.startswith('Icos (5 3 2)'):
			tempfile = "temp.mrc"
			emancmd = 'proc3d %s %s icos5fTo2f' % (modelfile, tempfile)
			apEMAN.executeEmanCmd(emancmd, verbose=True)
			modelfile = tempfile

		if modelsym.startswith('Icos (5 3 2)') or modelsym.startswith('Icos (2 5 3)'):
			tempfile = "temp.mrc"
			emancmd = 'proc3d %s %s rotspin=0,0,1,90' % (modelfile, tempfile)
			apEMAN.executeEmanCmd(emancmd, verbose=True)
			modelfile = tempfile

		if self.model['file'] != modelfile:
			shutil.mv(modelfile,self.model['file'])
		return self.model['file']

	#===============
	def bc(self, val):
		""" Convert bool to single letter T or F """
		if val is True:
			return "T"
		return "F"

	#===============
	def appendFrealignJobFile(self, iternum,jobfile, first=1, last=None, 
			recon=True, iflag=None, logfile=None):
	
		### hard coded parameters
		self.defaults = {
			'cform':'I', #(I) use imagic, (M) use mrc, (S) use spider
			'fstat': False, # memory saving function, calculates many stats, such as SSNR
			'ifsc': 0, # memory saving function, usually false
			'fmatch': False, # make matching projection for each particle
			'iewald': 0.0, #  
			'fbeaut': True, # 
			'dfstd': 100,   # defocus standard deviation (in Angstroms), usually +/- 100 A, only for defocus refinement
			'beamtiltx': 0.0, #assume zero beam tilt
			'beamtilty': 0.0, #assume zero beam tilt
		}
		if recon is True:
			self.defaults['fstat'] = True

		if last is None:
			last = self.params['last']
		if logfile is None:
			logfile = "frealign.out"
		if iflag is None:
			iflag = self.iflag

		f = open(jobfile, 'a')
		if recon is True:
			### environmental variable decide how many cpus for volume
			f.write('export NCPUS=%d\n'%(self.params['ppn']))
		f.write('\n')
		f.write('# IFLAG %d\n'%(iflag))
		f.write('# PARTICLES %d THRU %d\n'%(first, last))
		f.write('# RECON %s\n'%(recon))
		f.write('\n')
		f.write('### START FREALIGN ###\n')
		#f.write('frealign.exe << EOF\n')
		f.write('frealign.exe << EOF > '+logfile+'\n')

		### CARD 1
		f.write('%s,%d,%s,%s,%s,%s,%d,%s,%s,%s,%d,%s,%d\n' % (
			self.defaults['cform'],
			iflag, 
			self.bc(self.params['fmag'][iternum-1]), self.bc(self.params['fdef'][iternum-1]), #T/F refinements
			self.bc(self.params['fastig'][iternum-1]), self.bc(self.params['fpart'][iternum-1]), #T/F refinements
			self.defaults['iewald'], 
			self.bc(self.defaults['fbeaut']), self.bc(self.params['fcref'][iternum-1]), self.bc(self.defaults['fmatch']), 
			self.defaults['ifsc'],
			self.bc(self.defaults['fstat']), self.iblow))

		### CARD 2
		f.write('%d,%d,%.3f,%.2f,%.2f,%d,%d,%d,%d,%d\n' % (
			self.params['mask'][iternum-1], self.params['imask'][iternum-1], ### mask radii are in Angstroms
			self.apix, self.params['wgh'][iternum-1], 
			self.params['xstd'][iternum-1], self.params['pbc'][iternum-1], 
			self.params['boff'][iternum-1], self.params['dang'][iternum-1], self.params['itmax'][iternum-1], self.params['ipmax'][iternum-1]))

		### CARD 3 fixing of an Euler angle or shift parameters, 1 = refine all
		f.write('%d %d %d %d %d\n' % (1,1,1,1,1))


		### CARD 4 -- particle limits
		f.write('%d, %d\n' % (first, last))

		### CARD 5
		f.write('%s\n' % (self.params['symm_name']))

		### CARD 6
		f.write('%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f\n' % (
			1.0, self.apix, 
			self.params['target'][iternum-1], self.params['thresh'][iternum-1], 
			self.params['cs'], self.params['kv'], 
			self.defaults['beamtiltx'], self.defaults['beamtilty']))

		### CARD 7
		### lp should be ~25 A for iflag 3 and ~12 A for iflag 1
	 	f.write('%.2f,%.2f,%.2f,%.2f,%.2f\n' % (
			self.params['rrec'][iternum-1], self.params['hp'][iternum-1], 
			self.params['lp'][iternum-1], self.defaults['dfstd'], self.params['rbfact'][iternum-1]))

		### CARD 8
		f.write('%s\n'%(self.stackfile))
		f.write('match\n')
		f.write('%s\n'%(self.currentparam))
		f.write('outparams.par\n')
		f.write('shift.par\n')

		if recon is False:
			# set relmag to -100, if no 3d reconstruction is desired for parallel mode
			reconrelmag = -100.0
		else:
			reconrelmag = 0.0
		f.write('%.1f,0.0,0.0,0.0,0.0,0.0,0.0,0.0\n' %reconrelmag)
		f.write('%s\n'%(os.path.splitext(self.currentvol)[0]))
		f.write('weights\n')
		f.write('odd\n')
		f.write('even\n')
		f.write('phasediffs\n')
		f.write('pointspread\n')
		f.write('EOF\n\n\n')
		f.write('### END FREALIGN ###\n')
		f.write('echo "END FREALIGN"\n')
		f.write('\n')

		f.close()
		os.chmod(jobfile, 0755)

	#===============
	def createMultipleJobs(self, iternum):
		"""
		Create multiple job files for frealign reconstruction
		using the mpiexec command
		"""
		### create script that will launch all mpi scripts
		iterdir = "iter%03d"%(iternum)
		iterjobfile = 'frealign.iter%03d.run.sh'%(iternum)

		#frscript = os.path.join(workdir,'frealign.$PBS_VNODENUM.sh')
		#fr.write("sh "+frscript+"\n")

		### create individual mpi scripts
		partperjob = math.floor(self.params['last']/self.params['nproc'])
		#apDisplay.printMsg("%d particles per processor"%(partperjob))
		r = self.params['last']%self.params['nproc']
		lastp = 0
		procjobfiles = []
		for n in range(self.params['nproc']):
			firstp = lastp + 1
			lastp = firstp + partperjob - 1
			if r > 0:
				lastp+=1
				r-=1

			procdir = "iter%03d/proc%03d"%(iternum, n+1)
			#print procdir
			apParam.createDirectory("iter%03d"%(iternum), warning=False)
			procjobfile = "iter%03d/frealign.iter%03d.proc%03d.sh"%(iternum, iternum, n+1)

			### start jobfile
			f = open(procjobfile, "w")
			f.write("#!/bin/sh\n")
			f.write("\n")
			f.write("### Job #%03d, Particles %6d - %6d\n" %(n+1, firstp, lastp))
			f.write('mkdir -p %s\n' %procdir)
			f.write('cd %s\n' %procdir)
			time.sleep(0.05)
			f.close()

			### add frealign code
			self.currentvol = "../../"+os.path.basename(self.currentvol)
			self.currentparam = "../../"+os.path.basename(self.currentparam)
			logfile = "frealign.proc%03d.out"%(n+1)
			self.appendFrealignJobFile(iternum,procjobfile, first=firstp, last=lastp, recon=False, logfile=logfile)

			### append to list
			procjobfiles.append(procjobfile)

		return procjobfiles

	#===============
	def combineMultipleJobs(self, iternum):
		"""
		combine all the parameter files & combine into 1
		then reconstruct the density
		"""
		combineparamfile = 'params.iter%03d.par'%(iternum)
		combinevolfile = 'threed.%03da.hed'%(iternum)
		combinejobfile = 'iter%03d/frealign.iter%03d.combine.sh'%(iternum, iternum)
		cmd = "cat proc*/outparams.par | egrep -v '^C' | sort -n > "+combineparamfile

		f = open(combinejobfile, 'w')
		f.write("#!/bin/sh\n\n")
		iterdir = "iter%03d"%(iternum)
		f.write('cd %s\n' % iterdir)
		f.write(cmd+"\n\n")
		f.write("wc -l %s \n"%(combineparamfile))
		f.write("/bin/rm -fv iter%03d.???\n"%(iternum))
		f.write("/bin/rm -fv threed.%03da.???\n"%(iternum))
		time.sleep(0.05)
		f.close()

		self.currentparam = combineparamfile
		self.currentvol = combinevolfile
		self.appendFrealignJobFile(iternum,combinejobfile, iflag=0, logfile="frealign.combine.out")

		f = open(combinejobfile, 'a')
		### calculate EMAN fsc curve
		f.write('proc3d odd.hed even.hed fsc=fsc.eotest.%d\n'%(iternum))
		f.write('getRes.pl %d %d %.3f >> ../resolution.txt\n'%(iternum, self.refineboxsize, self.apix))

		### move file down directory
		f.write('/bin/cp -v threed.%03da.hed ..\n'%(iternum))
		f.write('/bin/cp -v threed.%03da.img ..\n'%(iternum))
		f.write('/bin/cp -v %s ..\n'%(combineparamfile))
		time.sleep(0.05)
		f.close()

		return combinejobfile

	#===============
	def singleNodeRun(self, iternum):
		"""
		single node run
		"""
		### single node run
		apDisplay.printMsg("Single node run, iteration %d"%(iternum))

		### create individual processor jobs
		stackbase = os.path.splitext(os.path.basename(self.refinestackfile))[0]
		self.stackfile = "../../%s"%(stackbase)
		procjobfiles = self.createMultipleJobs(iternum)

		### convert job files to commands
		procjobcmds = []
		for procjobfile in procjobfiles:
			procjobcmd = "sh "+procjobfile
			procjobcmds.append(procjobcmd)

		### run individual processor jobs
		t0 = time.time()
		apThread.threadCommands(procjobcmds, nproc=self.params['nproc'], pausetime=30.0)
		apDisplay.printColor("Refinement complete in %s"%(apDisplay.timeString(time.time()-t0)), "green")

		### create combine processor jobs
		stackbase = os.path.splitext(os.path.basename(self.reconstackfile))[0]
		self.stackfile = "../%s"%(stackbase)
		combinejobfile = self.combineMultipleJobs(iternum)


		### run combine processor jobs
		t0 = time.time()
		proc = subprocess.Popen("sh "+combinejobfile, shell=True)
		proc.wait()
		apDisplay.printColor("Volume complete in %s"%(apDisplay.timeString(time.time()-t0)), "green")

		if apFile.fileSize('iter%03d.img'%(iternum)) < 100:
			apDisplay.printError("Failed to generate volume for iter %d"%(iternum))

		return

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
	def calcMemNeeded(self):
		### from frealign paper
		nn1 = self.refineboxsize
		nnbig = nn1 * self.iblow
		memneed = 24 * nn1**3 + 4 * nnbig**3 + 200e6

		### multiply by number of procs per node
		memneed *= self.params['rpn']

		## double it just in case
		memneed *= 2.0

		return memneed

	#===============
	def setupMultiNode(self):
		self.mainjobfile = 'frealign.run.job'
		mainf = open(self.mainjobfile, 'w')
		#mainf.write("#PBS -l nodes=%d:ppn=%d\n"%(self.params['nodes'], self.params['ppn']))
		memrequest = self.calcMemNeeded()
		apDisplay.printMsg("requesting %s of memory"%(apDisplay.bytes(memrequest)))
		#mainf.write("#PBS -l mem=%s\n"%(apDisplay.clusterBytes(memrequest)))
		#mainf.write("#PBS -m e\n")
		#mainf.write("#PBS -r n\n")
		#mainf.write("#PBS -j oe\n")
		#mainf.write("\n")
		### if local cluster
		#mainf.write("cd %s\n"%(self.params['rundir']))
		### elseif remote cluster
		mainf.write("tar -xkf %s.tar\n"%(self.params['runname']))
		mainf.write("\n")

	#===============
	def multiNodeRun(self, iternum):
		"""
		multi node run
		"""
		### mutli node run
		apDisplay.printMsg("Multi node run, iteration %d"%(iternum))

		### create individual processor jobs
		stackbase = os.path.splitext(os.path.basename(self.refinestackfile))[0]
		self.stackfile = "../../%s"%(stackbase)
		procjobfiles = self.createMultipleJobs(iternum)

		stackbase = os.path.splitext(os.path.basename(self.reconstackfile))[0]
		self.stackfile = "../%s"%(stackbase)
		combinejobfile = self.combineMultipleJobs(iternum)

		### write to jobfile
		iterjobfile = 'iter%03d/frealign.iter%03d.run.sh'%(iternum,iternum)
		iterf = open(iterjobfile, "w")
		for procjobfile in procjobfiles:
			iterf.write("-np 1 %s\n" % procjobfile)
		iterf.close()

		mainf = open(self.mainjobfile, 'a')
		### use MPI to launch multiple jobs
		if iternum == 1:
			mainf.write("echo 'starting particle refinement for iter %d' > refine.log\n"%(iternum))
		else:
			mainf.write("echo 'starting particle refinement for iter %d' >> refine.log\n"%(iternum))
		mainf.write("mpirun --hostfile $PBS_NODEFILE -np %d --app %s\n"
			%(self.params['nproc'], iterjobfile))
		mainf.write("echo 'particle refinement complete for iter %d' >> refine.log\n"%(iternum))
		mainf.write("echo 'starting volume reconstruction for iter %d' >> refine.log\n"%(iternum))
		mainf.write("mpirun --hostfile $PBS_NODEFILE -np 1 %s\n"
			%(combinejobfile))

		### stop job if files is missing or has size of zero
		volfile = "threed.%03da.img"%(iternum)
		mainf.write("test -s %s || exit\n"%(volfile))
		paramfile = "params.iter%03d.par"%(iternum)
		mainf.write("test -s %s || exit\n"%(paramfile))

		mainf.write("echo 'volume reconstruction complete for iter %d' >> refine.log\n"%(iternum))
		mainf.write("echo 'iteration %d is complete' >> refine.log\n"%(iternum))
		mainf.write("echo '' >> refine.log\n\n")

		### PBS pro
		#mainf.write("pbsdsh -v %s\n" % iterjobfile)
		mainf.close()

		return self.mainjobfile

	#===============
	def prepareForCluster(self):
		#package data for transfer to cluster
		apFile.removeFile(self.params['runname']+".tar")
		cmd = "tar --exclude=*.tar -cf %s.tar *"%(self.params['runname'])
		print cmd
		proc = subprocess.Popen(cmd, shell=True)
		proc.wait()

		needf = open("files-needed.txt", "w")
		needf.write("%s.tar\n"%(os.path.join(self.params['rundir'], self.params['runname'])))
		needf.write("%s\n"%(os.path.splitext(self.refinestackfile)[0]+".hed"))
		needf.write("%s\n"%(os.path.splitext(self.refinestackfile)[0]+".img"))
		needf.close()

		### find cluster job based on path
		partq = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
		jobq = appiondata.ApAppionJobData()
		jobq['path'] = partq
		jobq['jobtype'] = 'preprefinefrealign'
		jobdatas = jobq.query(results=1)
		if not jobdatas:
			apDisplay.printError("Could not find job data for prepRefineFrealign")
		jobdata = jobdatas[0]

		### create a frealign table
		frealignq = appiondata.ApFrealignPrepareData()
		frealignq['name'] = self.params['runname']
		frealignq['memory'] = self.calcMemNeeded()/1e9 #memory in gigabytes
		frealignq['hidden'] = False
		frealignq['tarfile'] = "%s.tar"%(self.params['runname'])
		frealignq['path'] = partq
		frealignq['stack'] = appiondata.ApStackData.direct_query(self.params['stackid'])
		if self.params['reconstackid'] is not None:
			frealignq['reconstack'] = appiondata.ApStackData.direct_query(self.params['reconstackid'])
		frealignq['model'] = appiondata.ApInitialModelData.direct_query(self.params['modelid'])
		frealignq['job'] = jobdata
		frealignq['symmetry'] = self.symmdata
		if self.params['reconiterid'] is not None:
			frealignq['refineIter'] = appiondata.ApRefineIterData.direct_query(self.params['reconiterid'])
		frealignq.insert()

	def proc2dFormatConversion(self):
		extname = 'hed'
		#format = 'invert'
		format = ''
		return extname, format

	#===============
	def setupRefineScript(self):
		self.iflag = 1
		self.setIBLOW()

		### get stack info
		self.refinestackfile = self.stack['file']
		#apImagicFile.setImagic4DHeader(self.refinestackfile)

		### TO FIX: Don't know what to do with this yet
		if self.params['reconstackid'] is not None:
			self.reconstackdata = apStack.getOnlyStackData(self.params['reconstackid'])
			reconstackpath,reconstackfile = apStackFormat.linkFormattedStack(self.reconstackdata, 'frealign','recon0')
			self.reconstackfile = os.path.join(reconstackpath, reconstackfile)		
		else:
			self.reconstackfile = self.refinestackfile


		### create initial model file
		self.currentvol = os.path.basename(self.setupInitialModel())

		### create parameter file
		self.currentparam = os.path.basename(self.setupParticleParams())
		apDisplay.printColor("Initial files:\n Stack: %s\n Volume: %s\n Params: %s\n"
			%(os.path.basename(self.refinestackfile), self.currentvol, self.currentparam), "violet")

		### copy stack or start job file
		if self.params['cluster'] is False:
			#create alias to stack data
			pass
		if self.params['cluster'] is True:
			self.setupMultiNode()

		## run frealign for number for refinement cycles
		for i in range(self.params['numiter']):
			iternum = i+1
			if self.params['cluster'] is True:
				self.multiNodeRun(iternum)
			else:
				self.singleNodeRun(iternum)
				time.sleep(2)

			### calculate FSC
			#emancmd = 'proc3d %s %s fsc=fsc.eotest.%d' % (evenvol, oddvol, self.params['iter'])
			#apEMAN.executeEmanCmd(emancmd, verbose=True)

		if self.params['cluster'] is True:
			self.prepareForCluster()

		print "Done!"

if __name__ =='__main__':
	frealign = frealignJob()
	frealign.start()
	frealign.close()
	
