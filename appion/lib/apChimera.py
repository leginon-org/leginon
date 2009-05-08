###############
# Tools for using Chimera
###############

import os
import time
import glob
import shutil
import random
import subprocess
#appion
import apFile
import apEMAN
import apParam
import apDisplay
import apVolume

#=========================================
#=========================================
def filterAndChimera(density, res=30, apix=None, box=None, chimtype='snapshot',
		contour=None, zoom=1.0, sym=None, colorstr=None, silhouette=True):
	if apVolume.isValidVolume(density) is False:
		apDisplay.printError("Volume file is not valid")
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
		if box % 4 == 0:
			shrinkby = 2
		elif box % 6 == 0:
			shrinkby = 3
		elif box % 10 == 0:
			shrinkby = 5
		else:
			apDisplay.printWarning('This box size might cause error in shrinking with low pass filtering')
		lpcmd = ('proc3d %s %s apix=%.3f lp=%.2f shrink=%d origin=0,0,0 norm=0,1' % (density, tmpf, apix, filtres,shrinkby))
	else:
		lpcmd = ('proc3d %s %s apix=%.3f lp=%.2f origin=0,0,0 norm=0,1' % (density, tmpf, apix, filtres))
	apDisplay.printMsg("Low pass filtering model for images")
	apEMAN.executeEmanCmd(lpcmd)
	os.environ['CHIMTEMPVOL'] = tmpf

	### render images
	renderSlice(density, box=box, tmpfile=tmpf, sym=sym)
	if chimtype != 'snapshot':
		renderAnimation(density, contour, zoom, sym, colorstr, silhouette)
	elif chimtype != 'animate':
		renderSnapshots(density, contour, zoom, sym, colorstr, silhouette)
	apFile.removeFile(tmpf)

#=========================================
#=========================================
def renderSlice(density, box=None, tmpfile=None, sym='c1'):
	"""
	create mrc of central slice for viruses
	"""
	if apVolume.isValidVolume(density) is False:
		apDisplay.printError("Volume file is not valid")
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
def renderSnapshots(density, contour=None, zoom=1.0, sym=None, colorstr=None, silhouette=True):
	if apVolume.isValidVolume(density) is False:
		apDisplay.printError("Volume file is not valid")
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
	if colorstr is not None:
		os.environ['CHIMCOLORS'] = colorstr
	else:
		colorstr = getColorString()
		os.environ['CHIMCOLORS'] = colorstr
	if zoom is not None:
		os.environ['CHIMZOOM'] = str(zoom)
	os.environ['CHIMIMGSIZE'] = "1024"
	### unused
	#'CHIMBACK',  'CHIMIMGSIZE', 'CHIMIMGFORMAT', 'CHIMFILEFORMAT',
	chimsnappath = os.path.join(apParam.getAppionDirectory(), "bin", "apChimSnapshot.py")
	apDisplay.printColor("running Chimera Snapshot for sym "+str(sym), "cyan")
	runChimeraScript(chimsnappath)

	image1 = density+".1.png"
	if not os.path.isfile(image1):
		apDisplay.printWarning("Chimera failed to generate images")

	return

#=========================================
#=========================================
def renderAnimation(density, contour=None, zoom=1.0, sym=None, colorstr=None, silhouette=False):
	if apVolume.isValidVolume(density) is False:
		apDisplay.printError("Volume file is not valid")
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
	if colorstr is not None:
		os.environ['CHIMCOLORS'] = colorstr
	else:
		colorstr = getColorString()
		os.environ['CHIMCOLORS'] = colorstr
	if zoom is not None:
		os.environ['CHIMZOOM'] = str(zoom)
	os.environ['CHIMIMGSIZE'] = "256"
	### unused
	#'CHIMBACK',  'CHIMIMGSIZE', 'CHIMIMGFORMAT', 'CHIMFILEFORMAT',
	chimsnappath = os.path.join(apParam.getAppionDirectory(), "bin", "apChimSnapshot.py")
	apDisplay.printColor("running Chimera Animation for sym "+str(sym), "cyan")
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
		#if os.path.isfile(finalgif):
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

#=========================================
#=========================================
def getColorString():
	#return secondColor()+",None,"+minuteColor()
	#print "first"
	first = secondColor()
	#print "third"
	third = hourColor()
	return first+",None,"+third

#=========================================
#=========================================
def dayColor():
	valrange = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
	day = int( (time.time()/(3600*24.0)-8.0/24.0)%216 )
	rgbindex = [ day%6, (day/6)%6, (day/36)%6 ]
	rgbindex = checkRGBwhite(rgbindex)
	colorstr = "%.1f:%.1f:%.1f"%(valrange[rgbindex[0]], valrange[rgbindex[1]], valrange[rgbindex[2]])
	return colorstr

#=========================================
#=========================================
def hourColor():
	valrange = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
	hour = int( (time.time()/3600)%216 )
	rgbindex = [ hour%6, (hour/6)%6, (hour/36)%6 ]
	rgbindex = checkRGBwhite(rgbindex)
	colorstr = "%.1f:%.1f:%.1f"%(valrange[rgbindex[0]], valrange[rgbindex[1]], valrange[rgbindex[2]])
	return colorstr

#=========================================
#=========================================
def minuteColor():
	valrange = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
	mins = int( (time.time()/60)%216 )
	rgbindex = [ mins%6, (mins/6)%6, (mins/36)%6 ]
	rgbindex = checkRGBwhite(rgbindex)
	colorstr = "%.1f:%.1f:%.1f"%(valrange[rgbindex[0]], valrange[rgbindex[1]], valrange[rgbindex[2]])
	return colorstr

#=========================================
#=========================================
def secondColor():
	valrange = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
	secs = int( time.time()%216 )
	rgbindex = [ secs%6, (secs/6)%6, (secs/36)%6 ]
	rgbindex = checkRGBwhite(rgbindex)
	colorstr = "%.1f:%.1f:%.1f"%(valrange[rgbindex[0]], valrange[rgbindex[1]], valrange[rgbindex[2]])
	return colorstr

#=========================================
#=========================================
def randomColor():
	valrange = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
	rand = int(random.random()*216.0)
	rgbindex = [ rand%6, (rand/6)%6, (rand/36)%6 ]
	rgbindex = checkRGBwhite(rgbindex)
	colorstr = "%.1f:%.1f:%.1f"%(valrange[rgbindex[0]], valrange[rgbindex[1]], valrange[rgbindex[2]])
	return colorstr

#=========================================
#=========================================
def checkRGBwhite(rgbindex):
	mindiff = 3
	maxsum = 12
	d1 = abs(rgbindex[0]-rgbindex[1])
	d2 = abs(rgbindex[0]-rgbindex[2])
	d3 = abs(rgbindex[1]-rgbindex[2])
	csum = rgbindex[0]+rgbindex[1]+rgbindex[2]
	if d1 < mindiff and d2 < mindiff and d3 < mindiff:
		# color is too gray
		rand = int(random.random()*216.0)
		randindex = [ rand%6, (rand/6)%6, (rand/36)%6 ]
		#print "too gray", rgbindex, d1, d2, d3, randindex, csum
		return checkRGBwhite(randindex)
	if csum > maxsum:
		# color is too light-colored
		upindex = [rgbindex[0]+1, rgbindex[1]+1, rgbindex[2]+1, ]
		for i in range(3):
			if upindex[i] > 5:
				upindex[i] = 5
		#print "too light", rgbindex, d1, d2, d3, upindex, csum
		return checkRGBwhite(upindex)
	#print "good", d1, d2, d3, rgbindex,  csum
	return rgbindex



