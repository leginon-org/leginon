import os
import apStack
import apCtf
import apDefocalPairs
from pyami import mrc
import apVolume
import apDisplay
import appionData
import apFrealign

#===============
def imagicToMrc(params, msg=True):
	# convert imagic stack to mrc "stack"
	outstack = os.path.join(params['rundir'],'start.mrc')
	params['stackfile']=outstack

	# if mrc stack exists, don't overwrite
	# TO DO: check if existing stack is correct
	if os.path.exists(outstack):
		apDisplay.printWarning(outstack + " exists, not overwriting")
		return

	# first get stack info
	stackdata = apStack.getOnlyStackData(params['stackid'], msg=False)
	stackfile = os.path.splitext(os.path.join(stackdata['path']['path'],stackdata['name']))

	# make sure to use the 'img' file, which contains the binary data
	stackimg = stackfile[0]+'.img'

	# get box size
	box = apStack.getStackBoxsize(params['stackid'], msg=False)
	nump = apStack.getNumberStackParticlesFromId(params['stackid'])

	## create a new MRC header
	header = mrc.newHeader()
	mrc.updateHeaderDefaults(header)

	# fill with stack params
	nump=2000
	header['nx']=box
	header['ny']=box
	header['nz']=nump
	header['mode']=2
	header['mx']=box
	header['my']=box
	header['mz']=nump
	header['xlen']=box
	header['ylen']=box
	header['zlen']=nump
	header['amin']=0.0
	header['amax']=0.0
	header['amean']=0.0
	header['rms']=0.0
	header['xorigin']=0.0
	header['yorigin']=0.0
	header['zorigin']=0.0

	# write header to temporary file
	hbytes = mrc.makeHeaderData(header)
	tmpheadername = apVolume.randomfilename(8)+'.mrc'
	f = open(tmpheadername,'w')
	f.write(hbytes)
	f.close()

	if msg is True:
		apDisplay.printMsg('saving MRC stack file:')
		apDisplay.printMsg(os.path.join(params['rundir'],outstack))
	catcmd = "cat %s %s > %s" % (tmpheadername, stackimg, outstack)
#	os.system(catcmd)
#	os.remove(tmpheadername)
	
#===============
def generateParticleParams(params):
	params['inpar']=os.path.join(params['rundir'],'params.0.par')
	apDisplay.printMsg("Creating parameter file: "+params['inpar'])
	params['mode']=3
	stackdata=apStack.getStackParticlesFromId(params['stackid'])
	apix=params['apix']
	particleparams={}
	f=open(params['inpar'],'w')
	print "Writing out particle parameters"
	for particle in stackdata:
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
			# first see if there are ctf2 values
			ctfdata, confidence=apCtf.getBestAceTwoValueForImage(imagedata, msg=False)
			if ctfdata is None:
				ctfdata, confidence=apCtf.getBestCtfValueForImage(imagedata, msg=False)

			# use defocus & astigmatism values 
			particleparams['df1']=ctfdata['defocus1']*1e10
			particleparams['df2']=ctfdata['defocus2']*1e10
			particleparams['angast']=-ctfdata['angle_astigmatism']

		# if using parameters from previous reconstruction
		if params['compStackId'] is not None:
			params['mode']=1
			apFrealign.getStackParticleEulersForIteration(params,particle['particleNumber'])
			fr_eulers = apFrealign.convertEmanEulersToFrealign(params['eman_orient'])
			particleparams['psi'] = fr_eulers['psi']
			particleparams['theta'] = fr_eulers['theta']
			particleparams['phi'] = fr_eulers['phi']
			particleparams['shx']=params['eman_orient']['shiftx']
			particleparams['shy']=params['eman_orient']['shifty']
		
		writeParticleParamLine(particleparams,f)
		if particle['particleNumber']==2000:
			return
	f.close()
	
#===============
def writeParticleParamLine(particleparams, fileobject):
	p=particleparams
	fileobject.write("%7d%8.3f%8.3f%8.3f%8.3f%8.3f%9.1f%5d%9.1f%9.1f%8.2f%7.2f%8.2f\n" % (p['ptclnum'],p['psi'],p['theta'],p['phi'],p['shx'],p['shy'],p['mag'],p['film'],p['df1'],p['df2'],p['angast'],p['presa'],p['dpres']))

