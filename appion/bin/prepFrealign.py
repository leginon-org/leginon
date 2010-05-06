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
from appionlib import appiondata
from pyami import mrc

#================
#================
class frealignJob(appionScript.AppionScript):
	#================
	def setupParserOptions(self):

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
		self.parser.add_option('--mask', dest="mask", type='float',
			help="mask from center of particle to outer edge")
		self.parser.add_option('--imask', dest="imask", default=0, type='float',
			help="inner mask radius")
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
		self.parser.add_option('--last', dest="last", type='int',
			help="last particle to process")
	
		####card 5
		self.parser.add_option('--sym', dest="sym", help="symmetry ")
	
		####card 6
		self.parser.add_option('--target', dest="target", default=10.0, type='float',
			help="target phase residual during refinement")
		self.parser.add_option('--thresh', dest="thresh", default=90.0, type='float',
			help="phase residual threshold cut-off")
		self.parser.add_option('--cs', dest="cs", default=2.0, type='float',
			help="spherical aberation")
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
		self.parser.add_option('--stackid', dest='stackid', type='int',
			help="stack id from database")
		self.parser.add_option('--modelid', dest='modelid', type='int',
			help="initial model id from database")
		self.parser.add_option('--reconiterid', dest='reconiterid', type='int',
			help="id for specific iteration from a refinement, used for retrieving particle orientations")
		self.parser.add_option('--ppn', dest='ppn', type='int',
			help="number of processors per node")
		self.parser.add_option('--nodes', dest='nodes', default=1, type='int',
			help="number of nodes")
		self.parser.add_option("--cluster", dest="cluster", default=True,
			action="store_true", help="Make script for running on a cluster")
		self.parser.add_option("--no-cluster", dest="cluster", default=True,
			action="store_false", help="Run script interactively on current machine")

		self.parser.add_option('--numiter', dest='numiter', type='int', default=1,
			help="number of refinement iterations to perform")
		self.parser.add_option('--noctf', dest='noctf', default=False, action='store_true',
			help="choose if frealign should not perform ctf correction")
		self.parser.add_option('--ctfmethod', dest='ctfmethod',
			help="Only use ctf values coming from this method of estimation", metavar="TYPE",
			type="choice", choices=self.ctfestopts)

	#=====================
	def checkConflicts(self):
		if self.params['stackid'] is None:
			apDisplay.printError("stack id was not defined")
		if self.params['modelid'] is None:
			apDisplay.printError("model id was not defined")
		if self.params['runname'] is None:
			apDisplay.printError("missing a reconstruction name")
		if self.params['last'] is None:
			self.params['last'] = apStack.getNumberStackParticlesFromId(self.params['stackid'])
		self.boxsize = apStack.getStackBoxsize(self.params['stackid'], msg=False)
		self.apix = apStack.getStackPixelSizeFromStackId(self.params['stackid'])
		maxmask = math.floor(self.apix*(self.boxsize-10)/2.0)
		if self.params['mask'] is None:
			apDisplay.printWarning("mask was not defined, setting to boxsize: %d"%(maxmask))
			self.params['mask'] = maxmask
		if self.params['mask'] > maxmask:
			apDisplay.printWarning("mask was too big, setting to boxsize: %d"%(maxmask))
			self.params['mask'] = maxmask
		if self.params['noctf'] is True:
			 self.params['wgh'] = -1.0
		if self.params['nodes'] > 1 and self.params['cluster'] is False:
			apDisplay.printError("cluster mode must be enabled to run on more than 1 node")
		if self.params['ppn'] is None:
			if self.params['cluster'] is True:
				apDisplay.printError("you must define ppn for cluster mode")
			self.params['ppn'] = apParam.getNumProcessors()
			apDisplay.printMsg("Setting number of processors to %d"%(self.params['ppn']))
		self.params['nproc'] = self.params['nodes']*self.params['ppn']
		### get the symmetry data
		if self.params['sym'] is None:
			apDisplay.printError("Symmetry was not defined")
		else:
			self.symmdata = apSymmetry.findSymmetry(self.params['sym'])
			self.params['symm_id'] = self.symmdata.dbid
			self.params['symm_name'] = self.symmdata['eman_name']
			apDisplay.printMsg("Selected symmetry %s with id %s"%(self.symmdata['eman_name'], self.symmdata.dbid))

	#=====================
	def setRunDir(self):
		self.stackdata = apStack.getOnlyStackData(self.params['stackid'], msg=False)
		path = self.stackdata['path']['path']
		uppath = os.path.abspath(os.path.join(path, "../.."))
		self.params['rundir'] = os.path.join(uppath,'recon',self.params['runname'])

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
		refstackp = apStack.getStackParticleFromParticleId(particleid, self.params['reconstackid'], nodie=True)
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
				particleparams['shx'] = emaneuler['shiftx']
				particleparams['shy'] = emaneuler['shifty']
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
			self.params['reconstackid'] = apStack.getStackIdFromIterationId(self.params['reconiterid'])
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
		modeldata = apModel.getModelFromId(self.params['modelid'])
		modelfile = os.path.join(modeldata['path']['path'], modeldata['name'])
		modelsym = modeldata['symmetry']['symmetry']

		# if icosahedral recon, rotate volume to 3DEM standard orientation
		if modelsym == 'Icos (5 3 2)':
			tempfile = "temp.mrc"
			emancmd = 'proc3d %s %s icos5fTo2f' % (modelfile, tempfile)
			apEMAN.executeEmanCmd(emancmd, verbose=True)
			modelfile = tempfile

		if modelsym == 'Icos (5 3 2)' or modelsym == 'Icos (2 5 3)':
			tempfile = "temp.mrc"
			emancmd = 'proc3d %s %s rotspin=0,0,1,90' % (modelfile, tempfile)
			apEMAN.executeEmanCmd(emancmd, verbose=True)
			modelfile = tempfile

		boxsize = apStack.getStackBoxsize(self.params['stackid'])

		outmodelfile = os.path.join(self.params['rundir'], "initmodel.hed")
		apFile.removeStack(outmodelfile, warn=False)
		emancmd = "proc3d %s %s clip=%d,%d,%d " % (modelfile, outmodelfile, boxsize, boxsize, boxsize)

		# rescale initial model if necessary
		scale = modeldata['pixelsize']/self.apix
		if abs(scale - 1.0) > 1e-3:
 			emancmd += "scale=%.4f "%(scale)

		apEMAN.executeEmanCmd(emancmd, verbose=True)
		apImagicFile.setImagic4DHeader(outmodelfile,machineonly=True)

		return outmodelfile

	#===============
	def bc(self, val):
		""" Convert bool to single letter T or F """
		if val is True:
			return "T"
		return "F"

	#===============
	def appendFrealignJobFile(self, jobfile, first=1, last=None, 
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
			self.bc(self.params['fmag']), self.bc(self.params['fdef']), #T/F refinements
			self.bc(self.params['fastig']), self.bc(self.params['fpart']), #T/F refinements
			self.defaults['iewald'], 
			self.bc(self.defaults['fbeaut']), self.bc(self.params['fcref']), self.bc(self.defaults['fmatch']), 
			self.defaults['ifsc'],
			self.bc(self.defaults['fstat']), self.iblow))

		### CARD 2
		f.write('%d,%d,%.3f,%.2f,%.2f,%d,%d,%d,%d,%d\n' % (
			self.params['mask'], self.params['imask'], 
			self.apix, self.params['wgh'], 
			self.params['xstd'], self.params['pbc'], 
			self.params['boff'], self.params['dang'], self.params['itmax'], self.params['ipmax']))

		### CARD 3 fixing of an Euler angle or shift parameters, 1 = refine all
		f.write('%d %d %d %d %d\n' % (1,1,1,1,1))


		### CARD 4 -- particle limits
		f.write('%d, %d\n' % (first, last))

		### CARD 5
		if self.params['sym'].lower() == 'icos':
			f.write('I\n')
		else:
			f.write('%s\n' % (self.params['sym']))

		### CARD 6
		f.write('%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f\n' % (
			1.0, self.apix, 
			self.params['target'], self.params['thresh'], 
			self.params['cs'], self.params['kv'], 
			self.defaults['beamtiltx'], self.defaults['beamtilty']))

		### CARD 7
		### lp should be ~25 A for iflag 3 and ~12 A for iflag 1
	 	f.write('%.2f,%.2f,%.2f,%.2f,%.2f\n' % (
			self.params['rrec'], self.params['hp'], 
			self.params['lp'], self.defaults['dfstd'], self.params['rbfact']))

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
			self.appendFrealignJobFile(procjobfile, first=firstp, last=lastp, recon=False, logfile=logfile)

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
		f.write("rm -fv iter%03d.???\n"%(iternum))
		time.sleep(0.05)
		f.close()

		self.currentparam = combineparamfile
		self.currentvol = combinevolfile
		self.appendFrealignJobFile(combinejobfile, iflag=0, logfile="frealign.combine.out")

		f = open(combinejobfile, 'a')
		f.write('cp -v iter%03d.hed ..\n'%(iternum))
		f.write('cp -v iter%03d.img ..\n'%(iternum))
		f.write('cp -v %s ..\n'%(combineparamfile))
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
		self.stackfile = "../../start"
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
		self.stackfile = "../start"
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
		apDisplay.printMsg("IBLOW set to %d, requiring %s memory"
			%(self.iblow, apDisplay.bytes(self.calcMemNeeded())))

	#===============
	def calcMemNeeded(self):
		### from frealign paper
		nn1 = self.boxsize
		nnbig = nn1 * self.iblow
		memneed = 24 * nn1**3 + 4 * nnbig**3 + 200e6

		### multiply by number of procs per node
		memneed *= self.params['ppn']

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
		### if guppy
		#mainf.write("cd %s\n"%(self.params['rundir']))
		### elseif garibaldi
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
		self.stackfile = "../../start"
		procjobfiles = self.createMultipleJobs(iternum)
		self.stackfile = "../start"
		combinejobfile = self.combineMultipleJobs(iternum)

		### write to jobfile
		iterjobfile = 'iter%03d/frealign.iter%03d.run.sh'%(iternum,iternum)
		iterf = open(iterjobfile, "w")
		for procjobfile in procjobfiles:
			iterf.write("-np 1 %s\n" % procjobfile)
		iterf.close()

		mainf = open(self.mainjobfile, 'a')
		### use MPI to launch multiple jobs
		mainf.write("echo 'starting particle refinement for iter %d' >> refine.log\n"%(iternum))
		mainf.write("mpirun --hostfile $PBS_NODEFILE -np %d --app %s\n"
			%(self.params['nproc'], iterjobfile))
		mainf.write("echo 'particle refinement complete for iter %d' >> refine.log\n"%(iternum))
		mainf.write("echo 'starting volume reconstruction for iter %d' >> refine.log\n"%(iternum))
		mainf.write("mpirun --hostfile $PBS_NODEFILE -np 1 %s\n"
			%(combinejobfile))
		mainf.write("echo 'volume reconstruction complete for iter %d' >> refine.log\n"%(iternum))
		mainf.write("echo 'iteration %d is complete' >> refine.log\n"%(iternum))
		mainf.write("echo '' >> refine.log\n")
		#mainf.write("if [ -e 'iter%03d' ]\nthen\n  exit\nfi\n\n"%(iternum))	

		### PBS pro
		#mainf.write("pbsdsh -v %s\n" % iterjobfile)
		mainf.close()

		return self.mainjobfile

	#===============
	def prepareForCluster(self):
		#package data for transfer to cluster
		apFile.removeFile(self.params['runname']+".tar")
		cmd = "tar --exclude=*.tar -cf %s.tar *"%(self.params['runname'])
		proc = subprocess.Popen(cmd, shell=True)
		proc.wait()

		needf = open("files-needed.txt", "w")
		needf.write("%s.tar\n"%(os.path.join(self.params['rundir'], self.params['runname'])))
		needf.write("%s\n"%(os.path.splitext(self.origstackfile)[0]+".hed"))
		needf.write("%s\n"%(os.path.splitext(self.origstackfile)[0]+".img"))
		needf.close()

		### find cluster job based on path
		partq = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
		jobq = appiondata.ApAppionJobData()
		jobq['path'] = partq
		jobq['jobtype'] = 'prepfrealign'
		jobdatas = jobq.query(results=1)
		if not jobdatas:
			apDisplay.printError("Could not find job data for prepFrealign")
		jobdata = jobdatas[0]

		### create a frealign table
		frealignq = appiondata.ApFrealignPrepareData()
		frealignq['name'] = self.params['runname']
		frealignq['ppn'] = self.params['ppn']
		frealignq['nodes'] = self.params['nodes']
		frealignq['memory'] = self.calcMemNeeded()/1e9 #memory in gigabytes
		frealignq['hidden'] = False
		frealignq['tarfile'] = "%s.tar"%(self.params['runname'])
		frealignq['path'] = partq
		frealignq['stack'] = appiondata.ApStackData.direct_query(self.params['stackid'])
		frealignq['model'] = appiondata.ApInitialModelData.direct_query(self.params['modelid'])
		frealignq['job'] = jobdata
		frealignq['symmetry'] = self.symmdata
		frealignq.insert()

	#===============
	def start(self):
		self.iflag = 1
		self.setIBLOW()

		### get stack info
		self.stackdata = apStack.getOnlyStackData(self.params['stackid'])
		self.stackfile = os.path.join(self.stackdata['path']['path'], self.stackdata['name'])
		apImagicFile.setImagic4DHeader(self.stackfile)
		### copy stack or start job file
		if self.params['cluster'] is False:
			#create alias to stack data
			pass
		if self.params['cluster'] is True:
			self.setupMultiNode()
		self.origstackfile = self.stackfile
		self.stackfile = "start"

		### create initial model file
		self.currentvol = os.path.basename(self.setupInitialModel())

		### create parameter file
		self.currentparam = os.path.basename(self.setupParticleParams())
		apDisplay.printColor("Initial files:\n Stack: %s\n Volume: %s\n Params: %s\n"
			%(self.stackfile, self.currentvol, self.currentparam), "violet")

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
	
