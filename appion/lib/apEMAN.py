
import apDisplay
import subprocess
import sys
import time

#try:
#	import EMAN
#except ImportError:
#	apDisplay.printWarning("EMAN module did not get imported")
#pass

def executeEmanCmd(emancmd, verbose=False, showcmd=True):
	if showcmd is True:
		sys.stderr.write(apDisplay.colorString("EMAN: ","magenta")+emancmd+"\n")
	try:
		if verbose is False:
			emanproc = subprocess.Popen(emancmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		else:
			emanproc = subprocess.Popen(emancmd, shell=True)
		t0 = time.time()
		emanproc.wait()
		tdiff = time.time() - t0
		if tdiff > 20:
			apDisplay.printMsg("completed in "+apDisplay.timeString(tdiff))
	except:
		apDisplay.printWarning("could not run eman command: "+emancmd)
		raise

def getNumParticlesInStack(stackname):
	numparticles = EMAN.fileCount(stackname)[0]
	return numparticles


def getEMANPcmp(ref,img):
	"""returns EMAN quality factor for pcmp properly scaled"""
	dot=ref.pcmp(img)
	return((2.0-dot)*500.0)

def getCC(ref,img):
	"""returns straight up correlation coefficient"""
 	npix=ref.xSize()*ref.ySize()
	avg1=ref.Mean()
	avg2=img.Mean()
	
	var1=ref.Sigma()
	var1=var1*var1
	var2=img.Sigma()
	var2=var2*var2
	
	cc=ref.dot(img)
	cc=cc/npix
	cc=cc-(avg1*avg2)
	cc=cc/math.sqrt(var1*var2)
	return(cc)
