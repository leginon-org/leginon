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
def renderSnapshots(density, res=30, contour=1.5, zoom=1.0,
		apix=None, sym=None, box=None, lpfilter=True, sliceimg=True):
	### if eotest failed, filter to 30
	badres = False
	if not res:
		res=30
	elif str(res) == 'nan':
		res=100
		badres = True

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

	if sliceimg is True:
		# create mrc of central slice for viruses
		halfbox = int(box/2)
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
def renderAnimation(density, res=30, contour=1.5, zoom=1.0,
		apix=None, sym=None, box=None, lpfilter=True, color=None):
	### if eotest failed, filter to 30
	if not res or str(res) == 'nan':
		res = 30
	halfbox = int(box/2)

	### low pass filter the volume to 60% of reported res
	tmpf = density+'.tmp.mrc'
	if lpfilter is True:
		filtres = 0.6*res
		if box > 250:
			lpcmd = ('proc3d %s %s apix=%.3f lp=%.2f shrink=2 origin=0,0,0 norm=0,1' % (density, tmpf, apix, filtres))
		else:
			lpcmd = ('proc3d %s %s apix=%.3f lp=%.2f origin=0,0,0 norm=0,1' % (density, tmpf, apix, filtres))
		apDisplay.printMsg("Low pass filtering model for images")
		apEMAN.executeEmanCmd(lpcmd)
	else:
		shutil.copy(density, tmpf)

	### setup chimera params
	if color is not None:
		chimsnapenv = "%s,%s,%s,%.3f,%.3f,%s" % (tmpf, density, sym, contour, zoom, color)
	else:
		chimsnapenv = "%s,%s,%s,%.3f,%.3f" % (tmpf, density, sym, contour, zoom)
	os.environ["CHIMENV"] = chimsnapenv
	#print chimsnapenv
	chimsnappath = os.path.join(apParam.getAppionDirectory(), "bin", "apChimAnimate.py")
	runChimeraScript(chimsnappath)
	apFile.removeFile(tmpf)

	image1 = density+".000.png"
	if not os.path.isfile(image1):
		apDisplay.printWarning("Chimera failed to generate images")
	else:
		finalgif = density+".animate.gif"
		#finalpng = density+".average.png"
		imagemagickcmd1 = "convert -delay 10 -loop 15 "
		#imagemagickcmd2 = "convert -average "
		images = glob.glob(density+".*[0-9][0-9].png")
		images.sort()
		imagestr = ""
		for image in images:
			imagestr += image+" "
		imagemagickcmd1 += imagestr+finalgif
		#imagemagickcmd2 += imagestr+finalpng
		apFile.removeFile(finalgif)
		apEMAN.executeEmanCmd(imagemagickcmd1, verbose=True)
		#apFile.removeFile(finalpng)
		#apEMAN.executeEmanCmd(imagemagickcmd2, verbose=True)
		if os.path.isfile(finalgif):
			apFile.removeFilePattern(density+".*[0-9][0-9].png")
	
	return


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


