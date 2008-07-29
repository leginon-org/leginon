#!/usr/bin/env python
import sys, os, glob
import shutil
import apParam
from optparse import OptionParser
import apDB
import apStack
import apVolume
import apCtf
from pyami import mrc
import threading
import glob

apdb=apDB.apdb
workingstackname="start.hed"

def createMultipleJobs (params):
	params['jobs']=[]
	ptcls_per_job = params['last']/params['proc']
	remainder= params['last']%params['proc']
	lastparticle=0
	params['outparlst']=[]	
	for n in range(0,params['proc']):
		#print "remainder", remainder		
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

def createFrealignJob (params, jobname, mode, inparname, outparname, firstparticle, lastparticle, norecon=False):

	if norecon:
		#relmag=-100.0
		relmag=1
	else:
		relmag=params['relmag']
	
	f=open(jobname,'w')

	f.write('%s,%d,%s,%s,%s,%s,%d,%s,%s,%s,%s,%d\n' % ('M', mode, params['magrefine'], params['defocusrefine'], params['astigrefine'], params['fliptilt'], params['ewald'], params['matches'], params['history'], params['finalsym'], params['fomfilter'], params['fsc']))
	f.write('%d,%d,%.3f,%.2f,%.2f,%d,%d,%d,%d,%d\n' % (params['radius'], params['iradius'], params['apix'], params['ampcontrast'], params['maskthresh'], params['phaseconstant'], params['avgresidual'], params['ang'], params['itmax'], params['maxmatch']))
	f.write('%d %d %d %d %d\n' % (params['psi'], params['theta'], params['phi'], params['deltax'], params['deltay']))
	f.write('%d, %d\n' % (firstparticle, lastparticle))
	f.write('%s\n' % (params['sym']))
	f.write('%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f\n' % (relmag, params['dstep'], params['targetresidual'], params['residualthresh'], params['cs'], params['kv'], params['beamtiltx'], params['beamtilty']))
	f.write('%.2f,%.2f,%.2f,%.2f\n' % (params['reslimit'], params['hp'], params['lp'], params['bfactor']))
	f.write('%s\n' % (os.path.join(params['rundir'],params['stack'])))
	f.write('%s\n' % (os.path.join(params['workingdir'],params['matchstack'])))
	f.write('%s\n' % (os.path.join(params['rundir'],inparname)))
	f.write('%s\n' % (os.path.join(params['rundir'],outparname)))
	f.write('%s\n' % (os.path.join(params['workingdir'],params['outshiftpar'])))
	f.write('0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0\n')
	f.write('%s\n' % (os.path.join(params['workingdir'],params['workingvol'])))
	f.write('%s\n' % (os.path.join(params['workingdir'],params['weight3d'])))
	f.write('%s\n' % (os.path.join(params['workingdir'],params['oddvol'])))
	f.write('%s\n' % (os.path.join(params['workingdir'],params['evenvol'])))
	f.write('%s\n' % (os.path.join(params['workingdir'],params['outresidual'])))
	f.write('%s\n' % (os.path.join(params['workingdir'],params['pointspreadvol'])))
	f.close()
		
