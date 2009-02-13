#!/usr/bin/env python
import sys, os, glob
import shutil
import apParam
import apStack
import apVolume
import apCtf
from pyami import mrc
import threading
import glob
import apImagicFile
import appionScript
import apProject
import apDisplay
import apFrealign

#================
#================
class frealignJob(appionScript.AppionScript):
	#================
	def setupParserOptions(self):

		self.parser.set_usage("Usage: %prog -options")

		####card 1
		self.parser.add_option('--mode', dest="mode" , default = 1, type='int',
				       help = "refine and reconstruct")
		self.parser.add_option('--magrefine', dest="magrefine" , default = False,
				       help = "no magnification refinement")
		self.parser.add_option('--defocusrefine', dest="defocusrefine" , default = False,
				       help = "no defocus refinement")
		self.parser.add_option('--astigrefine', dest="astigrefine" , default = False,
				       help = "no astigmatism refinemet")
		self.parser.add_option('--fliptilt', dest="fliptilt" , default = False,
				       help = "no rotation of theta by 180 degrees")
		self.parser.add_option('--ewald', dest="ewald" , default = 0, type='int',
				       help = "no ewald curvature correction")
		self.parser.add_option('--matches', dest="matches" , default = True,
				       help = "write out particles with matching projections")
		self.parser.add_option('--history', dest="history" , default = False,
				       help = "write out history of itmax randomization trials")
		self.parser.add_option('--finalsym', dest="finalsym" , default = True,
				       help = "apply final real space symmetrization to beautify reconstruction")
		self.parser.add_option('--fomfilter', dest="fomfilter" , default = True,
				       help = "apply FOM filter to final reconstruction")
		self.parser.add_option('--fsc', dest="fsc" , default = 0, type='int',
				       help = "internall calculate FSC between even and odd particles")
	
		####card 2
		self.parser.add_option('--radius', dest="radius" , type='int',
				       help = "radius from center of particle to outer edge")
		self.parser.add_option('--iradius', dest="iradius" , default = 0, type='int',
				       help = "inner mask radius")
		self.parser.add_option('--apix', dest="apix" , type='float', help = "pixel size in angstroms")
		self.parser.add_option('--ampcontrast', dest="ampcontrast" , default = 0.07, type='float',
				       help = "amplitude contrast")
		self.parser.add_option('--maskthresh', dest="maskthresh" , default = 0.0, type='float',
				       help = "standard deviations above mean for masking of input model")
		self.parser.add_option('--phaseconstant', dest="phaseconstant" , default = 3.0,type='float',
				       help = "conversion constant for phase residual weighting of particles. 100 gives equal weighting")
		self.parser.add_option('--avgresidual', dest="avgresidual" , default = 75, type='int',
				       help = "average phase residual of all particles. used for weighting")
		self.parser.add_option('--ang', dest="ang" , default = 5, type='int',
				       help = "step size if using modes 3 and 4")
		self.parser.add_option('--itmax', dest="itmax" , default = 10, type='int',
				       help = "number of iterations of randomization. used for modes 2 and 4")
		self.parser.add_option('--maxmatch', dest="maxmatch" , default = 0, type='int',
				       help = "number of potential matches in a search that should be tested further in local refinement")
		
		####card 3
		self.parser.add_option('--psi', dest="psi" , default = 1, type='int',
				       help = "refine psi")
		self.parser.add_option('--theta', dest="theta" , default = 1, type='int',
				       help = "refine theta")
		self.parser.add_option('--phi', dest="phi" , default = 1, type='int',
				       help = "refine phi")
		self.parser.add_option('--deltax', dest="deltax" , default = 1, type='int',
				       help = "refine delta X")
		self.parser.add_option('--deltay', dest="deltay" , default = 1, type='int',
				       help = "refine delta Y")
		
		####card 4
		self.parser.add_option('--first', dest="first" , default = 1, type='int',
				       help = "first particle")
		self.parser.add_option('--last', dest="last" , type='int',
				       help = "last particle")
	
		####card 5
		self.parser.add_option('--sym', dest="sym" , help = "symmetry ")
	
		####card 6
		self.parser.add_option('--relmag', dest="relmag" , default = 1, type='float',
				       help = "relative magnification of dataset?")
		self.parser.add_option('--targetresidual', dest="targetresidual" , default = 10.0, type='float',
				       help = "target phase residual during refinement")
		self.parser.add_option('--residualthresh', dest="residualthresh" , default = 90.0, type='float',
				       help = "phase residual threshold cut-off")
		self.parser.add_option('--cs', dest="cs" , default = 2.0, type='float',
				       help = "spherical aberation")
		self.parser.add_option('--kv', dest="kv" , default = 120.0, type='float',
				       help = "accelerlating voltage")
		self.parser.add_option('--beamtiltx', dest="beamtiltx" , default = 0.0, type='float',
				       help = "beam tilt x (mrad)")
		self.parser.add_option('--beamtilty', dest="beamtilty" , default = 0.0, type='float',
				       help = "beam tilt y (mrad)")
	
		####card 7
		self.parser.add_option('--reslimit', dest="reslimit" , default = 10.0, type='float',  help = "resolution to which to limit the reconstruction")
		self.parser.add_option('--hp', dest="hp" , default = 100.0, type='float',
				       help = "upper limit for low resolution signal")
		self.parser.add_option('--lp', dest="lp" , default = 10.0, type='float',
				       help = "lower limit for high resolution signal")
		self.parser.add_option('--bfactor', dest="bfactor" , default = 0.0, type='float',
				       help = "bfactor to apply to particles before classification. 0.0 applies no bfactor.")
	
		####card 8
		self.parser.add_option('--stack', dest="stack" , default = 'start.mrc',
				       help = "input particles to be classified")
	
		####card 9
		self.parser.add_option('--matchstack', dest="matchstack" , default = 'match.mrc',
				       help = "output projection matches")
	
		####card 10
		self.parser.add_option('--inpar', dest="inpar" ,
				       help = "input particle parameter file")
	
		####card 11
		self.parser.add_option('--outpar', dest="outpar" , default = 'params.1.par',
				       help = "output particle parameter file")
		
		####card 12
		self.parser.add_option('--outshiftpar', dest="outshiftpar" , default = 'shift.par',
				       help = "output particle shift parameter file")
	
		####card 13
		self.parser.add_option('--invol', dest="invol" , default = 'threed.0.mrc',
				       help = "input reference volume")
		
		####card 14
		self.parser.add_option('--weight3d', dest="weight3d" , default = 'weights.mrc',
				       help = "???")
		
		####card 15
		self.parser.add_option('--oddvol', dest="oddvol" , default = 'odd.mrc',
				       help = "output odd volume")
		
		####card 16
		self.parser.add_option('--evenvol', dest="evenvol" , default = 'even.mrc',
				       help = "output even volume")
		
		####card 17
		self.parser.add_option('--outresidual', dest="outresidual" , default = 'phasediffs.mrc',
				       help = "3d phase residuals")
		
		####card 18
		self.parser.add_option('--pointspreadvol', dest="pointspreadvol" , default = 'pointspread.mrc',
				       help = "output 3d point spread function")


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
				       help="name of output volume", default = 'threed.1.mrc')
		self.parser.add_option('--proc', dest='proc', default=1, type='int',
				       help="number of processors")
		self.parser.add_option('--setuponly', dest='setuponly', default=False, action='store_true',
				       help="if setuponly is specified, everything will be set up but frealign will not be run")
		self.parser.add_option('--refcycles', dest='refcycles', type='int', default=1,
				       help="number of refinement iterations to perform")
		self.parser.add_option('--noctf', dest='noctf', default=False, action='store_true',
				       help="choose if frealign should not perform ctf correction")
	 
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
		
	#=====================
	def createMultipleJobs (params):
		params['jobs']=[]
		ptcls_per_job = params['last']/params['proc']
		remainder= params['last']%params['proc']
		lastparticle=0
		params['outparlst']=[]	
		for n in range(0,params['proc']):
			firstparticle=lastparticle+1
			lastparticle=firstparticle+ptcls_per_job-1
		
			if remainder > 0:
				lastparticle+=1
				remainder-=1
		
			jobname=("frealign.%d.job" % (n))
			params['jobs'].append(jobname)
			outparname=params['outpar']+'.'+str(n)
			params['outparlst'].append(outparname)
			print 'outparname is', outparname
			createFrealignJob(params, jobname, params['mode'], params['inpar'], outparname, firstparticle, lastparticle, norecon=True)

	def forceMrcHeader(array=None):
		'''
		Hack to force MRC header to something that frealign will accept.
		This may only be necessary on 64-bit machine
		'''
		h=mrc.newHeader()
		mrc.updateHeaderDefaults(h)
		if array is not None:
			mrc.updateHeaderUsingArray(h,array)
		h['byteorder']=0x4144
		return h

	def imagicToMrc(stackname,mrcname):
		stackdict=apImagicFile.readImagic(stackname)
		#force machine stamp integer
		print "forcing machine stamp"
		h=forceMrcHeader(array=stackdict['images'])
		mrc.write(stackdict['images'],mrcname, header=h)

	def fixMrcHeaderHack(involname, outvolname):
		a=mrc.read(involname)
		#force machine stamp integer
		print "forcing machine stamp"
		h=forceMrcHeader(array=a)
		mrc.write(a,outvolname,header=h)

	def runParallel(params):
		createMultipleJobs(params)
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
		combinefile=open(os.path.join(params['rundir'],combinedparams),'w')
		for outpar in params['outparlst']:
			f=open(os.path.join(params['rundir'],outpar), 'r')
			lines=f.readlines()
			f.close()

			for n in lines:
				if n[0] != 'C':
					combinefile.write(n)
				else:
					print "comment"
		combinefile.close()
		combinejobname="frealign.job" 
		createFrealignJob(params, combinejobname, 0, combinedparams, params['outpar'], params['first'], params['last'], norecon=False)
		command='frealign < ' + combinejobname
		print 'command is',command
		os.system(command)	

	def runSingle(params):
		jobname='frealign.job'
		createFrealignJob(params, jobname)
		command='freaalign < ' + jobname
		print 'command is',command
		os.system(command)
		
	def start(self):
		# if using parameters from previous reconstruction
		if self.params['reconiterid'] is not None:
			# get reference stackid
			self.params['compStackId'] = apStack.getStackIdFromIterationId(self.params['reconiterid'])

		#set up directories
		self.params['workingvol']="workingvol.mrc"
		self.params['workingdir']=os.path.join(self.params['rundir'],"working")	
		apParam.makedirs(self.params['workingdir'], mode=0755)
	
		
		self.stackdata = apStack.getOnlyStackData(self.params['stackid'])
		self.params['stackfile'] = os.path.join(self.stackdata['path']['path'],self.stackdata['name'])

		# check if the stack is made with defocal pairs
		self.params['defocpair'] = apStack.checkDefocPairFromStackId(self.params['stackid'])

		# check to see if input stack has to be converted to mrc
		stackext = os.path.splitext(self.params['stackfile'])[1]
		if stackext=='.hed' or stackext=='.img':
			apDisplay.printMsg('converting to IMAGIC stack to MRC stack...')
			apFrealign.imagicToMrc(self.params)

		#if no parameter file specified then generate input parameter file
		if self.params['inpar'] is None:
			apFrealign.generateParticleParams(self.params)

		else:
			apDisplay.printMsg("Using parameter file: "+self.params['inpar'])
			
		#get initial model path
		modeldata = apVolume.getModelFromId(self.params['modelid'])
		self.params['initmodel'] = os.path.join(modeldata['path']['path'],modeldata['name'])

		#create Frealign job(s)
		jobname = os.path.join(self.params['rundir'],self.params['runname']+'.job')
		apFrealign.createFrealignJob(self.params, jobname, norecon=False)

		#run frealign
#		os.chdir(params['workingdir'])
	
#		if not params['setuponly']:
#			if params['proc'] > 1:
#				runParallel(params)
#			else:
#				runSingle(params)
			
			#copy results back to run dir
#			shutil.copy(params['workingvol'],(os.path.join(params['rundir'],params['outvol'])))

		print "Done!"

if __name__ =='__main__':
	frealign = frealignJob()
	frealign.start()
	frealign.close()
	
