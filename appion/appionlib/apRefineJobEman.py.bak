#!/usr/bin/env python
import os
import sys
import math
import time
#appion
from appionlib import apDisplay
from appionlib import apRefineJob

#================
#================
class EmanRefineJob(apRefineJob.RefineJob):
	#================
	def setIterationParamList(self):
		super(EmanRefineJob,self).setIterationParamList()
		self.iterparams.extend([
				{'name':'amask','default':'','help':'amask in radius'},
				{'name':'maxshift','default':'','help':'Maximum translation during image alignment'},
				{'name':'hard','default':'','help':'Hard limit for make3d'},
				{'name':'pad','default':'100','help':'Pad the model during Fourier recon'},
				{'name':'classkeep','default':'0.8','help':'Classkeep value for classalignall'},
				{'name':'classiter','default':'','help':'Iterations for classalignall'},
				{'name':'xfiles','default':'','help':'Used to generate 3d models that are easy to evaluate'},
				{'name':'shrink','default':'','help':'shrinks images at several points for faster runs'},
				{'name':'euler2','default':'','help':'Reassigns Euler angles to class averages'},
				{'name':'median','default':'','help':'Specify this when CTF correction is NOT being performed'},
				{'name':'phasecls','default':'T','help':'Uses weighted mean phase error for classification'},
				{'name':'refine','default':'F','help':'Do subpixel alignment of the particle translations for classification and averaging'},
		
				{'name':'coranCC','default':'','help':'Coran subclassification correlation limit'},
				{'name':'coranmask','default':'','help':'Coran subclassification mask radius'},
				{'name':'coranlp','default':'','help':'Coran subclassification low-pass filter'},
				{'name':'coranhp','default':'','help':'Coran subclassification high-pass filter'},
				{'name':'coranhcc','default':'','help':'Coran subclassification hcc'},
				])
		
	#=====================
	def checkPackageConflicts(self):
		pass

	def checkIterationConflicts(self):
		super(EmanRefineJob,self).checkIterationConflicts()
		# determine padding automatically
		pad = int(self.params['boxsize']*1.25/2.0)*2
		self.params['pad'] = map((lambda x: pad),range(self.params['numiter']))
		# copy to eman standard name for easier parameter settings.
		# EMAN know the mask and imask in pixels, not angstroms
		self.params['mask'] = map((lambda x: self.convertAngstromToPixel(x)),self.params['outerMaskRadius'])
		self.params['sym'] = self.params['symmetry']
		self.params['imask'] = map((lambda x: self.convertAngstromToPixel(x)),self.params['innerMaskRadius'])
		self.params['ang'] = self.params['angSampRate']

	def convertSymmetryNameForPackage(self,inputname):
		'''
		hedral symmetry key is of possible name, value is that of this package
		'''
		eman_hedral_symm_names = {'O':'oct','Icos':'icos'}
		inputname = inputname.lower().split(' ')[0]
		if inputname[0] in ('c','d') or inputname in eman_hedral_symm_names.values():
			symm_name = inputname.lower()
		elif inputname in eman_hedral_symm_names.keys():
			symm_name = eman_hedral_symm_names[inputname]
		else:
			apDisplay.printError("unknown symmetry name conversion to EMAN")
		return symm_name

	def setEmanRefineParams(self,iter):
		refineparams = ('ang','mask','sym','hard','pad', 'median', 'classiter', 'refine', 'amask', 'phasecls', 'shrink', 'euler2',  'classkeep', 'imask', 'maxshift', 'xfiles', 'tree', 'filt3d')
		eotestparams = ('mask','sym','hard','pad', 'median', 'classiter', 'refine',  'classkeep', 'imask')
		return refineparams,eotestparams	
		
	def combineEmanParams(self,iter_index,valid_paramkeys):
		task_params = []
		for key in valid_paramkeys:
			if key in self.params.keys():
				if type(self.params[key]) == type([]):
					paramvalue = self.params[key][iter_index]
				else:
					paramvalue = self.params[key]
				paramtype = type(paramvalue)
				if paramtype == type(True):
					if paramvalue is True:
						task_params.append(key)
				elif paramtype == type(0.5):
					task_params.append('%s=%.3f' % (key,paramvalue))
				elif paramtype == type(1):
					task_params.append('%s=%d' % (key,paramvalue))
				elif paramvalue == '':
					continue
				else:
					task_params.append('%s=%s' % (key,paramvalue))
		return task_params

	def getSymmetryOrder(self,sym_name):
		'''
		This only covers chiral symmetry of 3d point group
		'''
		print "'%s'"%(sym_name)
		proper = sym_name[0]
		if proper.lower() == 'c':
			order = eval(sym_name[1:])
		elif proper.lower() == 'd':
			order = eval(sym_name[1:]) * 2
		elif proper.lower() == 't':
			order = 12
		elif proper.lower() == 'o':
			order = 24
		elif proper.lower() == 'i':
			order = 60
		else:
			apDisplay.printError("Symmetry not found for %s"%(sym_name))
		return order

	def calcRefineMem(self, ppn, boxsize, sym, ang):
		print "calcRefineMem"
		foldsym = self.getSymmetryOrder(sym)
		print "foldsym",foldsym
		endnumproj = 18000.0/(foldsym*ang*ang)
		print "endnumproj",endnumproj
		#need to open all projections and 1024 particles in memory
		numpartinmem = endnumproj + 1024
		memneed = numpartinmem*boxsize*boxsize*16.0*ppn
		print memneed
		numgiga = math.ceil(memneed/1073741824.0)
		return int(numgiga)

	def makeNewTrialScript(self):
		self.addSimpleCommand('ln -s  %s threed.0a.mrc' % self.params['modelnames'][0])

	def makeRefineTasks(self,iter):
		print self.params['symmetry']
		print "eman iter %d"%(iter)
		iter_index = iter - self.params['startiter']
		print "calc mem"
		refine_mem = self.calcRefineMem(self.ppn,self.params['boxsize'],self.params['symmetry'],self.params['ang'][iter_index])
		print refine_mem
		nproc = self.params['nproc']
		print "ref params"
		refineparams,eotestparams = self.setEmanRefineParams(iter)
		refinetask_list = ['refine','%d'%iter,'proc=%d' % nproc]
		refinetask_list.extend(self.combineEmanParams(iter_index,refineparams))
		eotesttask_list = ['eotest','proc=%d' % nproc]
		eotesttask_list.extend(self.combineEmanParams(iter_index,eotestparams))

		tasks = {}
		refinelog = 'refine%d.txt' % (iter)
		eotestlog = 'eotest%d.txt' % (iter)
		tasks = self.addToTasks(tasks,' '.join(refinetask_list)+' > %s' % (refinelog),refine_mem,nproc)
		tasks = self.logTaskStatus(tasks,'refine',refinelog)
		tasks = self.logTaskStatus(tasks,'make3d','threed.%da.mrc' % iter)
		tasks = self.addToTasks(tasks,'/bin/mv -v classes.%d.hed classes_eman.%d.hed' % (iter,iter))
		tasks = self.addToTasks(tasks,'ln -s classes_eman.%d.hed classes.%d.hed' % (iter,iter))
		tasks = self.addToTasks(tasks,'/bin/mv -v classes.%d.img classes_eman.%d.img' % (iter,iter))
		tasks = self.addToTasks(tasks,'ln -s classes_eman.%d.img classes.%d.img' % (iter,iter))
		appion_getProjEulers = os.path.join(self.appion_bin_dir,'getProjEulers.py')
		tasks = self.addToTasks(tasks,'%s proj.img proj.%d.txt' % (appion_getProjEulers,iter))
		tasks = self.addToTasks(tasks,' '.join(eotesttask_list)+' > %s' % (eotestlog),refine_mem,nproc)
		tasks = self.addToTasks(tasks,'/bin/mv -v fsc.eotest fsc.eotest.%d' % (iter))
		print "get res"
		appion_getres = os.path.join(self.appion_bin_dir,'getRes.pl')
		tasks = self.addToTasks(tasks,
			'%s %d %d %.3f >> resolution.txt' % (appion_getres,iter,self.params['boxsize'], self.params['apix']))
		tasks = self.logTaskStatus(tasks,'eotest','resolution.txt',iter)
		tasks = self.addToTasks(tasks,'/bin/rm -fv cls*.lst')
		print "return"
		return tasks

if __name__ == '__main__':
	app = EmanRefineJob()
	app.start()
	app.close()