def setupParserOptions():
	parser=OptionParser()
	#### card 1
	parser.add_option('--format', dest="format" , default = 'M', help = "MRC")
	parser.add_option('--mode', dest="mode" , default = 1, type='int', help = "refine and reconstruct")
	parser.add_option('--magrefine', dest="magrefine" , default = 'F', help = "no magnification refinement")
	parser.add_option('--defocusrefine', dest="defocusrefine" , default = 'F', help = "no defocus refinement")
	parser.add_option('--astigrefine', dest="astigrefine" , default = 'F', help = "no astigmatism refinemet")
	parser.add_option('--fliptilt', dest="fliptilt" , default = 'F', help = "no rotation of theta by 180 degrees")
	parser.add_option('--ewald', dest="ewald" , default = 0, type='int', help = "no ewald curvature correction")
	parser.add_option('--matches', dest="matches" , default = 'T', help = "write out particles with matching projections")
	parser.add_option('--history', dest="history" , default = 'F', help = "write out history of itmax randomization trials")
	parser.add_option('--finalsym', dest="finalsym" , default = 'F', help = "apply final real space symmetrization to beautify reconstruction")
	parser.add_option('--fomfilter', dest="fomfilter" , default = 'F', help = "apply FOM filter to final reconstruction")
	parser.add_option('--fsc', dest="fsc" , default = 0, type='int', help = "internall calculate FSC between even and odd particles")
	
	####card 2
	parser.add_option('--radius', dest="radius" , type='int', help = "radius from center of particle to outer edge")
	parser.add_option('--iradius', dest="iradius" , default = 0, type='int', help = "inner mask radius")
	parser.add_option('--apix', dest="apix" , type='float', help = "pixel size in angstroms")
	parser.add_option('--ampcontrast', dest="ampcontrast" , default = 0.07, type='float', help = "amplitude contrast")
	parser.add_option('--maskthresh', dest="maskthresh" , default = 0.0, type='float', help = "standard deviations above mean for masking of input model")
	parser.add_option('--phaseconstant', dest="phaseconstant" , default = 100,type='int', help = "conversion constant for phase residual weighting of particles. 100 gives equal weighting")
	parser.add_option('--avgresidual', dest="avgresidual" , default = 35, type='int', help = "average phase residual of all particles. used for weighting")
	parser.add_option('--ang', dest="ang" , default = 200, type='int', help = "step size if using modes 3 and 4")
	parser.add_option('--itmax', dest="itmax" , default = 50, type='int', help = "number of iterations of randomization. used for modes 2 and 4")
	parser.add_option('--maxmatch', dest="maxmatch" , default = 10, type='int', help = "number of potential matches in a search that should be tested further in local refinement")
	
	####card 3
	parser.add_option('--psi', dest="psi" , default = 1, type='int', help = "refine psi")
	parser.add_option('--theta', dest="theta" , default = 1, type='int', help = "refine theta")
	parser.add_option('--phi', dest="phi" , default = 1, type='int',help = "refine phi")
	parser.add_option('--deltax', dest="deltax" , default = 1, type='int', help = "refine delta X")
	parser.add_option('--deltay', dest="deltay" , default = 1, type='int', help = "refine delta Y")
	
	####card 4
	parser.add_option('--first', dest="first" , default = 1, type='int', help = "first particle")
	parser.add_option('--last', dest="last" , default = 200, type='int', help = "last particle")
	
	####card 5
	parser.add_option('--sym', dest="sym" , default = 'I', help = "symmetry ")
	
	####card 6
	parser.add_option('--relmag', dest="relmag" , default = 1, type='float', help = "relative magnification of dataset?")
	#parser.add_option('--dstep', dest="dstep" , default = 14.0, type='float', help = "densitometer step size")
	parser.add_option('--targetresidual', dest="targetresidual" , default = 25.0, type='float', help = "target phase residual during refinement")
	parser.add_option('--residualthresh', dest="residualthresh" , default = 90.0, type='float', help = "phase residual threshold cut-off")
	parser.add_option('--cs', dest="cs" , default = 2.0, type='float', help = "spherical aberation")
	parser.add_option('--kv', dest="kv" , default = 300.0, type='float', help = "accelerlating voltage")
	parser.add_option('--beamtiltx', dest="beamtiltx" , default = 0.0, type='float', help = "beam tilt x (mrad)")
	parser.add_option('--beamtilty', dest="beamtilty" , default = 0.0, type='float', help = "beam tilt y (mrad)")
	
	####card 7
	parser.add_option('--reslimit', dest="reslimit" , default = 10.0, type='float',  help = "resolution to which to limit the reconstruction")
	parser.add_option('--hp', dest="hp" , default = 500.0, type='float', help = "upper limit for low resolution signal")
	parser.add_option('--lp', dest="lp" , default = 10.0, type='float', help = "lower limit for high resolution signal")
	parser.add_option('--bfactor', dest="bfactor" , default = 0.0, type='float', help = "bfactor to apply to particles before classification. 0.0 applies no bfactor.")
	
	####card 8
	parser.add_option('--stack', dest="stack" , default = 'start.mrc', help = "input particles to be classified")
	
	####card 9
	parser.add_option('--matchstack', dest="matchstack" , default = 'match.mrc', help = "output projection matches")
	
	####card 10
	parser.add_option('--inpar', dest="inpar" , default = 'params.0.par', help = "input particle parameter file")
	
	####card 11
	parser.add_option('--outpar', dest="outpar" , default = 'params.1.par', help = "output particle parameter file")

	####card 12
	parser.add_option('--outshiftpar', dest="outshiftpar" , default = 'shift.par', help = "output particle shift parameter file")
	
	####card 13
	parser.add_option('--invol', dest="invol" , default = 'threed.0.mrc', help = "input reference volume")
	
	####card 14
	parser.add_option('--weight3d', dest="weight3d" , default = 'weights.mrc', help = "???")
	
	####card 15
	parser.add_option('--oddvol', dest="oddvol" , default = 'odd.mrc', help = "output odd volume")
	
	####card 16
	parser.add_option('--evenvol', dest="evenvol" , default = 'even.mrc', help = "output even volume")
	
	####card 17
	parser.add_option('--outresidual', dest="outresidual" , default = 'phasediffs.mrc', help = "3d phase residuals")
	
	####card 18
	parser.add_option('--pointspreadvol', dest="pointspreadvol" , default = 'pointspread.mrc', help = "output 3d point spread function")




	#### Appion params
	parser.add_option('--stackid', dest='stackid', help="stack id from database")
	parser.add_option('--mrchack', dest='mrchack', action='store_true', help="hack to fix machine stamp in mrc header")
	parser.add_option('--outvol', dest='outvol', help="name of output volume", default = 'threed.1.mrc')
	parser.add_option('--proc', dest='proc', default=1, type='int', help="number of processors")
	parser.add_option('--setuponly', dest='setuponly', default=False, action='store_true', help="if setuponly is specified, everything will be set up but frealign will not be run")
	 
	return parser

