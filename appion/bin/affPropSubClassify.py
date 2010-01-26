#!/usr/bin/env python

from subprocess import call


import os
import sys
import time
import glob
import math
import numpy
import shutil
import string
import tarfile
import subprocess
### appion
from appionlib import apImagicFile
from appionlib import apParam
from appionlib import apEMAN
from appionlib import apFile
from appionlib import apDisplay

#=====================
def getCCValue(imgarray1, imgarray2):
	### old method for cc
	npix = imgarray1.shape[0] * imgarray1.shape[1]

	avg1=imgarray1.mean()
	avg2=imgarray2.mean()

	std1=imgarray1.std()
	var1=std1*std1
	std2=imgarray2.std()
	var2=std2*std2

	### convert 2d -> 1d array and compute dot product
	cc = numpy.dot(numpy.ravel(imgarray1), numpy.ravel(imgarray2))
	cc /= npix
	cc -= (avg1*avg2)
	cc /= math.sqrt(var1*var2)
	return cc

#=====================
def fillSimilarityMatrix(stackfile):
	### Get initial correlation values
	### this is really, really slow

	numpart = apFile.numImagesInStack(stackfile)

	similarfile = "similarities.dat"
	if os.path.isfile(similarfile):
		simf = open(similarfile, 'r')
		simlist = []
		count = 0
		for line in simf:
			count += 1
			sline = line.strip()
			slist = sline.split()
			ccval = float(slist[2])
			simlist.append(ccval)
		simf.close()
		apDisplay.printMsg("There are %d lines in the sim file: %s"%(count, similarfile))
		if count == numpart*(numpart-1):
			### we have a valid file already
			return similarfile, simlist

	### read data and estimate time
	imagicdict = apImagicFile.readImagic(stackfile)
	partarray = imagicdict['images']
	numpart = partarray.shape[0]
	boxsize = partarray.shape[1]
	#timeper = 27.0e-9
	timeper = 17.0e-9
	apDisplay.printMsg("Computing CC values in about %s"
		%(apDisplay.timeString(timeper*numpart**2*boxsize**2)))

	### Computing CC values
	simf = open(similarfile, 'w')
	cctime = time.time()
	simlist = []
	for i in range(0, numpart):
		if i % 100 == 99:
			sys.stderr.write(".")
		for j in range(i+1, numpart):
			ccval = self.getCCValue(partarray[i],partarray[j])
			str1 = "%05d %05d %.10f\n" % (i+1, j+1, ccval)
			simf.write(str1)
			str2 = "%05d %05d %.10f\n" % (j+1, i+1, ccval)
			simf.write(str2)
			simlist.append(ccval)
	sys.stderr.write("\n")
	simf.close()
	del partarray
	del imagicdict['images']
	apDisplay.printMsg("CC calc time: %s :: %s per part :: %s per part per pixel"
		%(apDisplay.timeString(time.time()-cctime),
		apDisplay.timeString((time.time()-cctime)/numpart**2),
		apDisplay.timeString((time.time()-cctime)/numpart**2/boxsize**2)))

	return similarfile, simlist

#=====================
def setPreferences(simlist, preftype):
	numpart = len(simlist)
	### Preference value stats
	prefarray = numpy.asarray(simlist, dtype=numpy.float32)
	apDisplay.printMsg("CC stats:\n %.5f +/- %.5f\n %.5f <> %.5f"
		%(prefarray.mean(), prefarray.std(), prefarray.min(), prefarray.max()))	

	### Determine median preference value
	if preftype == 'minlessrange':
		apDisplay.printMsg("Determine minimum minus total range (fewer classes) preference value")
		simarray = numpy.asarray(simlist)
		prefvalue = simarray.min() - (simarray.max() - simarray.min())
	elif preftype == 'minimum':
		apDisplay.printMsg("Determine minimum (few classes) preference value")
		simarray = numpy.asarray(simlist)
		prefvalue = simarray.min()
	else:
		apDisplay.printMsg("Determine median (normal classes) preference value")
		simlist.sort()
		index = int(len(simlist)*0.5)
		medianpref = simlist[index]
		prefvalue = medianpref

	apDisplay.printColor("Final preference value %.6f"%(prefvalue), "cyan")

	### Dumping median preference value
	preffile = 'preferences.dat'
	apDisplay.printMsg("Dumping preference value to file")
	f1 = open(preffile, 'w')
	for i in range(0,numpart):
		f1.write('%.10f\n' % (prefvalue))
	f1.close()

	return preffile


