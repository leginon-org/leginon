
## python
import time
import os
import re
import subprocess
import cPickle
import sys
import math
import random
import numpy
## PIL
## spider
import spyder
## EMAN
import EMAN
## appion
import apEMAN
import apParam
import apDisplay
import apFile
from apSpider import operations

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
def stackToSpiderStack(stack,spiderstack,apix,boxsize,lp=0,hp=0,bin=1,numpart=0):
	"""
	convert an input stack (i.e. imagic) and write it out to a spider-formatted stack
	"""
	emancmd  = "proc2d "
	if not os.path.isfile(stack):
		apDisplay.printError("stackfile does not exist: "+stack)
	emancmd += stack+" "

	apFile.removeFile(spiderstack, warn=True)
	emancmd += spiderstack+" "

	emancmd += "apix="+str(apix)+" "
	if lp > 0:
		emancmd += "lp="+str(lp)+" "
	if hp > 0:
		emancmd += "hp="+str(hp)+" "
	if bin > 1:
		clipboxsize = boxsize*bin
		emancmd += "shrink="+str(bin)+" "
		emancmd += "clip="+str(clipboxsize)+","+str(clipboxsize)+" "
	if numpart > 0:
		emancmd += "last="+str(numpart-1)+" "
	emancmd += "spiderswap edgenorm"
	starttime = time.time()
	apDisplay.printColor("Running spider stack conversion this can take a while", "cyan")
	apEMAN.executeEmanCmd(emancmd, verbose=True)
	apDisplay.printColor("finished eman in "+apDisplay.timeString(time.time()-starttime), "cyan")
	return

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

def runCoranClass(params,cls):
	print "processing class",cls

	#set up cls dir
	clsdir=cls.split('.')[0]+'.dir'
	os.mkdir(clsdir)

	clscmd='clstoaligned.py ' + cls
	## if multiprocessor, don't run clstoaligned yet
	if params['proc'] == 1:
		#make aligned stack
		proc = subprocess.Popen(clscmd, shell=True)
		proc.wait()

	corancmd=clscmd+'\n'

	coranbatch='coranfor'+cls.split('.')[0]+'.bat'

	#make spider batch
	params['nptcls']=apEMAN.getNPtcls(cls)

	# if no particles, create an empty class average
	if params['nptcls'] == 0:
		# don't run clscmd, just make directory and empty average
		apEMAN.writeBlankImage(os.path.join(clsdir,'classes_avg.spi'),params['boxsize'],0,'spider')
		print "WARNING!! no particles in class"
		return

	# if only 3 particles or less, turn particles into the class averages
	elif params['nptcls'] < 4:
		#this is an ugly hack, just average the particles together, no ref-free
		# don't use mpi, just make directory with clscmd and average particles
		proc = subprocess.Popen(clscmd, shell=True)
		proc.wait()
		avgcmd=("proc2d %s %s average" % (os.path.join(clsdir,'aligned.spi'),os.path.join(clsdir,'classes_avg.spi')))
		proc = subprocess.Popen(avgcmd, shell=True)
		proc.wait()
		dummyclsdir=os.path.join(clsdir,'classes')
		os.mkdir(dummyclsdir)
		dummyfilename='clhc_cls0001.spi'
		dummyfile=open(os.path.join(dummyclsdir,dummyfilename),'w')
		dummyfile.write(';bat/spi\n')
		for ptcl in range(0,params['nptcls']):
			dummyfile.write('%d 1 %d\n' % (ptcl,ptcl+1))
		dummyfile.close()
		print "WARNING!! not enough particles in class for subclassification"
		return

	# otherwise, run coran
	else:
		makeSpiderCoranBatch(params,coranbatch,clsdir)
		### this is how we should do this
		#mySpider = spyder.SpiderSession(logo=False, nproc=1)
		#mySpider.toSpiderQuiet("@%s\n" % coranbatch.split('.')[0])
		spidercmd = ("cd %s\n" % clsdir)
		
		if params['hp'] is not None:
			spidercmd+=("proc2d aligned.spi alignedhp.spi spiderswap apix=%s hp=%s\n" % (params['apix'],params['hp']))
		spidercmd+= ("spider bat/spi @%s\n" % coranbatch.split('.')[0])
		## if multiprocessor, don't run spider yet
		if params['proc'] == 1:
			proc = subprocess.Popen(spidercmd, shell=True)
			proc.wait()
		corancmd+=spidercmd
		return corancmd

#===============================
def readDocFile(docfile):
	"""
	returns an array of the values contained within a spider doc file
	"""
	if not os.path.isfile(docfile):
		apDisplay.printError("Doc file: '"+docfile+"' does not exist")
	docf = open(docfile,"r")
	content=[]
	for line in docf:
		d = line.strip().split()
		if d[0][0]==";":
			continue
		if len(d) < 3:
			continue
		content.append(d)
	return content
	
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
def copyImg(inimg,outimg,dataext=".spi",inMySpi=False):
	if inMySpi is False:
		mySpi = spyder.SpiderSession(dataext=dataext, logo=False, log=False)
	else:
		mySpi=inMySpi
	img1=spyder.fileFilter(inimg)
	img2=spyder.fileFilter(outimg)
	mySpi.toSpiderQuiet("CP",img1,img2)
	if inMySpi is False:
		mySpi.close()

#===============================
def mirrorImg(inimg,outimg,dataext=".spi",inMySpi=False):
	if inMySpi is False:
		mySpi = spyder.SpiderSession(dataext=dataext, logo=False, log=False)
	else:
		mySpi=inMySpi
	img1=spyder.fileFilter(inimg)
	img2=spyder.fileFilter(outimg)
	mySpi.toSpiderQuiet("MR",img1,img2,"Y")
	if inMySpi is False:
		mySpi.close()

