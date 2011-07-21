#python
import os
import math
import numpy
import shutil
import subprocess
#pyami
from pyami import mrc
#appionlib
from appionlib import apCtf
from appionlib import apStack
from appionlib import apDisplay
from appionlib import appiondata
from appionlib import apDefocalPairs
from appionlib import apRecon

#=====================
def parseFrealignParamFile(paramfile):
	"""
	parse a typical FREALIGN parameter file from v8.08
	"""
	if not os.path.isfile(paramfile):
		apDisplay.printError("Parameter file does not exist: %s"%(paramfile))

	### cannot assume spaces will separate columns.
	#0000000001111111111222222222233333333334444444444555555555566666666667777777777888888888899999999990000000000
	#1234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789
	#     24  219.73   84.00  299.39   15.33  -17.51  10000.     1  27923.7  27923.7  -11.41   0.00    0.00
	f = open(paramfile, "r")
	parttree = []
	apDisplay.printMsg("Processing parameter file: %s"%(paramfile))
	for line in f:
		sline = line.strip()
		if sline[0] == "C":
			### comment line
			continue
		partdict = {
			'partnum': int(line[0:7].strip()),
			'euler1': float(line[8:15]),
			'euler2': float(line[16:23]),
			'euler3': float(line[24:31]),
			'shiftx': float(line[32:39]),
			'shifty': float(line[40:47]),
			'phase_residual': float(line[88:94]),
		}
		parttree.append(partdict)
	f.close()
	if len(parttree) < 2:
		apDisplay.printError("No particles found in parameter file %s"%(paramfile))


	apDisplay.printMsg("Processed %d particles"%(len(parttree)))
	return parttree



#===============
def generateParticleParams(params,initparfile='params.0.par'):
	params['inpar']=os.path.join(params['rundir'],initparfile)
	apDisplay.printMsg("Creating parameter file: "+params['inpar'])
	params['mode']=3
	stackdata=apStack.getStackParticlesFromId(params['stackid'])
	particleparams={}
	f=open(params['inpar'],'w')
	params['noClassification']=0
	if params['reconiterid']:
		iterdata = apRecon.getRefineIterDataFromIterationId(params['reconiterid'])
		eman_sym_name = iterdata['symmetry']['eman_name']
		
	print "Writing out particle parameters"
	if 'last' not in params:
		params['last'] = len(stackdata)
	for particle in stackdata[:params['last']]:
		# defaults
		particleparams['ptclnum']=particle['particleNumber']
		particleparams['psi']=0
		particleparams['theta']=0
		particleparams['phi']=0
		particleparams['df1']=0.1 # workaround if no ctf correction
		particleparams['df2']=0.1 # set defocus to 0.1 Angstroms
		particleparams['angast']=0.0
		particleparams['mag'] = 10000 # workaround to get around dstep
		particleparams['shx']=0
		particleparams['shy']=0
		particleparams['film']=1
		particleparams['presa']=0
		particleparams['dpres']=0

		imagedata=particle['particle']['image']
		if params['noctf'] is False:
			if params['defocpair'] is True:
				imagedata = apDefocalPairs.getDefocusPair(imagedata)
			# first see if there are ctf values
			ctfdata, confidence=apCtf.getBestCtfValueForImage(imagedata, msg=False)
			if ctfdata is None:
				ctfdata, confidence=apCtf.getBestCtfValueForImage(imagedata, msg=False)
			if ctfdata is not None:
				# use defocus & astigmatism values
				particleparams['df1']=abs(ctfdata['defocus1']*1e10)
				particleparams['df2']=abs(ctfdata['defocus2']*1e10)
				particleparams['angast']=-ctfdata['angle_astigmatism']

		# if using parameters from previous reconstruction
		if params['reconiterid'] is not None:
			params['mode']=1
			getStackParticleEulersForIteration(params,particle['particleNumber'])
			fr_eulers = convertEmanEulersToFrealign(params['eman_orient'])
			e1 = fr_eulers['phi']
			e2 = fr_eulers['theta']
			e3 = fr_eulers['psi']
			# if icos, rotate eulers to 3dem standard orientation
			if eman_sym_name.lower == 'icos':
				newEulers = sumEulers([90,-31.7174744,0],[e1,e2,e3])
				fr_eulers['phi']=newEulers[0]
				fr_eulers['theta']=newEulers[1]
				fr_eulers['psi']=newEulers[2]
			particleparams['psi'] = fr_eulers['psi']
			particleparams['theta'] = fr_eulers['theta']
			particleparams['phi'] = fr_eulers['phi']
			particleparams['shx']=params['eman_orient']['shiftx']
			particleparams['shy']=params['eman_orient']['shifty']
			if params['eman_orient']['mirror'] is True:
				particleparams['shx']*=-1
		writeParticleParamLine(particleparams,f)
	f.close()

