#!/usr/bin/env python
import os
import sys
import math
import time
#appion
from appionlib import apDisplay
from appionlib import apRefineJob
from appionlib import apParam

#================
#================
class FrealignRefineJob(apRefineJob.RefineJob):
	#================
	def setupParserOptions(self):
		super(FrealignRefineJob,self).setupParserOptions()
		self.parser.add_option('--recononly', dest='recononly', default=False, action='store_true',
		help="run recon part only, allowed only if startiter=enditer")
		self.parser.add_option('--refineonly', dest='refineonly', default=False, action='store_true',
		help="run refine part only, allowed only if startiter=enditer")

	#================
	def setIterationParamList(self):
		super(FrealignRefineJob,self).setIterationParamList()
		self.iterparams.extend([
				####card 1
				# cform is determined by stackname extension
				{'name':"mode" , 'default':1,
					'help':"refine and reconstruct. (=IFLAG in frealign documentation)"},
				{'name':"fmag", 'default':False,
					 'help':"Refine the magnification"},
				{'name':"fdef", 'default':False,
					 'help':"Refine the defocus"},
				{'name':"fastig", 'default':False,
					 'help':"Refine the defocus astigmatism"},
				{'name':"fpart", 'default':False,
					 'help':"Refine the defocus per particle"},
				{'name':'iewald', 'default':0, 'help':'Ewald sphere distortion correction (0:disable,1:simple,2:reference-base etc.'},
				{'name':'fbeaut', 'default': True,'help':'real-space symmetrization'},
				{'name':"fcref", 'default':False,
					 'help':"apply FOM filter to final reconstruction"},
				{'name':'fmatch', 'default':False, 'help':'make matching projection for each particle'},
				{'name':'ifsc','default': 0, 'help':'memory saving function (0:disable)'},
				{'name':'fstat','default': False, 'help':'memory saving function, calculates many stats, such as SSNR'},
				{'name':"iblow", 'default':4,
					'help':"1,2, or 4. Padding factor for reference structure. iblow=4 requires the most memory but results in the fastest search & refinement."},

				####card 2
				#{'name':"outerMaskRadius", 
				#	'help':"mask from center of particle to outer edge"},
				#{'name':"innerMaskRadius", 'default':0, 
				#	'help':"inner mask radius"},
				{'name':"wgh", 'default':0.07, 
					'help':"amplitude contrast"},
				{'name':"xstd", 'default':0.0, 
					'help':"standard deviations above mean for masking of input model"},
				{'name':"pbc", 'default':100.0, 
					'help':"conversion constant for phase residual weighting of particles. 100 gives equal weighting"},
				{'name':"boff", 'default':75.0,
					'help':"average phase residual of all particles. used for weighting"},
				#{'name':"ang", , 'default':5.0, 
				#	'help':"step size if using modes 3 and 4"},
				{'name':"itmax", 'default':10,
					'help':"number of iterations of randomization. used for modes 2 and 4"},
				{'name':"ipmax", 'default':0,
					'help':"number of potential matches in a search that should be tested further in local refinement"},

				####card 4
				{'name':"last", 'default':'',
					'help':"last particle to process"},

				####card 5
				#{'name':"sym", 'default':'', 'help':"symmetry. Options are I, O, Dx (e.g. D7), or Cx (e.g. C7)"},

				####card 6
				{'name':"target", 'default':15.0, 
					'help':"target phase residual during refinement"},
				{'name':"thresh", 'default':90.0, 
					'help':"phase residual threshold cut-off"},
				{'name':"cs", 'default':2.0, 
					'help':"spherical aberation"},
				{'name':"kv", 'default':120.0, 
					'help':"accelerlating voltage"},
				{'name':'beamtiltx', 'default': 0.0, 'help':'beam tilt in x direction'},
				{'name':'beamtilty', 'default': 0.0, 'help':'beam tilt in y direction'},

				####card 7
				{'name':"rrec", 'default':10.0,   
					'help':"resolution to which to limit the reconstruction"},
				{'name':"hp", 'default':100.0, 
					'help':"upper limit for low resolution signal"},
				{'name':"lp", 'default':10.0, 
					'help':"lower limit for high resolution signal"},
				{'name':'dfstd', 'default': 100, 'help':'defocus standard deviation (in Angstroms), usually +/- 100 A, only for defocus refinement'},
				{'name':"rbfact", 'default':0.0, 
					'help':"rbfact to apply to particles before classification."},

				####card 10
				{'name':"inpar", 'default':'',
					'help':"Input particle parameters."},
					
				####card 11
				{'name':"outpar", 'default':'',
					'help':"Output particle parameters."},
		
				])

	#=====================
	def checkPackageConflicts(self):
		if self.params['startiter'] != self.params['enditer']:
			if self.params['recononly'] or self.params['refineonly']:
				apDisplay.printError("partial iteration only allowed if startiter==enditer.")
		self.params['relmag'] = 1.0
		pieces = self.params['stackname'].split('.')
		ext = pieces[-1]
		if ext == 'mrc':
			self.params['cform'] = 'M'
		elif ext == 'hed':
			self.params['cform'] = 'I'
		else:
			self.params['cform'] = 'S'

	def checkIterationConflicts(self):
		''' 
		Conflict checking of per-iteration parameters
		'''
		super(FrealignRefineJob,self).checkIterationConflicts()

		self.recon_mem,iblow = self.calcRefineMem(self.params['ppn'],self.params['boxsize'],self.params['mem'])
		if iblow < max(self.params['iblow']):
			apDisplay.printWarning("iblow will be reduced to %d due to lack of memory" % iblow)
			self.params['iblow'] = map((lambda x: min(iblow,x)), self.params['iblow'])

	def convertSymmetryNameForPackage(self,inputname):
		'''
		hedral symmetry key is of possible name, value is that of this package
		'''
		frealign_hedral_symm_names = {'oct':'O','icos':'I'}
		inputname = inputname.lower()
		if inputname[0] in ('c','d'):
			bits = inputname.split(' ')
			symm_name = bits[0].upper()
		elif inputname in frealign_hedral_symm_names.keys():
			symm_name = frealign_hedral_symm_names[inputname]
		else:
			apDisplay.printWarning("unknown symmetry name conversion. Use it directly")
			symm_name = inputname.upper()
		return symm_name

	def setFrealignRefineParams(self):
		frealign_inputparams = []
		# card 1
		card = ("cform", "mode" , "fmag", "fdef", "fastig", "fpart", "iewald","fbeaut", "fcref", "fmatch", "ifsc", "fstat", "iblow",)
		frealign_inputparams.append(card)
		####card 2
		card = ("outerMaskRadius", "innerMaskRadius", "apix", "wgh", "xstd", "pbc", "boff", "angSampRate", "itmax", "ipmax",)
		frealign_inputparams.append(card)
		####card 5
		card = ("symmetry",)
		frealign_inputparams.append(card)
		####card 6
		card = ("relmag","apix","target", "thresh", "cs", "kv", "beamtiltx", "beamtilty",) 
		frealign_inputparams.append(card)
		####card 7
		card = ("rrec", "hp", "lp", "dfstd", "rbfact",)
		frealign_inputparams.append(card)
		return frealign_inputparams
		
	def combineFrealignParams(self,iter_index,valid_paramkeys):
		task_params = []
		card = ("outerMaskRadius", "innerMaskRadius", "apix", "wgh", "xstd", "pbc", "boff", "angSampRate", "itmax", "ipmax",)
		for key in valid_paramkeys:
			if key in self.params.keys():
				if type(self.params[key]) == type([]):
					paramvalue = self.params[key][iter_index]
				else:
					paramvalue = self.params[key]
				paramtype = type(paramvalue)
				if paramtype == type(True):
					if paramvalue is True:
						task_params.append('T')
					else:
						task_params.append('F')
				elif paramtype == type(0.5):
					task_params.append('%.3f' % (paramvalue))
				elif paramtype == type(1):
					task_params.append('%d' % (paramvalue))
				elif paramvalue == '':
					continue
				else:
					task_params.append('%s' % (paramvalue))
		return task_params

	def createFrealignInputLineTemplate(self,iter,input_params):
		constant_inputlines = []
		iter_index = iter - self.params['startiter']
		for cardkey in input_params:
			constant_inputlines.append(','.join(self.combineFrealignParams(iter_index,cardkey)))
		constant_inputlines.insert(2,'1,1,1,1,1')
		constant_inputlines.insert(3,'1, %d' % self.params['totalpart'])
		stackfile = os.path.basename(self.params['stackname'])
		pieces = stackfile.split('.')
		stackfilehead = '.'.join(pieces[:len(pieces)-1])
		appendcards = [
				'../../%s' % stackfile,
				'match',
				'../../params.%03d.par' % (iter-1),
				'outparams.par',
				'shift.par',
				'-100.0,0,0,0,0,0,0,0',
				'../../threed.%03da.mrc' % (iter-1),
				'weights',
				'odd.mrc',
				'even.mrc',
				'phasediffs',
				'pointspread',
				]
		constant_inputlines.extend(appendcards)
		return constant_inputlines

	def writeReconShell(self,iter,inputlines,iterpath,nproc):
		pieces = inputlines[0].split(',')
		pieces[1] = '0'
		inputlines[0] = (',').join(pieces)
		pieces = inputlines[7].split('../')
		inputlines[7] = ('../').join(pieces[1:])
		inputlines[9] = 'params.%03d.par' % iter
		inputlines[12] = '0.0,0,0,0,0,0,0,0'
		inputlines[13] = 'threed.%03da.mrc' % iter
		lines_before_input = [
			'#!/bin/sh',
			'cd %s' % iterpath,
			'env |grep SHELL',
			'/bin/rm -fv params.%03d.par' % iter,
			"cat proc*/outparams.par |grep -v '^C' | sort -n > params.%03d.par" % iter,
			'wc -l params.%03d.par' % iter,
			'/bin/rm -fv iter%03d.???' % iter,
			'/bin/rm -fv threed.%03da.???' % iter,
			'/bin/rm -fv frealign.recon.out',
			'export NCPUS=%d' % nproc,
			'hostname'
			'',
			'### START FREALIGN ###',
			'frealign_mp << EOF > frealign.recon.out',
			]
		lines_after_input=[
			'EOF',
			'',
			'',
			'### END FREALIGN ###',
			'echo "END FREALIGN"',
			'',
			'proc3d odd.mrc even.mrc fsc=fsc.eotest.%d' % iter,
			'/bin/cp -v threed.%03da.mrc ..' % iter,
			'/bin/cp -v params.%03d.par ..' % iter,
			]
		alllines = lines_before_input+inputlines+lines_after_input

		procfile = os.path.join(iterpath,'frealign.iter%03d.recon.sh' %	(iter))
		f = open(procfile,'w')
		f.writelines(map((lambda x: x+'\n'),alllines))
		f.close()
		os.chmod(procfile, 0755)
		return procfile

	def writeMultipleRefineShells(self,iter,constant_inputlines,iterpath,nproc):
		scripts = []
		files = []
		last_particle = self.params['totalpart']
		# This is integer division and will return integer
		stepsize = int(math.ceil(float(last_particle) / nproc))
		for proc in range(nproc):
			proc_start_particle = stepsize * proc + 1
			proc_end_particle = min(stepsize * (proc+1), last_particle)
			proc_inputlines = list(constant_inputlines)
			proc_inputlines[3] = '%d, %d' % (proc_start_particle,proc_end_particle)
			
			procpath = os.path.join(iterpath,'proc%03d' % (proc))
			apParam.createDirectory(procpath, warning=False)
			lines_before_input = [
				'#!/bin/sh',
				'# Proc %03d, Particles %d - %d' % (proc,proc_start_particle,proc_end_particle),
				'rm -rf %s' % procpath,
				'mkdir %s' % procpath,
				'cd %s' % procpath,
				'',
				'',
				'### START FREALIGN ###',
				'frealign_mp << EOF > frealign.proc%03d.out' % proc,
				]
			lines_after_input=[
				'EOF',
				'',
				'### END FREALIGN',
				'echo "END FREALIGN"',
				]
			alllines = lines_before_input+proc_inputlines+lines_after_input

			procfile = os.path.join(iterpath,'frealign.iter%03d.proc%03d.sh' %	(iter,proc))
			f = open(procfile,'w')
			f.writelines(map((lambda x: x+'\n'),alllines))
			f.close()
			os.chmod(procfile, 0755)
			scripts.append(procfile)
		return scripts

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

	def calcRefineMem(self,ppn,boxsize,max_mem):
		for iblow  in (4,2,1):
			memneed = (24*boxsize**3+4*(boxsize*iblow)**3+200e6)*2.0*ppn
			numgig = math.ceil(memneed/1073741824.0)
			if numgig <= max_mem:
				break
		return int(numgig),iblow

	def makeNewTrialScript(self):
		self.addSimpleCommand('ln -s  %s threed.000a.mrc' % self.params['modelnames'][0])

	def makeRefineTasks(self,iter):
		tasks = {}
		nproc = self.params['nproc']
		iterpath = os.path.join(self.params['recondir'],'iter%03d' % (iter))
		apParam.createDirectory(iterpath, warning=False)
		# set frealign param keys
		frealign_param_keys = self.setFrealignRefineParams()
		inputlines_template = self.createFrealignInputLineTemplate(iter,frealign_param_keys)
		if not self.params['recononly']:
			# refine parallelizable to multiple nodes
			refine_files = self.writeMultipleRefineShells(iter,inputlines_template,iterpath,self.nproc)
			# use mpi to parallelize the processes
			masterfile_name = 'mpi.iter%03d.run.sh' % (iter)
			mpi_refine = self.setupMPIRun(refine_files,self.nproc,iterpath,masterfile_name)
			tasks = self.addToTasks(tasks,mpi_refine,self.mem,self.ppn)
		if not self.params['refineonly']:
			# combine and recon parallelized only on one node
			recon_file = self.writeReconShell(iter,inputlines_template,iterpath,self.ppn)	
			tasks = self.addToTasks(tasks,recon_file,self.recon_mem,self.ppn)
			tasks = self.addToTasks(tasks,'cd %s' % iterpath)
			tasks = self.addToTasks(tasks,'getRes.pl %s %d %.3f >> ../resolution.txt' % (iter,self.params['boxsize'],self.params['apix']))
			tasks = self.addToTasks(tasks,'cd %s' % self.params['recondir'])
		return tasks

if __name__ == '__main__':
	app = FrealignRefineJob()
	app.start()
	app.close()