#===============================
def rotAndShiftImg(inimg,outimg,rot=0,shx=0,shy=0,dataext=".spi",inMySpi=False):
	if inMySpi is False:
		mySpi = spyder.SpiderSession(dataext=dataext, logo=False, log=False)
	else:
		mySpi=inMySpi
	img1=spyder.fileFilter(inimg)
	img2=spyder.fileFilter(outimg)
	mySpi.toSpiderQuiet("RT SQ",img1,img2,rot,str(shx)+","+str(shy))
	if inMySpi is False:
		mySpi.close()

#===============================
def maskImg(inimg,outimg,outrad,cutoff,background="P",inrad="0",center="0",dataext=".spi",inMySpi=False):
	if inMySpi is False:
		mySpi = spyder.SpiderSession(dataext=dataext,logo=False,log=False)
	else:
		mySpi=inMySpi
	img1=spyder.fileFilter(inimg)
	img2=spyder.fileFilter(outimg)
	mySpi.toSpiderQuiet("MA",img1,img2,str(outrad)+","+str(inrad),cutoff,background)
	if background=="E":
		mySpi.toSpiderQuiet("0",str(center)+","+str(center))
	if cutoff=="C" or cutoff=="G":
		mySpi.toSpiderQuiet("3.5")
	if inMySpi is False:
		mySpi.close()

#===============================
def padImg(inimg,outimg,dim,avg,topleftx,toplefty,const=1.2,dataext=".spi",inMySpi=False):
	if inMySpi is False:
		mySpi = spyder.SpiderSession(dataext=dataext,logo=False,log=False)
	else:
		mySpi=inMySpi
	img1=spyder.fileFilter(inimg)
	img2=spyder.fileFilter(outimg)
	mySpi.toSpiderQuiet(
		"PD",
		img1,
		img2,
		str(dim)+","+str(dim),
		avg,
	)
	if avg=="N" or avg=="n":
		mySpi.toSpiderQuiet(str(const))
	mySpi.toSpiderQuiet(str(topleftx)+","+str(toplefty))
	if inMySpi is False:
		mySpi.close()

#===============================
def windowImg(inimg,outimg,dim,topleftx,toplefty,dataext=".spi",inMySpi=False):
	if inMySpi is False:
		mySpi = spyder.SpiderSession(dataext=dataext,logo=False,log=False)
	else:
		mySpi=inMySpi
	img1=spyder.fileFilter(inimg)
	img2=spyder.fileFilter(outimg)
	mySpi.toSpiderQuiet(
		"WI",
		img1,
		img2,
		str(dim)+","+str(dim),
		str(topleftx)+","+str(toplefty)
	)
	if inMySpi is False:
		mySpi.close()

#===============================
def getCC(image1,image2,outcc,dataext=".spi",inMySpi=False):
	if inMySpi is False:
		mySpi = spyder.SpiderSession(dataext=dataext,logo=False,log=False)
	else:
		mySpi=inMySpi
	img1=spyder.fileFilter(image1)
	img2=spyder.fileFilter(image2)
	outimg=spyder.fileFilter(outcc)
	mySpi.toSpiderQuiet("CC N",img1,img2,outimg)
	if inMySpi is False:
		mySpi.close()

#===============================
def docSplit(file1,file2,file3,dataext=".spi",inMySpi=False):
	if inMySpi is False:
		mySpi = spyder.SpiderSession(dataext=dataext,logo=False,log=False)
	else:
		mySpi=inMySpi
	checkFile(file2)
	checkFile(file3)
	f1=spyder.fileFilter(file1)
	f2=spyder.fileFilter(file2)
	f3=spyder.fileFilter(file3)
	mySpi.toSpiderQuiet("DOC SPLIT",f1,f2,f3)
	if inMySpi is False:
		mySpi.close()

#===============================
def calcFSC(vol1,vol2,fscfile,dataext=".spi",inMySpi=False):
	"""
	Calculate the differential 3-D phase residual and the
	Fourier Shell Correlation between two volumes.
	The Differential Phase Residual over a shell with thickness
	given by shell width and the Fourier Shell Correlation
	between shells of specified widths are computed and stored
	in the document file.
	"""
	if inMySpi is False:
		mySpi = spyder.SpiderSession(dataext=dataext,logo=False,log=False)
	else:
		mySpi=inMySpi
	checkFile(fscfile)
	v1=spyder.fileFilter(vol1)
	v2=spyder.fileFilter(vol2)
	fsc=spyder.fileFilter(fscfile)
	mySpi.toSpiderQuiet("RF 3",v1,v2,"1","0.5,1.5","C","90","3",fsc)
	if inMySpi is False:
		mySpi.close()

#===============================
def spiderFSCtoEMAN(spiderFSC,emanFSC):
	"""
	Convert a spider-formatted fsc resulting from RF 3
	to the EMAN-style FSC plot
	"""
	infile = readDocFile(spiderFSC)
	outfile = open(emanFSC,"w")
	for i in range(0,len(infile)):
		pix = int(infile[i][0])-1
		cc = float(infile[i][4])
		outfile.write("%d\t%.6f\n" % (pix,cc))
	outfile.close()

#===============================
def symmetryDoc(symtype,symfold=None,outfile="sym.spi",dataext=".spi"):
	mySpi=spyder.SpiderSession(dataext=dataext,logo=False,log=False)
	checkFile(outfile)
	mySpi.toSpiderQuiet("SY",spyder.fileFilter(outfile),symtype)
	if symfold is not None:
		mySpi.toSpiderQuiet(symfold)
	mySpi.close()