#===============
def writeParticleParamLine(particleparams, fileobject):
	p=particleparams
	fileobject.write("%7d%8.3f%8.3f%8.3f%8.3f%8.3f%9.1f%5d%9.1f%9.1f%8.2f%7.2f%8.2f\n" 
		% (p['ptclnum'],p['psi'],p['theta'],p['phi'],p['shx'],p['shy'],p['mag'],
		p['film'],p['df1'],p['df2'],p['angast'],p['presa'],p['dpres']))

#===============
def createFrealignJob (params, jobname, nodenum=None, mode=None, inpar=None, invol=None, first=None, last=None, norecon=False):

	if mode is None:
		mode=params['mode']
	if inpar is None:
		inpar = params['inpar']
	if invol is None:
		invol = params['initmodel']
	if first is None:
		first=params['first']
	if last is None:
		last=params['last']

	# get angular increment for search, if none set a default
	ang = params['ang']
	if ang is None:
		ang=5

	# set relmag to -100 if no 3d reconstruction
	if norecon is True:
		reconrelmag=-100.0
	else:
		reconrelmag=0.0

	f=open(jobname,'w')
	f.write("#!/bin/csh\n")

	# first copy files
	f.write('cd %s\n' % params['rundir'])
	f.write('cd working\n')
	if nodenum is not None:
		workdir = "sub"+str(nodenum)
		f.write('/bin/rm -rf %s\n' %workdir)
		f.write('mkdir %s\n' %workdir)
		f.write('cd %s\n' %workdir)
	f.write('/bin/cp %s workingvol.mrc\n' % invol)
	f.write('\n')
	f.write('frealign << EOF > frealign.out\n')
	f.write('%s,%d,%s,%s,%s,%s,%d,%s,%s,%s,%s,%d\n' 
		% ('M', mode, params['magrefine'], params['defocusrefine'], params['astigrefine'], 
		params['fliptilt'], params['ewald'], params['matches'], params['history'], 
		params['finalsym'], params['fomfilter'], params['fsc']))
	f.write('%d,%d,%.3f,%.2f,%.2f,%d,%d,%d,%d,%d\n' 
		% (params['radius'], params['iradius'], params['apix'], params['ampcontrast'], 
		params['maskthresh'], params['phaseconstant'], params['avgresidual'], ang, 
		params['itmax'], params['maxmatch']))
	f.write('%d %d %d %d %d\n' % (params['psi'], params['theta'], params['phi'], 
		params['deltax'], params['deltay']))
	f.write('%d, %d\n' % (first, last))
	if params['sym']=='Icos':
		f.write('I\n')
	else:
		f.write('%s\n' % (params['sym']))
	f.write('%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f\n' 
		% (params['relmag'], params['apix'], params['targetresidual'], 
		params['residualthresh'], params['cs'], params['kv'], params['beamtiltx'], 
		params['beamtilty']))
	f.write('%.2f,%.2f,%.2f,%.2f\n' 
		% (params['reslimit'], params['hp'], params['lp'], params['bfactor']))
	f.write('%s\n' % (params['stackfile']))
	f.write('match.mrc\n')
	f.write('%s\n' % inpar)
	f.write('params.1.par\n')
	f.write('shift.par\n')
	f.write('%.1f,0.0,0.0,0.0,0.0,0.0,0.0,0.0\n' %reconrelmag)
	f.write('workingvol.mrc\n')
	f.write('weights.mrc\n')
	f.write('odd.mrc\n')
	f.write('even.mrc\n')
	f.write('phasediffs.mrc\n')
	f.write('pointspread.mrc\n')
	f.write('EOF\n')
	f.write('\n')
	f.close()
	os.chmod(jobname,0755)

