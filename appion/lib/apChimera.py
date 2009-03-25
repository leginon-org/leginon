###############
# Tools for using Chimera
###############

import os
import subprocess
import shutil
import glob
#appion
import apFile
import apEMAN
import apParam
import apDisplay

#=========================================
#=========================================
def filterAndChimera(density, res=30, apix=None, box=None, chimtype='snapshot',
		contour=None, zoom=1.0, sym=None, color=None, silhouette=True):
	if box is None:
		boxdims = apFile.getBoxSize(density)
		box = boxdims[0]
	### if eotest failed, filter to 30
	if not res or str(res) == 'nan':
		res = 30
	### low pass filter the volume to 60% of reported res
	tmpf = density+'.tmp.mrc'
	filtres = 0.6*res
	if box is not None and box > 250:
		lpcmd = ('proc3d %s %s apix=%.3f lp=%.2f shrink=2 origin=0,0,0 norm=0,1' % (density, tmpf, apix, filtres))
	else:
		lpcmd = ('proc3d %s %s apix=%.3f lp=%.2f origin=0,0,0 norm=0,1' % (density, tmpf, apix, filtres))
	apDisplay.printMsg("Low pass filtering model for images")
	apEMAN.executeEmanCmd(lpcmd)
	os.environ['CHIMTEMPVOL'] = tmpf

	### render images
	renderSlice(density, box=box, tmpfile=tmpf, sym=sym)
	if chimtype != 'snapshot':
		renderAnimation(density, contour, zoom, sym, color, silhouette)
	elif chimtype != 'animate':
		renderSnapshots(density, contour, zoom, sym, color, silhouette)
	apFile.removeFile(tmpf)

#=========================================
#=========================================
def renderSlice(density, box=None, tmpfile=None, sym='c1'):
	"""
	create mrc of central slice for viruses
	"""
	if tmpfile is None:
		tmpfile = density
	if box is None:
		boxdims = apFile.getBoxSize(tmpfile)
		box = boxdims[0]
	halfbox = int(box/2)
	tmphed = density + '.hed'
	tmpimg = density + '.img'
	hedcmd = ('proc3d %s %s' % (tmpfile, tmphed))
	if sym.lower()[:4] != 'icos':
		hedcmd = hedcmd + " rot=90"
	apEMAN.executeEmanCmd(hedcmd)
	pngslice = density + '.slice.png'
	slicecmd = ('proc2d %s %s first=%i last=%i' % (tmphed, pngslice, halfbox, halfbox))
	apEMAN.executeEmanCmd(slicecmd)
	apFile.removeStack(tmphed, warn=False)
	return

#=========================================
#=========================================
def renderSnapshots(density, contour=None, zoom=1.0, sym=None, color=None, silhouette=True):
	### setup chimera params
	os.environ['CHIMVOL'] = density
	os.environ['CHIMTYPE'] = 'snapshot'
	if silhouette is True:
		os.environ['CHIMSILHOUETTE'] = 'true'
	else:
		os.unsetenv('CHIMSILHOUETTE')
	if sym is not None:
		os.environ['CHIMSYM'] = sym
	if contour is not None:
		os.environ['CHIMCONTOUR'] = str(contour)
	if color is not None:
		os.environ['CHIMCOLOR'] = color
	if zoom is not None:
		os.environ['CHIMZOOM'] = str(zoom)
	os.environ['CHIMIMGSIZE'] = "1024"
	### unused
	#'CHIMBACK',  'CHIMIMGSIZE', 'CHIMIMGFORMAT', 'CHIMFILEFORMAT',
	chimsnappath = os.path.join(apParam.getAppionDirectory(), "bin", "apChimSnapshot.py")
	runChimeraScript(chimsnappath)

	image1 = density+".1.png"
	if not os.path.isfile(image1):
		apDisplay.printWarning("Chimera failed to generate images")

	return

#=========================================
#=========================================
def renderAnimation(density, contour=None, zoom=1.0, sym=None, color=None, silhouette=True):
	### setup chimera params
	os.environ['CHIMVOL'] = density
	os.environ['CHIMTYPE'] = 'animate'
	if silhouette is True:
		os.environ['CHIMSILHOUETTE'] = 'true'
	else:
		os.unsetenv('CHIMSILHOUETTE')
	if sym is not None:
		os.environ['CHIMSYM'] = sym
	if contour is not None:
		os.environ['CHIMCONTOUR'] = str(contour)
	if color is not None:
		os.environ['CHIMCOLOR'] = color
	if zoom is not None:
		os.environ['CHIMZOOM'] = str(zoom)
	os.environ['CHIMIMGSIZE'] = "128"
	### unused
	#'CHIMBACK',  'CHIMIMGSIZE', 'CHIMIMGFORMAT', 'CHIMFILEFORMAT',
	chimsnappath = os.path.join(apParam.getAppionDirectory(), "bin", "apChimSnapshot.py")
	runChimeraScript(chimsnappath)
	image1 = density+".001.png"
	if not os.path.isfile(image1):
		apDisplay.printWarning("Chimera failed to generate images")
	else:
		### merge into animated GIF
		finalgif = density+".animate.gif"
		imagemagickcmd1 = "convert -delay 10 -loop 15 "
		images = glob.glob(density+".*[0-9][0-9].png")
		images.sort()
		imagestr = ""
		for image in images:
			imagestr += image+" "
		imagemagickcmd1 += imagestr+finalgif
		apFile.removeFile(finalgif)
		apEMAN.executeEmanCmd(imagemagickcmd1, verbose=True)
		if os.path.isfile(finalgif):
			apFile.removeFilePattern(density+".*[0-9][0-9].png")
	return


#=========================================
#=========================================
def runChimeraScript(chimscript):
	#apDisplay.printColor("Trying to use chimera for model imaging","cyan")
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
	logf = open("chimeraRun.log", "a")
	apDisplay.printColor("running Chimera:\n "+rendercmd, "cyan")
	proc = subprocess.Popen(rendercmd, shell=True, stdout=logf, stderr=logf)
	proc.wait()
	logf.close()
	return


