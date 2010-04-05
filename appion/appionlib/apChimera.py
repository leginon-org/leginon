###############
# Tools for using Chimera
###############

import os
import math
import time
import glob
import numpy
import shutil
import random
import colorsys
import subprocess
#appion
from appionlib import apFile
from appionlib import apParam
from appionlib import apDisplay
from pyami import mrc

satvalue = 0.9
hsvalue = 0.5

#=========================================
#=========================================
def getSnapPath():
	chimsnappath = os.path.join(apParam.getAppionDirectory(), "bin", "apChimSnapshot.py")
	if not os.path.isfile(chimsnappath):
		libdir = os.path.dirname(__file__)
		chimsnappath = os.path.join(libdir, "apChimSnapshot.py")
	if not os.path.isfile(chimsnappath):
		apDisplay.printError("Could not find file: apChimSnapshot.py")
	return chimsnappath

#=========================================
#=========================================
def isValidVolume(volfile):
	"""
	Checks to see if a MRC volume is valid
	"""
	if not os.path.isfile(volfile):
		return False
	volarray = mrc.read(volfile)
	if volarray.shape[0]*volarray.shape[1]*volarray.shape[2] > 400**3:
		apDisplay.printWarning("Volume is very large")
		return True
	if abs(volarray.min() - volarray.max()) < 1e-6:
		apDisplay.printWarning("Volume has zero standard deviation")
		return False
	return True

#=========================================
#=========================================
def setVolumeMass(volumefile, apix=1.0, mass=1.0, rna=0.0):
	"""
	set the contour of 1.0 to the desired mass (in kDa) of the
	macromolecule based on its density
	
	use RNA to set the percentage of RNA in the structure
	"""
	if isValidVolume(volumefile) is False:
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
		contour=None, zoom=1.0, sym='c1', color=None, silhouette=True, mass=None):
	"""
	filter volume and then create a few snapshots for viewing on the web
	"""
	if isValidVolume(density) is False:
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
	shrinkby = 1
	if box is not None and box > 250:
		shrinkby = int(math.ceil(box/160.0))
		if box % (2*shrinkby) == 0:
			### box is divisible by shrink by
			lpcmd = ('proc3d %s %s apix=%.3f tlp=%.2f shrink=%d origin=0,0,0 norm=0,1'
				% (density, tmpf, apix, filtres, shrinkby))
		else:
			### box not divisible by shrink by, need a clip
			clip = math.floor(box/shrinkby/2.0)*2*shrinkby
			lpcmd = ('proc3d %s %s apix=%.3f tlp=%.2f shrink=%d origin=0,0,0 norm=0,1 clip=%d,%d,%d'
				% (density, tmpf, apix, filtres, shrinkby, clip, clip, clip))
	else:
		lpcmd = ('proc3d %s %s apix=%.3f tlp=%.2f origin=0,0,0 norm=0,1'
			% (density, tmpf, apix, filtres))
	apDisplay.printMsg("Low pass filtering model for images")
	proc = subprocess.Popen(lpcmd, shell=True)
	proc.wait()

	### flatten solvent
	vol = mrc.read(tmpf)
	numpy.where(vol < 0, 0.0, vol)
	mrc.write(vol, tmpf)
	del vol

	### contour volume to mass
	if mass is not None:
		setVolumeMass(tmpf, apix*shrinkby, mass)
		contour = 1.0

	### set pixelsize and origin
	recmd = "proc3d %s %s apix=%.3f origin=0,0,0"%(tmpf, tmpf, apix)
	proc = subprocess.Popen(recmd, shell=True)
	proc.wait()

	### render images
	renderSlice(density, box=box, tmpfile=tmpf, sym=sym)
	if chimtype != 'snapshot':
		renderAnimation(tmpf, contour, zoom, sym, color, silhouette, name=density)
	elif chimtype != 'animate':
		renderSnapshots(tmpf, contour, zoom, sym, color, silhouette, name=density)
	#apFile.removeFile(tmpf)