#===============
def convertEmanEulersToFrealign(eman_eulers, sym='c1'):
	e1 = eman_eulers['az']
	e2 = eman_eulers['alt']
	e3 = eman_eulers['phi']
	m = eman_eulers['mirror']

	# first get Frealign theta
	if m is not True:
		e2+=180
	if e2 < 0:
		e2+=360
	if e2 > 360:
		e2-=360

	# get Frealign phi
	e1-=90
	if e1 < 0:
		e1+=360-(360*int(e1/360.0))
	if e1 > 360:
		e1-=360*int(e1/360.0)

	# get Frealign psi
	if m is True:
		e3+=90
		e3*=-1
	else:
		e3*=-1
		e3+=90
	if e3 < 0:
		e3+=360-(360*int(e3/360.0))
	if e3 > 360:
		e3-=360*int(e3/360.0)

	if sym.lower() == 'icos':
		(e1,e2,e3) = sumEulers([90,-31.7174744,0],[e1,e2,e3])

	eulers={"phi":e1,"theta":e2,"psi":e3}
	return eulers

#===============
def sumEulers(eul1,eul2):
	"""
	combine two successive euler rotations
	NOTE: eulers should be in degrees
	"""
	e11=math.radians(eul1[0])
	e12=math.radians(eul1[1])
	e13=math.radians(eul1[2])
	e21=math.radians(eul2[0])
	e22=math.radians(eul2[1])
	e23=math.radians(eul2[2])

	# convert each set of eulers to a rotation matrix
	r1 = eulersToRotationMatrix(e11,e12,e13)
	r2 = eulersToRotationMatrix(e21,e22,e23)

	m = [[0,0,0],[0,0,0],[0,0,0]]
	for i in range(0,3):
		for j in range (0,3):
			m[i][j] = 0.0
			for k in range (0,3):
				m[i][j] = m[i][j] + (r2[i][k]*r1[k][j])

	# convert near-zeroes and ones
	for j in range (0,3):
		for i in range (0,3):
			if abs(m[i][j]) < 1e-6:
				m[i][j] = 0
			if m[i][j] - 1.0 > -1e-6:
				m[i][j] = 1
			if m[i][j] + 1 < 1e-6:
				m[i][j] = -1

	if m[2][2] == 1:
		theta = 0.0
		psi = 0.0
		if m[0][0] == 0:
			phi = math.degrees(math.asin(m[0][1]))
		else:
			if m[0][0] < 0:
				phi = math.degrees(math.pi+math.atan(m[0][1]/m[0][0]))
			else:
				phi = math.degrees(math.atan(m[0][1]/m[0][0]))
	elif m[2][2] == -1:
		theta = 180.0
		psi = 0.0
		if m[0][0] == 0:
			phi = math.degrees(math.asin(-m[0][1]))
		else:
			if -m[0][0] < 0:
				phi = math.degrees(math.pi+math.atan(-m[0][1]/-m[0][0]))
			else:
				phi = math.degrees(math.atan(-m[0][1]/-m[0][0]))
	else:
		theta = math.degrees(math.acos(m[2][2]))
		sign = cmp(theta,0) # get sign of theta
		if m[2][0] == 0:
			if sign != cmp(m[2][1],0):
				phi = 270.0
			else:
				phi = 90.0
		else:
			if m[2][0] < 0:
				phi = math.degrees(math.pi+math.atan(m[2][1]/m[2][0]))
			else:
				phi = math.degrees(math.atan(m[2][1]/m[2][0]))
		if m[0][2] == 0:
			if sign != cmp(m[1][2],0):
				psi=270.0
			else:
				psi=90.0
		else:
			if -m[0][2] < 0:
				psi = math.degrees(math.pi+math.atan(m[1][2]/-m[0][2]))
			else:
				psi = math.degrees(math.atan(m[1][2]/-m[0][2]))

	if phi < 0:
		phi+=360
	if theta < 0:
		theta+=360
	if psi < 0:
		psi+=360

	return [phi,theta,psi]

def eulersToRotationMatrix(e1,e2,e3):
	"""
	converts 3 eulers to a rotation matrix using
	a zyz convention
	"""
	cphi = math.cos(e1)
	sphi = math.sin(e1)
	ctheta = math.cos(e2)
	stheta = math.sin(e2)
	cpsi = math.cos(e3)
	spsi = math.sin(e3)

	m11 = cphi*ctheta*cpsi-sphi*spsi
	m21 = -cphi*ctheta*spsi-sphi*cpsi
	m31 = cphi*stheta
	m12 = sphi*ctheta*cpsi+cphi*spsi
	m22 = -sphi*ctheta*spsi+cphi*cpsi
	m32 = sphi*stheta
	m13 = -stheta*cpsi
	m23 = stheta*spsi
	m33 = ctheta

	return [[m11,m12,m13],[m21,m22,m23],[m31,m32,m33]]

