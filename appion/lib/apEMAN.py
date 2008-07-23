
import apDisplay
import subprocess
import sys
import time

try:
	import EMAN
except ImportError:
	apDisplay.printWarning("EMAN module did not get imported")
	pass

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
def checkStackNumbering(stackname):
	# check that the numbering is stored in the NImg parameter
	apDisplay.printMsg("checking that original stack is numbered")
	n=EMAN.fileCount(stackname)[0]
	im=EMAN.EMData()
	im.readImage(stackname,n-1)

	# if last particle is not numbered with same value as # of particles,
	# renumber the entire stack
	if n-1 != im.NImg():
		apDisplay.printWarning("Original stack is not numbered! numbering now...")
		numberParticlesInStack(stackname)
	return
	
#=====================
def numberParticlesInStack(stackname, startnum=0):
	# store the particle number in the stack header
	# NOTE!!! CONFORMS TO EMAN CONVENTION, STARTS AT 0!!!
	apDisplay.printMsg("saving particle numbers to header")
	n=EMAN.fileCount(stackname)[0]
	print n, "particles in stack"
	im=EMAN.EMData()
	for i in range(n):
		j=startnum+i
		im.readImage(stackname,i)
		im.setNImg(j)
		im.writeImage(stackname,i)
		print j
	return

#=====================
def writeStackParticlesToFile(stackname, filename):
	# write out the particle numbers from imagic header to a file
	# NOTE!!! CONFORMS TO EMAN CONVENTION, STARTS AT 0!!!
	apDisplay.printMsg("saving list of saved particles to:")
	apDisplay.printMsg(filename)
	f = open(filename,'w')
	n=EMAN.fileCount(stackname)[0]
	im=EMAN.EMData()
	for i in range(n):
		im.readImage(stackname,i)
		f.write(str(im.NImg())+"\n")
	f.close()
	return

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

def getClassInfo(classes):
	# read a classes.*.img file, get # of images
	imgnum, imgtype = EMAN.fileCount(classes)
	img = EMAN.EMData()
	img.readImage(classes, 0, 1)

	# for projection images, get eulers
	projeulers=[]
	for i in range(imgnum):
		img.readImage(classes, i, 1)
		e = img.getEuler()
		alt = e.thetaMRC()*180./math.pi
		az = e.phiMRC()*180./math.pi
		phi = e.omegaMRC()*180./math.pi
		eulers=[alt,az,phi]
		if i%2==0:
			projeulers.append(eulers)
	return projeulers