#=========================================
#=========================================
def renderSlice(density, box=None, tmpfile=None, sym='c1'):
	"""
	create mrc of central slice for viruses
	"""
	if isValidVolume(density) is False:
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
	proc = subprocess.Popen(hedcmd, shell=True)
	proc.wait()
	pngslice = density + '.slice.png'
	slicecmd = ('proc2d %s %s first=%i last=%i' % (tmphed, pngslice, halfbox, halfbox))
	proc = subprocess.Popen(slicecmd, shell=True)
	proc.wait()
	apFile.removeStack(tmphed, warn=False)
	return

#=========================================
#=========================================
def renderSnapshots(density, contour=None, zoom=1.0, sym=None, color=None, 
		silhouette=True, xvfb=True, pdb=None, name=None):
	"""
	create a few snapshots for viewing on the web
	"""
	if isValidVolume(density) is False:
		apDisplay.printError("Volume file is not valid")
	### setup chimera params
	if name is None:
		os.environ['CHIMVOL'] = density
	else:
		### set chimera to use temp volume
		os.environ['CHIMTEMPVOL'] = density
		os.environ['CHIMVOL'] = name
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
	if pdb is not None:
		os.environ['CHIMPDBFILE'] = pdb
	os.environ['CHIMIMGSIZE'] = "1024"
	### unused
	#'CHIMBACK',  'CHIMIMGSIZE', 'CHIMIMGFORMAT', 'CHIMFILEFORMAT',
	chimsnappath = getSnapPath()
	apDisplay.printColor("running Chimera Snapshot for sym "+str(sym), "cyan")
	runChimeraScript(chimsnappath, xvfb=xvfb)

	image1 = os.environ['CHIMVOL']+".1.png"
	if not os.path.isfile(image1):
		apDisplay.printWarning("Chimera failed to generate images")
		runChimeraScript(chimsnappath, xvfb=xvfb)

	if not os.path.isfile(image1):
		apDisplay.printWarning("Chimera failed to generate images, twice")

	return

#=========================================
#=========================================
def renderAnimation(density, contour=None, zoom=1.0, sym=None, color=None,
		silhouette=False, xvfb=True, name=None):
	"""
	create several snapshots and merge into animated GIF
	"""
	if isValidVolume(density) is False:
		apDisplay.printError("Volume file is not valid")
	### setup chimera params
	if name is None:
		os.environ['CHIMVOL'] = density
	else:
		### set chimera to use temp volume
		os.environ['CHIMTEMPVOL'] = density
		os.environ['CHIMVOL'] = name
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
	os.environ['CHIMIMGSIZE'] = "512"
	### unused
	#'CHIMBACK',  'CHIMIMGSIZE', 'CHIMIMGFORMAT', 'CHIMFILEFORMAT',
	chimsnappath = getSnapPath()
	apDisplay.printColor("running Chimera Animation for sym "+str(sym), "cyan")
	runChimeraScript(chimsnappath, xvfb=xvfb)
	image1 = os.environ['CHIMVOL']+".001.png"

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
		proc = subprocess.Popen(imagemagickcmd1, shell=True)
		proc.wait()
		#if os.path.isfile(finalgif):
		apFile.removeFilePattern(density+".*[0-9][0-9].png")
	return

#=========================================
#=========================================
def runChimeraScript(chimscript, xvfb=True):
	if not chimscript or not os.path.isfile(chimscript):
		print chimscript
		apDisplay.printError("Could not find file: apChimSnapshot.py")
	#apDisplay.printColor("Trying to use chimera for model imaging","cyan")
	if xvfb is True:
		port = apParam.resetVirtualFrameBuffer()
		time.sleep(1)
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
	rendercmd = (chimexe+" --debug python:"+chimscript)
	logf = open("chimeraRun.log", "a")
	apDisplay.printColor("running Chimera:\n "+rendercmd, "cyan")
	if xvfb is True:
		print "import -verbose -display :%d -window root screencapture.png"%(port)
	proc = subprocess.Popen(rendercmd, shell=True, stdout=logf, stderr=logf)
	proc.wait()
	logf.close()
	if xvfb is True:
		apParam.killVirtualFrameBuffer(port)
	return