def convertParserToJSHelp(parser):
	for n in parser.option_list[1:]:
		name=n.dest
		help=n.help
		print ("\t\t'%s' : '%s',\n" % (name, help)),

def convertParserToJSDefaults(parser):
	for n in parser.option_list[1:]:
		name=n.dest
		default=n.default
		if default == 'T' or ((name=='psi' or name=='phi' or name=='theta' or name=='deltax' or name=='deltay') and default==1):
			print("      obj.%s1.checked = true;" % (name))
		elif default == 'F' or ((name=='psi' or name=='phi' or name=='theta' or name=='deltax' or name=='deltay') and default==0):
			print("      obj.%s1.checked = false;" % (name))
		else:
			print("      obj.%s1.value = '%s';" % (name,default))		

def writeParticleParamLine(particleparams, fileobject):
	p=particleparams
	fileobject.write("%7d  %6.2f  %6.2f  %6.2f  %6.2f  %6.2f  %7.1f  %3d  %7.1f  %7.1f  %6.2f  %5.2f  %6.2f\n" % (p['ptclnum'],p['psi'],p['theta'],p['phi'],p['shx'],p['shy'],p['mag'],p['film'],p['df1'],p['df2'],p['angast'],p['presa'],p['dpres']))

def generateParticleParams(params):
	stackdata=apStack.getStackParticlesFromId(params['stackid'])
	apix=params['apix']
	particleparams={}
	f=open(params['inpar'],'w')
	print "Writing out particle parameters"
	for particle in stackdata:
		imagedata=particle['particle']['image']
		ctfdata, confidence=apCtf.getBestCtfValueForImage(imagedata)
		particleparams['ptclnum']=particle['particleNumber']
		particleparams['df1']=ctfdata['defocus1']*1e10
		particleparams['df2']=ctfdata['defocus2']*1e10
		particleparams['angast']=ctfdata['angle_astigmatism']
		particleparams['mag'] = (params['dstep']*10000)/apix #calculate mag from apix and step sizels
		particleparams['psi']=0
		particleparams['theta']=0
		particleparams['phi']=0
		particleparams['shx']=0
		particleparams['shy']=0
		particleparams['film']=1
		particleparams['presa']=0
		particleparams['dpres']=0
		writeParticleParamLine(particleparams,f)
	f.close()
	
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
	stackdict=apStack.readImagic(stackname)
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

class FrealignJob(threading.Thread):
	def __init__ (self, command):
		threading.Thread.__init__(self)
		self.command = command
	def run (self):
		print self.command
		os.system(self.command)
		
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
	os.system(command)	

def runSingle(params):
	jobname='frealign.job'
	createFrealignJob(params, jobname, params['mode'], params['inpar'], params['outpar'], params['first'], params['last'], norecon=False)
	command='frealign < ' + jobname
	os.system(command)
		
if __name__ =='__main__':

	#write to log file
	apParam.writeFunctionLog(sys.argv)
	
	#set up parameters
	parser=setupParserOptions()
	params=apParam.convertParserToParams(parser)
	
	#force densitometer step size to be 14.0. This param is required, so we fake it for CCD
	params['dstep']=14.0
	params['iter']=3

	#set up directories
	params['rundir']=os.getcwd()
	params['workingvol']="workingvol.mrc"
	params['workingdir']=os.path.join(params['rundir'],"working")	
	print params['workingdir']
	apParam.makedirs(params['workingdir'], mode=0755)
	
	#if format is type "I" then convert imagic stack to mrc
	if params['format']=='I':
		print "Converting imagic stack to mrc stack"
		newstackname=params['stack'].split('.')[0] + '.mrc'
		imagicToMrc(params['stack'],newstackname)
		params['stack']=newstackname


	#use hack to "fix" mrc header
	if params['mrchack']:
		print "Hack: Setting machine stamp on invol MRC header"
		newinvol=os.path.splitext(params['invol'])[0] + '.fix.mrc'
		fixMrcHeaderHack(params['invol'],newinvol)
		params['invol']=newinvol
	
	#if mode is type "search" then generate input parameter file
	if params['mode']==3 or params['mode']==4:
		generateParticleParams(params)
	
	
	#copy necessary files to working dir
	shutil.copy(params['invol'],os.path.join(params['workingdir'],params['workingvol']))
	

	#run frealign
	os.chdir(params['workingdir'])
	
	if not params['setuponly']:
		if params['proc'] > 1:
			runParallel(params)
		else:
			runSingle(params)
			
		#copy results back to run dir
		shutil.copy(params['workingvol'],(os.path.join(params['rundir'],params['outvol'])))

	print "Done!"
