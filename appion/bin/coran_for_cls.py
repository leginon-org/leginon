#!/usr/bin/env python

import glob,os,sys
import EMAN
import shutil
import math
import string
import re
import apEMAN
from apSpider import alignment

clslist=glob.glob('cls*.lst')

def parseInput(args,params):
	for arg in args:
		elements=arg.split('=')
		if elements[0]=='iter':
			params['iter']=int(elements[1])
		elif elements[0]=='mask':
			params['mask']=int(elements[1])
		elif elements[0]=='haccut':
			params['haccut']=float(elements[1])
		elif elements[0]=='proc':
			params['proc']=int(elements[1])
		elif elements[0]=='sym':
			params['sym']=elements[1]
		elif elements[0]=='hard':
			params['hard']=int(elements[1])
		elif arg=='eotest':
			params['eotest']=True
		else:
			print "\nERROR: undefined parameter \'"+arg+"\'\n"
			sys.exit(1)
def createDefaults():
	params={}
	params['corandir']='coran'
	params['mask']=None
	params['iter']=None
	params['haccut']=0.15
	params['proc']=1
	params['sym']='c1'
	params['hard']=None
	params['eotest']=False
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
	
	#Determine box size
	tmpimg=EMAN.readImages('start.hed',1,1)
	params['boxsize']=tmpimg[0].xSize()

	#Set up for coran
	params['corandir']=params['corandir']+str(params['iter'])
	if os.path.exists(params['corandir']):
		print "Warning %s exists and is being overwritten" % params['corandir']
		shutil.rmtree(params['corandir'])
		os.mkdir(params['corandir'])
	else:
		os.mkdir(params['corandir'])
	classfile='cls.'+str(params['iter'])+'.tar'
	shutil.copy(classfile,os.path.join(params['corandir'],classfile))
	shutil.copy('proj.hed',os.path.join(params['corandir'],'proj.hed'))
	shutil.copy('proj.img',os.path.join(params['corandir'],'proj.img'))
	os.chdir(params['corandir'])
	os.system('tar xf %s' % classfile)
	os.system('ln -s ../start.hed .')
	os.system('ln -s ../start.img .')
	
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
		cscript = open("coranscript.csh",'w')
		cscript.write("#!/bin/csh\n")
		spiscript = os.path.join(os.path.abspath('.'),'spider.$PBS_VNODENUM.csh')
		cscript.write("csh "+spiscript+"\n")
		cscript.close()
		os.chmod("coranscript.csh",0777)
		
		spnum = 0
		coranscript=os.path.join(os.path.abspath('.'),'coranscript.csh')
		while spnum < len(clslist):
			for n in range(params['proc']):
				if spnum==len(clslist):
					spnum+=1
					continue
				cls = clslist[spnum]
				clsdir=cls.split('.')[0]+'.dir'
				print "creating mpi jobfile for "+cls 
				spidercmd = alignment.runCoranClass(params,cls)
				procfile=('spider.%i.csh' %n)
				f=open(procfile, 'w')
				f.write("#!/bin/csh\n\n")
				f.write("cd "+os.path.abspath('.')+"\n");
				f.write(spidercmd)
				f.write("exit\n")
				f.close()
				spnum+=1
			os.system('pbsdsh -v '+coranscript)
			## remove spider files after completed
			for n in range(params['proc']):
				procfile=('spider.%i.csh' %n)
				os.remove(procfile)
				
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
			apEMAN.writeBlankImage('allavgs.hed',params['boxsize'],-1)
			if params['eotest'] is True:
				apEMAN.writeBlankImage('goodavgs.even.hed',params['boxsize'],-1)
				apEMAN.writeBlankImage('goodavgs.odd.hed',params['boxsize'],-1)
				continue
			
		avgname=os.path.join(clsdir,'classes_avg.spi')
		averages=EMAN.readImages(avgname,-1,-1,0)
		e=projections[cls].getEuler()
		cclist=[]
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
			avg.writeImage('allavgs.hed',-1)
		f.close()
		bestclass=cclist.index(max(cclist))
		print "Using average %d for class %d" % (bestclass, cls)

		#get N imgs
		classnamepath = os.path.join(clsdir,'classes')
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
				newline = re.sub('start','../../start',lines[line])
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
	os.system(mvcommand)
	mvcommand='mv ../threed.%da.mrc ../threed.%da.old.mrc' % (params['iter'],params['iter'])
	os.system(mvcommand)
	
	# create 3d model:
	make3dcommand='make3d goodavgs.hed out=threed.%d.mrc mask=%d sym=%s pad=%d mode=2 hard=%d' % (params['iter'], params['mask'], params['sym'], pad, params['hard'])
	apEMAN.writeEMANTime('../refine.log', make3dcommand)
	print make3dcommand
	os.system(make3dcommand)
	proc3dcommand='proc3d threed.%d.mrc ../threed.%da.mrc mask=%d norm' % (params['iter'],params['iter'],params['mask'])
	apEMAN.writeEMANTime('../refine.log', proc3dcommand)
	print proc3dcommand
	os.system(proc3dcommand)

	if params['eotest'] is True:
		# create even 3d model:
		make3dcommand='make3d goodavgs.even.hed out=threed.te.mrc mask=%d sym=%s pad=%d mode=2 hard=%d' % (params['mask'], params['sym'], pad, params['hard'])
		apEMAN.writeEMANTime('../refine.log', make3dcommand)
		print make3dcommand
		os.system(make3dcommand)

		# create odd 3d model:
		make3dcommand='make3d goodavgs.odd.hed out=threed.to.mrc mask=%d sym=%s pad=%d mode=2 hard=%d' % (params['mask'], params['sym'], pad, params['hard'])
		apEMAN.writeEMANTime('../refine.log', make3dcommand)
		print make3dcommand
		os.system(make3dcommand)
	
		# calculate fsc for even/odd models:
		fsccommand='proc3d threed.te.mrc threed.to.mrc fsc=../fsc.eotest.%d' % params['iter']
		apEMAN.writeEMANTime('../refine.log', fsccommand)
		print fsccommand
		os.system(fsccommand)
	
	mvcommand='mv goodavgs.hed ../classes_coran.%d.hed' % params['iter']
	os.system(mvcommand)
	mvcommand='mv goodavgs.img ../classes_coran.%d.img' % params['iter']
	os.system(mvcommand)
	rmcommand='rm -f ../classes.%d.hed ../classes.%d.img' % (params['iter'], params['iter'])
	os.system(rmcommand)
	lncommand='ln -s classes_coran.%d.hed ../classes.%d.hed' % (params['iter'], params['iter'])
	os.system(lncommand)
	lncommand='ln -s classes_coran.%d.img ../classes.%d.img' % (params['iter'], params['iter'])
	os.system(lncommand)

	print "updating %s" % classfile
	os.system('tar -cvf %s cls*.lst' % classfile)
	mvcommand='mv %s ../%s' % (classfile,classfile)
	os.system(mvcommand)
	
	
	print "Done!"