#=========================================
#=========================================
def colorToString(color):
	color = color.lower()
	apDisplay.printMsg("selecting color: "+color)
	### primary colors
	if color == "red":
		apDisplay.printColor("using color RED", "red")
		return "0.71:0.06:0.00,None,0.71:0.06:0.00"
	if color == "orange":
		apDisplay.printColor("using color ORANGE", "orange")
		return "0.90:0.57:0.00,None,0.94:0.57:0.00"
	if color == "yellow":
		apDisplay.printColor("using color YELLOW", "yellow")
		return "0.99:0.89:0.00,None,0.95:0.95:0.00"
	if color == "green":
		apDisplay.printColor("using color GREEN", "green")
		return "0.28:0.59:0.00,None,0.28:0.59:0.00"
	if color == "blue":
		apDisplay.printColor("using color BLUE", "blue")
		return "0.00:0.21:0.75,None,0.00:0.21:0.75"
	if color == "violet":
		apDisplay.printColor("using color VIOLET", "violet")
		return "0.39:0.00:0.51,None,0.39:0.00:0.51"
	### seconary colors
	if color == "red-orange":
		apDisplay.printColor("using color RED_ORANGE", "red")
		return "0.91:0.28:0.00,None,0.91:0.28:0.00"
	if color == "yellow-orange" or color == "gold":
		apDisplay.printColor("using color GOLD", "yellow")
		return "0.94:0.70:0.00,None,0.94:0.70:0.00"
	if color == "yellow-green" or color == "limegreen":
		apDisplay.printColor("using color LIMEGREEN", "yellow")
		return "0.65:0.74:0.07,None,0.65:0.74:0.07"
	if color == "blue-green" or color == "cyan":
		apDisplay.printColor("using color CYAN", "cyan")
		return "0.00:0.54:0.77,None,0.00:0.54:0.77"
	if color == "blue-violet" or color == "purple":
		apDisplay.printColor("using color PURPLE", "violet")
		return "0.18:0.00:0.48,None,0.18:0.00:0.48"
	if color == "red-violet" or color == "maroon" or color == "magenta":
		apDisplay.printColor("using color MAROON", "magenta")
		return "0.49:0.07:0.22,None,0.49:0.07:0.22"
	### boring colors
	if color == "black":
		apDisplay.printColor("using color BLACK", "white")
		return "0.2:0.2:0.2,None,0.2:0.2:0.2"
	if color == "gray":
		apDisplay.printColor("using color GRAY", "white")
		return "0.6:0.6:0.6,None,0.6:0.6:0.6"
	return "None,None,None"

#=========================================
#=========================================
def getColorString():
	#return secondColor()+",None,"+minuteColor()
	first = hourColor()
	#print "first", first
	third = minuteColor()
	#third = secondColor()
	#print "third", third
	colortuple = first+",None,"+third
	#print colortuple
	return colortuple

#=========================================
#=========================================
def dayColor():
	hue = ((time.time()/(24*3600.))%365)/365
	rgbindex = colorsys.hsv_to_rgb(hue, satvalue, hsvalue)
	colorstr = "%.1f:%.1f:%.1f"%(rgbindex[0], rgbindex[1], rgbindex[2])
	return colorstr

#=========================================
#=========================================
def hourColor():
	hue = ((time.time()/3600.)%24)/24
	rgbindex = colorsys.hsv_to_rgb(hue, satvalue, hsvalue)
	colorstr = "%.1f:%.1f:%.1f"%(rgbindex[0], rgbindex[1], rgbindex[2])
	return colorstr

#=========================================
#=========================================
def minuteColor():
	hue = ((time.time()/60.)%60)/60
	rgbindex = colorsys.hsv_to_rgb(hue, satvalue, hsvalue)
	colorstr = "%.1f:%.1f:%.1f"%(rgbindex[0], rgbindex[1], rgbindex[2])
	return colorstr

#=========================================
#=========================================
def secondColor():
	hue = ((time.time()/10.)%60)/60
	rgbindex = colorsys.hsv_to_rgb(hue, satvalue, hsvalue)
	colorstr = "%.1f:%.1f:%.1f"%(rgbindex[0], rgbindex[1], rgbindex[2])
	return colorstr

#=========================================
#=========================================
def randomColor():
	hue = random.random()
	rgbindex = colorsys.hsv_to_rgb(hue, satvalue, hsvalue)
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

