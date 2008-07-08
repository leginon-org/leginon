
## python
import time
import os
import subprocess
import cPickle
import sys
import math
import random
## PIL
#import Image
## spider
import spyder
## appion
import apImage
import apEMAN
import apParam
import apDisplay
import apFile

"""
A large collection of SPIDER functions

I try to keep the trend
image file: 
	*****img.spi
doc/keep/reject file: 
	*****doc.spi
file with some data:
	*****data.spi

that way its easy to tell what type of file it is

neil
"""

#===============================
def refFreeAlignParticles(stackfile, template, numpart, pixrad,
		firstring=2, lastring=100, dataext=".spi"):
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
	rundir = "alignment"
	apParam.createDirectory(rundir)

	### remove previous iterations
	numiter = 0
	while os.path.isfile(rundir+"/avgimg%02d%s" % (numiter+1, dataext)):
		apFile.removeFile(rundir+"/avgimg%02d%s" % (numiter+1, dataext))
		pngfile = rundir+"/avgimg%02d%s" % (numiter+1, ".png")
		apFile.removeFile(pngfile)
		numiter += 1

	### perform alignment
	mySpider = spyder.SpiderSession(dataext=dataext, logo=True)
	apDisplay.printMsg("Performing particle alignment")
	# copy template to memory
	mySpider.toSpiderQuiet("CP", (template+"@1"), "_9") 
	mySpider.toSpider("AP SR", 
		stackfile+"@******", "1-"+str(numpart), 
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
		apDisplay.printError("alignment failed")
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
	for line in docf:
		data = line.strip().split()
		if data[0][0] == ";":
			continue
		if len(data) < 4:
			continue
		partdict = {
			'num': int(data[0]),
			'rot': float(data[2]),
			'xshift': float(data[3]),
			'yshift': float(data[4]),
		}
		partlist.append(partdict)
	docf.close()
	picklef = open(picklefile, "w")
	cPickle.dump(partlist, picklef)
	picklef.close()
	return partlist

#===============================
def refBasedAlignParticles(stackfile, templatestack, 
		xysearch, xystep, 
		numpart, numtemplate,
		firstring=2, lastring=100, 
		dataext=".spi", iternum=1):
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
	t0 = time.time()
	rundir = "alignments"
	apParam.createDirectory(rundir)

	### remove previous iterations
	apFile.removeFile(rundir+"/paramdoc%02d%s" % (iternum, dataext))

	### perform alignment
	mySpider = spyder.SpiderSession(dataext=dataext, logo=True)
	mySpider.toSpider("AP MQ", 
		templatestack+"@**",                        # reference image series
		"1-"+str(numtemplate),                      # enter number of templates of doc file
		str(int(xysearch))+","+str(int(xystep)),    # translation search range, step size
		str(int(firstring))+","+str(int(lastring)), # first and last ring for rotational correlation
		stackfile+"@******",                         # unaligned image series
		"1-"+str(numpart),                          # enter number of particles of doc file
		rundir+("/paramdoc%02d" % (iternum)),                       # output angles document file
	)
	mySpider.close()

	### convert spider rotation, shift data to python
	docfile = rundir+("/paramdoc%02d" % (iternum))+dataext
	picklefile = rundir+("/paramdoc%02d" % (iternum))+".pickle"
	partlist = readRefBasedDocFile(docfile, picklefile)

	### write aligned stack -- with python loop
	alignedstack = rundir+("/alignedstack%02d" % (iternum))
	alignStack(stackfile, alignedstack, partlist, dataext)

	### average stack
	emancmd = ( "proc2d "+alignedstack+dataext+" "
		+rundir+("/avgimg%02d" % (iternum))+".mrc "
		+" average")
	apEMAN.executeEmanCmd(emancmd, verbose=False, showcmd=True)

	td1 = time.time()-t0
	apDisplay.printMsg("completed alignment of "+str(numpart)
		+" particles in "+apDisplay.timeString(td1))

	return alignedstack+dataext, partlist

#===============================
def readRefBasedDocFile(docfile, picklefile):
	apDisplay.printMsg("processing alignment doc file")
	if not os.path.isfile(docfile):
		apDisplay.printError("Doc file, "+docfile+" does not exist")
	docf = open(docfile, "r")
	partlist = []
	for line in docf:
		data = line.strip().split()
		if data[0][0] == ";":
			continue
		if len(data) < 6:
			continue
		templatenum = float(data[2])
		partdict = {
			'num': int(data[0]),
			'template': int(abs(templatenum)),
			'mirror': checkMirror(templatenum),
			'score': float(data[3]),
			'rot': float(data[4]),
			'xshift': float(data[5]),
			'yshift': float(data[6]),
		}
		partlist.append(partdict)
	docf.close()
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
	
	I tried this loop in both spider and python; 
	python was faster?!? -neil
	"""

	apDisplay.printMsg("applying alignment parameters to stack")

	apFile.removeFile(alignedstack+dataext)

	mySpider = spyder.SpiderSession(dataext=dataext, logo=False)
	for partdict in partlist:
		p = partdict['num']
		mySpider.toSpiderQuiet(
			"RT SQ",
			oldstack+"@"+("%06d" % (p)),
			"_1",
			str(partdict['rot']), str(partdict['xshift'])+","+str(partdict['yshift']),
		)
		if 'mirror' in partdict and partdict['mirror'] is True:
			mySpider.toSpiderQuiet(
				"MR", "_1",
				alignedstack+"@"+("%06d" % (p)),	"Y", 
			)
		else:
			mySpider.toSpiderQuiet(
				"CP", "_1",
				alignedstack+"@"+("%06d" % (p)),	
			)
	mySpider.close()
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
	mySpider = spyder.SpiderSession(dataext=dataext, logo=True)
	mySpider.toSpiderQuiet("MO", "_9", "%d,%d" % (boxsize, boxsize), "C", str(maskpixrad*2))

	### performing correspondence analysis
	apDisplay.printMsg("Performing correspondence analysis (long wait)")
	mySpider.toSpider(
		"CA S",
		alignedstack+"@******", "1-"+str(numpart),
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
	mySpider = spyder.SpiderSession(dataext=dataext, logo=False)
	for fact in range(1,numfactors+1):
		mySpider.toSpiderQuiet(
			#"CA SRE", rundir+"/corandata", str(fact), 
			#rundir+"/eigenstack@"+("%02d" % (fact)), )
			"CA SRD", rundir+"/corandata", str(fact), str(fact), 
			rundir+"/eigenstack@***", )
	mySpider.close()

	### convert to nice individual eigen image pngs for webpage
	for fact in range(1,numfactors+1):
		pngfile = rundir+"/eigenimg"+("%02d" % (fact))+".png"
		apFile.removeFile(pngfile)
		emancmd = ("proc2d "+rundir+"/eigenstack.spi "
			+pngfile+" "
			+" first="+str(fact-1)+" last="+str(fact-1))
		apEMAN.executeEmanCmd(emancmd, verbose=False, showcmd=False)

	### convert eigen SPIDER stack to IMAGIC for stack viewer
	eigenstack = rundir+"/eigenstack.hed"
	apFile.removeStack(eigenstack)
	emancmd = "proc2d "+rundir+"/eigenstack.spi "+eigenstack
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
	for f1 in range(1,numfactors):
		sys.stderr.write(".")
		for f2 in range(f1+1, numfactors+1):
			createFactorMap(f1, f2, rundir, dataext)
	sys.stderr.write("\n")

	return contriblist

#===============================
def createFactorMap(f1, f2, rundir, dataext):
	### 3. factor plot
	apParam.createDirectory(rundir+"/factors", warning=False)
	mySpider = spyder.SpiderSession(dataext=dataext, logo=False)
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
	cmd = "convert -trim -colorspace Gray -density 150x150 "+factorfile+".ps "+factorfile+".png"
	proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	proc.wait()
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
def makeDendrogram(alignedstack, numfactors=1, corandata="coran/corandata", dataext=".spi"):

	rundir = "cluster"
	apParam.createDirectory(rundir)
	### make list of factors 	 
	factorstr = "" 	 
	for fact in range(1,numfactors+1): 	 
		factorstr += str(fact)+","
	factorstr = factorstr[:-1]

	### do hierarchical clustering
	mySpider = spyder.SpiderSession(dataext=dataext, logo=False)
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
		"T", rundir+"/dendrogram.ps", "5.1", #dendrogram image file
		"Y", rundir+"/dendrogramdoc", #dendrogram doc file
	)
	mySpider.close()

	imagemagickcmd = "convert -trim -resize 1024x1024 cluster/dendrogram.ps dendrogram.png"
	apEMAN.executeEmanCmd(imagemagickcmd, verbose=False, showcmd=False)
	if not os.path.isfile("dendrogram.png"):
		apDisplay.printWarning("Dendrogram image conversion failed")


#===============================
def hierarchCluster(alignedstack, numpart=None, numclasses=40, 
		factorlist=range(1,5), corandata="coran/corandata", dataext=".spi"):
	"""
	inputs:

	outputs:

	"""
	if alignedstack[-4:] == dataext:
		alignedstack = alignedstack[:-4]

	rundir = "cluster"
	classavg = rundir+"/"+("classavgstack%03d" % numclasses)
	classvar = rundir+"/"+("classvarstack%03d" % numclasses)
	apParam.createDirectory(rundir)
	apFile.removeFile(rundir+"/dendrogramdoc"+dataext)

	### make list of factors 	 
	factorstr = "" 	 
	for fact in factorlist: 	 
		factorstr += str(fact)+","
	factorstr = factorstr[:-1]

	### do hierarchical clustering
	mySpider = spyder.SpiderSession(dataext=dataext, logo=False)
	mySpider.toSpider(
		"CL HC",
		corandata+"_IMC", # path to coran data
		factorstr, # factor string
	)
	## weight for each factor
	for fact in factorlist:
		mySpider.toSpiderQuiet("1.0")	
	mySpider.toSpider(
		"5",         #use Ward's method
		"T", rundir+"/dendrogram.ps", "5.1", #dendrogram image file
		"Y", rundir+"/dendrogramdoc", #dendrogram doc file
	)
	mySpider.close()

	if not os.path.isfile(rundir+"/dendrogramdoc"+dataext):
		apDisplay.printError("dendrogram creation (CL HC) failed")

	thresh, classes = findThreshold(numclasses, rundir, dataext)

	### create class doc files
	mySpider = spyder.SpiderSession(dataext=dataext, logo=False)
	mySpider.toSpider(
		"CL HE",
		thresh,
		rundir+"/dendrogramdoc", # dendrogram doc file 
		rundir+"/classdoc****", # class doc file
	)

	### delete existing files
	sys.stderr.write("delete existing files")
	for dext in (".hed", ".img", dataext):
		apFile.removeFile(classavg+dext)
		apFile.removeFile(classvar+dext)
	print ""

	### create class averages
	for i in range(classes):
		classnum = i+1
		mySpider.toSpiderQuiet(
			"AS R",
			alignedstack+"@******",
			rundir+("/classdoc%04d" % (classnum)),
			"A",
			(classavg+"@%04d" % (classnum)),
			(classvar+"@%04d" % (classnum)),
		)
	mySpider.close()

	### convert to IMAGIC
	emancmd = "proc2d "+classavg+".spi "+classavg+".hed"
	apEMAN.executeEmanCmd(emancmd, verbose=False, showcmd=True)
	emancmd = "proc2d "+classvar+".spi "+classvar+".hed"
	apEMAN.executeEmanCmd(emancmd, verbose=False, showcmd=True)

	imagemagickcmd = "convert -trim -resize 1024x1024 cluster/dendrogram.ps dendrogram.png"
	apEMAN.executeEmanCmd(imagemagickcmd, verbose=False, showcmd=False)
	if not os.path.isfile("dendrogram.png"):
		apDisplay.printWarning("Dendrogram image conversion failed")

	return

#===============================
def kmeansCluster(alignedstack, numpart=None, numclasses=40, 
		factorlist=range(1,5), corandata="coran/corandata", dataext=".spi"):
	"""
	inputs:

	outputs:

	"""
	if alignedstack[-4:] == dataext:
		alignedstack = alignedstack[:-4]

	rundir = "cluster"
	classavg = rundir+"/"+("classavgstack%03d" % numclasses)
	classvar = rundir+"/"+("classvarstack%03d" % numclasses)
	apParam.createDirectory(rundir)
	for i in range(numclasses):
		apFile.removeFile(rundir+("/classdoc%04d" % (i+1))+dataext)
	apFile.removeFile(rundir+("/allclassesdoc%04d" % (numclasses))+dataext)

	### make list of factors 	 
	factorstr = "" 	 
	for fact in factorlist: 	 
		factorstr += str(fact)+","
	factorstr = factorstr[:-1]

	### do hierarchical clustering
	mySpider = spyder.SpiderSession(dataext=dataext, logo=True)
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
		rundir+"/classdoc****",	#clusterdoc file
		rundir+("/allclassesdoc%04d" % (numclasses)),	#clusterdoc file
	)
	mySpider.close()

	### delete existing files
	sys.stderr.write("delete existing files")
	for dext in (".hed", ".img", dataext):
		apFile.removeFile(classavg+dext)
		apFile.removeFile(classvar+dext)
	print ""

	mySpider = spyder.SpiderSession(dataext=dataext, logo=True)
	### create class averages
	apDisplay.printMsg("Averaging particles into classes")
	for i in range(numclasses):
		classnum = i+1
		mySpider.toSpiderQuiet(
			"AS R",
			alignedstack+"@******",
			rundir+("/classdoc%04d" % (classnum)),
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

	return

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

	### do hierarchical clustering
	mySpider = spyder.SpiderSession(dataext=dataext, logo=True)
	mySpider.toSpider(
		"CL CLA",
		corandata, # path to coran data
		rundir+"/clusterdoc",	#clusterdoc file
		str(factorlist[-1]), #factor numbers
		"5,8", 
		"4", 
		"0", # minimum number of particles per class
		"Y", rundir+"/dendrogram.ps",
		"Y", rundir+"/dendrogramdoc",
	)
	mySpider.close()

#===============================
def findThreshold(numclasses, rundir, dataext):
	if not os.path.isfile(rundir+"/dendrogramdoc"+dataext):
		apDisplay.printError("dendrogram creation (CL CLA) failed")

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
		mySpider = spyder.SpiderSession(dataext=dataext, logo=False)
		mySpider.toSpiderQuiet(
			"CL HD",
			thresh, #threshold
			rundir+"/dendrogramdoc", # dendrogram doc file 
			classfile
		)
		mySpider.close()
		claf = open(classfile+dataext, "r")
		classes = len(claf.readlines()) - 1
		claf.close()
		if classes > numclasses:
			minthresh = thresh
			maxclass = classes
		elif classes < numclasses:
			maxthresh = thresh
			minclass = classes
		sys.stderr.write(".")
		#print " ",count, classes, thresh, maxthresh, minthresh
	print count, "rounds for", classes, "classes"

	return thresh, classes
