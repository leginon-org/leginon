#!/usr/bin/env python
import os
import sys
import math
import time
#appion
from appionlib import apDisplay
from appionlib import apRefineJob
from appionlib import apParam
from appionlib import apFrealign

#================
#================
class FrealignRefineJob(apRefineJob.RefineJob):
	#================
	def setupParserOptions(self):
		super(FrealignRefineJob,self).setupParserOptions()
		self.parser.add_option('--recononly', dest='recononly', default=False, action='store_true',
			help="run recon part only, allowed only if startiter=enditer")
		self.parser.add_option('--ffilt', dest='ffilt', default=False, action='store_true',
			help="apply SSNR filter to reconstruction")
		self.parser.add_option('--fpbc', dest='fpbc', default=False, action='store_true',
			help="phase residual weighting of particles. False gives 100 (equal weighting), True gives 4.0")
		self.parser.add_option('--psi', dest='psi', default=False, action='store_true',
			help="include phi in refinement if set to True")
		self.parser.add_option('--theta', dest='theta', default=False, action='store_true',
			help="include phi in refinement if set to True")
		self.parser.add_option('--phi', dest='phi', default=False, action='store_true',
			help="include phi in refinement if set to True")
		self.parser.add_option('--x', dest='x', default=False, action='store_true',
			help="include phi in refinement if set to True")
		self.parser.add_option('--y', dest='y', default=False, action='store_true',
			help="include phi in refinement if set to True")
		self.parser.add_option("--dstep", dest="dstep", type="float",
			help="Camera physical pixel size in micron", metavar="#")

	#================
	def setIterationParamList(self):
		super(FrealignRefineJob,self).setIterationParamList()
		self.iterparams.extend([
				####card 1
				# cform is determined by stackname extension
				{'name':"mode" , 'default':1,
					'help':"refine or reconstruct. (=IFLAG in frealign documentation)"},
				{'name':"fmag", 'default':False,
					 'help':"Refine the magnification"},
				{'name':"fdef", 'default':False,
					 'help':"Refine the defocus"},
				#fastig is always False
				{'name':"fpart", 'default':False,
					 'help':"Refine the defocus per particle"},
				# iewald is always 0
					#{'name':'iewald', 'default':0, 'help':'Ewald sphere distortion correction (0:disable,1:simple,2:reference-base etc.'},
				{'name':'fbeaut', 'default': False,'help':'real-space symmetrization'},
				# ffilt is set globally
				{'name':"fbfact", 'default':False,
					 'help':"correct B-factor in reconstruction"},
				{'name':'fmatch', 'default':False, 'help':'make matching projection for each particle'},
				#ifsc is always 0
					#{'name':'ifsc','default': 0, 'help':'memory saving function (0:disable)'},
				#fstat is always False
					#{'name':'fstat','default': False, 'help':'memory saving function, calculates many stats, such as SSNR'},
				#iblow is determined by memory requirement
					#{'name':"iblow", 'default':4,
					#	'help':"1,2, or 4. Padding factor for reference structure. iblow=4 requires the most memory but results in the fastest search & refinement."},

				####card 2
				#{'name':"outerMaskRadius", 
					#	'help':"mask from center of particle to outer edge"},
				#{'name':"innerMaskRadius", 'default':0, 
					#	'help':"inner mask radius"},
				{'name':"wgh", 'default':0.07, 
					'help':"amplitude contrast"},
				#xstd is always 0.0
					#{'name':"xstd", 'default':0.0, 
					#	'help':"standard deviations above mean for masking of input model"},
				#fpbc is the same for all iteration
				# boff is always 0.0
					#{'name':"boff", 'default':75.0,
					#	'help':"average phase residual of all particles. used for weighting"},
				# dang is always 5.0
					#{'name':"dang" , 'default':5.0, 
					#	'help':"step size if using modes 3 and 4"},
				# itmax is always 10
					#{'name':"itmax", 'default':10,
					#	'help':"number of iterations of randomization. used for modes 2 and 4"},
				# ipmax is always 10
					#{'name':"ipmax", 'default':0,
					#	'help':"number of potential matches in a search that should be tested further in local refinement"},

				####card 3
				# set as global parameters

				####card 4
				{'name':"last", 'default':'',
					'help':"last particle to process"},

				####card 5
				#{'name':"sym", 'default':'', 'help':"symmetry. Options are I, O, Dx (e.g. D7), or Cx (e.g. C7)"},

				####card 6
				# relmag is refined when magnification is refined.
				# dstep is the physical pixel size of the camera
				# target is always 30.0
					#{'name':"target", 'default':30.0, 
					#	'help':"target phase residual during refinement"},
				# to be consistent with other packages, we will use percentDiscard instead of thresh as input param
				{'name':"percentDiscard", 'default':0.2,
					'help':"percent to include"},
				# cs and kv are options in apRefineJob.py
				#{'name':"cs", 'default':2.0, 
				#	'help':"spherical aberation"},
				#{'name':"kv", 'default':120.0, 
				#	'help':"accelerlating voltage"},
				# beamtiltx is always 0.0
					#{'name':'beamtiltx', 'default': 0.0, 'help':'beam tilt in x direction'},
				# beamtilty is always 0.0
					#{'name':'beamtilty', 'default': 0.0, 'help':'beam tilt in y direction'},

				####card 7
				# rrec is set to 2 * Nyquist limit
					#{'name':"rrec", 'default':10.0,   
					#	'help':"resolution to which to limit the reconstruction"},
				{'name':"hp", 'default':300.0, 
					'help':"upper limit for low resolution signal"},
				{'name':"lp", 'default':10.0, 
					'help':"lower limit for high resolution signal"},
				# dfstd is always 100.0
					#{'name':'dfstd', 'default': 100, 'help':'defocus standard deviation (in Angstroms), usually +/- 100 A, only for defocus refinement'},
				# rbfact is always 30.0
					#{'name':"rbfact", 'default':0.0, 
					#	'help':"rbfact to apply to particles before classification."},

				####card 10
				{'name':"inpar", 'default':'',
					'help':"Input particle parameters."},
					
				####card 11
				{'name':"outpar", 'default':'',
					'help':"Output particle parameters."},
		
				])

	def setConstantParams(self):
		self.params['cform'] = 'M'
		self.params['fastig'] = False
		self.params['iewald'] = 0
		self.params['ifsc'] = 0
		self.params['fstat'] = False
		self.params['xstd'] = 0.0
		self.params['boff'] = 0.0
		self.params['dang'] = 5.0
		self.params['itmax'] = 10
		self.params['ipmax'] = 10
		self.params['ifirst'] = 1
		self.params['relmag'] = 1.0
		self.params['dstep'] = self.params['dstep']
		self.params['target'] = 30.0
		self.params['beamtiltx'] = 0.0
		self.params['beamtilty'] = 0.0
		self.params['dfstd'] = 100.0
		self.params['rbfact'] = 0.0
		self.params['includePsi'] = int(self.params['psi'])
		self.params['includeTheta'] = int(self.params['theta'])
		self.params['includePhi'] = int(self.params['phi'])
		self.params['includeX'] = int(self.params['x'])
		self.params['includeY'] = int(self.params['y'])

	#=====================
	def checkPackageConflicts(self):
		self.setConstantParams()
		if self.params['fpbc'] == False:
			self.params['pbc'] = 100.0
		else:
			self.params['pbc'] = 0.0
		self.recon_mem,self.params['iblow'] = self.calcRefineMem(self.params['ppn'],self.params['boxsize'],self.params['mem'])
		self.params['rrec'] = self.params['apix'] * 2

	def checkIterationConflicts(self):
		''' 
		Conflict checking of per-iteration parameters
		'''
		super(FrealignRefineJob,self).checkIterationConflicts()
		self.params['thresh'] = map((lambda x: 100 - x), self.params['percentDiscard'])

	def convertSymmetryNameForPackage(self,inputname):
		'''
		hedral symmetry key is of possible name, value is that of this package
		'''
		# (5 3 2) EMAN and (2 5 3) crowther icos would have been converted into (2 3 5) 3dem orientation during the preparation
		frealign_hedral_symm_names = {'oct':'O','icos (2 3 5) viper/3dem':'I','icos (2 5 3) crowther':'I','icos (5 3 2) eman':'I'}
		inputname = inputname.lower()
		if inputname[0] in ('c','d'):
			bits = inputname.split(' ')
			symm_name = bits[0].upper()
		elif inputname in frealign_hedral_symm_names.keys():
			symm_name = frealign_hedral_symm_names[inputname]
		else:
			symm_name = inputname.upper()
			apDisplay.printWarning("unknown symmetry name conversion. Use it directly as %s" % symm_name)
		return symm_name

	def setFrealignRefineParams(self):
		frealign_inputparams = []
		# card 1
		card = ("cform", "mode" , "fmag", "fdef", "fastig", "fpart", "iewald","fbeaut", "ffilt", "fbfact", "fmatch", "ifsc", "fstat", "iblow",)
		frealign_inputparams.append(card)
		####card 2
		card = ("outerMaskRadius", "innerMaskRadius", "apix", "wgh", "xstd", "pbc", "boff", "angSampRate", "itmax", "ipmax",)
		frealign_inputparams.append(card)
		####card 3
		card = ("includePsi", "includeTheta", "includePhi", "includeX", "includeY",)
		frealign_inputparams.append(card)
		####card 5
		card = ("symmetry",)
		frealign_inputparams.append(card)
		####card 6
		card = ("relmag","dstep","target", "thresh", "cs", "kv", "beamtiltx", "beamtilty",) 
		frealign_inputparams.append(card)
		####card 7
		card = ("rrec", "hp", "lp", "dfstd", "rbfact",)
		frealign_inputparams.append(card)
		return frealign_inputparams
		
	def combineFrealignParams(self,iter_index,valid_paramkeys):
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
		constant_inputlines.insert(3,'1, %d' % self.params['totalpart'])
		stackfile = os.path.basename(self.params['stackname'])
		pieces = stackfile.split('.')
		stackfilehead = '.'.join(pieces[:len(pieces)-1])
		appendcards = [
				'../../%s' % stackfile,
				'match.mrc',
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

	def getCombineShellLines(self,iter,iterpath):
		combine_lines = [
			'#!/bin/sh',
			'cd %s' % iterpath,
			'env |grep SHELL',
			'/bin/rm -fv params.%03d.par' % iter,
			"cat proc*/outparams.par |grep -v '^C' | sort -n > params.%03d.par" % iter,
			'wc -l params.%03d.par' % iter,
			]
		return combine_lines
	def writeRefineOnlyCombineShell(self,iter,iterpath):
		lines = self.getCombineShellLines(iter,iterpath)
		lines.extend([
			'cd ..',
			'/bin/ln -s threed.%03da.mrc threed.%03da.mrc' % (iter-1,iter),
			'cd %s' % iterpath,
			'/bin/cp -v params.%03d.par ..' % iter,
			])
		procfile = os.path.join(iterpath,'frealign.iter%03d.combine.sh' %	(iter))
		f = open(procfile,'w')
		f.writelines(map((lambda x: x+'\n'),lines))
		f.close()
		os.chmod(procfile, 0755)
		return procfile

	def writeReconShell(self,iter,inputlines,iterpath,ppn):
		pieces = inputlines[0].split(',')
		pieces[1] = '0' #mode = 0 for recon
		pieces[10] = 'F' #fmatch = F or no recon will be created
		inputlines[0] = (',').join(pieces)
		pieces = inputlines[7].split('../')
		inputlines[7] = ('../').join(pieces[1:])
		inputlines[9] = 'params.%03d.par' % iter
		inputlines[12] = '0.0,0,0,0,0,0,0,0'
		inputlines[13] = 'threed.%03da.mrc' % iter
		lines_before_input = []
		if not iter == 0:
			combine_params_lines = self.getCombineShellLines(iter,iterpath)[3:]
		else:
			combine_params_lines = [
				'/bin/cp -v ../params.%03d.par .' % iter,
				'/bin/rm -fv ../threed.%03da.mrc' % iter,
			]
		lines_before_input.extend( [
			'#!/bin/sh',
			'cd %s' % iterpath,
			'env |grep SHELL',
		])
		lines_before_input.extend(combine_params_lines)
		lines_before_input.extend( [
			'wc -l params.%03d.par' % iter,
			'/bin/rm -fv iter%03d.???' % iter,
			'/bin/rm -fv threed.%03da.???' % iter,
			'/bin/rm -fv frealign.recon.out',
			'export NCPUS=%d' % ppn,
			'hostname'
			'',
			'### START FREALIGN ###',
			'frealign_v8_mp.exe << EOF > frealign.recon.out',
			])
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
				'frealign_v8.exe << EOF > frealign.proc%03d.out' % proc,
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
		# refine only does not need to adjust iblow by available memory
		if self.params['refineonly']:
			return int(max_mem),2
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
		if not self.params['recononly'] and iter > 0:
			# refine parallelizable to multiple nodes
			refine_files = self.writeMultipleRefineShells(iter,inputlines_template,iterpath,self.nproc)
			# use mpi to parallelize the processes
			masterfile_name = 'mpi.iter%03d.run.sh' % (iter)
			mpi_refine = self.setupMPIRun(refine_files,self.nproc,iterpath,masterfile_name)
			tasks = self.addToTasks(tasks,mpi_refine,self.mem,self.ppn)
			tasks = self.logTaskStatus(tasks,'refine',os.path.join(iterpath,'proc%03d/frealign.proc%03d.out' % (self.nproc-1,self.nproc-1)),iter)
		if not self.params['refineonly'] or iter == 0:
			# combine and recon parallelized only on one node
			recon_file = self.writeReconShell(iter,inputlines_template,iterpath,self.ppn)	
			mp_recon = self.setupMPRun(recon_file,self.recon_mem,self.ppn)
			tasks = self.addToTasks(tasks,mp_recon,self.recon_mem,self.ppn)
			tasks = self.addToTasks(tasks,'cd %s' % iterpath)
			tasks = self.addToTasks(tasks,'getRes.pl %s %d %.3f >> ../resolution.txt' % (iter,self.params['boxsize'],self.params['apix']))
			tasks = self.logTaskStatus(tasks,'eotest','../resolution.txt',iter)
			tasks = self.addToTasks(tasks,'cd %s' % self.params['recondir'])
			tasks = self.logTaskStatus(tasks,'recon',os.path.join(iterpath,'frealign.recon.out'),iter)
		else:
			recon_file = self.writeRefineOnlyCombineShell(iter,iterpath)	
			mp_recon = self.setupMPRun(recon_file,2,1)
			tasks = self.addToTasks(tasks,mp_recon,2,1)
			tasks = self.addToTasks(tasks,'cd %s' % iterpath)

		return tasks

	def isNewTrial(self):
		'''
		Check if clean up before start is needed.
		'''
		return self.params['startiter'] == 1 and not self.params['recononly']
		
	def needIter0Recon(self):
		'''
		Function to determine if a reconstruction should be made before the first refimement.
		New Trial using euler angles from other refinement run should do an reconstruction first
		'''
		if self.params['startiter'] > 1:
			return False
		### need iteration 0 recon if params.000.par came from a reconiter
		# Not using database in case of limited access.
		initparamfile = 'params.000.par'
		parttree = apFrealign.parseFrealignParamFile(initparamfile)
		for p in parttree:
			if not (p['psi']==p['phi']==p['theta']==p['shiftx']==p['shifty']):
				return True
		return False

if __name__ == '__main__':
	app = FrealignRefineJob()
	app.start()
	app.close()
