
## python
import os
import sys
import time
import random
## PIL
## spider
from appionlib import spyder
from appionlib import apEMAN
from appionlib import apImage
from appionlib import apParam
from appionlib import apDisplay
from appionlib import apFile
from appionlib.apSpider import operations

"""
A large collection of SPIDER functions for 2D PARTICLE CLASSIFICATION purposes only

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
def estimateTime(numparts, maskpixrad=None):
	#min time 60 sec vs. 289 from model
	#linear time 0 sec vs. -1.1587 from model
	"""
	esttime = ( 60.0
		+ 0.0 * numparts
		+ 1.6642e-3 * numparts**2
		+ 5.6333e-7 * numparts**3
		+ 6.7367e-11 * numparts**4 )
	"""
	#quadradic time March 14, 2008
	x = float(maskpixrad*numparts*2.0)
	esttime = ( 26.83 + 0.001809 * x + 1.8542e-09 * x**2 )
	#ln(y) = -13.182 + 1.531 * ln(x) ==>
	#esttime = 1.884e-6 * (x**1.531) + 26.0
	return esttime

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
	apImage.convertPostscriptToPng(factorfile+".ps", factorfile+".png", size=200)
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

	apImage.convertPostscriptToPng("cluster/dendrogram.ps", "dendrogram.png")

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
		apDisplay.printError("SPIDER dendrogram creation (CL HC) failed, too many particles??")
	apImage.convertPostscriptToPng("cluster/dendrogram.ps", "dendrogram.png")

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
