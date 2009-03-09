###############
# Tools for using Chimera
###############


#=========================================
#=========================================
def renderSnapshots(density, res=30, contour=1.5, zoom=1.0,
		apix=None, sym=None, box=None, lpfilter=True):
	### if eotest failed, filter to 30
	badres = False
	if not res:
		res=30
	elif str(res) == 'nan':
		res=100
		badres = True
	halfbox = int(box/2)

	### low pass filter the volume to 60% of reported res
	tmpf = density+'.tmp.mrc'
	if lpfilter is True:
		filtres = 0.6*res
		if box > 250:
			lpcmd = ('proc3d %s %s apix=%.3f lp=%.2f shrink=2 origin=0,0,0' % (density, tmpf, apix, filtres))
		else:
			lpcmd = ('proc3d %s %s apix=%.3f lp=%.2f origin=0,0,0' % (density, tmpf, apix, filtres))
		apDisplay.printMsg("Low pass filtering model for images")
		apEMAN.executeEmanCmd(lpcmd)
	else:
		shutil.copy(density, tmpf)

	### setup chimera params
	chimsnapenv = "%s,%s,%s,%.3f,%.3f" % (tmpf, density, sym, contour, zoom)
	os.environ["CHIMENV"] = chimsnapenv
	chimsnappath = os.path.join(apParam.getAppionDirectory(), "bin", "apChimSnapshot.py")
	runChimeraScript(chimsnappath)
	apFile.removeFile(tmpf)

	image1 = density+".1.png"
	if not os.path.isfile(image1):
		apDisplay.printWarning("Chimera failed to generate images")

	# create mrc of central slice for viruses
	tmphed = density + '.hed'
	tmpimg = density + '.img'
	hedcmd = ('proc3d %s %s' % (density,tmphed))
	if sym.lower()[:4] != 'icos':
		hedcmd = hedcmd + " rot=90"
	apEMAN.executeEmanCmd(hedcmd)
	pngslice = density + '.slice.png'
	slicecmd = ('proc2d %s %s first=%i last=%i' % (tmphed, pngslice, halfbox, halfbox))
	apEMAN.executeEmanCmd(slicecmd)
	apFile.removeStack(tmphed, warn=False)
	return badres

#=========================================
#=========================================
def runChimeraScript(chimscript):
	apDisplay.printColor("Trying to use chimera for model imaging","cyan")
	apParam.resetVirtualFrameBuffer()
	if 'CHIMERA' in os.environ and os.path.isdir(os.environ['CHIMERA']):
		chimpath = os.environ['CHIMERA']
		os.environ['CHIMERA'] = chimpath
		os.environ['CHIMERAPATH'] = os.path.join(chimpath,"share")
		os.environ['LD_LIBRARY_PATH'] = os.path.join(chimpath,"lib")+":"+os.environ['LD_LIBRARY_PATH']
		chimexe = os.path.join(chimpath,"bin/chimera")
		if not os.path.isfile(chimexe):
			apDisplay.printWarning("Could not find chimera at: "+chimexe)
	else:
		chimpath = None
		chimexe = "chimera"
		#apDisplay.printWarning("'CHIMERA' environmental variable is unset")
	rendercmd = (chimexe+" python:"+chimscript)
	logf = open("chimera.log", "a")
	proc = subprocess.Popen(rendercmd, shell=True, stdout=logf, stderr=logf)
	proc.wait()
	logf.close()
	return







