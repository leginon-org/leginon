#!/usr/bin/env python

import glob,os,sys
import operator
import EMAN
import shutil
import math
import subprocess
import string
import re
import time
import apEMAN
from apSpider import alignment

def parseInput(args,params):
	for arg in args:
		elements=arg.split('=')
		if elements[0]=='iter':
			params['iter']=int(elements[1])
		elif elements[0]=='mask':
			params['mask']=int(elements[1])
		elif elements[0]=='coranmask':
			params['coranmask']=int(elements[1])
		elif elements[0]=='haccut':
			params['haccut']=float(elements[1])
		elif elements[0]=='proc':
			params['proc']=int(elements[1])
		elif elements[0]=='sym':
			params['sym']=elements[1]
		elif elements[0]=='hard':
			params['hard']=int(elements[1])
		elif elements[0]=='ccCutoff':
			params['ccCutoff']=float(elements[1])
		elif elements[0]=='hp':
			params['hp']=float(elements[1])
		elif elements[0]=='apix':
			params['apix']=float(elements[1])
		elif arg=='eotest':
			params['eotest']=True
		else:
			print "\nERROR: undefined parameter \'"+arg+"\'\n"
			sys.exit(1)
def createDefaults():
	params={}
	params['corandir']='coran'
	params['mask']=None
	params['coranmask']=None
	params['iter']=None
	params['haccut']=0.15
	params['proc']=1
	params['sym']='c1'
	params['hard']=None
	params['eotest']=False
	params['ccCutoff']=1.0
	params['hp']=None
	params['apix']=None
	return(params)

