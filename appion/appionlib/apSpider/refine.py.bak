
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
## appion
from appionlib import spyder
from appionlib import apEMAN
from appionlib import apImage
from appionlib import apParam
from appionlib import apDisplay
from appionlib import apFile
## EMAN
try:
	import EMAN
except:
	pass

"""
A large collection of SPIDER functions for 3D RECONSTRUCTION purposes only

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
"""

#===============================
def createClassAverages(stack,projs,apmq,numprojs,boxsz,outclass="classes",rotated=False,shifted=False,dataext=".spi"):
	"""
	creates EMAN-style class average file "classes.hed" & "classes.img"
	and variance files "variances.hed" & "variances.img"
	from spider classification
	"""
	apFile.removeFile(outclass)
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
	### I would prefer to use apImagicFile.readImagic, writeImagic
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
def spiderVOEA(incr,ang,fold=1.0,dataext=".spi"):
	apFile.removeFile(ang)
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
	apFile.removeFile(file2)
	apFile.removeFile(file3)
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
	apFile.removeFile(fscfile)
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
	apFile.removeFile(out)

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
	apFile.removeFile(out)
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

	apFile.removeFile(apmqfile)
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

	apFile.removeFile(outang)
	mySpi.toSpiderQuiet(
		"VO MD",
		spyder.fileFilter(ang),
		spyder.fileFilter(apmqfile),
		spyder.fileFilter(outang),
	)

	mySpi.close()
	return outang

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

	apFile.removeFile(sel)
	mySpi.toSpiderQuiet(
		"DOC CREATE",
		spyder.fileFilter(sel),
		"1",
		"1-"+str(numprojs),
	)

	apFile.removeFile(projs)
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

#===============================
def symmetryDoc(symtype,symfold=None,outfile="sym.spi",dataext=".spi"):
	mySpi=spyder.SpiderSession(dataext=dataext,logo=False,log=False)
	apFile.removeFile(outfile)
	mySpi.toSpiderQuiet("SY",spyder.fileFilter(outfile),symtype)
	if symfold is not None:
		mySpi.toSpiderQuiet(symfold)
	mySpi.close()