#===============================
def backProjection(
		stack,
		select,
		ang,
		out,
		sym=None,
		nproc=1,
		dataext=".spi",
		inMySpi=False):
	if inMySpi is False:
		mySpi = spyder.SpiderSession(nproc=nproc,dataext=dataext,logo=False,log=False)
	else:
		mySpi=inMySpi
	checkFile(out)

	if sym is None:
		sym="*"
	mySpi.toSpiderQuiet(
		"BP 3F",
		spyder.fileFilter(stack)+"@******",
		spyder.fileFilter(select),
		spyder.fileFilter(ang),
		spyder.fileFilter(sym),
		spyder.fileFilter(out)
	)
	if inMySpi is False:
		mySpi.close()

#===============================
def iterativeBackProjection(
		stack,
		select,
		rad,
		ang,
		out,
		lam,
		iterlimit,
		mode,
		smoothfac,
		sym=None,
		nproc=1,
		dataext=".spi",
		inMySpi=False):
	if inMySpi is False:
		mySpi = spyder.SpiderSession(nproc=nproc,dataext=dataext,logo=False,log=False)
	else:
		mySpi=inMySpi

	if sym is None:
		sym="*"
	checkFile(out)
	# calculate the smoothing factor
	smooth=(1/(1+6*lam))*smoothfac
	mySpi.toSpiderQuiet("x11=0")
	mySpi.toSpiderQuiet("x47="+str(lam))
	mySpi.toSpiderQuiet("x48="+str(smooth))
	mySpi.toSpiderQuiet("DO LB11 i=1,%d" % (iterlimit*2))
	mySpi.toSpiderQuiet("IF (x11.EQ.%d) GOTO LB11" % iterlimit)
	mySpi.toSpiderQuiet(
		"BP RP x11",
		spyder.fileFilter(stack)+"@******",
		spyder.fileFilter(select),
		"("+str(rad)+")",
		spyder.fileFilter(ang),
		spyder.fileFilter(sym),
		spyder.fileFilter(out),
		"(x47,0)",
		"("+str(iterlimit)+","+str(mode)+")",
		"(0,0)",
		"x48",
	)

	# check if BP RP finished the requested iterations,
	# if not, modify lambda and smoothing constant and rerun
	mySpi.toSpiderQuiet("IF (x11.LT.%d) THEN" % iterlimit)
	mySpi.toSpiderQuiet("x47=x47/2")
	mySpi.toSpiderQuiet("x48=(1/1+6*x47))*"+str(smoothfac))
	mySpi.toSpiderQuiet("GOTO LB11")
	mySpi.toSpiderQuiet("ENDIF")
	mySpi.toSpiderQuiet("LB11")
	if inMySpi is False:
		mySpi.close()

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


#===============================
def correspondenceAnalysis(alignedstack, boxsize, maskpixrad, numpart, numfactors=8, dataext=".spi"):
	"""
	inputs:
		aligned stack
		search params
	outputs:
		eigen images
		eigen vectors
		coran parameters
	"""
	### setup
	if dataext in alignedstack:
		alignedstack = alignedstack[:-4]
	t0 = time.time()
	rundir = "coran"
	apParam.createDirectory(rundir)

	### make template in memory
	mySpider = spyder.SpiderSession(dataext=dataext, logo=True, log=False)
	mySpider.toSpiderQuiet("MO", "_9", "%d,%d" % (boxsize, boxsize), "C", str(maskpixrad*2.0))

	### performing correspondence analysis
	apDisplay.printMsg("Performing correspondence analysis (long wait)")
	mySpider.toSpider(
		"CA S",
		spyder.fileFilter(alignedstack)+"@******", "1-"+str(numpart),
		"_9", str(numfactors), "C", "10",
		rundir+"/corandata")
	mySpider.close()

	contriblist = analyzeEigenFactors(alignedstack, rundir, numpart, numfactors, dataext)

	td1 = time.time()-t0
	apDisplay.printMsg("completed correspondence analysis of "+str(numpart)
		+" particles in "+apDisplay.timeString(td1))

	return contriblist


#===============================
def analyzeEigenFactors(alignedstack, rundir, numpart, numfactors=8, dataext=".spi"):
	"""
	inputs:
		coran run data
	outputs:
		1. generate eigen images
		2. collect eigenimage contribution percentage
		3. 2D factor plot
		Broken 4. 2D factor plot visualization
	"""
	### 1. generate eigen images
	mySpider = spyder.SpiderSession(dataext=dataext, logo=False, log=False)
	for fact in range(1,numfactors+1):
		mySpider.toSpiderQuiet(
			#"CA SRE", rundir+"/corandata", str(fact),
			#rundir+"/eigenstack@"+("%02d" % (fact)), )
			"CA SRD", rundir+"/corandata", str(fact), str(fact),
			rundir+"/eigenstack@***", )
	mySpider.close()

	### convert to nice individual eigen image pngs for webpage
	eigenspistack = os.path.join(rundir, "eigenstack.spi")
	if not os.path.isfile(eigenspistack):
		apDisplay.printError("Failed to create Eigen images")
	for fact in range(1,numfactors+1):
		pngfile = rundir+"/eigenimg"+("%02d" % (fact))+".png"
		apFile.removeFile(pngfile)
		emancmd = ("proc2d "+eigenspistack+" "
			+pngfile+" "
			+" first="+str(fact-1)+" last="+str(fact-1))
		apEMAN.executeEmanCmd(emancmd, verbose=False, showcmd=False)

	### convert eigen SPIDER stack to IMAGIC for stack viewer
	eigenimagicstack = rundir+"/eigenstack.hed"
	apFile.removeStack(eigenimagicstack)
	emancmd = "proc2d "+eigenspistack+" "+eigenimagicstack
	apEMAN.executeEmanCmd(emancmd, verbose=False, showcmd=True)

	### 2. collect eigenimage contribution percentage
	eigf = open(rundir+"/corandata_EIG"+dataext, "r")
	count = 0
	contriblist = []
	for line in eigf:
		bits = line.strip().split()
		if len(contriblist) == numfactors:
			break
		if len(bits) < 3:
			continue
		contrib = float(bits[1])
		cumm = float(bits[2])
		eigval = float(bits[0])
		if len(bits) == 3:
			count += 1
			contriblist.append(contrib)
			print "Factor", count, contrib, "%\t", cumm, "%\t", eigval
	### need to plot & insert this data

	### hack to get 'CA VIS' to work: break up stack into individual particles
	"""
	### this is broken in SPIDER 13.0
	apParam.createDirectory("unstacked")
	mySpider = spyder.SpiderSession(dataext=dataext, logo=False)
	mySpider.toSpiderQuiet(
		"DO LB1 i=1,"+str(numpart),
		" CP",
		" "+alignedstack+"@{******x0}",
		" unstacked/img{******x0}",
		"LB1",
	)
	mySpider.close()
	"""

	### generate factor maps
	apDisplay.printMsg("creating factor maps")
	for f1 in range(1,min(numfactors,2)):
		for f2 in range(f1+1, min(3,numfactors+1)):
			sys.stderr.write(".")
			try:
				createFactorMap(f1, f2, rundir, dataext)
			except:
				sys.stderr.write("#")
				pass
	sys.stderr.write("\n")

	return contriblist

