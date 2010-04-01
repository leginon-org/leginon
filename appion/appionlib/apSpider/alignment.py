
## python
import os
import sys
import time
import math
import numpy
import cPickle
## appion
from appionlib import spyder
from appionlib import apEMAN
from appionlib import apImage
from appionlib import apParam
from appionlib import apDisplay
from appionlib import apFile

"""
A large collection of SPIDER functions

I try to keep the trend
image file:
	*****img.spi
image stack file:
	*****stack.spi
doc/keep/reject file:
	*****doc.spi
file with some data:
	*****data.spi

that way its easy to tell what type of file it is

neil
"""

#===============================
def refFreeAlignParticles(stackfile, template, numpart, pixrad,
		firstring=2, lastring=100, dataext=".spi", rundir = "alignment"):
	"""
	inputs:
		stack
		template
		search params
	outputs:
		aligned stack
		rotation/shift params
	"""
	### setup
	if dataext in template:
		template = template[:-4]
	if dataext in stackfile:
		stackfile = stackfile[:-4]
	t0 = time.time()
	apParam.createDirectory(rundir)

	### remove previous iterations
	numiter = 0
	while os.path.isfile(rundir+"/avgimg%02d%s" % (numiter+1, dataext)):
		apFile.removeFile(rundir+"/avgimg%02d%s" % (numiter+1, dataext))
		pngfile = rundir+"/avgimg%02d%s" % (numiter+1, ".png")
		apFile.removeFile(pngfile)
		numiter += 1

	### perform alignment
	mySpider = spyder.SpiderSession(dataext=dataext, logo=True, log=False)
	apDisplay.printMsg("Performing particle alignment")
	# copy template to memory
	mySpider.toSpiderQuiet("CP", (template+"@1"), "_9")
	mySpider.toSpider("AP SR",
		spyder.fileFilter(stackfile)+"@******", "1-"+str(numpart),
		str(int(pixrad)), str(int(firstring))+","+str(int(lastring)),
		"_9", rundir+"/avgimg**", rundir+"/paramdoc**")
	mySpider.close()

	### find number of iterations
	numiter = 0
	while os.path.isfile(rundir+"/avgimg%02d%s" % (numiter+1, dataext)):
		emancmd = ("proc2d "
			+" "+rundir+"/avgimg"+("%02d%s" % (numiter+1, dataext))
			+" "+rundir+"/avgimg"+("%02d%s" % (numiter+1, ".png"))
		)
		apEMAN.executeEmanCmd(emancmd, verbose=False, showcmd=False)
		numiter += 1
	if numiter == 0:
		apDisplay.printError("alignment failed, no iterations were found")
	emancmd = ("proc2d "
		+" "+rundir+"/avgimg"+("%02d%s" % (numiter, dataext))
		+" "+rundir+"/average.mrc"
	)
	apEMAN.executeEmanCmd(emancmd, verbose=False, showcmd=False)
	apDisplay.printMsg(str(numiter)+" alignment iterations were run by spider")

	### convert spider rotation, shift data to python
	docfile = rundir+("/paramdoc%02d" % (numiter))+dataext
	picklefile = rundir+("/paramdoc%02d" % (numiter))+".pickle"
	partlist = readRefFreeDocFile(docfile, picklefile)

	### write aligned stack -- with python loop
	alignedstack = "alignedstack"
	alignStack(stackfile, alignedstack, partlist, dataext)

	td1 = time.time()-t0
	apDisplay.printMsg("completed alignment of "+str(numpart)
		+" particles in "+apDisplay.timeString(td1))

	return ("alignedstack.spi", partlist)

#===============================
def readRefFreeDocFile(docfile, picklefile):
	apDisplay.printMsg("processing alignment doc file")
	if not os.path.isfile(docfile):
		apDisplay.printError("Doc file, "+docfile+" does not exist")
	docf = open(docfile, "r")
	partlist = []
	angs = []
	shifts = []
	for line in docf:
		data = line.strip().split()
		if data[0][0] == ";":
			continue
		if len(data) < 4:
			continue
		angle = wrap360(float(data[2]))
		partdict = {
			'num': int(data[0]),
			'rot': angle,
			'xshift': float(data[3]),
			'yshift': float(data[4]),
		}
		angs.append(angle)
		shift = math.hypot(float(data[3]), float(data[4]))
		shifts.append(shift)
		partlist.append(partdict)
	shifts = numpy.array(shifts, dtype=numpy.float32)
	angs = numpy.array(angs, dtype=numpy.float32)
	apDisplay.printMsg("Angles = %.3f +/- %.3f"%(angs.mean(), angs.std()))
	apDisplay.printMsg("Shifts = %.3f +/- %.3f"%(shifts.mean(), shifts.std()))
	docf.close()
	picklef = open(picklefile, "w")
	cPickle.dump(partlist, picklef)
	picklef.close()
	return partlist

