#!/usr/bin/env python
import os
import sys
import math
import time
import shutil
import subprocess
import optparse

### Please do not make classes or import any appion libraries or pointlessly change variable names.

def setupParserOptions(parser):

	#parser.set_usage("Usage: %prog -options")
	####card 1
	parser.add_option('--mode', dest="mode" , default = 1, type='int', 
		help = "refine and reconstruct. xxx more here")
	parser.add_option("--fmag", dest="fmag", default=False,
		action="store_true", help="Refine the magnification")
	parser.add_option("--fdef", dest="fdef", default=False,
		action="store_true", help="Refine the defocus")
	parser.add_option("--fastig", dest="fastig", default=False,
		action="store_true", help="Refine the defocus astigmatism")
	parser.add_option("--fpart", dest="fpart", default=False,
		action="store_true", help="Refine the defocus per particle")
	parser.add_option('--fcref', dest="fcref", default=False,
		action="store_true", help="apply FOM filter to final reconstruction")
	parser.add_option('--iblow', dest="iblow", default=1,
		action="store_true", help="1,2, or 4. Padding factor for reference structure. iblow=4 requires the most memory but results in the fastest search & refinement.")

	####card 2
	parser.add_option('--mask', dest="mask", type='float',
		help="mask from center of particle to outer edge")
	parser.add_option('--imask', dest="imask", default=0, type='float',
		help="inner mask radius")
	parser.add_option('--wgh', dest="wgh", default=0.07, type='float',
		help="amplitude contrast")
	parser.add_option('--xstd', dest="xstd", default=0.0, type='float',
		help="standard deviations above mean for masking of input model")
	parser.add_option('--pbc', dest="pbc", default=100.0, type='float',
		help="conversion constant for phase residual weighting of particles. 100 gives equal weighting")
	parser.add_option('--boff', dest="boff", default=75, type='int',
		help="average phase residual of all particles. used for weighting")
	parser.add_option('--dang', dest="dang", type='int', default=5, 
		help="step size if using modes 3 and 4")
	parser.add_option('--itmax', dest="itmax", default=10, type='int',
		help="number of iterations of randomization. used for modes 2 and 4")
	parser.add_option('--ipmax', dest="ipmax", default=0, type='int',
		help="number of potential matches in a search that should be tested further in local refinement")

	####card 4
	parser.add_option('--last', dest="last", type='int',
		help="last particle to process")

	####card 5
	parser.add_option('--sym', dest="sym", help="symmetry. Options are I, O, Dx (e.g. D7), or Cx (e.g. C7)")

	####card 6
	parser.add_option('--target', dest="target", default=10.0, type='float',
		help="target phase residual during refinement")
	parser.add_option('--thresh', dest="thresh", default=90.0, type='float',
		help="phase residual threshold cut-off")
	parser.add_option('--cs', dest="cs", default=2.0, type='float',
		help="spherical aberation")
	parser.add_option('--kv', dest="kv", default=120.0, type='float',
		help="accelerlating voltage")

	####card 7
	parser.add_option('--rrec', dest="rrec", default=10.0, type='float',  
		help="resolution to which to limit the reconstruction")
	parser.add_option('--hp', dest="hp", default=100.0, type='float',
		help="upper limit for low resolution signal")
	parser.add_option('--lp', dest="lp", default=10.0, type='float',
		help="lower limit for high resolution signal")
	parser.add_option('--rbfact', dest="rbfact", default=0, type='float',
		help="rbfact to apply to particles before classification. 0.0 applies no rbfact.")

	####card 10
	parser.add_option('--inpar', dest="inpar",
		help="Input particle parameters.")
		
	####card 11
	parser.add_option('--outpar', dest="outpar",
		help="Output particle parameters.")

	#### Appion params
	parser.add_option('--noctf', dest='noctf', default=False, action='store_true',
		help="choose if frealign should not perform ctf correction")
	parser.add_option('--rundir', dest='rundir', default=os.getcwd(),
		help="directory in which to run job")
	parser.add_option('--apix', dest='apix', type='float',
		help="pixel size of the stack")
	parser.add_option('--maxprocs', dest='maxprocs', type='int',default=20,
		help="maximum number of processors to use")
	parser.add_option('--invol', dest='invol', 
		help="input volume")
	parser.add_option('--outvol', dest='outvol', 
		help="output volume")
	parser.add_option('--launcher', dest='launcher', default=None,
		help="job launcher, e.g. qsub or msub")
	parser.add_option('--queue', dest='queue', default=None,
		help="job queue, sometimes required depending on set up")
	parser.add_option('--setuponly', dest='setuponly', default=False, action='store_true',
		help="setup without executing")
	parser.add_option('--ppn', dest='ppn', default=8, type='int',
		help='processors per node')
	parser.add_option('--wallclock', dest='wallclock', default=4, type='int',
		help='time limit for processing jobs')
	
	