#===============================
def createClassAverages(stack,projs,apmq,numprojs,boxsz,outclass="classes",rotated=False,shifted=False,dataext=".spi"):
	"""
	creates EMAN-style class average file "classes.hed" & "classes.img"
	and variance files "variances.hed" & "variances.img"
	from spider classification
	"""
	checkFile(outclass)
	outf=spyder.fileFilter(outclass)
	outvf="tmpvar"
	apmqlist = readDocFile(apmq)
	mySpi = spyder.SpiderSession(dataext=dataext, logo=False, log=False)

	# create file containing the number of particles matched to each projection
	mySpi.toSpiderQuiet(
		"VO MQ",
		"0.0",
		spyder.fileFilter(apmq),
		str(numprojs),
		"cls*****",
		"numinclass",
	)
	mySpi.close()
	os.remove("numinclass%s" % dataext)

	# create class average file
	mySpi = spyder.SpiderSession(dataext=dataext, logo=False, log=False)
	for i in range(0,numprojs):
		clsfile = readDocFile("cls%05d%s" % (i+1,dataext))
		if clsfile == []:
			apDisplay.printMsg("class %d has no particles" %(i+1))
			mySpi.toSpiderQuiet("BL","%s@%d" % (outf,(i+1)),"(%d,%d)" % (boxsz,boxsz),"N","(0.0)",)
			mySpi.toSpiderQuiet("BL","%s@%d" % (outvf,(i+1)),"(%d,%d)" % (boxsz,boxsz),"N","(0.0)",)
		else:
			mySpi.toSpiderQuiet("DE","_2@")
			mySpi.toSpiderQuiet("MS","_2@","%d,%d,1" % (boxsz,boxsz), str(len(clsfile)))
			for p in range(0,len(clsfile)):
				mySpi.toSpiderQuiet("DE","_1")
				# get the particle
				part = int(float(clsfile[p][2]))-1
				pimg = spyder.fileFilter(stack)+"@%d"%(part+1)
				
				rot=float(apmqlist[part][4])
				shx=float(apmqlist[part][5])
				shy=float(apmqlist[part][6])
				if shifted is True:
					shx=0
					shy=0
				if rotated is True:
					rot=0
				p_out="_2@%d" % (p+1)
				rotAndShiftImg(
					pimg,
					"_1",
					rot,
					shx,
					shy,
					inMySpi=mySpi
				)
				# mirror
				if int(float(apmqlist[part][2])) < 0:
					mirrorImg("_1",p_out,inMySpi=mySpi)
				else:
					mySpi.toSpiderQuiet("CP","_1",p_out)
			if len(clsfile) == 1:
				mySpi.toSpiderQuiet("CP","_2@1","%s@%d" % (outf,(i+1)))
				mySpi.toSpiderQuiet("BL","%s@%d" % (outvf,(i+1)),"(%d,%d)" % (boxsz,boxsz),"N","(0.0)",)
			else:
				mySpi.toSpiderQuiet("AS R","_2@*****","1-%d" % len(clsfile), "A","%s@%d" % (outf,(i+1)),"%s@%d" % (outvf,i+1))
	mySpi.close()

	# convert the class averages to EMAN class averages
	# read classes & projections for EMAN classes output
	if os.path.exists('variances.hed'):
		os.remove('variances.hed')
	if os.path.exists('variances.img'):
		os.remove('variances.img')
	if os.path.exists('classes.hed'):
		os.remove('classes.hed')
	if os.path.exists('classes.img'):
		os.remove('classes.img')
	variances = EMAN.readImages(outvf+dataext,-1,-1,0)
	averages = EMAN.readImages(outf+dataext,-1,-1,0)
	projections=EMAN.readImages(projs,-1,-1,0)
	for i in range (0,numprojs):
		# copy projection to class average file
		projections[i].writeImage('classes.hed')
		projections[i].writeImage('variances.hed')
		# get num of particles in class
		clsfile=readDocFile("cls%05d%s" % (i+1,dataext))
		averages[i].setNImg(len(clsfile))
		averages[i].writeImage('classes.hed',-1)
		variances[i].setNImg(len(clsfile))
		variances[i].writeImage('variances.hed',-1)
		os.remove("cls%05d%s" % (i+1,dataext))
	os.remove(outf+dataext)
	return