#===============
def getStackParticleEulersForIteration(params,pnum):
	"""
	find the eulers assigned to a stack particle
	during a refinement.  This function will first
	find the particle id for the given stack particle,
	then find its position in the reference stack, and
	will get the eulers for that particle in the recon
	"""

	# get stack particle id
	stackp = apStack.getStackParticle(params['stackid'],pnum)
	particleid = stackp['particle'].dbid

	# find particle in reference stack
	refstackid = apStack.getStackIdFromIterationId(params['reconiterid'])
	refstackp = apStack.getStackParticleFromParticleId(particleid,refstackid, nodie=True)
	if not refstackp:
		apDisplay.printWarning('No classification for stack particle %d in reconstruction iteration id: %d' % (pnum, params['reconiterid']))
		params['noClassification']+=1
		if params['noClassification'] > (float(params['last'])*0.10):
			apDisplay.printError('More than 10% of the particles have no classification, use a different reference reconstruction')
		pclass={}
		pclass['eulers']={}
		pclass['eulers']['euler1']=0.0
		pclass['eulers']['euler2']=0.0
		pclass['inplane_rotation']=0.0
		pclass['mirror']=False
		pclass['shiftx']=0.0
		pclass['shifty']=0.0
	else:
		pclassq = appiondata.ApRefineParticleData()
		pclassq['particle'] = refstackp
		pclassq['refineIter'] = appiondata.ApRefineIterData.direct_query(params['reconiterid'])
		pclass = pclassq.query()
		pclass=pclass[0]

	params['eman_orient']={}
	params['eman_orient']['alt']=pclass['euler1']
	params['eman_orient']['az']=pclass['euler2']
	params['eman_orient']['phi']=pclass['euler3']

	params['eman_orient']['mirror']=pclass['mirror']
	params['eman_orient']['shiftx']=pclass['shiftx']
	params['eman_orient']['shifty']=pclass['shifty']

	return params

#===============
def createMultipleJobs(params):
	"""
	Create multiple job files for frealign reconstruction
	using the mpiexec command
	"""
	# create script that will launch all mpi scripts
	workdir = os.path.join(params['rundir'],"working")
	shutil.rmtree(workdir)
	os.mkdir(workdir)
	cscript = os.path.join(workdir,'frealign_MP.csh')
	params['mp_script']=cscript
	fr = open(cscript,'w')
	#frscript = os.path.join(workdir,'frealign.$PBS_VNODENUM.csh')
	#fr.write("csh "+frscript+"\n")

	# create individual mpi scripts
	ptcls_per_job = params['last']/params['proc']
	r = params['last']%params['proc']
	lastp = 0
	for n in range(params['proc']):
		firstp = lastp+1
		lastp = firstp+ptcls_per_job-1

		if r > 0:
			lastp+=1
			r-=1

		jobname=os.path.join(workdir,"frealign.%d.csh" %n)
		fr.write("-np 1 %s\n" % jobname)
		createFrealignJob(params,jobname,invol=params['itervol'], inpar=params['iterparam'],nodenum=n, first=firstp, last=lastp,norecon=True)
	fr.close()
	os.chmod(cscript,0755)


#===============
def submitMultipleJobs(params):
	"""
	Launch jobs using mpiexec
	Must be launched from within a PBS job!
	"""
	#cmd = 'pbsdsh -v '+params['mp_script']
	cmd = 'mpiexec --app '+params['mp_script']
	print cmd
	proc = subprocess.Popen(cmd, shell=True)
	proc.wait()

#===============
def combineMultipleJobs(params):
	"""
	combine all the parameter files & combine into 1
	then reconstruct the density
	"""
	workdir = os.path.join(params['rundir'],"working")
	paramname = os.path.join(workdir,'params.all.par')
	combine = open(paramname,'w')
	for n in range(params['proc']):
		subdir = "sub"+str(n)
		outpar = os.path.join(workdir,subdir,'params.1.par')
		f=open(outpar,'r')
		lines = f.readlines()
		f.close()
		for n in lines:
			if n[0] != 'C':
				combine.write(n)
	combine.close()
	combinejobname = os.path.join(workdir,'frealign.all.csh')
	createFrealignJob(params,combinejobname,mode=0,invol=params['itervol'],inpar=paramname)
	proc = subprocess.Popen('csh '+combinejobname, shell=True)
	proc.wait()



