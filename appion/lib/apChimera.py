###############
# Tools for using Chimera
###############

import os
import time
import glob
import shutil
import random
import colorsys
import subprocess
#appion
import apFile
import apEMAN
import apParam
import apDisplay
import apVolume

hsvalue = 0.4

#=========================================
#=========================================
def setVolumeMass(volumefile, apix=1.0, mass=1.0, rna=0.0):
	"""
	set the contour of 1.0 to the desired mass (in kDa) of the
	macromolecule based on its density
	
	use RNA to set the percentage of RNA in the structure
	"""
	if apVolume.isValidVolume(volumefile) is False:
		apDisplay.printError("Volume file is not valid")

	procbin = apParam.getExecPath("proc2d")
	emandir = os.path.dirname(procbin)
	volumebin = os.path.join(emandir, "volume")
	if not os.path.isfile(volumebin):
		apDisplay.printWarning("failed to find volume program")
		return False
	command = "%s %s %.3f set=%.3f"%(	
		volumebin, volumefile, apix, mass
	)
	t0 = time.time()
	proc = subprocess.Popen(command, shell=True)
	proc.wait()
	if time.time()-t0 < 0.01:
		apDisplay.printWarning("failed to scale by mass in "+apDisplay.timeString(time.time()-t0))
		return False
	apDisplay.printMsg("finished scaling by mass in "+apDisplay.timeString(time.time()-t0))
	return True

#=========================================
#=========================================
def filterAndChimera(density, res=30, apix=None, box=None, chimtype='snapshot',
		contour=None, zoom=1.0, sym=None, color=None, silhouette=True):
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
def renderSnapshots(density, contour=None, zoom=1.0, sym=None, color=None, silhouette=True):
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
	if color is not None:
		colorstr = colorToString(color)
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
		runChimeraScript(chimsnappath)

	return

#=========================================
#=========================================
def renderAnimation(density, contour=None, zoom=1.0, sym=None, color=None, silhouette=False):
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
	if color is not None:
		colorstr = colorToString(color)
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
		runChimeraScript(chimsnappath)

	if os.path.isfile(image1):
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
		apEMAN.executeEmanCmd(imagemagickcmd1, verbose=False, showcmd=False)
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
def colorToString(color):
	if color == "red":
		return "0.6:0.0:0.0,None,0.6:0.0:0.0"
	elif color == "orange":
		return "0.6:0.2:0.0,None,0.6:0.2:0.0"
	elif color == "yellow":
		return "0.8:0.6:0.0,None,0.8:0.6:0.0"
	elif color == "green":
		return "0.0:0.6:0.0,None,0.0:0.6:0.0"
	elif color == "blue":
		return "0.0:0.0:0.6,None,0.0:0.0:0.6"
	elif color == "violet":
		return "0.6:0.2:0.6,None,0.6:0.2:0.6"
	else:
		return "None,None,None"

#=========================================
#=========================================
def getColorString():
	#return secondColor()+",None,"+minuteColor()
	first = hourColor()
	#print "first", first
	third = dayColor()
	#print "third", third
	colortuple = first+",None,"+third
	#print colortuple
	return colortuple

#=========================================
#=========================================
def dayColor():
	hue = ((time.time()/(24*3600.))%365)/365
	rgbindex = colorsys.hsv_to_rgb(hue, 1, hsvalue)
	colorstr = "%.1f:%.1f:%.1f"%(rgbindex[0], rgbindex[1], rgbindex[2])
	return colorstr

#=========================================
#=========================================
def hourColor():
	hue = ((time.time()/3600.)%24)/24
	rgbindex = colorsys.hsv_to_rgb(hue, 1, hsvalue)
	colorstr = "%.1f:%.1f:%.1f"%(rgbindex[0], rgbindex[1], rgbindex[2])
	return colorstr

#=========================================
#=========================================
def minuteColor():
	hue = ((time.time()/60.)%60)/60
	rgbindex = colorsys.hsv_to_rgb(hue, 1, hsvalue)
	colorstr = "%.1f:%.1f:%.1f"%(rgbindex[0], rgbindex[1], rgbindex[2])
	return colorstr

#=========================================
#=========================================
def secondColor():
	hue = (time.time()%60.)/60
	rgbindex = colorsys.hsv_to_rgb(hue, 1, hsvalue)
	colorstr = "%.1f:%.1f:%.1f"%(rgbindex[0], rgbindex[1], rgbindex[2])
	return colorstr

#=========================================
#=========================================
def randomColor():
	hue = random.random()
	rgbindex = colorsys.hsv_to_rgb(hue, 1, hsvalue)
	colorstr = "%.1f:%.1f:%.1f"%(rgbindex[0], rgbindex[1], rgbindex[2])
	return colorstr

#=========================================
#=========================================
def isTooGray(rgbindex):
	mindiff = 0.16
	d1 = abs(rgbindex[0]-rgbindex[1])
	d2 = abs(rgbindex[0]-rgbindex[2])
	d3 = abs(rgbindex[1]-rgbindex[2])
	if d1 < mindiff and d2 < mindiff and d3 < mindiff:
		return True
	return False

#=========================================
#=========================================
def isTooLight(rgbindex):
	maxsum = 0.67
	csum = rgbindex[0]+rgbindex[1]+rgbindex[2]
	if csum > maxsum:
		return True
	return False

#=========================================
#=========================================
def isGoodColor(rgbindex):
	if isTooGray(rgbindex):
		# color is too gray
		return False
	if isTooLight(rgbindex):
		# color is too light-colored
		return False
	return True

#=========================================
#=========================================
def getColorList():
	colorlist = []
	for i in range(216):
		rgbindex = [ i%6, (i/6)%6, (i/36)%6 ]
		if isGoodColor(rgbindex):
			colorlist.append(rgbindex)