if __name__== '__main__':
	# write command & time to emanlog if exists:
	if os.path.exists('refine.log'):
		cmd = string.join(sys.argv,' ')
		apEMAN.writeEMANTime('refine.log',cmd)
	#Parse inputs
	args=sys.argv[1:]
	params=createDefaults()
	parseInput(args,params)
	
	if params['coranmask'] is None:
		params['coranmask'] = params['mask']
		
	#Determine box size
	tmpimg=EMAN.readImages('start.hed',1,1)
	params['boxsize']=tmpimg[0].xSize()

	#Set up for coran
	params['corandir']=params['corandir']+str(params['iter'])
	if os.path.exists(params['corandir']):
		print "WARNING!!! %s exists and is being overwritten" % params['corandir']
		shutil.rmtree(params['corandir'])
		os.mkdir(params['corandir'])
	else:
		os.mkdir(params['corandir'])
	classfile='cls.'+str(params['iter'])+'.tar'
	shutil.copy(classfile,os.path.join(params['corandir'],classfile))
	shutil.copy('proj.hed',os.path.join(params['corandir'],'proj.hed'))
	shutil.copy('proj.img',os.path.join(params['corandir'],'proj.img'))
	os.chdir(params['corandir'])
	proc = subprocess.Popen(('tar xf %s' % classfile), shell=True)
	proc.wait()
	proc = subprocess.Popen('ln -s ../start.hed .', shell=True)
	proc.wait()
	proc = subprocess.Popen('ln -s ../start.img .', shell=True)
	proc.wait()
		
	#Loop through classes and prepare for spider
	clslist=glob.glob('cls*.lst')
	
	# sort the list numerically
	clslist.sort()
	
	projections=EMAN.readImages('proj.hed',-1,-1,0)
	if len(projections)!=len(clslist):
		print "Error: Number of projections (%d) not equal to number of classes (%d)" % (len(projections),len(clslist))
		sys.exit()

	### if multiprocessor, create the jobs to run
	if params['proc'] > 1:
		### create pbsdsh script
		spnum = 0
		coranscript=os.path.join(os.path.abspath('.'),'coranscript.csh')
		while spnum < len(clslist):
			cscript = open(coranscript,'w')

			### loop through number of processors
			for n in range(params['proc']):
				if spnum==len(clslist):
					break
				
				cls = clslist[spnum]
				clsdir=cls.split('.')[0]+'.dir'
				print "creating mpi jobfile for "+cls 
				spidercmd = alignment.runCoranClass(params,cls)
				## if enough particles, run spider
				if spidercmd is not None:
					pfile=('spider.%i.csh' %spnum)
					procfile=os.path.join(os.path.abspath('.'),clsdir,pfile)
					f=open(procfile, 'w')
					f.write("#!/bin/csh\n\n")
					f.write("cd "+os.path.abspath('.')+"\n");
					f.write(spidercmd)
					f.write("exit\n")
					f.close()
					os.chmod(procfile,0755)
					cscript.write("-np 1 %s\n" % procfile)
				spnum+=1
			cscript.close()
			print "executing coranscript: ",coranscript
			os.chmod("coranscript.csh",0755)
			proc = subprocess.Popen('mpiexec --hostfile $PBS_NODEFILE --app '+coranscript, shell=True)
			proc.wait()
			time.sleep(2)
			## remove spider files after completed
			for file in glob.glob('spider.*.csh'):
				os.remove(file)
			os.remove(coranscript)
			time.sleep(2)

		### make sure class averages were created for all classes if aligned.spi exists,
		### sometimes for some reason the spider job doesn't run
                print "Checking that all spider jobs completed"
                for cls in clslist:
                        clsdir=cls.split('.')[0]+'.dir'
                        alignedfile = os.path.join(clsdir,'aligned.spi')
                        clsavgfile = os.path.join(clsdir,'classes_avg.spi')
			clscsh=glob.glob(os.path.join(clsdir,'spider.*.csh'))
			if not clscsh :
				print "ERROR!!! no spider csh file was created in "+clsdir
			if not os.path.exists(alignedfile) and clscsh: 
				print "WARNING!!! re-executing" + clscsh[0]
				proc = subprocess.Popen(clscsh[0])
				proc.wait()
			if os.path.exists(alignedfile) and not os.path.exists(clsavgfile):
				spijobfile='coranfor'+cls.split('.')[0]+'.bat'
                                print "WARNING!!! rerunning "+spijobfile
                                if os.path.exists(os.path.join(clsdir,spijobfile)):
                                        #f = open("spider.log", "a")
                                        spicmd = "spider bat/spi @%s\n" % spijobfile.split('.')[0]
                                        proc = subprocess.Popen("cd %s\n%s\ncd .." % (clsdir,spicmd), shell=True)
                                        proc.wait()
                                else:
                                        print "ERROR!!! "+clsdir+"/"+spijobfile+" does not exist"
	else:
		for cls in clslist:
		## create SPIDER batch file and run coran	
			spidercmd = alignment.runCoranClass(params,cls)

	print "classification complete"
	print "Determining best class averages"
	#Determine best averages
	#Create list of cc values	
	for cls in range(0,len(clslist)):
		clsdir=clslist[cls].split('.')[0]+'.dir'
		# if no particles in class, create empty class averages
		if not os.path.exists(os.path.join(clslist[cls].split('.')[0]+'.dir','aligned.spi')):
			# blank projection image
			apEMAN.writeBlankImage('goodavgs.hed',params['boxsize'],-1)
			# blank class average
			apEMAN.writeBlankImage('goodavgs.hed',params['boxsize'],-1)
			# blank "good" average
			#apEMAN.writeBlankImage('allavgs.hed',params['boxsize'],-1)
			if params['eotest'] is True:
				apEMAN.writeBlankImage('goodavgs.even.hed',params['boxsize'],-1)
				apEMAN.writeBlankImage('goodavgs.odd.hed',params['boxsize'],-1)
				continue
			
		avgname=os.path.join(clsdir,'classes_avg.spi')
		averages=EMAN.readImages(avgname,-1,-1,0)
		e=projections[cls].getEuler()
		cclist=[]
		cutofflist=[]
		projections[cls].setNImg(-1)
		projections[cls].writeImage('goodavgs.hed',-1)

		### get the cc values for each images
		f = open(os.path.join(clsdir,'ccvals.txt'),'w')
		for avg in averages:
			ccval=apEMAN.getCC(projections[cls],avg)
			cclist.append(ccval)
			f.write(str(ccval)+'\n')
			avg.setNImg(10)
			avg.setRAlign(e)
		#	avg.writeImage('allavgs.hed',-1)
		f.close()

		### order class averages in order of highest cc value
		sortccindex = [i for (i,j) in sorted(enumerate(cclist),key=operator.itemgetter(1),reverse=True)]
		classnamepath = os.path.join(clsdir,'classes')
		for n in sortccindex:
			## get N imgs
			clhcbasename = 'clhc_cls'+string.zfill(n+1,4)
			classname=os.path.join(classnamepath, clhcbasename+'.spi')
			## save if has cc higher than cutoff
			if cclist[n] > params['ccCutoff']:
				cutofflist.append(n)
			nptcls=apEMAN.getNPtcls(classname,spider=True)
			apEMAN.writeImageToImage(os.path.join(clsdir,'classes_avg.spi'),n,os.path.join(clsdir,'sortavg.hed'),particles=nptcls)
		
		### if multiple classes have values higher than cutoff
		if len(cutofflist) > 1:
			print "combining "+str(len(cutofflist))+" of "+str(len(cclist))+" classes"
			spilist=[]
			for n in cutofflist:
				clhcbasename = 'clhc_cls'+string.zfill(n+1,4)
				classname=os.path.join(classnamepath, clhcbasename+'.spi')
				spilist.append(classname)
			classname=os.path.join(classnamepath,'combined.spi')
			apEMAN.combineSpiParticleList(spilist,classname)
			clhcbasename='combined'
					      
			# convert spider lst to EMAN lst
			convertlst = apEMAN.convertSpiderToEMAN(classname,clslist[cls])
			# change location of start file reference
			f=open(convertlst,'r')
			fnew = open(convertlst+'.tmp','w')
			for l in f:
				fnew.write(re.sub('\tstart','\t../../start',l))
			f.close()
			fnew.close()
			os.rename(convertlst+'.tmp',convertlst)
			
			apEMAN.makeClassAverages(convertlst,'goodavgs.hed',e,params['mask'])

		### otherwise just use the best class average
		else:
			bestclass=cclist.index(max(cclist))
			print "Using average %d for class %d" % (bestclass, cls)

			#get N imgs
			clhcbasename = 'clhc_cls'+string.zfill(bestclass+1,4)
			classname=os.path.join(classnamepath, clhcbasename+'.spi')
		
			nptcls=apEMAN.getNPtcls(classname,spider=True)
			averages[bestclass].setNImg(nptcls)
			averages[bestclass].setRAlign(e)
			averages[bestclass].writeImage('goodavgs.hed',-1)
			

			# convert spider lst to EMAN lst
			convertlst = apEMAN.convertSpiderToEMAN(classname,clslist[cls])

		#create new flaged class list from good particle list
		apEMAN.flagGoodParticleInClassLst(clslist[cls],convertlst)
    
		if params['eotest'] is True:
			f = open(convertlst,'r')
			f.readline()
			lines=f.readlines()
			f.close()
			# set up even & odd lst files
			evenlst = os.path.join(classnamepath, clhcbasename+'.even.lst')
			oddlst = os.path.join(classnamepath, clhcbasename+'.odd.lst')
			even = open(evenlst,'w')
			odd = open(oddlst,'w')
			even.write("#LST\n")
			odd.write("#LST\n")
			neven=0
			nodd=0
			for line in range(0,len(lines)):
				newline = re.sub('\tstart','\t../../start',lines[line])
				if line%2:
					nodd+=1
					odd.write(newline)
				else:
					neven+=1
					even.write(newline)
			even.close()
			odd.close()

			# create even and odd class stacks
			evenstack = 'goodavgs.even.hed'
			oddstack = 'goodavgs.odd.hed'

			if neven>0:
				apEMAN.makeClassAverages(evenlst,evenstack,e,params['mask'])
			if nodd>0:
		       		apEMAN.makeClassAverages(oddlst,oddstack,e,params['mask'])
			

	pad=int(params['boxsize']*1.25)
	if pad%2:
		pad=pad+1

	# save previous model
	mvcommand='mv ../threed.%d.mrc ../threed.%d.old.mrc' % (params['iter'],params['iter'])
	proc = subprocess.Popen(mvcommand, shell=True)
	proc.wait()

	mvcommand='mv ../threed.%da.mrc ../threed.%da.old.mrc' % (params['iter'],params['iter'])
	proc = subprocess.Popen(mvcommand, shell=True)
	proc.wait()

	# create 3d model:
	make3dcommand='make3d goodavgs.hed out=threed.%d.mrc mask=%d sym=%s pad=%d mode=2 hard=%d' % (params['iter'], params['mask'], params['sym'], pad, params['hard'])
	apEMAN.writeEMANTime('../refine.log', make3dcommand)
	print make3dcommand
	proc = subprocess.Popen(make3dcommand, shell=True)
	proc.wait()

	proc3dcommand='proc3d threed.%d.mrc ../threed.%da.mrc mask=%d norm' % (params['iter'],params['iter'],params['mask'])
	apEMAN.writeEMANTime('../refine.log', proc3dcommand)
	print proc3dcommand
	proc = subprocess.Popen(proc3dcommand, shell=True)
	proc.wait()

	if params['eotest'] is True:
		# create even 3d model:
		make3dcommand='make3d goodavgs.even.hed out=threed.te.mrc mask=%d sym=%s pad=%d mode=2 hard=%d' % (params['mask'], params['sym'], pad, params['hard'])
		apEMAN.writeEMANTime('../refine.log', make3dcommand)
		print make3dcommand
		proc = subprocess.Popen(make3dcommand, shell=True)
		proc.wait()

		# create odd 3d model:
		make3dcommand='make3d goodavgs.odd.hed out=threed.to.mrc mask=%d sym=%s pad=%d mode=2 hard=%d' % (params['mask'], params['sym'], pad, params['hard'])
		apEMAN.writeEMANTime('../refine.log', make3dcommand)
		print make3dcommand
		proc = subprocess.Popen(make3dcommand, shell=True)
		proc.wait()
	
		# calculate fsc for even/odd models:
		fsccommand='proc3d threed.te.mrc threed.to.mrc fsc=../fsc.eotest.%d' % params['iter']
		apEMAN.writeEMANTime('../refine.log', fsccommand)
		print fsccommand
		proc = subprocess.Popen(fsccommand, shell=True)
		proc.wait()
	
	mvcommand='mv goodavgs.hed ../classes_coran.%d.hed' % params['iter']
	proc = subprocess.Popen(mvcommand, shell=True)
	proc.wait()
	mvcommand='mv goodavgs.img ../classes_coran.%d.img' % params['iter']
	proc = subprocess.Popen(mvcommand, shell=True)
	proc.wait()
	rmcommand='rm -f ../classes.%d.hed ../classes.%d.img' % (params['iter'], params['iter'])
	proc = subprocess.Popen(rmcommand, shell=True)
	proc.wait()
	lncommand='ln -s classes_coran.%d.hed ../classes.%d.hed' % (params['iter'], params['iter'])
	proc = subprocess.Popen(lncommand, shell=True)
	proc.wait()
	lncommand='ln -s classes_coran.%d.img ../classes.%d.img' % (params['iter'], params['iter'])
	proc = subprocess.Popen(lncommand, shell=True)
	proc.wait()

	print "updating %s" % classfile
	proc = subprocess.Popen(('tar -cvf %s cls*.lst' % classfile), shell=True)
	proc.wait()
	mvcommand='mv %s ../%s' % (classfile,classfile)
	proc = subprocess.Popen(mvcommand, shell=True)
	proc.wait()
	
	
	print "Done!"