#===============================
def createFactorMap(f1, f2, rundir, dataext):
	### 3. factor plot
	apParam.createDirectory(rundir+"/factors", warning=False)
	mySpider = spyder.SpiderSession(dataext=dataext, logo=False, log=False)
	factorfile = rundir+"/factors/factorps"+("%02d-%02d" % (f1,f2))
	mySpider.toSpiderQuiet(
		"CA SM", "I",
		rundir+"/corandata", #coran prefix
		"0",
		str(f1)+","+str(f2), #factors to plot
		"S", "+", "Y",
		"5", "0",
		factorfile,
		"\n\n\n\n","\n\n\n\n","\n", #9 extra steps, use defaults
	)
	time.sleep(2)
	mySpider.close()
	# hack to get postscript converted to png, require ImageMagick
	convertPostscriptToPng(factorfile+".ps", factorfile+".png", size=200)
	apFile.removeFile(factorfile+".ps")

	### 4. factor plot visualization
	"""
	### this is broken in SPIDER 13.0
	mySpider = spyder.SpiderSession(dataext=dataext, logo=False)
	mySpider.toSpider(
		"SD C", #create coordinate file
		rundir+"/corandata", #coran prefix
		str(f1)+","+str(f2), #factors to plot
		rundir+"/sdcdoc"+("%02d%02d" % (f1,f2)),
	)
	visimg = rundir+"/visimg"+("%02d%02d" % (f1,f2))
	mySpider.toSpider(
		"CA VIS", #visualization
		"(1024,1024)",
		rundir+"/sdcdoc"+("%02d%02d" % (f1,f2)), #input doc from 'sd c'
		rundir+"/visdoc"+("%02d%02d" % (f1,f2)), #output doc
		"alignedstack@00001", # image in series ???
		"(12,12)", #num of rows, cols
		"5.0",       #stdev range
		"(5.0,5.0)",   #upper, lower thresh
		visimg, #output image
		"1,"+str(numpart),
		"1,2",
	)
	mySpider.close()
	emancmd = ("proc2d "+visimg+dataext+" "+visimg+".png ")
	apEMAN.executeEmanCmd(emancmd, verbose=False, showcmd=False)
	"""
	return

#===============================
def makeDendrogram(numfactors=1, corandata="coran/corandata", dataext=".spi"):

	rundir = "cluster"
	apParam.createDirectory(rundir)
	### make list of factors
	factorstr = ""
	for fact in range(1,numfactors+1):
		factorstr += str(fact)+","
	factorstr = factorstr[:-1]

	### do hierarchical clustering
	mySpider = spyder.SpiderSession(dataext=dataext, logo=False, log=True)
	mySpider.toSpider(
		"CL HC",
		corandata+"_IMC", # path to coran data
		factorstr, # factor string
	)

	## weight for each factor
	for fact in range(numfactors):
		mySpider.toSpiderQuiet("1.0")
	mySpider.toSpider(
		"5",         #use Ward's method
		"T", "5.1", rundir+"/dendrogram.ps",  #dendrogram image file
		"Y", rundir+"/dendrogramdoc", #dendrogram doc file
	)
	mySpider.close()

	convertPostscriptToPng("cluster/dendrogram.ps", "dendrogram.png")

#===============================
def convertPostscriptToPng(psfile, pngfile, size=1024):

	### better pstopnm pre-step
	pstopnmcmd = "pstopnm -xsize=2000 -ysize=2000 -xborder=0 -yborder=0 -portrait "+psfile
	proc = subprocess.Popen(pstopnmcmd, shell=True)
	proc.wait()

	### direct conversion
	ppmfile = os.path.splitext(psfile)[0]+"001.ppm"
	if os.path.isfile(ppmfile):
		imagemagickcmd = ("convert -colorspace Gray -trim -resize "
			+str(size)+"x"+str(size)+" "+ppmfile+" "+pngfile)
	else:
		ppmfile = psfile+"001.ppm"
		if os.path.isfile(ppmfile):
			imagemagickcmd = ("convert -colorspace Gray -trim -resize "
				+str(size)+"x"+str(size)+" "+ppmfile+" "+pngfile)
		else:
			imagemagickcmd = ("convert -colorspace Gray -trim -resize "
				+str(size)+"x"+str(size)+" "+psfile+" "+pngfile)
	proc = subprocess.Popen(imagemagickcmd, shell=True)
	proc.wait()

	if os.path.isfile(ppmfile):
		apFile.removeFile(ppmfile)

	if not os.path.isfile(pngfile):
		apDisplay.printWarning("Postscript image conversion failed")


#===============================
def hierarchCluster(alignedstack, numpart=None, numclasses=40, timestamp=None,
		factorlist=range(1,5), corandata="coran/corandata", dataext=".spi"):

	rundir = "cluster"
	apParam.createDirectory(rundir)
	### step 1: use coran data to create hierarchy
	dendrogramfile = hierarchClusterProcess(numpart, factorlist, corandata, rundir, dataext)
	### step 2: asssign particles to groups based on hierarchy
	classavg,classvar = hierarchClusterClassify(alignedstack, dendrogramfile, numclasses, timestamp, rundir, dataext)
	return classavg,classvar