#===============
def createFrealignJob (params, jobname, norecon=False):

	mode = params['mode']
	inparname = params['inpar']
	outparname = params['outpar']
	firstparticle = params['first']
	lastparticle = params['last']

	if norecon:
		relmag=1
	else:
		relmag=params['relmag']

	f=open(jobname,'w')

	# first copy files
	f.write('cd %s\n' % params['rundir'])
	f.write('rm -rf working\n')
	f.write('mkdir working\n')
	f.write('cd working\n')
	f.write('cp %s threed.0.mrc\n' % params['initmodel'])
	f.write('cp %s params.0.par\n' % inparname)

	# set mode if not refining(1=refine)
	if mode != 1:
		f.write("set m = %d\n" % mode)
	f.write("\n")
	
	# create loop for refinement cycles
	f.write("@ i = 0\n")
	f.write("@ j = 1\n")
	f.write('while ($i <= %d)\n' % params['refcycles'])
	# make a copy of the file that will be overwritten
	f.write('cp threed.$i.mrc workingvol.mrc\n')
	f.write('frealign << EOF > frealign.$j.out\n')
	f.write('%s,%d,%s,%s,%s,%s,%d,%s,%s,%s,%s,%d\n' % ('M', mode, params['magrefine'], params['defocusrefine'], params['astigrefine'], params['fliptilt'], params['ewald'], params['matches'], params['history'], params['finalsym'], params['fomfilter'], params['fsc']))
	f.write('%d,%d,%.3f,%.2f,%.2f,%d,%d,%d,%d,%d\n' % (params['radius'], params['iradius'], params['apix'], params['ampcontrast'], params['maskthresh'], params['phaseconstant'], params['avgresidual'], params['ang'], params['itmax'], params['maxmatch']))
	f.write('%d %d %d %d %d\n' % (params['psi'], params['theta'], params['phi'], params['deltax'], params['deltay']))
	f.write('%d, %d\n' % (firstparticle, lastparticle))
	f.write('%s\n' % (params['sym']))
	f.write('%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f\n' % (relmag, params['apix'], params['targetresidual'], params['residualthresh'], params['cs'], params['kv'], params['beamtiltx'], params['beamtilty']))
	f.write('%.2f,%.2f,%.2f,%.2f\n' % (params['reslimit'], params['hp'], params['lp'], params['bfactor']))
	f.write('%s\n' % (params['stackfile']))
	f.write('match.mrc\n')
	f.write('params.$i.par\n')
	f.write('params.$j.par\n')
	f.write('shift.$j.par\n')
	f.write('0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0\n')
	f.write('workingvol.mrc\n')
	f.write('weights.mrc\n')
	f.write('odd.mrc\n')
	f.write('even.mrc\n')
	f.write('phasediffs.mrc\n')
	f.write('pointspread.mrc\n')
	f.write('EOF\n')
	f.write('mv workingvol.mrc threed.$j.mrc\n')
	f.write('\n')
	f.write('@ i ++\n')
	f.write('@ j ++\n')
	if mode != 1:
		f.write('set m = 1\n')
	f.write('end\n')
	f.write('\n')
	f.close()

#===============
def convertEmanEulersToFrealign(eman_eulers):
	e1 = eman_eulers['az']
	e2 = eman_eulers['alt']
	e3 = eman_eulers['phi']
	m = eman_eulers['mirror']

	# if mirror plane, invert az & alt
	if m is True:
		e1*=-1
		e2*=-1

	# get Frealign phi (add 90 degrees)
	if e1 < 0:
		e1+=360
	e1-=90
	if e1 < 0:
		e1+=360

	# get Frealign theta
	if e2 < 0:
		e2+=360
		
	# get Frealign psi (subtract 90 degrees)
	if e3 < 0:
		e3+=360
	e3+=90
	if e3 > 360:
		e3-=360
	eulers={"phi":e1,"theta":e2,"psi":e3}
	return eulers

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
	refstackp = apStack.getStackParticleFromParticleId(particleid,params['compStackId'])
	pclassq = appionData.ApParticleClassificationData()
	pclassq['particle'] = refstackp
	pclassq['refinement'] = appionData.ApRefinementData.direct_query(params['reconiterid'])
	pclass = pclassq.query()

	if not pclass:
		apDisplay.printError('No classification for stack particle %d in reconstruction iteration id: %d' % (pnum, params['reconiterid']))

	pclass=pclass[0]
	params['eman_orient']={}
	params['eman_orient']['alt']=pclass['eulers']['euler1']
	params['eman_orient']['az']=pclass['eulers']['euler2']
	params['eman_orient']['phi']=pclass['inplane_rotation']

	params['eman_orient']['mirror']=pclass['mirror']
	params['eman_orient']['shiftx']=pclass['shiftx']
	params['eman_orient']['shifty']=pclass['shifty']
	
	return params
	
	
