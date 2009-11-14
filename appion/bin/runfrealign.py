#!/usr/bin/env python
import sys, os, glob
import subprocess
import shutil
import apParam
import apStack
import apVolume
import apCtf
from pyami import mrc
import threading
import apImagicFile
import appionScript
import apProject
import apDisplay
import apFrealign
import apEMAN

#================
#================
class frealignJob(appionScript.AppionScript):
	#================
	def setupParserOptions(self):

		self.parser.set_usage("Usage: %prog -options")

		#self.parser.add_option("--commit", dest="commit", default=True,
		#	action="store_true", help="Commit processing run to database")

		####card 1
		self.parser.add_option('--iflag', dest="iflag", default=1, type='int',
			help="mode of operation [-4,4]: refine (1) and reconstruct (3)")
		self.parser.add_option("--fmag", dest="fmag", default=False,
			action="store_true", help="Refine the magnification")

		self.parser.add_option('--defocusrefine', dest="defocusrefine", default=False,
			help="no defocus refinement")
		self.parser.add_option('--astigrefine', dest="astigrefine", default=False,
			help="no astigmatism refinemet")
		self.parser.add_option('--defocusperpart', dest="defocusperpart", default=False,
			help="no rotation of theta by 180 degrees")
		self.parser.add_option('--ewald', dest="ewald", default=0, type='int',
			help="no ewald curvature correction")
		self.parser.add_option('--matches', dest="matches", default=True,
			help="write out particles with matching projections")
		self.parser.add_option('--history', dest="history", default=False,
			help="write out history of itmax randomization trials")
		self.parser.add_option('--finalsym', dest="finalsym", default=True,
			help="apply final real space symmetrization to beautify reconstruction")
		self.parser.add_option('--fomfilter', dest="fomfilter", default=True,
			help="apply FOM filter to final reconstruction")
		self.parser.add_option('--fsc', dest="fsc", default=0, type='int',
			help="internall calculate FSC between even and odd particles")
	
		####card 2
		self.parser.add_option('--radius', dest="radius", type='int',
			help="radius from center of particle to outer edge")
		self.parser.add_option('--iradius', dest="iradius", default=0, type='int',
			help="inner mask radius")
		self.parser.add_option('--apix', dest="apix", type='float', help="pixel size in angstroms")
		self.parser.add_option('--ampcontrast', dest="ampcontrast", default=0.07, type='float',
			help="amplitude contrast")
		self.parser.add_option('--maskthresh', dest="maskthresh", default=0.0, type='float',
			help="standard deviations above mean for masking of input model")
		self.parser.add_option('--phaseconstant', dest="phaseconstant", default=100.0, type='float',
			help="conversion constant for phase residual weighting of particles. 100 gives equal weighting")
		self.parser.add_option('--avgresidual', dest="avgresidual", default=75, type='int',
			help="average phase residual of all particles. used for weighting")
		self.parser.add_option('--ang', dest="ang", type='int', default=5, 
			help="step size if using modes 3 and 4")
		self.parser.add_option('--itmax', dest="itmax", default=10, type='int',
			help="number of iterations of randomization. used for modes 2 and 4")
		self.parser.add_option('--maxmatch', dest="maxmatch", default=0, type='int',
			help="number of potential matches in a search that should be tested further in local refinement")
		
		####card 3
		self.parser.add_option('--psi', dest="psi", default=1, type='int',
			help="refine psi")
		self.parser.add_option('--theta', dest="theta", default=1, type='int',
			help="refine theta")
		self.parser.add_option('--phi', dest="phi", default=1, type='int',
			help="refine phi")
		self.parser.add_option('--deltax', dest="deltax", default=1, type='int',
			help="refine delta X")
		self.parser.add_option('--deltay', dest="deltay", default=1, type='int',
			help="refine delta Y")
		
		####card 4
		self.parser.add_option('--last', dest="last", type='int',
			help="last particle")
	
		####card 5
		self.parser.add_option('--sym', dest="sym", help="symmetry ")
	
		####card 6
		self.parser.add_option('--relmag', dest="relmag", default=1, type='float',
			help="relative magnification of dataset")
		self.parser.add_option('--targetresidual', dest="targetresidual", default=10.0, type='float',
			help="target phase residual during refinement")
		self.parser.add_option('--residualthresh', dest="residualthresh", default=90.0, type='float',
			help="phase residual threshold cut-off")
		self.parser.add_option('--cs', dest="cs", default=2.0, type='float',
			help="spherical aberation")
		self.parser.add_option('--kv', dest="kv", default=120.0, type='float',
			help="accelerlating voltage")
		self.parser.add_option('--beamtiltx', dest="beamtiltx", default=0.0, type='float',
			help="beam tilt x (mrad)")
		self.parser.add_option('--beamtilty', dest="beamtilty", default=0.0, type='float',
			help="beam tilt y (mrad)")
	
		####card 7
		self.parser.add_option('--reslimit', dest="reslimit", default=10.0, type='float',  help="resolution to which to limit the reconstruction")
		self.parser.add_option('--hp', dest="hp", default=100.0, type='float',
			help="upper limit for low resolution signal")
		self.parser.add_option('--lp', dest="lp", default=10.0, type='float',
			help="lower limit for high resolution signal")
		self.parser.add_option('--bfactor', dest="bfactor", default=0.0, type='float',
			help="bfactor to apply to particles before classification. 0.0 applies no bfactor.")
	
		####card 8
		self.parser.add_option('--stack', dest="stack", default='start.mrc',
			help="input particles to be classified")
	
		####card 9
		self.parser.add_option('--matchstack', dest="matchstack", default='match.mrc',
			help="output projection matches")
	
		####card 10
		self.parser.add_option('--inpar', dest="inpar",
			help="input particle parameter file")
	
		####card 11
		self.parser.add_option('--outpar', dest="outpar", default='params.1.par',
			help="output particle parameter file")
		
		####card 12
		self.parser.add_option('--outshiftpar', dest="outshiftpar", default='shift.par',
			help="output particle shift parameter file")
		
		####card 14
		self.parser.add_option('--weight3d', dest="weight3d", default='weights.mrc',
			help="???")
		
		####card 15
		self.parser.add_option('--oddvol', dest="oddvol", default='odd.mrc',
			help="output odd volume")
		
		####card 16
		self.parser.add_option('--evenvol', dest="evenvol", default='even.mrc',
			help="output even volume")
		
		####card 17
		self.parser.add_option('--outresidual', dest="outresidual", default='phasediffs.mrc',
			help="3d phase residuals")
		
		####card 18
		self.parser.add_option('--pointspreadvol', dest="pointspreadvol", default='pointspread.mrc',
			help="output 3d point spread function")


		#### Appion params
		self.parser.add_option('--stackid', dest='stackid', type='int',
			help="stack id from database")
		self.parser.add_option('--modelid', dest='modelid', type='int',
			help="initial model id from database")
		self.parser.add_option('--reconiterid', dest='reconiterid', type='int',
			help="id for specific iteration from a refinement, used for retrieving particle orientations")
		self.parser.add_option('--mrchack', dest='mrchack', default=False, action='store_true',
			help="hack to fix machine stamp in mrc header")
		self.parser.add_option('--outvol', dest='outvol',
			help="name of output volume", default='threed.1.mrc')
		self.parser.add_option('--proc', dest='proc', default=1, type='int',
			help="number of processors")
		self.parser.add_option("--cluster", dest="cluster", default=False,
			action="store_true", help="Make script for running on a cluster")

		self.parser.add_option('--refcycles', dest='refcycles', type='int', default=1,
			help="number of refinement iterations to perform")
		self.parser.add_option('--noctf', dest='noctf', default=False, action='store_true',
			help="choose if frealign should not perform ctf correction")
		self.parser.add_option('--iter', dest='iter', default=0, type='int',
					help="continue previous run from this iteration number")

	#=====================
	def checkConflicts(self):
		if self.params['stackid'] is None:
			apDisplay.printError("stack id was not defined")
		if self.params['modelid'] is None:
			apDisplay.printError("model id was not defined")
		if self.params['runname'] is None:
			apDisplay.printError("missing a reconstruction name")

	#=====================
	def setRunDir(self):
		self.stackdata = apStack.getOnlyStackData(self.params['stackid'], msg=False)
		path = self.stackdata['path']['path']
		uppath = os.path.abspath(os.path.join(path, "../.."))
		self.params['rundir'] = os.path.join(uppath,'recon',self.params['runname'])

	#===============
	def runParallel(self):
		createMultipleJobs(self.params)
		joblist=[]
		for n in params['jobs']:		
			command=("frealign < %s " % (n))
			print "command is", command
			job=FrealignJob(command)
			job.start()
			joblist.append(job)

		for job in joblist:
			job.join()

		#combine results of multiple runs and create volume
		combinedparams = params['outpar']+'.all'
		combinefile=open(os.path.join(self.params['rundir'],combinedparams),'w')
		for outpar in params['outparlst']:
			f=open(os.path.join(self.params['rundir'],outpar), 'r')
			lines=f.readlines()
			f.close()

			for n in lines:
				if n[0] != 'C':
					combinefile.write(n)
				else:
					print "comment"
		combinefile.close()
		combinejobname="frealign.job" 
		createFrealignJob(self.params, combinejobname, 0, combinedparams, params['outpar'], params['first'], params['last'], norecon=False)
		command='frealign < ' + combinejobname
		print 'command is',command
		proc = subprocess.Popen(command, shell=True)
		proc.wait()	

	#===============
	def runSingle(self):
		jobname='frealign.job'
		createFrealignJob(self.params, jobname)
		command='frealign < ' + jobname
		print 'command is',command
		proc = subprocess.Popen(command, shell=True)
		proc.wait()

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
		stackp = apStack.getStackParticle(self.params['stackid'],pnum)
		particleid = stackp['particle'].dbid

		# find particle in reference stack
		refstackp = apStack.getStackParticleFromParticleId(particleid, self.params['reconstackid'], nodie=True)
		if not refstackp:
			apDisplay.printWarning('No classification for stack particle %d in reconstruction iteration id: %d' % (pnum, params['reconiterid']))
			self.params['noClassification'] += 1
			if self.params['noClassification'] > (float(self.params['last'])*0.10):
				apDisplay.printError('More than 10% of the particles have no classification, use a different reference reconstruction')
			pclass={
				'eulers': { 'euler1': 0.0, 'euler2': 0.0 },
				'inplane_rotation': 0.0,
				'mirror': False,
				'shiftx': 0.0,
				'shifty': 0.0,
			}
		else:
			pclassq = appiondata.ApParticleClassificationData()
			pclassq['particle'] = refstackp
			pclassq['refinement'] = appiondata.ApRefinementData.direct_query(self.params['reconiterid'])
			pclasses = pclassq.query(results=1)
			pclass = pclasses[0]

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
		paramfile = os.path.join(self.params['rundir'], 'params.0.par')
		apDisplay.printMsg("Creating parameter file: "+paramfile)

		if os.path.isfile(paramfile):
			numpart = apStack.getNumberStackParticlesFromId(self.params['stackid'])
			f = open(paramfile, 'r')
			numparam = len(f.readlines())
			if numparam == numpart:
				apDisplay.printMsg("Param file exists")
				return
			else:
				apDisplay.printWarning("Param file exists but has wrong number of parts: %d vs %d"%(numparam,numpart))

		stackdata = apStack.getStackParticlesFromId(self.params['stackid'])
		apix=self.params['apix']
		particleparams={}

		f = open(paramfile, 'w')
		apDisplay.printMsg("Writing out particle parameters")
		count = 0
		for particle in stackdata:
			count += 1
			if (count % 200 == 0):
				sys.stderr.write(".")
			# defaults
			particleparams = {
				'ptclnum': particle['particleNumber'],
				'psi': 0.0,
				'theta': 0.0,
				'phi': 0.0,
				'df1': 0.1, # workaround if no ctf correction
				'df2': 0.1, # set defocus to 0.1 Angstroms
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
				ctfdata, confidence = apCtf.getBestCtfValueForImage(imagedata, msg=False)
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
			apFrealign.writeParticleParamLine(particleparams,f)
		f.close()
		return paramfile

	#===============
	def setupParticleParams(self):
		if self.params['reconiterid'] is not None:
			### use parameters from previous reconstruction
			self.params['iflag'] = 1
			self.params['reconstackid'] = apStack.getStackIdFromIterationId(self.params['reconiterid'])
		elif self.params['ang'] is not None:
			### use slow projection matching search to determine initial Eulers
			self.params['iflag'] = 3

		if self.params['inpar'] is None:
			### if no parameter file specified then generate input parameter file
			self.params['iflag'] = 3
			self.params['noClassification'] = 0
			paramfile = self.generateParticleParams()
			self.params['inpar'] = paramfile
		else:
			### use specified parameter file
			apDisplay.printMsg("Using parameter file: "+self.params['inpar'])		

	#===============
	def setupInitialModel(self):
		modeldata = apVolume.getModelFromId(self.params['modelid'])
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
		emancmd = "proc3d %s %s clip=%d,%d,%d" % (modelfile, outmodelfile, boxsize, boxsize, boxsize)

		# rescale initial model if necessary
		scale = modeldata['pixelsize']/self.params['apix']
		if abs(scale - 1.0) > 1e-3:
 			emancmd += "scale=%.4f "%(scale)

		apEMAN.executeEmanCmd(emancmd, verbose=True)

		return outmodelfile

	#===============
	def startFrealignJobFile(self, jobfile, stackfile, volfile, paramfile, nodenum=None):
		f = open(jobname, 'w')
		f.write("#!/bin/csh\n")

		# copy files to working directory
		f.write('cd %s\n' % self.params['workingdir'])
		if nodenum is not None:
			workdir = "sub%04d"%(nodenum)
			f.write('rm -rf %s\n' %workdir)
			f.write('mkdir %s\n' %workdir)
			f.write('cd %s\n' %workdir)
		volroot = os.path.splitext(volfile)[0]
		f.write('rsync -vaP %s model.hed\n' % volroot+".hed")
		f.write('rsync -vaP %s model.img\n' % volroot+".img")
		f.write('rsync -vaP %s inparams.par\n' % paramfile)
		f.write('\n')

	#===============
	def appendFrealignJobFile(self, jobfile, paramfile, first=1, last=None, norecon=False):
		### hard coded parameters
		self.defaults = {
			'fstat': False, # memory saving function, usually false
			'iblow': False, # expand volume in memory, larger is faster, but needs more mem
			'fcref': False, # apply FOM weighting
			'dfstd': 100,   # defocus standard deviation (in Angstroms), usually +/- 100 A
		}

		if last is None:
			last = self.params['last']

		f = open(jobfile, 'a')
		f.write('frealign << EOF > frealign.out\n')

		### CARD 1
		f.write('%s,%d,%s,%s,%s,%s,%d,%s,%s,%s,%s,%d,%s,%d\n' % (
			'I', #(I) use imagic, (M) use mrc, (S) use spider
			self.params['iflag'], 
			self.params['fmag'], self.params['defocusrefine'], #T/F refinements
			self.params['astigrefine'], self.params['defocusperpart'], #T/F refinements
			self.params['ewald'], 
			self.params['matches'], self.defaults['fcref'], self.params['finalsym'], 
			self.params['fomfilter'], self.params['fsc'], 
			self.defaults['fstat'], self.defaults['iblow']))

		### CARD 2
		f.write('%d,%d,%.3f,%.2f,%.2f,%d,%d,%d,%d,%d\n' % (
			self.params['radius'], self.params['iradius'], 
			self.params['apix'], self.params['ampcontrast'], 
			self.params['maskthresh'], self.params['phaseconstant'], 
			self.params['avgresidual'], self.params['ang'], self.params['itmax'], self.params['maxmatch']))

		### CARD 3
		f.write('%d %d %d %d %d\n' % (
			self.params['psi'], self.params['theta'], self.params['phi'], 
			self.params['deltax'], self.params['deltay']))

		### CARD 4 -- particle limits
		f.write('%d, %d\n' % (first, last))

		### CARD 5
		if self.params['sym']=='Icos':
			f.write('I\n')
		else:
			f.write('%s\n' % (self.params['sym']))

		### CARD 6
		f.write('%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f\n' % (
			self.params['relmag'], self.params['apix'], 
			self.params['targetresidual'], self.params['residualthresh'], 
			self.params['cs'], self.params['kv'], 
			self.params['beamtiltx'], self.params['beamtilty']))

		### CARD 7
		### lp should be ~25 A for iflag 3 and ~12 A for iflag 1
	 	f.write('%.2f,%.2f,%.2f,%.2f,%.2f\n' % (
			self.params['reslimit'], self.params['hp'], 
			self.params['lp'], self.defaults['dfstd'], self.params['bfactor']))

		### CARD 8
		f.write('%s\n' % (self.stackfile))
		f.write('match\n')
		f.write('inparams.par\n')
		f.write('outparams.par\n')
		f.write('shift.par\n')

		# set relmag to -100 if no 3d reconstruction
		if norecon is True:
			reconrelmag=-100.0
		else:
			reconrelmag=0.0
		f.write('%.1f,0.0,0.0,0.0,0.0,0.0,0.0,0.0\n' %reconrelmag)
		f.write('workingvol\n')
		f.write('weights\n')
		f.write('odd\n')
		f.write('even\n')
		f.write('phasediffs\n')
		f.write('pointspread\n')
		f.write('EOF\n')
		f.write('\n')
		f.close()
		os.chmod(jobname,0755)

	#===============	
	def start(self):
		#set up directories
		self.params['workingdir'] = os.path.join(self.params['rundir'], "working")	
		apParam.createDirectory(self.params['workingdir'], msg=False)

		### create parameter file
		currentparam = self.setupParticleParams()
		
		self.stackdata = apStack.getOnlyStackData(self.params['stackid'])
		self.stackfile = os.path.join(self.stackdata['path']['path'], self.stackdata['name'])

		# set input parameter file if continuing a run
		self.currentvol = self.setupInitialModel()
		self.currentparam = os.path.join(self.params['rundir'], "params.0.par")

		## run frealign for number for refinement cycles
		for i in range(self.params['refcycles']):
			iternum = i+1
			if self.params['cluster'] is True:
				# create jobs
				apFrealign.createMultipleJobs(self.params)
				self.appendFrealignJob(jobfile)
				# run split jobs
				apFrealign.submitMultipleJobs(self.params)
				# combine results & create density
				apFrealign.combineMultipleJobs(self.params)
			else:
				### single node run
				jobfile = os.path.join(self.params['rundir'], self.params['runname']+'.job')
				self.createFrealignJob(jobfile)
				self.appendFrealignJob(jobfile)

			# copy density & parameter file to rundir
			self.params['itervol'] = os.path.join(self.params['rundir'],"threed."+str(self.params['iter'])+".mrc")
			self.params['iterparam'] = os.path.join(self.params['rundir'],"params."+str(self.params['iter'])+".par")
			shutil.copy(self.params['workingvol'], self.params['itervol'])
			shutil.copy(self.params['workingparam'], self.params['iterparam'])

			### calculate FSC
			emancmd = 'proc3d %s %s fsc=fsc.eotest.%d' % (evenvol, oddvol, self.params['iter'])
			apEMAN.executeEmanCmd(emancmd, verbose=True)

		print "Done!"

if __name__ =='__main__':
	frealign = frealignJob()
	frealign.start()
	frealign.close()
	