#===============================
def refBasedAlignParticles(stackfile, templatestack,
		origstackfile,
		xysearch, xystep,
		numpart, numtemplate,
		firstring=2, lastring=100,
		dataext=".spi",
		iternum=1, oldpartlist=None):
	"""
	inputs:
		stack
		template
		search params
	outputs:
		aligned stack
		rotation/shift params
	"""
	### setup
	if dataext in templatestack:
		templatestack = templatestack[:-4]
	if dataext in stackfile:
		stackfile = stackfile[:-4]
	if dataext in origstackfile:
		origstackfile = origstackfile[:-4]
	t0 = time.time()
	rundir = "alignments"
	apParam.createDirectory(rundir)
	nproc = apParam.getNumProcessors()

	### remove previous iterations
	apFile.removeFile(rundir+"/paramdoc%02d%s" % (iternum, dataext))

	### perform alignment, should I use 'AP SH' instead?
	mySpider = spyder.SpiderSession(dataext=dataext, logo=True, nproc=nproc, log=False)
	mySpider.toSpider("AP MQ",
		spyder.fileFilter(templatestack)+"@**",     # reference image series
		"1-"+str(numtemplate),                      # enter number of templates of doc file
		str(int(xysearch))+","+str(int(xystep)),    # translation search range, step size
		str(int(firstring))+","+str(int(lastring)), # first and last ring for rotational correlation
		spyder.fileFilter(stackfile)+"@******",     # unaligned image series
		"1-"+str(numpart),                          # enter number of particles of doc file
		rundir+("/paramdoc%02d" % (iternum)),       # output angles document file
	)
	mySpider.close()

	### convert spider rotation, shift data to python
	docfile = rundir+("/paramdoc%02d" % (iternum))+dataext
	picklefile = rundir+("/paramdoc%02d" % (iternum))+".pickle"
	if oldpartlist is not None and iternum > 1:
		apDisplay.printMsg("updating particle doc info")
		partlist = updateRefBasedDocFile(oldpartlist, docfile, picklefile)
	elif iternum == 1:
		apDisplay.printMsg("reading initial particle doc info")
		partlist = readRefBasedDocFile(docfile, picklefile)
	else:
		apDisplay.printError("reading (not updating) particle doc info on iteration "+str(iternum))

	### write aligned stack -- with python loop
	alignedstack = rundir+("/alignedstack%02d" % (iternum))
	alignStack(origstackfile, alignedstack, partlist, dataext)

	### average stack
	emancmd = ( "proc2d "+alignedstack+dataext+" "
		+rundir+("/avgimg%02d" % (iternum))+".mrc "
		+" average")
	apEMAN.executeEmanCmd(emancmd, verbose=False, showcmd=True)

	td1 = time.time()-t0

	apDisplay.printMsg("completed alignment of "+str(numpart)
		+" particles in "+apDisplay.timeString(td1))
	if numpart < 1:
		apDisplay.printError("Failed to find any particles")

	return alignedstack+dataext, partlist

#===============================
def updateRefBasedDocFile(oldpartlist, docfile, picklefile):
	apDisplay.printMsg("updating data from alignment doc file "+docfile)
	if not os.path.isfile(docfile):
		apDisplay.printError("Doc file, "+docfile+" does not exist")
	docf = open(docfile, "r")
	partlist = []
	angs = []
	shifts = []
	for line in docf:
		data = line.strip().split()
		if data[0][0] == ";":
			continue
		if len(data) < 6:
			continue
		templatenum = float(data[2])
		angle = wrap360(float(data[4]))
		newpartdict = {
			'num': int(data[0]),
			'template': int(abs(templatenum)),
			'mirror': checkMirror(templatenum),
			'score': float(data[3]),
			'rot': angle,
			'xshift': float(data[5]),
			'yshift': float(data[6]),
		}
		angs.append(angle)
		shift = math.hypot(float(data[5]), float(data[6]))
		shifts.append(shift)
		oldpartdict = oldpartlist[newpartdict['num']-1]
		### this is wrong because the shifts are not additive without a back rotation
		if newpartdict['num'] == oldpartdict['num']:
			partdict = getNewPartDict(oldpartdict, newpartdict)
		else:
			print oldpartdict
			print newpartdict
			apDisplay.printError("wrong particle in update")
		partlist.append(partdict)
	shifts = numpy.array(shifts, dtype=numpy.float32)
	angs = numpy.array(angs, dtype=numpy.float32)
	apDisplay.printMsg("Angles = %.3f +/- %.3f"%(angs.mean(), angs.std()))
	apDisplay.printMsg("Shifts = %.3f +/- %.3f"%(shifts.mean(), shifts.std()))
	docf.close()
	picklef = open(picklefile, "w")
	cPickle.dump(partlist, picklef)
	picklef.close()
	return partlist