#===============================
def hierarchClusterProcess(numpart=None, factorlist=range(1,5),
		corandata="coran/corandata", rundir=".", dataext=".spi"):
	"""
	inputs:
		coran data
		number of particles
		factor list
		output directory
	output:
		dendrogram doc file
		factorkey
	"""
	#apFile.removeFile(rundir+"/dendrogramdoc"+dataext)

	factorstr, factorkey = operations.intListToString(factorlist)

	dendrogramfile = rundir+"/dendrogramdoc"+factorkey+dataext
	if os.path.isfile(dendrogramfile):
		apDisplay.printMsg("Dendrogram file already exists, skipping processing "+dendrogramfile)
		return dendrogramfile

	apDisplay.printMsg("Creating dendrogram file: "+dendrogramfile)
	### do hierarchical clustering
	mySpider = spyder.SpiderSession(dataext=dataext, logo=False, log=True)
	mySpider.toSpider(
		"CL HC",
		spyder.fileFilter(corandata)+"_IMC", # path to coran data
		factorstr, # factor string
	)
	## weight for each factor
	for fact in factorlist:
		mySpider.toSpiderQuiet("1.0")
	minclasssize = "%.4f" % (numpart*0.0001+2.0)
	mySpider.toSpider(
		"5",         #use Ward's method
		"T", minclasssize, rundir+"/dendrogram.ps", #dendrogram image file
		"Y", spyder.fileFilter(dendrogramfile), #dendrogram doc file
	)
	mySpider.close()

	if not os.path.isfile(dendrogramfile):
		apDisplay.printError("dendrogram creation (CL HC) failed")
	convertPostscriptToPng("cluster/dendrogram.ps", "dendrogram.png")

	return dendrogramfile

#===============================
def hierarchClusterClassify(alignedstack, dendrogramfile, numclasses=40, timestamp=None, rundir=".", dataext=".spi"):
	"""
	inputs:
		aligned particle stack
		number of classes
		timestamp
		output directory
	output:
		class averages
		class variances
		dendrogram.png
	"""
	if timestamp is None:
		timestamp = apParam.makeTimestamp()

	classavg = rundir+"/"+("classavgstack_%s_%03d" %  (timestamp, numclasses))
	classvar = rundir+"/"+("classvarstack_%s_%03d" %  (timestamp, numclasses))

	thresh, classes = findThreshold(numclasses, dendrogramfile, rundir, dataext)

	### create class doc files
	mySpider = spyder.SpiderSession(dataext=dataext, logo=False, log=True)
	mySpider.toSpider(
		"CL HE",
		thresh,
		spyder.fileFilter(dendrogramfile), # dendrogram doc file
		rundir+"/classdoc_"+timestamp+"_****", # class doc file
	)

	### delete existing files
	sys.stderr.write("delete existing files")
	for dext in (".hed", ".img", dataext):
		apFile.removeFile(classavg+dext)
		apFile.removeFile(classvar+dext)
	print ""

	### create class averages
	sys.stderr.write("create class averages")
	for i in range(classes):
		sys.stderr.write(".")
		classnum = i+1
		mySpider.toSpiderQuiet(
			"AS R",
			spyder.fileFilter(alignedstack)+"@******",
			rundir+("/classdoc_"+timestamp+"_%04d" % (classnum)),
			"A",
			(classavg+"@%04d" % (classnum)),
			(classvar+"@%04d" % (classnum)),
		)
	mySpider.close()
	print ""

	### convert to IMAGIC
	emancmd = "proc2d "+classavg+".spi "+classavg+".hed"
	apEMAN.executeEmanCmd(emancmd, verbose=False, showcmd=True)
	emancmd = "proc2d "+classvar+".spi "+classvar+".hed"
	apEMAN.executeEmanCmd(emancmd, verbose=False, showcmd=True)

	return classavg,classvar


#===============================
def kmeansCluster(alignedstack, numpart=None, numclasses=40, timestamp=None,
		factorlist=range(1,5), corandata="coran/corandata", dataext=".spi"):
	"""
	inputs:

	outputs:

	"""
	if timestamp is None:
		timestamp = apParam.makeTimestamp()

	if alignedstack[-4:] == dataext:
		alignedstack = alignedstack[:-4]

	rundir = "cluster"
	classavg = rundir+"/"+("classavgstack_%s_%03d" %  (timestamp, numclasses))
	classvar = rundir+"/"+("classvarstack_%s_%03d" %  (timestamp, numclasses))
	apParam.createDirectory(rundir)
	for i in range(numclasses):
		apFile.removeFile(rundir+("/classdoc%04d" % (i+1))+dataext)
	apFile.removeFile(rundir+("/allclassesdoc%04d" % (numclasses))+dataext)

	### make list of factors
	factorstr, factorkey = operations.intListToString(factorlist)

	### do k-means clustering
	mySpider = spyder.SpiderSession(dataext=dataext, logo=True, log=False)
	mySpider.toSpider(
		"CL KM",
		corandata+"_IMC", # path to coran data
		str(numclasses), # num classes
		factorstr, # factor string
	)
	## weight for each factor
	for fact in factorlist:
		mySpider.toSpiderQuiet("1.0")
	randnum = (int(random.random()*1000) + 1)
	mySpider.toSpider(
		str(randnum),
		rundir+"/classdoc_"+timestamp+"_****", # class doc file
		rundir+("/allclassesdoc%04d" % (numclasses)),	#clusterdoc file
	)
	mySpider.close()

	### delete existing files
	sys.stderr.write("delete existing files")
	for dext in (".hed", ".img", dataext):
		apFile.removeFile(classavg+dext)
		apFile.removeFile(classvar+dext)
	print ""

	mySpider = spyder.SpiderSession(dataext=dataext, logo=True, log=False)
	### create class averages
	apDisplay.printMsg("Averaging particles into classes")
	for i in range(numclasses):
		classnum = i+1
		mySpider.toSpiderQuiet(
			"AS R",
			spyder.fileFilter(alignedstack)+"@******",
			rundir+("/classdoc_"+timestamp+"_%04d" % (classnum)),
			"A",
			(classavg+"@%04d" % (classnum)),
			(classvar+"@%04d" % (classnum)),
		)
		if classnum % 10 == 0:
			sys.stderr.write(".")
		time.sleep(1)
	mySpider.close()

	### convert to IMAGIC
	emancmd = "proc2d "+classavg+".spi "+classavg+".hed"
	apEMAN.executeEmanCmd(emancmd, verbose=False, showcmd=True)
	emancmd = "proc2d "+classvar+".spi "+classvar+".hed"
	apEMAN.executeEmanCmd(emancmd, verbose=False, showcmd=True)

	return classavg,classvar

