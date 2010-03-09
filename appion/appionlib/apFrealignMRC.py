
###MRC functions for Frealign
from pyami import mrc

#===============
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

#===============
def fixMrcHeaderHack(involname, outvolname):
	a=mrc.read(involname)
	#force machine stamp integer
	print "forcing machine stamp"
	h=forceMrcHeader(array=a)
	mrc.write(a,outvolname,header=h)

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
	print catcmd
	proc = subprocess.Popen(catcmd, shell=True)
	proc.wait()
	os.remove(tmpheadername)
