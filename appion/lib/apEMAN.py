import os
import re
import subprocess
import sys
import time
import math
import apDisplay
try:
	import apImagicFile
except:
	print "You must be running on Garibaldi"
try:
	import EMAN
except ImportError:
	apDisplay.printWarning("EMAN module did not get imported")
	pass

#=====================
def writeEMANTime(filename, cmd):
	### write the cmd and time to the filename
	lc=time.strftime("%a %b %d %H:%M:%S %Y", time.localtime())
	out = cmd+"   "+lc+"\n"
	f=open(filename,'a')
	f.write(out)
	f.close()

#=====================
def getNPtcls(filename,spider=False):
	### get number of particles from cls file
	f=open(filename,'r')
	lines=f.readlines()
	f.close()
	nlines=len(lines)
	if spider is True:
		return (nlines-1)
	return(nlines-2)

#=====================
def combineSpiParticleList(infiles, outfile):
	out = open(outfile,'w')
	n=0 # particle number
	for file in infiles:
		f=open(file,'r')
		for line in f:
			if line.strip()[0]!=';':
				p=parseSpiderPtcl(line)
				n += 1
				out.write('%d\t1\t%d\n' % (n,p))
		f.close()
	out.close()
	return

#=====================
def makeClassAverages(lst, outputstack,e,mask):
	#align images in class
	print "creating class average from",lst,"to",outputstack
	images=EMAN.readImages(lst,-1,-1,0)
	for image in images:
		image.rotateAndTranslate()
		if image.isFlipped():
			image.hFlip()

	#make class average
	avg=EMAN.EMData()
	avg.makeMedian(images)

	#write class average
	avg.setRAlign(e)
	avg.setNImg(len(images))
	avg.applyMask(mask,0)
	avg.writeImage(outputstack,-1)

#=====================
def convertSpiderToEMAN(spifile, origlst):
	fileroot = os.path.splitext(spifile)[0]
	outfile = fileroot+".lst"
	out = open(outfile, "w")
	out.write('#LST\n')

	# save ptls in an array from cls####.lst file
	origptls=[]
	f=open(origlst,'r')
	for line in f:
		n=line.split('\t')
		if re.match("^[0-9]+",n[0]) and n[1].strip()!="proj.img":
			origptls.append(line)

	# handle skipped coran because of limited number of prtcls
	if getNPtcls(origlst) < 4:
		for line in origptls:
			out.write(line)
	# create new lst file
	else:
		inlines = open(spifile, "r")
		for line in inlines:
			if line.strip()[0]!=';':
				ptcl = parseSpiderPtcl(line)
				# get this particle in the cls####.lst array
				spiptcl = origptls[ptcl-1]
				out.write(spiptcl)
		inlines.close()

	out.close()
	f.close()
	return outfile

#=====================
def parseSpiderPtcl(line):
	if line.strip()[0]!=';':
		words = line.split()
		ptcl = int(float(words[2]))
	return ptcl

#=====================
def writeBlankImage(outfile,boxsize,place,type=None):
	a=EMAN.EMData()
	a.setSize(boxsize,boxsize)
	a.zero()
	if type == 'spider':
		a.writeImage(outfile,place,EMAN.EMData.SINGLE_SPIDER)
	else:
		a.writeImage(outfile,place)
	return

#=====================
def flagGoodParticleInClassLst(clsfile, goodclsfile):
	# read original class list file
	old_clsfile = open(clsfile,'r')
	ptcls = old_clsfile.readlines()
	ptext = ptcls[:]
	pretext = [ptext[0],ptext[1]]
	del ptext[0]
	del ptext[0]
	old_clsfile.close()

	f = open(goodclsfile,'r')
	f.readline()
	lines=f.readlines()
	f.close()

	goodptcls = []
	plines = lines[2:]
	goodptcls = map((lambda x: int(x.split("\t")[0])),plines)

	for i, t in enumerate(ptext):
		ptcl = int(t.split("\t")[0])
		if ptcl in goodptcls:
			keep='1'
		else:
			keep='0'
		newptext = ptext[i].split('\n')[0]+','+keep+'\n'
		pretext.append(newptext)
	new_clsfile = clsfile+'.new'
	f1 = open(new_clsfile, 'w')
	for l in pretext:
		f1.write(l)
	f1.close()
	os.rename(new_clsfile,clsfile)

#=====================
def executeEmanCmd(emancmd, verbose=False, showcmd=True, logfile=None, fail=False):
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
			emanproc = subprocess.Popen(emancmd, shell=True, 
				stdout=logf, stderr=logf)
		elif verbose is False:
			devnull = open('/dev/null', 'w')
			emanproc = subprocess.Popen(emancmd, shell=True, 
				stdout=devnull, stderr=devnull)
		else:
			emanproc = subprocess.Popen(emancmd, shell=True)
		if verbose is True:
#			emanproc.wait()
			out, err = emanproc.communicate()
			print "EMAN error", out, err
		else:
			out, err = emanproc.communicate()
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
	proc_code = emanproc.returncode
	if proc_code != 0:
		if proc_code == -11:
			if fail is True:
				apDisplay.printError("EMAN failed with Segmentation Fault")
			else:
				apDisplay.printWarning("EMAN failed with Segmentation Fault")
		else:
			if fail is True:
				apDisplay.printError("EMAN failed with subprocess error code %d" % proc_code)
			else:
				apDisplay.printWarning("EMAN failed with subprocess error code %d" % proc_code)
		

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
		numberParticlesInStack(stackname, startnum=0, verbose=True)
	return

def writeImageToImage(instack, inn, outstack, outn=-1, particles=0):
	# copy an image from an input stack to another one
	img = EMAN.EMData()
	img.readImage(instack,inn)
	img.setNImg(particles)
	img.writeImage(outstack,outn)
	return

#=====================
def numberParticlesInStack(stackname, startnum=0, verbose=True):
	### new faster methond
	apImagicFile.numberStackFile(stackname, startnum=0)
	return

	# store the particle number in the stack header
	# NOTE!!! CONFORMS TO EMAN CONVENTION, STARTS AT 0!!!
	t0 = time.time()
	apDisplay.printMsg("saving particle numbers to stack header")
	n=EMAN.fileCount(stackname)[0]
	im=EMAN.EMData()
	i = 0
	back = "\b\b\b\b\b\b\b"
	while i < n:
		j=startnum+i
		im.readImage(stackname,i)
		im.setNImg(j)
		im.writeImage(stackname,i)
		if verbose is True and i%100 == 0:
			sys.stderr.write(back+back+back+str(j)+" of "+str(n))
		i+=1
	sys.stderr.write("\n")
	apDisplay.printMsg("finished in "+apDisplay.timeString(time.time()-t0))
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

#=====================
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

#=====================
def make3d(stack, out, sym="c1", mode=2, hard=None):
	""" use eman make3d to create a density from a class averages stack"""
	apDisplay.printMsg("creating 3d density: %s" % out)
	emancmd="make3d %s out=%s sym=%s mode=%d" % (stack, out, sym, mode)
	if hard is not None:
		emancmd+=" hard=%d" % hard
	executeEmanCmd(emancmd)
	return

