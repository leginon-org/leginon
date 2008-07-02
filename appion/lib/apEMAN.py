
import apDisplay
import subprocess
import sys
import time

#try:
#	import EMAN
#except ImportError:
#	apDisplay.printWarning("EMAN module did not get imported")
#	pass

#=====================
def executeEmanCmd(emancmd, verbose=False, showcmd=True, logfile=None):
	"""
	executes an EMAN command in a controlled fashion
	"""
	waited = False
	if showcmd is True:
		sys.stderr.write(apDisplay.colorString("EMAN: ","magenta")+emancmd+"\n")
	t0 = time.time()
	try:
		if logfile is not None:
			logf = open(logfile, 'a')
			emanproc = subprocess.Popen(emancmd, shell=True, stdout=logf, stderr=logf)
		elif verbose is False:
			emanproc = subprocess.Popen(emancmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		else:
			emanproc = subprocess.Popen(emancmd, shell=True)
		if verbose is True:
			emanproc.wait()
		else:
			### continuous check
			waittime = 2.0
			while emanproc.poll() is None:
				if waittime > 10:
					waited = True
					sys.stderr.write(".")
				waittime *= 1.1
				time.sleep(waittime)
	except:
		apDisplay.printWarning("could not run eman command: "+emancmd)
		raise
	tdiff = time.time() - t0
	if tdiff > 20:
		apDisplay.printMsg("completed in "+apDisplay.timeString(tdiff))
	elif waited is True:
		print ""

#=====================
def getNumParticlesInStack(stackname):
	numparticles = EMAN.fileCount(stackname)[0]
	return numparticles

#=====================
def getEMANPcmp(ref,img):
	"""returns EMAN quality factor for pcmp properly scaled"""
	dot=ref.pcmp(img)
	return((2.0-dot)*500.0)

#=====================
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