#=====================
def writeNewClsfile(clsfile,pretext,Ptext,Ptcls):
	goodp=[]
	for l,t in enumerate(Ptcls):
		if l >0:
			goodp.append(int(t.split(' ')[0]))
	for i, t in enumerate(Ptext):
		if i in goodp:
			keep='1'
		else:
			keep='0'
		NewPtext = Ptext[i].split('\n')[0]+'\t'+keep+'\n'
		pretext.append(NewPtext)

	f1 = open(clsfile+'.new', 'w')
	for l in pretext:
		f1.write(l)
	f1.close()

#=====================
def readClassPtcltext(clsfile):
	f1 = open(clsfile, 'r')
	Ptcldict={}
	Ptext=f1.readlines()
	pretext=[Ptext[0],Ptext[1]]
	del Ptext[0]
	del Ptext[0]
	return pretext,Ptext

#=====================
def start():
	### backup old cls files
	classfile = os.path.join(params['emandir'], "cls.%d.tar"%(params['iter']))
	oldclassfile = os.path.join(params['emandir'], "cls.%d.old.tar"%(params['iter']))
	shutil.move(classfile, oldclassfile)

	projhed = os.path.join(params['emandir'], 'proj.hed')
	projhed = os.path.join(params['emandir'], 'proj.img')
	numproj = apFile.numImagesInStack(projhed)

	### extract cls files
	tar = tarfile.open(oldclassfile)
	tar.extractall(path=params['rundir'])
	tar.close()
	clslist = glob.glob("cls*.lst")

	if numproj != len(clslist):
		apDisplay.printError("array length mismatch")

	### loop through classes
	clsnum = 0
	goodavg = []
	for clsfile in clslist:
		clsnum += 1
		clsf = open(clsfile, 'r')
		partlist = clsf.readlines()
		clsf.close()

		### write the projection???
		#e=projections[clsNum].getEuler()
		#projections[clsNum].setNImg(-1)
		#projections[clsNum].writeImage('goodavgs.hed', -1)

		if len(partlist) < params['minpart']:
			### not enough particles skip to next projection
			#origaverage =
			goodavg.append()
			#emanClsAvgs[(clsNum+1)*2 - 1].writeImage('goodavgs.hed',-1)
			continue

		### make aligned stack
		if params['eotest'] is False:
			command='clstoaligned.py ' + cls
		elif params['eotest']=='odd':
			fw=open(cls,'r')
			Ptcls = fw.readlines()
			fw.close()
			fw = open('cls_odd.lst', 'w')
			fw.writelines(Ptcls[0])
			fw.writelines(Ptcls[1])
			for i1 in range(2,len(Ptcls)):
				if i1%2==0:
					fw.writelines(Ptcls[i1])
			fw.close()
			command='clstoaligned.py cls_odd.lst'
		elif params['eotest']=='even':
			fw=open(cls,'r')
			Ptcls = fw.readlines()
			fw.close()
			fw = open('cls_even.lst', 'w')
			fw.writelines(Ptcls[0])
			fw.writelines(Ptcls[1])
			for i1 in range(2,len(Ptcls)):
				if i1%2==1:
					fw.writelines(Ptcls[i1])
			fw.close()
			command='clstoaligned.py cls_even.lst'
		apDisplay.printMsg(command)
		proc = subprocess.Popen(command, shell=True)
		proc.wait()
		#set up cls dir
		clsdir=cls.split('.')[0]+'.dir'
		os.mkdir(clsdir)
		os.rename('aligned.spi',os.path.join(clsdir,'aligned.spi'))
		alignedImgsName = os.path.join(clsdir,'aligned.spi')
		#alignedImgs = EMAN.readImages(alignedImgsName,-1,-1,0)
		#N = len(alignedImgs)

		apDisplay.printMsg("Starting cluster process for "+clsdir)
		### fill similarity matrix with CC values
		similarfile, simlist = fillSimilarityMatrix(alignedImgsName)

		### set preferences
		preffile = setPreferences(simlist, params['preftype'])

		### run apcluster.exe program
		outfile = "clusters.out"
		apDisplay.printMsg("Run apcluster.exe program")
		apclusterexe = os.path.join("apcluster.exe")
		if os.path.isfile(outfile):
			os.remove(outfile)
		clustercmd = apclusterexe+" "+similarfile+" "+preffile+" "+outfile
		proc = subprocess.Popen(clustercmd, shell=True)
		proc.wait()

		if not os.path.isfile(outfile):
			apDisplay.printError("affinity propagration cluster program did not run")

		### Parse apcluster output file: clusters.out
		apDisplay.printMsg("Parse apcluster output file: "+outfile)
		clustf = open(outfile, "r")
		### each line is the particle and the number is the class
		partnum = 0
		classes = {}
		for line in clustf:
			sline = line.strip()
			if sline:
				partnum += 1
				classnum = int(sline)
				if not classnum in classes:
					classes[classnum] = [partnum,]
				else:
					classes[classnum].append(partnum)
		clustf.close()
		apDisplay.printMsg("Found %d classes"%(len(classes.keys())))

		### Create class averages
		classavgdata = []
		classnames = classes.keys()
		classnames.sort()
		for classnum in classnames:
			apDisplay.printMsg("Class %d, %d members"%(classnum, len(classes[classnum])))
			clsf = open('subcls%03d.lst'%(classnum), 'w')
			for partnum in classes[classnum]:
				clsf.write("%d\n"%(partnum))
			clsf.close()
			classdatalist = apImagicFile.readParticleListFromStack(stackfile, classes[classnum], msg=False)
			classdatarray = numpy.asarray(classdatalist)
			classavgarray = classdatarray.mean(0)
			classavgdata.append(classavgarray)
		apFile.removeStack("classaverage.hed")
		apImagicFile.writeImagic(classavgdata, "classaverage.hed")

		k=0
		for i in range(0,len(E)):
			if len(E[i])==0:
				continue
			else:
				f1=open('%s/subcls%02d.lst' % (str1,k), 'w')
				for j in range(0,len(E[i])):
					f1.write('%d aligned.spi clusterCenterImgNum%d\n' % (E[i][j], i))
				f1.close()
				proc = subprocess.Popen('proc2d aligned.spi tempClsAvg.hed list=%s/subcls%02d.lst mask=%d average edgenorm' % (str1,k,params['mask']), shell=True)
				proc.wait()
				k=k+1

		clsAvgs = EMAN.readImages('tempClsAvg.hed',-1,-1,0)
		j=0
		for i in range(0,len(E)):
			if len(E[i])==0:
				continue
			else:
				clsAvgs[j].setNImg(len(E[i]))
				clsAvgs[j].writeImage('subclasses_avg.hed',-1)
				j=j+1
		os.chdir('../')


		### Determine best averages

		proc = subprocess.Popen('rm tempClsAvg.*', shell=True)
		proc.wait()
		proc = subprocess.Popen('proc2d %s/aligned.spi tempClsAvg.hed mask=%d average edgenorm' % (clsdir, params['mask']), shell=True)
		proc.wait()
		class_avg = EMAN.readImages('tempClsAvg.hed',-1,-1,0)

		avgname=os.path.join(clsdir,'subclasses_avg.hed')
		averages=EMAN.readImages(avgname,-1,-1,0)

		cclist=[]
		for avg in averages:
			cclist.append(cc(projections[clsNum],avg))

		f1 = open('%s/CCValues.txt'%(clsdir), 'w')
		for i in range(len(cclist)):
			f1.write(str(cclist[i])+'\n')
		f1.close()

		### Merge top best subclasses

		ccListSort = cclist
		ccListSort.sort()
		Ptcls = []
		for i in range(0,len(ccListSort)):
			cci = ccListSort[len(ccListSort)-i-1]
			if cci>=params['corCutOff']:
				bestclass_i=cclist.index(cci)
				classname_i=clslist[clsNum].split('.')[0]+'.dir/subClassAvgs/subcls'+string.zfill(bestclass_i,2)+'.lst'
				f1=open(classname_i,'r')
				Ptcls_i = f1.readlines()
				f1.close()
				Ptcls.extend(Ptcls_i)
			else:
				print "Not included - ", cci
				pass
		if len(Ptcls)>0:

			fw=open('mergeClasses.lst', 'w')
			fw.writelines(Ptcls)
			fw.close()

			proc = subprocess.Popen('rm mergedClsAvg.spi', shell=True)
			proc.wait()
			proc = subprocess.Popen('proc2d %s/aligned.spi mergedClsAvg.spi list=mergeClasses.lst mask=%d average' % (clsdir, params['mask']), shell=True)
			proc.wait()
			mergedavg=EMAN.readImages('mergedClsAvg.spi',-1,-1,0)

			mergedavg[0].setNImg(len(Ptcls))
			mergedavg[0].setRAlign(e)
			mergedavg[0].writeImage('goodavgs.hed',-1)
		else:
			pass

		writeNewClsfile(cls,pretext,Ptext,Ptcls)

	#Create list of cc values
	for cls in range(0,len(clslist)):
		clsdir=clslist[cls].split('.')[0]+'.dir'
		apDisplay.printMsg("Starting class number %d" %(cls))

		#break
	pad=params['boxsize']*1.25
	if pad%2:
		pad=pad+1
	if params['sym']==None:
		make3dcommand='make3d goodavgs.hed out=threed.%d.mrc mask=%d pad=%d mode=2 hard=%d' % (params['iter'], params['mask'], pad, params['hard'])
	else:
		make3dcommand='make3d goodavgs.hed out=threed.%d.mrc mask=%d sym=%s pad=%d mode=2 hard=%d' % (params['iter'], params['mask'], params['sym'], pad, params['hard'])
	apDisplay.printMsg(make3dcommand)
	proc = subprocess.Popen(make3dcommand, shell=True)
	proc.wait()
	proc3dcommand='proc3d threed.%d.mrc threed.%da.mrc mask=%d norm' % (params['iter'],params['iter'],params['mask'])
	apDisplay.printMsg(proc3dcommand)
	proc = subprocess.Popen(proc3dcommand, shell=True)
	proc.wait()
	if params['eotest'] is False:
		#copy the resulting class average images to the main recon directory
		proc = subprocess.Popen('cp threed.%da.mrc ../.'%(params['iter']), shell=True)
		proc.wait()
		proc = subprocess.Popen('cp goodavgs.hed ../classes_msgp.%d.hed' %(params['iter']), shell=True)
		proc.wait()
		proc = subprocess.Popen('cp goodavgs.img ../classes_msgp.%d.img' %(params['iter']), shell=True)
		proc.wait()
		#link msgp result as the final result for this iteration
		rmcommand='rm -f ../classes.%d.hed ../classes.%d.img' % (params['iter'], params['iter'])
		proc = subprocess.Popen(rmcommand, shell=True)
		proc.wait()
		lncommand='ln -s classes_msgp.%d.hed ../classes.%d.hed' % (params['iter'], params['iter'])
		proc = subprocess.Popen(lncommand, shell=True)
		proc.wait()
		lncommand='ln -s classes_msgp.%d.img ../classes.%d.img' % (params['iter'], params['iter'])
		proc = subprocess.Popen(lncommand, shell=True)
		proc.wait()
	elif params['eotest']=='odd':
		proc = subprocess.Popen('cp threed.%da.mrc ../threed.%da.o.mrc' %(params['iter'], params['iter']), shell=True)
		proc.wait()
	elif params['eotest']=='even':
		proc = subprocess.Popen('cp threed.%da.mrc ../threed.%da.e.mrc' %(params['iter'], params['iter']), shell=True)
		proc.wait()
		proc = subprocess.Popen('proc3d threed.%da.mrc ../threed.%da.o.mrc fsc=../corEO%d.fsc.dat' %(params['iter'], params['iter'], params['iter']), shell=True)
		proc.wait()

	#replace the old cls*.lst with the new extended one
	proc = subprocess.Popen('tar cvzf %s %s' % (newclassfile,"cls*.lst.new"), shell=True)
	proc.wait()
	proc = subprocess.Popen('cp %s ../%s' %(newclassfile,classfile), shell=True)
	proc.wait()

	apDisplay.printMsg("Done!")


