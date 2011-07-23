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
		# copy to eman standard name for easier parameter settings
		self.params['mask'] = self.params['outerMaskRadius']
		self.params['imask'] = self.params['innerMaskRadius']
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
		refineparams = ('ang','mask','symmetry','hard','pad', 'median', 'classiter', 'refine', 'amask', 'phasecls', 'shrink', 'euler2',  'classkeep', 'imask', 'maxshift', 'xfiles', 'tree', 'filt3d')
		eotestparams = ('ang','mask','symmetry','hard','pad', 'median', 'classiter', 'refine', 'amask', 'euler2',  'classkeep', 'imask', 'xfiles')
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
		return order

	def calcRefineMem(self,ppn,boxsize,sym,ang):
		foldsym = self.getSymmetryOrder(sym)
		endnumproj = 18000.0/(foldsym*ang*ang)
		#need to open all projections and 1024 particles in memory
		numpartinmem = endnumproj + 1024
		memneed = numpartinmem*boxsize*boxsize*16.0*ppn
		numgig = math.ceil(memneed/1073741824.0)
		return int(numgig)

	def makePreIterationScript(self):
		super(EmanRefineJob,self).makePreIterationScript()
		initmodelfilepath = os.path.join(self.params['remoterundir'],self.params['modelnames'][0])
		self.addJobCommands(self.addToTasks({},'ln -s  %s threed.0a.mrc' % initmodelfilepath))

	def makeRefineScript(self,iter):
		iter_index = iter - self.params['startiter']
		refine_mem = self.calcRefineMem(self.ppn,self.params['boxsize'],self.params['symmetry'][iter_index],self.params['ang'][iter_index])
		nproc = self.params['nproc']
		refineparams,eotestparams = self.setEmanRefineParams(iter)
		refinetask_list = ['refine','%d'%iter,'proc=%d' % nproc]
		refinetask_list.extend(self.combineEmanParams(iter_index,refineparams))
		eotesttask_list = ['eotest','%d'%iter,'proc=%d' % nproc]
		eotesttask_list.extend(self.combineEmanParams(iter_index,eotestparams))

		tasks = {}
		tasks = self.addToTasks(tasks,' '.join(refinetask_list)+' > refine%d.txt' % (iter),refine_mem,nproc)
		tasks = self.addToTasks(tasks,'/bin/mv -v classes.%d.hed classes_eman.%d.hed' % (iter,iter))
		tasks = self.addToTasks(tasks,'ln -s classes_eman.%d.hed classes.%d.hed' % (iter,iter))
		tasks = self.addToTasks(tasks,'/bin/mv -v classes.%d.img classes_eman.%d.img' % (iter,iter))
		tasks = self.addToTasks(tasks,'ln -s classes_eman.%d.img classes.%d.img' % (iter,iter))
		tasks = self.addToTasks(tasks,'getProjEuler.py proj.img proj.%d.txt' % (iter))
		tasks = self.addToTasks(tasks,' '.join(eotesttask_list)+' > eotest%d.txt' % (iter),refine_mem,nproc)
		tasks = self.addToTasks(tasks,'/bin/mv -v fsc.eotest fsc.eotest.%d' % (iter))
		wrapper_getres = os.path.join(self.params['appionwrapper'],'getRes.pl')
		tasks = self.addToTasks(tasks,
			'%s %d %d %.3f >> resolution.txt' % (wrapper_getres,iter,self.params['boxsize'], self.params['apix']))
		tasks = self.addToTasks(tasks,'/bin/rm -fv cls*.lst')
		tasks = self.addToTasks(tasks,'')
		return tasks

if __name__ == '__main__':
	app = EmanRefineJob()
	app.start()
	app.close()
