import os
import sys
import subprocess
import apStack
import apCtf
import apDefocalPairs
from pyami import mrc
import apVolume
import apDisplay
import appiondata
import shutil
import math
import numpy


#===============
def writeParticleParamLine(particleparams, fileobject):
	p=particleparams
	fileobject.write( ("%7d"+"%8.2f%8.2f%8.2f"+"%8.2f%8.2f"+"%7d.%4d"+"%9.1f%9.1f%8.2f"+"%7.2f%8.2f\n") % 
		(p['ptclnum'], #part num
		p['psi'],p['theta'],p['phi'], #Eulers
		p['shx'],p['shy'], #shifts
		p['mag'],p['film'], #scope
		p['df1'],p['df2'],p['angast'], #defocus
		p['presa'],p['dpres']) #phase residual, change in phase residual from previous run
	)

#===============
def createFrealignJob(params, jobname, nodenum=None, mode=None, inpar=None, invol=None, first=None, last=None, norecon=False):

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
	params['defocusperpart'] = False
	if nodenum is not None:
		workdir = "sub"+str(nodenum)
		f.write('rm -rf %s\n' %workdir)
		f.write('mkdir %s\n' %workdir)
		f.write('cd %s\n' %workdir)
	f.write('rsync -vaP %s workingvol.mrc\n' % invol)
	f.write('\n')
	f.write('frealign << EOF > frealign.out\n')

	### CARD 1
	fstat = False # memory saving function
	iblow = 1 # expand volume in memory, larger is faster, but needs more mem
	## mem needed = box**3 * 
	fcref = False # apply FOM weighting
	f.write('%s,%d,%s,%s,%s,%s,%d,%s,%s,%s,%s,%d,%s,%d\n' % (
		'I', #(I) use imagic, (M) use mrc, (S) use spider
		mode, 
		params['magrefine'], params['defocusrefine'], #T/F refinements
		params['astigrefine'], params['defocusperpart'], #T/F refinements
		params['ewald'], 
		params['matches'], fcref, params['finalsym'], 
		params['fomfilter'], params['fsc'], 
		fstat, iblow))

	### CARD 2
	f.write('%d,%d,%.3f,%.2f,%.2f,%d,%d,%d,%d,%d\n' % (params['radius'], params['iradius'], params['apix'], params['ampcontrast'], params['maskthresh'], params['phaseconstant'], params['avgresidual'], ang, params['itmax'], params['maxmatch']))

	### CARD 3
	f.write('%d %d %d %d %d\n' % (params['psi'], params['theta'], params['phi'], params['deltax'], params['deltay']))

	### CARD 4
	f.write('%d, %d\n' % (first, last))

	### CARD 5
	if params['sym']=='Icos':
		f.write('I\n')
	else:
		f.write('%s\n' % (params['sym']))

	### CARD 6
	f.write('%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f\n' % (params['relmag'], params['apix'], params['targetresidual'], params['residualthresh'], params['cs'], params['kv'], params['beamtiltx'], params['beamtilty']))

	### CARD 7
	### lp should be ~25 A for mode 3 and ~12 A for mode 1
	dfstd = 100 # defocus standard deviation (in Angstroms), usually +/- 100 A
 	f.write('%.2f,%.2f,%.2f,%.2f,%.2f\n' % (params['reslimit'], params['hp'], params['lp'], dfstd, params['bfactor']))

	### CARD 8
	f.write('%s\n' % (params['stackfile']))
	f.write('match\n')
	f.write('%s\n' % inpar)
	f.write('params.1.par\n')
	f.write('shift.par\n')
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

	# if icos, rotate eulers to 3dem standard orientation
	if sym.lower() == 'icos':
		e1, e2, e3 = sumEulers([90, -31.7174744, 0], [e1,e2,e3])

	eulerdict = {"phi":e1, "theta":e2, "psi":e3}

	return eulerdict

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

#===============
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