def parserToParams(parser):
	(options, args) = parser.parse_args()
	if len(args) > 0:
		print "Unknown command line arguments: ", args
		sys.exit()	
	if len(sys.argv) < 2:
		parser.print_help()
		parser.error("no options defined")
	params={}
	for i in parser.option_list:
		if isinstance(i.dest,str):
			params[i.dest] = getattr(options, i.dest)
	
	return params
	
def recordLog(args):
	f=open('runFrealign.log','a')
	[f.write('%s '% arg) for arg in args]
	f.write('\n')
	f.close()

def checkConflicts(params):
	if params['mask'] is None:
		#fill in later
		pass
	if params['noctf'] is True:
		 self.params['wgh'] = -1.0
#	if self.params['nodes'] > 1 and self.params['cluster'] is False:
#		apDisplay.printError("cluster mode must be enabled to run on more than 1 node")
#	if self.params['ppn'] is None:
#		if self.params['cluster'] is True:
#			apDisplay.printError("you must define ppn for cluster mode")
#		self.params['ppn'] = apParam.getNumProcessors()
#		apDisplay.printMsg("Setting number of processors to %d"%(self.params['ppn']))
#	self.params['nproc'] = self.params['nodes']*self.params['ppn']
	### get the symmetry data
	if params['sym'] is None:
		print "Error: Symmetry was not defined"
		sys.exit()

def bc(val):
	""" Convert bool to single letter T or F """
	if val is True:
		return "T"
	return "F"