if __name__ == '__main__':
	### setup
	parser = OptionParser()
	### ints
	parser.add_option("-i", "--iter", dest="iter", type="int",
 		help="EMAN iteration number", metavar="#")
	parser.add_option("-m", "--mask", dest="mask", type="int",
 		help="EMAN mask size", metavar="#")
	parser.add_option("-p", "--minpart", dest="minpart", type="int", default=100,
 		help="Minimumn number of particles to process", metavar="#")
	parser.add_option("-h", "--hard", dest="hard", type="int",
 		help="EMAN hard cuttof", metavar="#")
	parser.add_option("--proc", dest="proc", type="int",
 		help="Number of processors", metavar="#")
	### floats
	parser.add_option("-c", "--cc-cut", dest="cccut", type="float", default=0.5
 		help="Cross-correlation cutoff", metavar="#")
	### strings
	parser.add_option("-s", "--sym", dest="sym",
 		help="EMAN symmetry", metavar=".")
	### true/false
	parser.add_option("-e", "--eotest", dest="eotest", default=False,
			action="store_true", help="Determine resolution by even/odd FSC")
	### choices
	prefvalues = ( "median", "minimum", "minlessrange" )
	parser.add_option("--preftype", "--preference-type", dest="preftype",
		help="Set preference value type", metavar="TYPE",
		type="choice", choices=prefvalues, default="minlessrange" )

	params = apParam.convertParserToParams(parser)
	if params['iter'] is None:
		apDisplay.printError("Please provide a EMAN iteration number")
	if params['hard'] is None:
		apDisplay.printError("Please provide a EMAN hard value")
	if params['sym'] is None:
		apDisplay.printError("Please provide a EMAN sym value")
	if params['mask'] is None:
		apDisplay.printError("Please provide a EMAN mask value")
	params['emandir'] = os.path.abspath(os.getcwd())
	params['rundir'] = os.path.join(params['emandir'], ("affprop%d"%(params['iter'])))
	if not os.path.isdir(params['rundir']):
		os.mkdir(params['rundir'])

	start(params)