#===============================
def ClCla(alignedstack, numpart=None, numclasses=40,
		factorlist=range(1,5), corandata="coran/corandata", dataext=".spi"):
	"""
	this doesn't work
	"""
	if alignedstack[-4:] == dataext:
		alignedstack = alignedstack[:-4]

	rundir = "cluster"
	classavg = rundir+"/"+("classavgstack%03d" % numclasses)
	classvar = rundir+"/"+("classvarstack%03d" % numclasses)
	apParam.createDirectory(rundir)
	for i in range(numclasses):
		apFile.removeFile(rundir+("/classdoc%04d" % (i+1))+dataext)
	apFile.removeFile(rundir+"/clusterdoc"+dataext)

	factorstr, factorkey = operations.intListToString(factorlist)

	### do hierarchical clustering
	mySpider = spyder.SpiderSession(dataext=dataext, logo=True)
	mySpider.toSpider(
		"CL CLA",
		corandata, # path to coran data
		rundir+"/clusterdoc",	#clusterdoc file
		factorstr, #factor numbers
		"5,8",
		"4",
		"2", # minimum number of particles per class
		"Y", rundir+"/dendrogram.ps",
		"Y", rundir+"/dendrogramdoc",
	)
	mySpider.close()

#===============================
def findThreshold(numclasses, dendrogramdocfile, rundir, dataext):
	if not os.path.isfile(dendrogramdocfile):
		apDisplay.printError("dendrogram doc file does not exist")

	### determining threshold cutoff for number of classes
	minthresh = 0.0
	maxthresh = 1.0
	minclass = 0.0
	maxclass = 1.0
	classes = 0
	count = 0

	sys.stderr.write("finding threshold")
	while(classes != numclasses and count < 50):
		count += 1
		if count % 70 == 0:
			sys.stderr.write("\n["+str(minclass)+"->"+str(minclass)+"]")
		thresh = (maxthresh-minthresh)/3.0 + minthresh
		classfile = rundir+"/classes"
		apFile.removeFile(classfile+dataext)
		mySpider = spyder.SpiderSession(dataext=dataext, logo=False, log=True)
		mySpider.toSpiderQuiet(
			"CL HD",
			thresh, #threshold
			spyder.fileFilter(dendrogramdocfile), # dendrogram doc file
			classfile
		)
		mySpider.close()
		claf = open(classfile+dataext, "r")
		classes = len(claf.readlines()) - 1
		claf.close()
		if classes > numclasses:
			minthresh = thresh
			maxclass = classes
			sys.stderr.write(">")
		elif classes < numclasses:
			maxthresh = thresh
			minclass = classes
			sys.stderr.write("<")
		#print " ",count, classes, thresh, maxthresh, minthresh
	print count, "rounds for", classes, "classes"

	return thresh, classes

#===============================
def checkFile(f):
	"""
	check if file exists, and if it does, delete it
	"""
	if os.path.isfile(f):
		apDisplay.printWarning("file: '%s' is being overwritten!" % f)
		os.remove(f)
	return

#===============================
def spiderVOEA(incr,ang,fold=1.0,dataext=".spi"):
	checkFile(ang)
	mySpider = spyder.SpiderSession(dataext=dataext, logo=False, log=False)
	mySpider.toSpiderQuiet(
		"VO EA",
		str(incr),
		"(0,90.0)",
		"(0,%.1f)" % ((360.0/fold)-0.1),
		spyder.fileFilter(ang),
	)
	mySpider.close()
	
#===============================
def createProjections(
		incr,
		boxsz,
		symfold,
		invol,
		rad,
		sel="selvoea.spi",
		ang="angvoea.spi",
		projs="proj.spi",
		nproc=1,
		dataext=".spi"):

	# create doc file containing euler angles
	spiderVOEA(incr,ang,symfold)
	projangles=readDocFile(ang)
	numprojs = len(projangles)

	mySpi = spyder.SpiderSession(nproc=nproc,dataext=dataext, logo=False, log=True)

	checkFile(sel)
	mySpi.toSpiderQuiet(
		"DOC CREATE",
		spyder.fileFilter(sel),
		"1",
		"1-"+str(numprojs),
	)

	checkFile(projs)
	mySpi.toSpiderQuiet(
		"PJ 3Q",
		spyder.fileFilter(invol),
		str(rad),
		spyder.fileFilter(sel),
		spyder.fileFilter(ang),
		spyder.fileFilter(projs)+"@*****",
	)
	mySpi.close()
	return projs,numprojs,ang,sel

def spiderAPMQ(projs,
		numprojs,
		tsearch,
		tstep,
		lastRing,
		stackfile,
		nump,
		ang,
		firstRing=1,
		startp=1,
		apmqfile="apmq.spi",
		nproc=1,
		outang="angular.spi",
		dataext=".spi"):

	checkFile(apmqfile)
	mySpi = spyder.SpiderSession(nproc=nproc, dataext=dataext, logo=False, log=True)
	mySpi.toSpiderQuiet(
		"AP MQ",
		spyder.fileFilter(projs)+"@*****",
		"1-"+str(numprojs),
		str(tsearch)+","+str(tstep),
		str(firstRing)+","+str(lastRing),
		spyder.fileFilter(stackfile)+"@******",
		str(startp)+"-"+str(nump),
		spyder.fileFilter(apmqfile),
	)

	checkFile(outang)
	mySpi.toSpiderQuiet(
		"VO MD",
		spyder.fileFilter(ang),
		spyder.fileFilter(apmqfile),
		spyder.fileFilter(outang),
	)

	mySpi.close()
	return outang

