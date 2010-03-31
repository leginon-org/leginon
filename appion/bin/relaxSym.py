#!/usr/bin/env python

import glob,os,sys
import operator

import shutil
import math
import subprocess
import string
import re
import time
from appionlib import apEMAN
from appionlib.apSpider import alignment

try:
	import EMAN
except:
	print "EMAN module did not get imported"

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
		elif arg=='eotest':
			params['eotest']=True
		else:
			print "\nERROR: undefined parameter \'"+arg+"\'\n"
			sys.exit(1)
def createDefaults():
	params={}
	params['relaxdir']='relax'
	params['mask']=None
	params['coranmask']=None
	params['iter']=None
	params['haccut']=0.15
	params['proc']=1
	params['sym']='c1'
	params['hard']=None
	params['eotest']=False
	params['ccCutoff']=1.0
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

	#determine num of projections needed
	im=EMAN.EMData()
	e=im.getEuler()
	e.setSym(params['sym'])
	params['symnum'] = e.getMaxSymEl()

	#Set up for symmetry relax
	params['relaxdir']=params['relaxdir']+str(params['iter'])
	if os.path.exists(params['relaxdir']):
		print "WARNING!!! %s exists and is being overwritten" % params['relaxdir']
		shutil.rmtree(params['relaxdir'])
		os.mkdir(params['relaxdir'])
	else:
		os.mkdir(params['relaxdir'])
	classfile='cls.'+str(params['iter'])+'.tar'
	shutil.copy(classfile,os.path.join(params['relaxdir'],classfile))
	shutil.copy('proj.hed',os.path.join(params['relaxdir'],'proj.hed'))
	shutil.copy('proj.img',os.path.join(params['relaxdir'],'proj.img'))
	os.chdir(params['relaxdir'])
	proc = subprocess.Popen(('tar -xf %s' % classfile), shell=True)
	proc.wait()
	time.sleep(2)
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
		relaxscript=os.path.join(os.path.abspath('.'),'relaxscript.csh')
		while spnum < len(clslist):
			cscript = open(relaxscript,'w')

			### loop through number of processors
			for n in range(params['proc']):
				if spnum==len(clslist):
					break
				
				cls = clslist[spnum]
				clsdir=cls.split('.')[0]+'.dir'
				print "creating mpi jobfile for "+cls 
				relaxcmd = alignment.runSymRelax(params,cls)
				## if enough particles, run symmetry relaxation
				if relaxcmd is not None:
					pfile=('relax.%i.csh' %spnum)
					procfile=os.path.join(os.path.abspath('.'),clsdir,pfile)
					f=open(procfile, 'w')
					f.write("#!/bin/csh\n\n")
					f.write("cd "+os.path.abspath('.')+"\n");
					f.write(relaxcmd)
					f.write("exit\n")
					f.close()
					os.chmod(procfile,0755)
					cscript.write("-np 1 %s\n" % procfile)
				spnum+=1
			cscript.close()
			print "executing relaxscript: ",relaxscript
			os.chmod("relaxscript.csh",0755)
			proc = subprocess.Popen('mpiexec --hostfile $PBS_NODEFILE --app '+relaxscript, shell=True)
			proc.wait()
			time.sleep(2)
			os.remove(relaxscript)
			time.sleep(2)

		### make sure class averages were created for all classes if aligned.spi exists,
		### sometimes for some reason the spider job doesn't run
                print "Checking that all csh jobs completed"
                for cls in clslist:
                        clsdir=cls.split('.')[0]+'.dir'
                        alignedfile = os.path.join(clsdir,'aligned.hed')
                        clsavgfile = os.path.join(clsdir,'classes.hed')
			clscsh=glob.glob(os.path.join(clsdir,'relax.*.csh'))
			if not clscsh :
				print "ERROR!!! no csh file was created in "+clsdir
			if not os.path.exists(alignedfile) and clscsh: 
				print "WARNING!!! re-executing" + clscsh[0]
				proc = subprocess.Popen(clscsh[0])
				proc.wait()
	else:
		for cls in clslist:
		## run symmetry relaxation	
			alignment.runSymRelax(params,cls)

	print "symmetry relaxation complete"
	print "Combining class averages"
	for cls in range(0,len(clslist)):
		clsdir=clslist[cls].split('.')[0]+'.dir'
		# if no particles in class, create empty class averages
		if not os.path.exists(os.path.join(clslist[cls].split('.')[0]+'.dir','aligned.hed')):
			for i in range (params['symnum']):
				# blank projection image
				apEMAN.writeBlankImage('newavgs.hed',params['boxsize'],-1)
				# blank class average
				apEMAN.writeBlankImage('newavgs.hed',params['boxsize'],-1)
				if params['eotest'] is True:
					apEMAN.writeBlankImage('newavgs.even.hed',params['boxsize'],-1)
					apEMAN.writeBlankImage('newavgs.odd.hed',params['boxsize'],-1)
			continue
			
		avgname=os.path.join(clsdir,'classes.hed')
		averages=EMAN.readImages(avgname,-1,-1,0)
		projname=os.path.join(clsdir,'proj.hed')
		projections=EMAN.readImages(projname,-1,-1,0)
		for i in range(params['symnum']):
			e=projections[i].getEuler()
			projections[i].setNImg(-1)
			projections[i].writeImage('newavgs.hed',-1)

			#get N imgs
			clslstname = os.path.join(clsdir,'cls%04d.lst' % i)
			nptcls=apEMAN.getNPtcls(clslstname)

			averages[i].setNImg(nptcls)
			averages[i].setRAlign(e)
			averages[i].writeImage('newavgs.hed',-1)
			
			# convert spider lst to EMAN lst
			#convertlst = apEMAN.convertSpiderToEMAN(classname,clslist[cls])

			if params['eotest'] is True:
				f = open(clslstname,'r')
				f.readline()
				lines=f.readlines()
				f.close()
				# set up even & odd lst files
				evenlst = os.path.join(clsdir, 'cls%04d.even.lst' % i)
				oddlst = os.path.join(clsdir, 'cls%04d.odd.lst' % i )
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
				odd.close()
				even.close()

				# create even and odd class stacks
				evenstack = 'newavgs.even.hed'
				oddstack = 'newavgs.odd.hed'

				if neven>0:
					apEMAN.makeClassAverages(evenlst,evenstack,e,params['mask'])
				if nodd>0:
		       			apEMAN.makeClassAverages(oddlst,oddstack,e,params['mask'])
			

	pad=int(params['boxsize']*1.25)
	if pad%2:
		pad=pad+1

	# create 3d model:
	make3dcommand='make3d newavgs.hed out=threed.%d.asym.mrc mask=%d sym=c1 pad=%d mode=2 hard=%d' % (params['iter'], params['mask'], pad, params['hard'])
	apEMAN.writeEMANTime('../refine.log', make3dcommand)
	print make3dcommand
	proc = subprocess.Popen(make3dcommand, shell=True)
	proc.wait()

	proc3dcommand='proc3d threed.%d.asym.mrc ../threed.%da.asym.mrc mask=%d norm' % (params['iter'],params['iter'],params['mask'])
	apEMAN.writeEMANTime('../refine.log', proc3dcommand)
	print proc3dcommand
	proc = subprocess.Popen(proc3dcommand, shell=True)
	proc.wait()

	if params['eotest'] is True:
		# create even 3d model:
		make3dcommand='make3d newavgs.even.hed out=threed.te.mrc mask=%d sym=c1 pad=%d mode=2 hard=%d' % (params['mask'], pad, params['hard'])
		apEMAN.writeEMANTime('../refine.log', make3dcommand)
		print make3dcommand
		proc = subprocess.Popen(make3dcommand, shell=True)
		proc.wait()

		# create odd 3d model:
		make3dcommand='make3d newavgs.odd.hed out=threed.to.mrc mask=%d sym=c1 pad=%d mode=2 hard=%d' % (params['mask'], pad, params['hard'])
		apEMAN.writeEMANTime('../refine.log', make3dcommand)
		print make3dcommand
		proc = subprocess.Popen(make3dcommand, shell=True)
		proc.wait()
	
		# calculate fsc for even/odd models:
		fsccommand='proc3d threed.te.mrc threed.to.mrc fsc=fsc.eotest.%d' % params['iter']
		apEMAN.writeEMANTime('../refine.log', fsccommand)
		print fsccommand
		proc = subprocess.Popen(fsccommand, shell=True)
		proc.wait()
	
	mvcommand='mv newavgs.hed ../classes_asym.%d.hed' % params['iter']
	proc = subprocess.Popen(mvcommand, shell=True)
	proc.wait()
	mvcommand='mv newavgs.img ../classes_asym.%d.img' % params['iter']
	proc = subprocess.Popen(mvcommand, shell=True)
	proc.wait()

	print "updating %s" % classfile
	proc = subprocess.Popen(('tar -cvf %s cls*.lst' % classfile), shell=True)
	proc.wait()
#	mvcommand='mv %s ../%s' % (classfile,classfile)
#	proc = subprocess.Popen(mvcommand, shell=True)
#	proc.wait()
	
	print "Done!"