def createFrealignJobFile(params, jobfile, outparname, first=1, last=None, recon=True, logfile=None):

	### hard coded parameters
	defaults = {
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
		defaults['fstat'] = True
		iflag=0
		ppn=params['ppn']
		nodes=1
		inpar=params['outpar']
	else:
		iflag=params['mode']
		procs=1
		nodes=1
		ppn=1
		inpar=params['inpar']
	procs=nodes*ppn

	if last is None:
		last = params['last']
	if logfile is None:
		logfile = "frealign.out"

	f = open(jobfile, 'w')
	f.write('\n')
	f.write('#!/bin/bash\n')
	f.write('#MOAB -l nodes=%d:ppn=%d\n' % (nodes,ppn))
	f.write('#MOAB -l walltime=%d:00:00\n\n' % params['wallclock'])
	f.write('export NCPUS=%d\n\n'%(procs))
	f.write('cd %s\n\n' % params['rundir'])

	f.write('# IFLAG %d\n'%(iflag))
	f.write('# PARTICLES %d THRU %d\n'%(first, last))
	f.write('# RECON %s\n'%(recon))
	f.write('\n')
	f.write('### START FREALIGN ###\n')
	f.write('frealign.exe << EOF > '+logfile+'\n')

	### CARD 1
		
	f.write('%s,%d,%s,%s,%s,%s,%d,%s,%s,%s,%d,%s,%d\n' % (
		params['cform'],
		iflag, 
		bc(params['fmag']), bc(params['fdef']), #T/F refinements
		bc(params['fastig']), bc(params['fpart']), #T/F refinements
		defaults['iewald'], 
		bc(defaults['fbeaut']), bc(params['fcref']), bc(defaults['fmatch']), 
		defaults['ifsc'],
		bc(defaults['fstat']), params['iblow']))

	### CARD 2
	f.write('%d,%d,%.3f,%.2f,%.2f,%d,%d,%d,%d,%d\n' % (
		params['mask'], params['imask'], 
		params['apix'], params['wgh'], 
		params['xstd'], params['pbc'], 
		params['boff'], params['dang'], params['itmax'], params['ipmax']))

	### CARD 3 fixing of an Euler angle or shift parameters, 1 = refine all
	f.write('%d %d %d %d %d\n' % (1,1,1,1,1))


	### CARD 4 -- particle limits
	f.write('%d, %d\n' % (first, last))

	### CARD 5
	if params['sym'].lower() == 'icos':
		f.write('I\n')
	else:
		f.write('%s\n' % (params['sym']))

	### CARD 6
	f.write('%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f\n' % (
		1.0, params['apix'], 
		params['target'], params['thresh'], 
		params['cs'], params['kv'], 
		defaults['beamtiltx'], defaults['beamtilty']))

	### CARD 7
	### lp should be ~25 A for iflag 3 and ~12 A for iflag 1
	f.write('%.2f,%.2f,%.2f,%.2f,%.2f\n' % (
		params['rrec'], params['hp'], 
		params['lp'], defaults['dfstd'], params['rbfact']))

	### CARD 8
	f.write('%s\n'%(params['stackfile']))
	f.write('match\n')
	f.write('%s\n'%(inpar))
	f.write('%s\n' % (outparname))
	f.write('shift.par\n')

	if recon is False:
		# set relmag to -100, if no 3d reconstruction is desired for parallel mode
		reconrelmag = -100.0
	else:
		reconrelmag = 0.0
	f.write('%.1f,0.0,0.0,0.0,0.0,0.0,0.0,0.0\n' %reconrelmag)
	f.write('%s\n'%(params['working']))
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
def createMultipleJobs(params):
	"""
	Create multiple job files for frealign reconstruction
	"""
	### create script that will launch all mpi scripts
#	iterdir = "iter%03d"%(iternum)
#	iterjobfile = 'frealign.iter%03d.run.sh'%(iternum)

	#frscript = os.path.join(workdir,'frealign.$PBS_VNODENUM.sh')
	#fr.write("sh "+frscript+"\n")

	### create scripts
	partperjob = params['last']//params['maxprocs']
	r = params['last']%params['maxprocs']
	lastp = 0
	params['outparlst'] = []
	params['joblst']=[]
	params['combinejob']='frealign.combine.sh'
	for n in range(params['maxprocs']):
		firstp = lastp + 1
		lastp = firstp + partperjob - 1
		if r > 0:
			lastp+=1
			r-=1

		#print procdir

		jobname=("frealign.proc%03d.sh" % (n))
		params['joblst'].append(jobname)
		outparname=params['outpar']+'.'+str(n)
		params['outparlst'].append(outparname)
		createFrealignJobFile(params, jobname, outparname, firstp, lastp, logfile='frealign'+str(n)+'.out', recon=False)
	createFrealignJobFile(params,params['combinejob'], 'combine.par', 1, params['last'], logfile='frealign.combine.out', recon=True)


def combineParameterFiles(params):
	"""
	combine all the parameter files
	"""
	outpar = open(params['outpar'], 'w')
	totparams=0
	for p in params['outparlst']:
		f=open(p)
		lines=f.readlines()
		f.close()
		for line in lines:
			if line[0]!='C':
				outpar.write(line)
				totparams+=1
	outpar.close()
	if totparams!=params['last']:
		print "Error: The number of particle parameters (",totparams,")does not equal the total number of particles(",params['last'],")"
		sys.exit()

def launchAlignJobs(params):
	jobids=[]
	for job in params['joblst']:
		jobids.append(launchJob(params,job))
	return jobids

def launchJob(params, jobname):
	cmd=[]
	if params['launcher'] is not None:
		cmd.append(params['launcher'])
	if params['queue'] is not None:
		cmd.append('-q')
		cmd.append(params['queue'])
	cmd.append(jobname)
	print cmd
	proc=subprocess.Popen(cmd,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	proc.wait()
	if params['launcher'] is not None:
		jobid=proc.stdout.readlines()[1].strip()
	else:
		jobid=proc.stdout.readlines()
	return jobid

def checkJobs(params,jobids):
	running=True
	while running:
		cmd=[params['qstat']]
		print cmd
		proc=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
		proc.wait()
		lines=proc.stdout.readlines()
	
		running=False
		for line in lines:
			words=line.split()
			if len(words) > 0 and (words[0] in jobids):
				print words[0], jobids			
				running=True
				print "waiting 5 minutes for jobs to finish"
				time.sleep(300)
				break

def copyImagic(srcroot,destroot):
	shutil.copy(srcroot+'.hed',destroot+'.hed')
	shutil.copy(srcroot+'.img',destroot+'.img')
		

##===============
#def setIBLOW(self):
#	"""
#	IBLOW expands the volume in memory, 
#	larger is faster, but needs more mem; 
#	can be 1, 2 or 4
#	"""
#	self.iblow = 4
#	if self.calcMemNeeded() > 4e9:
#		self.iblow = 2
#	if self.calcMemNeeded() > 4e9:
#		self.iblow = 1
#	apDisplay.printMsg("IBLOW set to %d, requiring %s memory"
#		%(self.iblow, apDisplay.bytes(self.calcMemNeeded())))
#
##===============
#def calcMemNeeded(self):
#	### from frealign paper
#	nn1 = self.boxsize
#	nnbig = nn1 * self.iblow
#	memneed = 24 * nn1**3 + 4 * nnbig**3 + 200e6
#
#	### multiply by number of procs per node
#	memneed *= self.params['ppn']
#
#	## double it just in case
#	memneed *= 2.0
#
#	return memneed
#
#

if __name__ =='__main__':
	
	print "\n\n"
	#setup
	parser=optparse.OptionParser()
	setupParserOptions(parser)
	params=parserToParams(parser)
	recordLog(sys.argv)
	
	#defaults for now
	params['stackfile']='start.hed'
	params['qstat']='showq'
	

	#create working volume
	print "Creating working volume"
	extension=params['invol'].split('.')[-1]
	if extension=='mrc':
		params['cform']='M'
		params['working']='working.mrc'
		shutil.copyfile(params['invol'],params['working'])
	elif extension=='hed' or extension==['img']:
		params['cform']='I'
		params['working']='working.hed'
		imagicroot=os.path.splitext(params['invol'])[0]
		copyImagic(imagicroot,'working')
	else:
		print "Warning: Assuming SPIDER format."
		params['cform']='S'
		params['working']='working.spi'		
		shutil.copyfile(params['invol'],params['working'])
	
	#create jobs
	createMultipleJobs(params)
	
	#launch jobs
	if params['setuponly'] is False:
		jobids=launchAlignJobs(params)
		print "Align jobs are", jobids
		
		if params['launcher'] is not None:  #only run this if launcher is specified because non cluster option waits for individual jobs to finish
			checkJobs(params,jobids)		

		#combine params
		combineParameterFiles(params)
	
		#launch recon job
		print "Launching reconstruction job"
		combinejob=[]
		combinejob.append(launchJob(params,params['combinejob']))
		print "Reconstruction job is",combinejob
		if params['launcher'] is not None:
			checkJobs(params,combinejob)

		#copy new volume to outvol
		print "Copying working volume to outvol"
		if params['cform']=='M' or params['cform']=='S':
			shutil.copyfile(params['working'],params['outvol'])
		elif params['cform']=='I':
			imagicroot=os.path.splitext(params['working'])[0]
			outimagicroot=os.path.splitext(params['outvol'])[0]
			copyImagic(imagicroot, outimagicroot)


	print "Done!"