#===============================
def makeSpiderCoranBatch(params,filename,clsdir):
	nfacts=20
	if params['nptcls'] < 21:
		nfacts=params['nptcls']-1
	f=open(os.path.join(clsdir,filename),'w')
	f.write('MD ; verbose off in spider log file\n')
	f.write('VB OFF\n')
	f.write('\n')
	f.write('x99=%d  ; number of particles in stack\n' % params['nptcls'])
	f.write('x98=%d   ; box size\n' % params['boxsize'])
	f.write('x94=%d    ; mask radius\n' % params['coranmask'])
	f.write('x93=%f  ; cutoff for hierarchical clustering\n' % params['haccut'])
	f.write('x92=20    ; additive constant for hierarchical clustering\n')
	f.write('\n')
	alignstack='aligned'
	if params['hp'] is not None:
		f.write('FR G ; aligned hp stack file\n')
		f.write('[alignedhp]alignedhp\n')
		alignstack='alignedhp'
	f.write('FR G ; aligned stack file\n')
	f.write('[aligned]aligned\n')
	f.write('\n')
	f.write(';;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;\n')
	f.write('\n')
	f.write('FR G ; where to write class lists\n')
	f.write('[clhc_cls]classes/clhc_cls\n')
	f.write('\n')
	f.write('FR G ; where to write alignment data\n')
	f.write('[ali]alignment/\n')
	f.write('\n')
	f.write('VM\n')
	f.write('mkdir alignment\n')
	f.write('\n')
	f.write(';;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;\n')
	f.write(';; create the sequential file and then use that file and do a hierarchical ;;\n')
	f.write(';; clustering. Run clhd and clhe to classify the particles into different  ;;\n')
	f.write(';; groups.                                                                 ;;\n')
	f.write(';;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;\n')
	f.write('\n')
	f.write('VM\n')
	f.write('echo Performing multivariate statistical analysis\n')
	f.write('VM\n')
	f.write('echo "  making template file"\n')
	f.write('\n')
	f.write('MO      ; make mask template\n')
	f.write('_9      ; save template in memory\n')
	f.write('x98,x98 ; box size\n')
	f.write('c       ; circle\n')
	f.write('x94     ; radius of mask\n')
	f.write('\n')
	f.write('VM\n')
	f.write('echo "  doing correspondence analysis"\n')
	f.write('\n')
	f.write('CA S           ; do correspondence analysis\n')
	f.write('[%s]@***** ; aligned stack\n' % alignstack)
	f.write('1-x99          ; particles to use\n')
	f.write('_9             ; mask file\n')
	f.write('%d             ; number of factors to be used\n' % nfacts)
	f.write('C              ; Coran analysis\n')
	f.write('x92            ; additive constant (since coran cannot have negative values)\n')
	f.write('[ali]coran     ; output file prefix\n')
	f.write('\n')
	f.write('\n')
	f.write('DO LB14 x11=1,%d\n' % nfacts)
	f.write('CA SRE\n')
	f.write('[ali]coran\n')
	f.write('x11\n')
	f.write('[ali]sre@{***x11}\n')
	f.write('LB14\n')
	f.write('\n')
	#f.write('VM\n')
	#f.write('eigendoc.py alignment/coran_EIG.spi alignment/eigendoc.out 30\n')
	#f.write('\n')
	f.write('VM\n')
	f.write('echo "  clustering..."\n')
	f.write('\n')
	f.write('CL HC          ; do hierarchical clustering\n')
	f.write('[ali]coran_IMC ; coran image factor coordinate file\n')
	f.write('1-3\n')
	f.write('1.00           ; factor numbers to be included in clustering algorithm\n')
	f.write('1.00           ; factor weights\n')
	f.write('1.00           ; for each factor number\n')
	f.write('5              ; use Wards method\n')
	f.write('Y              ; make a postscript of dendogram\n')
	f.write('[ali]clhc.ps   ; dendogram image file\n')
	f.write('Y              ; save dendogram doc file\n')
	f.write('[ali]clhc_doc  ; dendogram doc file\n')
	f.write('\n')
	f.write('\n')
	f.write(';;;determine number of classes for given threshold\n')
	f.write('CL HD\n')
	f.write('x93\n')
	f.write('[ali]clhc_doc\n')
	f.write('clhc_classes\n')
	f.write('\n')
	f.write('UD N,x12\n')
	f.write('clhc_classes\n')
	f.write('\n')
	f.write('VM\n')
	f.write('mkdir classes\n')
	f.write('\n')
	f.write('VM\n')
	f.write('echo "Creating {%F5.1%x12} classes using a threshold of {%F7.5%x93}"\n')
	f.write('CL HE         ; generate doc files containing particle numbers for classes\n')
	f.write('x93         ; threshold (closer to 0=more classes)\n')
	f.write('[ali]clhc_doc      ; dendogram doc file\n')
	f.write('[clhc_cls]****  ; selection doc file that will contain # of objects for classes\n')
	f.write('\n')
	f.write(';;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;\n')
	f.write(';; average aligned particles together ;;\n')
	f.write(';;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;\n')
	f.write('\n')
	f.write('VM\n')
	f.write('echo Averaging particles into classes\n')
	f.write('\n')
	f.write('DO LB20 x81=1,x12\n')
	f.write('AS R\n')
	f.write('[aligned]@*****\n')
	f.write('[clhc_cls]{****x81}\n')
	f.write('A\n')
	f.write('classes_avg@{****x81}\n')
	f.write('classes_var@{****x81}\n')
	f.write('LB20\n')
	f.write('\n')
	f.write('EN D\n')