#===============================
def getNewPartDict(oldpartdict, newpartdict):
	"""
	### solved matrix
	#define
	R[C,S] := matrix([C,S,0],[-S,C,0],[0,0,1]);
	S[Sx,Sy] := matrix([1,0,Sx],[0,1,Sy],[0,0,1]);
	M[My] := matrix([My,0,0],[0,1,0],[0,0,1]);
	T[C, S, Sx, Sy, My] := M[My].S[Sx,Sy].R[C,S]

	#composite
	T[C1, S1, Sx1, Sy1, My1] = 
	matrix([My1*C1,My1*S1,My1*(Sy1*S1+Sx1*C1)],[-S1,C1,Sy1*C1-Sx1*S1],[0,0,1])

	My' = My1*My2
	My3 = My'*My2
	M[My'].T[C2,S2,Sx2,Sy2,My2].T[C1,S1,Sx1,Sy1,My1] =
	matrix(
		[My3*(My1*C1*C2 - S1*S2), My3*(C1*S2 + My1*C2*S1), My3*(Sy1*S2 + My1*Sx1*C2 + Sx2)],
		[-My1*C1*S2 - C2*S1,      C1*C2 - My1*S1*S2,            Sy1*C2 - My1*Sx1*S2 + Sy2 ],
		[0,0,1]
	)

	## figure out rotation
	# double mirror
	trigreduce(T[cos(t2),sin(t2),0,0,-1].T[cos(t1),sin(t1),0,0,-1])
	# equal unmirror with negative t2
	trigreduce(T[cos(-t2),sin(-t2),0,0,1].T[cos(t1),sin(t1),0,0,1])
	"""
	### setup values
	newrot = math.radians(newpartdict['rot'])
	oldrot = math.radians(oldpartdict['rot'])
	#newmir = evalMirror(newpartdict['mirror'])
	S1 = math.sin(oldrot)
	C1 = math.cos(oldrot)
	S2 = math.sin(newrot)
	C2 = math.cos(newrot)
	My1 = evalMirror(oldpartdict['mirror'])
	My2 = evalMirror(newpartdict['mirror'])
	Sx1 = oldpartdict['xshift']
	Sy1 = oldpartdict['yshift']
	Sx2 = newpartdict['xshift']
	Sy2 = newpartdict['yshift']

	### calculate complex values
	### mirroring
	#My' = My1 * My2
	totalmir = bool(oldpartdict['mirror'] - newpartdict['mirror'])
	My3 = evalMirror(totalmir)

	### x shift
	#Sx' = My3*My2*(Sy1*S2 + My1*Sx1*C2 + Sx2)
	totalxshift = My3*My2*(Sy1*S2 + My1*Sx1*C2 + Sx2)

	### y shift
	#Sy' = -My1*Sx1*S2 + Sy1*C2 + Sy2
	totalyshift = -My1*Sx1*S2 + Sy1*C2 + Sy2

	### rotation
	#t' =  t1 + My1*t2
	totalrot = wrap360(oldpartdict['rot'] + My1*newpartdict['rot'])

	partdict = {
		'num': newpartdict['num'],
		'template': newpartdict['template'],
		'score': newpartdict['score'],
		'mirror': totalmir,
		'rot': totalrot,
		'xshift': totalxshift,
		'yshift': totalyshift,
	}
	"""
	if partdict['num'] in [3,6,7]:
		print ("old", oldpartdict['num'], oldpartdict['template'], 
			oldpartdict['mirror'], round(oldpartdict['rot'],3))
		print ("new", newpartdict['num'], newpartdict['template'], 
			newpartdict['mirror'], round(newpartdict['rot'],3))
		print ("update", partdict['num'], partdict['template'], 
			partdict['mirror'], round(partdict['rot'],3))
	"""
	return partdict


#===============================
def evalMirror(mirror):
	return -1*(int(mirror)*2 - 1)

#===============================
def wrap360(theta):
	f = theta % 360
	if f > 180:
		f = f - 360
	return f

#===============================
def readRefBasedDocFile(docfile, picklefile):
	apDisplay.printMsg("processing alignment doc file "+docfile)
	if not os.path.isfile(docfile):
		apDisplay.printError("Doc file, "+docfile+" does not exist")
	docf = open(docfile, "r")
	partlist = []
	angs = []
	shifts = []
	for line in docf:
		data = line.strip().split()
		if data[0][0] == ";":
			continue
		if len(data) < 6:
			continue
		templatenum = float(data[2])
		angle = wrap360(float(data[4]))
		partdict = {
			'num': int(data[0]),
			'template': int(abs(templatenum)),
			'mirror': checkMirror(templatenum),
			'score': float(data[3]),
			'rot': angle,
			'xshift': float(data[5]),
			'yshift': float(data[6]),
		}
		angs.append(angle)
		shift = math.hypot(float(data[5]), float(data[6]))
		shifts.append(shift)
		partlist.append(partdict)
	docf.close()
	shifts = numpy.array(shifts, dtype=numpy.float32)
	angs = numpy.array(angs, dtype=numpy.float32)
	apDisplay.printMsg("Angles = %.3f +/- %.3f"%(angs.mean(), angs.std()))
	apDisplay.printMsg("Shifts = %.3f +/- %.3f"%(shifts.mean(), shifts.std()))
	picklef = open(picklefile, "w")
	cPickle.dump(partlist, picklef)
	picklef.close()
	return partlist

#===============================
def checkMirror(templatenum):
	if templatenum < 0:
		return True
	return False

#===============================
def alignStack(oldstack, alignedstack, partlist, dataext=".spi"):
	"""
	write aligned stack -- with python loop

	inputs:
		oldstack
		newstack (empty)
		list of particle dictionaries for operations
	modifies:
		newstack
	output:
		none

	I tried this loop in both spider and python;
	python was faster?!? -neil
	"""
	if not os.path.isfile(oldstack+dataext):
		apDisplay.printError("Could not find original stack: "+oldstack+dataext)
	boxsize = apFile.getBoxSize(oldstack+dataext)

	apDisplay.printMsg("applying alignment parameters to stack")
	apFile.removeFile(alignedstack+dataext)
	count = 0
	t0 = time.time()
	nproc = apParam.getNumProcessors()

	mySpider = spyder.SpiderSession(dataext=dataext, logo=True, nproc=nproc, log=False)
	#create stack in core
	numpart = len(partlist)
	mySpider.toSpiderQuiet(
		"MS I", #command
		"_2@", #name
		"%d,%d,%d"%(boxsize), #boxsize
		str(numpart+1), #num part to create in memory
		str(numpart+1), #max particle number
	)
	for partdict in partlist:
		partnum = partdict['num']
		#if partdict['num'] in [3,6,7]:
		#	print partdict['num'], partdict['template'], partdict['mirror'], round(partdict['rot'],3)

		### Rotate and Shift operations
		count += 1
		#rotate/shift
		mySpider.toSpiderQuiet(
			"RT SQ",
			spyder.fileFilter(oldstack)+"@"+("%06d" % (partnum)),
			"_1",
			str(partdict['rot']), str(partdict['xshift'])+","+str(partdict['yshift']),
		)
		#mirror, if necessary
		if 'mirror' in partdict and partdict['mirror'] is True:
			mySpider.toSpiderQuiet(
				"MR", "_1",
				"_2@"+("%06d" % (partnum)),	"Y",
			)
		else:
			mySpider.toSpiderQuiet(
				"CP", "_1",
				"_2@"+("%06d" % (partnum)),
			)

	### finish up
	#save stack to file
	mySpider.toSpiderQuiet(
		"CP", "_2@",
		spyder.fileFilter(alignedstack)+"@",
	)
	#delete stack
	mySpider.toSpiderQuiet(
		"DE", "_2",
	)
	mySpider.close()

	apDisplay.printMsg("Completed transforming %d particles in %s"%(count, apDisplay.timeString(time.time()-t0)))
	if count < 1:
		apDisplay.printError("Failed to transform any particles")

	if not os.path.isfile(alignedstack+dataext):
		apDisplay.printError("Failed to create stack "+alignedstack+dataext)

	return
