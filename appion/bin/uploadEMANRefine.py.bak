#!/usr/bin/env python

#python
import glob, os, re, shutil, tarfile, math
import subprocess

#appion
from appionlib import appionScript
from appionlib import apDisplay
from appionlib import apFile
from appionlib import apParam
from appionlib import appiondata
from appionlib import apRecon
from appionlib import apXmipp
from appionlib import apEulerCalc
from appionlib import apSymmetry
from appionlib import reconUploader
from pyami import mrc


#======================
#======================
class uploadEmanProjectionMatchingRefinementScript(reconUploader.generalReconUploader):

	def __init__(self):
		###	DEFINE THE NAME OF THE PACKAGE
		self.package = "EMAN"
		self.multiModelRefinementRun = False
		super(uploadEmanProjectionMatchingRefinementScript, self).__init__()

	#=====================
	def findLastCompletedIteration(self):
		''' find the last iteration that finished in EMAN job, trying to make this more clever and look at actual volumes '''
		
		lastiter = 0
		if os.path.isdir(self.projmatchpath) is False:
			apDisplay.printError("projection matching did not run. Please double check and restart the job")
			
		files = glob.glob(os.path.join(self.projmatchpath, "threed.[0-9]*a.mrc"))
		if isinstance(files, list) and len(files)>0:
			for file in files:
				m = re.search("[0-9]+", os.path.basename(file))
				iternum = int(m.group(0))
				if iternum > lastiter:
					lastiter = iternum	
				
		### now open up in numpy and make sure that it's a valid file
		vol = mrc.read(os.path.join(self.projmatchpath, "threed.%da.mrc" % lastiter))
		if vol.mean() == 0 and vol.max() == 0 and vol.min() == 0:
			apDisplay.printError("there is something wrong with your volumes, make sure that the refinement ran correctly")
		else:
			apDisplay.printMsg("EMAN ran "+str(lastiter)+" iterations")

		return lastiter

	#======================
	def findEmanCommandFile(self):
		''' tries to find EMAN log file either through the jobinfo (retrieved through jobid) or runname '''
	
		### find the job file
		if 'jobinfo' in self.params and self.params['jobinfo'] is not None:
			jobfile = os.path.join(self.params['rundir'], self.params['jobinfo']['name'])
		elif 'runname' in self.params:
			jobfile = os.path.join(self.params['rundir'], self.params['runname']+".appionsub.job")
		else:
			self.params['jobinfo'] = None
			apDisplay.printError("no command file or jobfile found ... try uploading refinement as an external package")

		basename, extension = os.path.splitext(jobfile)
		commandfile = basename + ".commands"
		
		if not os.path.isfile(commandfile):
			apDisplay.printError("no command file found ... try uploading refinement as an external package")

		return commandfile
			
	#======================
	def findEmanJobFile(self):
		''' tries to find EMAN log file either through the jobinfo (retrieved through jobid) or runname '''
	
		### find the job file
		if 'jobinfo' in self.params and self.params['jobinfo'] is not None:
			jobfile = os.path.join(self.params['rundir'], self.params['jobinfo']['name'])
		elif 'runname' in self.params:
			jobfile = os.path.join(self.params['rundir'], self.params['runname']+".appionsub.job")
		else:
			self.params['jobinfo'] = None
			apDisplay.printError("no pickle file or jobfile found ... try uploading refinement as an external package")

		if not os.path.isfile(jobfile):
			apDisplay.printError("no pickle file or jobfile found ... try uploading refinement as an external package")

		return jobfile

#		logfile = os.path.join(self.params['rundir'], 'eman.log')
#		if os.path.isfile(logfile):
#			return logfile
#		logfile = os.path.join(self.params['rundir'], '.emanlog')
#		if os.path.isfile(logfile):
#			return logfile
#		apDisplay.printError("Could not find eman job or log file")

	#=====================
	def readParticleLog(self, iteration):
		plogf = os.path.join(self.projmatchpath, "particle.log")
		if not os.path.isfile(plogf):
			apDisplay.printError("no particle.log file found")

		f = open(plogf,'r')
		badprtls = []
		n = str(int(iteration)+1)
		for line in f:
			rline = line.rstrip()
			if re.search("X\t\d+\t"+str(iteration)+"$",rline):
				bits = rline.split()
				badprtls.append(int(bits[1]))
			# break out of into the next iteration
			elif re.search("X\t\d+\t"+n+"$",rline):
				break
		f.close()
		return badprtls
	
	#=====================
	def getEulersFromProj(self, iteration):
		''' EMAN Eulers saved in proj.#.txt file for alt and az eulers, phi is in cls####.lst file '''

		### get Eulers from the projection file
		eulers=[]
		projfile = os.path.join(self.projmatchpath, "proj.%d.txt" % iteration)
		if not os.path.exists(projfile):
			apDisplay.printError("no projection file found for iteration %d" % iteration)
		f = open(projfile,'r')
		for line in f:
			line = line[:-1] # remove newline at end
			i = line.split()
			angles = [i[1],i[2],i[3]]
			eulers.append(angles)
		f.close()
		return eulers

	#=====================
	def setDefaultPackageParameters(self):
		packageparams = {
			'package': '',
			'num': '',
			'ang': '',
			'mask': '',
			'imask': '',
			'pad': '',
			'sym': '',
			'maxshift': '',
			'hard': '',
			'classkeep': '',
			'classiter': '',
			'filt3d': '',
			'shrink': '',
			'euler2': '',
			'xfiles': '',
			'amask1': '',
			'amask2': '',
			'amask3': '',
			'median': '',
			'phasecls': '',
			'fscls': '',
			'refine': '',
			'goodbad': '',
			'perturb': '',
			'hpfilter': '',
			'lpfilter': '',
			'msgpasskeep': '',
			'msgpassminp': '',
		}
		return packageparams

	#=====================
	def parseFileForRunParameters(self):
		''' PACKAGE-SPECIFIC FILE PARSER: if the parameters were not pickled, parse protocols script to determine projection-matching params '''

		### parse out the refine command from the .emanlog to get the parameters for each iteration
		#jobfile = self.findEmanJobFile()
		jobfile = self.findEmanCommandFile()
		apDisplay.printMsg("parsing eman log file: "+jobfile)
		jobf = open(jobfile,'r')
		lines = jobf.readlines()
		jobf.close()
		itercount = 0
		packageparams = self.setDefaultPackageParameters()
		for i in range(len(lines)):
			### if read a refine line, get the parameters
			line = lines[i].rstrip()
			if re.search("refine \d+ ", line):
				itercount += 1
				emanparams=line.split(' ')
				if emanparams[0] is "#":
					emanparams.pop(0)
				### get rid of first "refine"
				emanparams.pop(0)
				packageparams['num'] += emanparams[0]
				packageparams['sym']=''
				for p in emanparams:
					elements = p.strip().split('=')
					if elements[0]=='ang':
						packageparams['ang'] += str(elements[1])+" "
					elif elements[0]=='mask':
						packageparams['mask'] += str(elements[1])+" "
					elif elements[0]=='imask':
						packageparams['imask'] += str(elements[1])+" "
					elif elements[0]=='pad':
						packageparams['pad'] += str(elements[1])+" "
					elif elements[0]=='sym':
						packageparams['sym'] += str(elements[1])+" "
					elif elements[0]=='maxshift':
						packageparams['maxshift'] += str(elements[1])+" "
					elif elements[0]=='hard':
						packageparams['hard'] += str(elements[1])+" "
					elif elements[0]=='classkeep':
						packageparams['classkeep'] += str(elements[1].strip())+" "
					elif elements[0]=='classiter':
						packageparams['classiter'] += str(elements[1])+" "
					elif elements[0]=='filt3d':
						packageparams['filt3d'] += str(elements[1])+" "
					elif elements[0]=='shrink':
						packageparams['shrink'] += str(elements[1])+" "
					elif elements[0]=='euler2':
						packageparams['euler2'] += str(elements[1])+" "
					elif elements[0]=='xfiles':
						### trying to extract "xfiles" as entered into emanJobGen.php
						values = elements[1]
						apix,mass,alito = values.split(',')
						packageparams['xfiles'] += str(mass)+" "
					elif elements[0]=='amask1':
						packageparams['amask1'] += str(elements[1])+" "
					elif elements[0]=='amask2':
						packageparams['amask2'] += str(elements[1])+" "
					elif elements[0]=='amask3':
						packageparams['amask3'] += str(elements[1])+" "
					elif elements[0]=='median':
						packageparams['median'] += str(True)+" "
					elif elements[0]=='phasecls':
						packageparams['phasecls'] += str(True)+" "
					elif elements[0]=='fscls':
						packageparams['fscls'] += str(True)+" "
					elif elements[0]=='refine':
						packageparams['refine'] += str(True)+" "
					elif elements[0]=='goodbad':
						packageparams['goodbad'] += str(True)+" "
					elif elements[0]=='perturb':
						packageparams['perturb'] += str(True)+" "
						
				### Coran / MsgP performed 6 lines after standard refinement
				if re.search("coran_for_cls.py", lines[i+6]): 
					packageparams['package'] += 'EMAN/SpiCoran '
					apDisplay.printMsg("correspondence analysis was performed on iteration %d to refine averages" % itercount)
				elif re.search("msgPassing_subClassification.py", lines[i+6]):
					packageparams['package'] += 'EMAN/MsgP '
					apDisplay.printMsg("Message-passing was performed on iteration %d to refine averages" % itercount)
					msgpassparams = lines[i+6].split()
					for p in msgpassparams:
						elements = p.split('=')
						if elements[0]=='corCutOff':
							packageparams['msgpasskeep'] += str(elements[1])+" "
						elif elements[0]=='minNumOfPtcls':
							packageparams['msgpassminp'] += str(elements[1])+" "
				else:
					packageparams['package'] += 'EMAN '
		apDisplay.printColor("Found %d iterations" % itercount, "green")
		
		### set global parameters
		runparams = {}
		runparams['numiter'] = itercount
		runparams['mask'] = packageparams['mask']
		runparams['imask'] = packageparams['imask']
		runparams['symmetry'] = apSymmetry.findSymmetry(packageparams['sym'])
		runparams['angularSamplingRate'] = packageparams['ang']
		runparams['package_params'] = packageparams		

		return runparams

	#=====================
	def createParticleDataFile(self, iteration, badparticles):
		''' puts all relevant particle information into a single text file that can be read by the uploader '''
		
		os.chdir(self.projmatchpath)
		
		### extract tarfile
		tmpdir = "tmp"
		apParam.createDirectory(tmpdir)
		clsf = "cls.%d.tar" % iteration
		try:
			clstar = tarfile.open(clsf)
			clsnames = clstar.getnames()
			clslist = clstar.getmembers()
		except tarfile.ReadError, e:
			apDisplay.printError("cannot open tarfile %s" % clsf)
		for clsfile in clslist:
			clstar.extract(clsfile, tmpdir)
		clstar.close()

		### write data in appion format to input file for uploading to the database
		particledataf = open(os.path.join(self.resultspath, "particle_data_%s_it%.3d_vol001.txt" % (self.params['timestamp'], iteration)), "w")
#		particledataf.write("### column info: ")
		particledataf.write("#%8s" % "partnum")
		particledataf.write("%10s" % "phi")
		particledataf.write("%10s" % "theta")
		particledataf.write("%10s" % "omega")
		particledataf.write("%10s" % "shiftx")
		particledataf.write("%10s" % "shifty")
#		particledataf.write("(7) mirror")
		particledataf.write("%8s" % "3D_ref#")
		particledataf.write("%8s" % "2D_cls#")
		particledataf.write("%10s" % "qfact")
		particledataf.write("%8s" % "keptp")
		particledataf.write("%8s\n" % "p_keptp")

		### read parameters from extracted cls files
		eulers = self.getEulersFromProj(iteration)
		for i, cls in enumerate(clsnames):
			f = open(os.path.join(tmpdir, cls))
			coranfail = False
			for line in f:
				if re.search("start", line):
					ali=line.split()
					prtlnum = int(ali[0])			
					# check if bad particle
					if prtlnum in badparticles:
						keptp = 0
					else:
						keptp = 1
					other=ali[3].split(',')
						
					### SPIDER coran kept particle
					refine_keptp = 0
					if apRecon.getComponentFromVector(self.runparams['package_params']['package'], iteration-1) == 'EMAN/SpiCoran':
						if len(other) > 4:
							refine_keptp = bool(int(other[4]))
						else:
							if coranfail is False:
								apDisplay.printWarning("Coran failed on this iteration")
								coranfail = True

					### message passing kept particle
					if apRecon.getComponentFromVector(self.runparams['package_params']['package'], iteration-1) == 'EMAN/MsgP' and len(ali) > 4:
						refine_keptp = bool(int(ali[4]))

					### write the results to Appion format
					alt = float(eulers[i][0])
					az = float(eulers[i][1])
					Ephi = float(other[0])*180./math.pi
					mirror = int(float(other[3]))
					if mirror:
						alt, az, Ephi = apEulerCalc.calculate_equivalent_EMANEulers_without_flip(alt, az, Ephi)
					phi, theta, omega = apEulerCalc.convertEmanEulersToXmipp(alt, az, Ephi)
					full_sym_name = self.runparams['symmetry']['symmetry']
					if 'Icos' in full_sym_name:
						# EMAN Icos is always 532 orientation, while particlefile is set to 235
						phi,theta,omega = apEulerCalc.convert3DEMIcosEulerFrom532('Icos (2 3 5) Viper/3DEM',phi,theta,omega)
					particledataf.write("%9d" % (int(prtlnum)+1)) ### NOTE: IT IS IMPORTANT TO START WITH 1, OTHERWISE STACKMAPPING IS WRONG!!!
					particledataf.write("%10.4f" % phi)
					particledataf.write("%10.4f" % theta)
					particledataf.write("%10.4f" % omega)
					particledataf.write("%10.4f" % float(other[1]))
					particledataf.write("%10.4f" % float(other[2]))
#					particledataf.write("%6d" % int(float(other[3]))) ### mirror is no longer accounted for
					particledataf.write("%8d" % 1)
					particledataf.write("%8d" % int(i))
					particledataf.write("%10.2f" % float(ali[2].strip(',')))
					particledataf.write("%8d" % keptp)
					particledataf.write("%8d\n" % refine_keptp)
		particledataf.close()

		### remove tmp directory
		apFile.removeDir(tmpdir)
		os.chdir(self.basepath)
				
		return
		
	#======================	
	def convertFSCFileForIteration(self, iteration):
		''' EMAN creates FSC files with pixel number in column 1, FSC in column 2, convert this to 3DEM format '''
	
		fscfile = os.path.join(self.projmatchpath, "fsc.eotest.%d" % iteration)

		try: 
			f = open(fscfile, "r")
		except IOError, e:
			apDisplay.printWarning("%s file could not be opened, data will NOT be inserted into the database" % fscfile)
			return False
		
		fsclines = f.readlines()
		f.close()
		split = [l.strip().split() for l in fsclines]
		newfscfile = open(os.path.join(self.resultspath, "recon_%s_it%.3d_vol001.fsc" % (self.params['timestamp'], iteration)), "w")
		newfscfile.write("### column (1) inverse Angstroms, column (2) Fourier Shell Correlation (FSC)")
		for info in split:
			ipixel = float(info[0]) / (self.runparams['boxsize'] * self.runparams['apix'])
			fsc = float(info[1])
			newfscfile.write("%.6f\t%.6f\n" % (ipixel, fsc))
		newfscfile.close()
		
		return True

	def moveAndLink(self,oldf,newf,move):
		if not os.path.isfile(newf):
			if move:
				shutil.move(oldf, newf)
				os.symlink(newf, oldf)
			else:
				os.symlink(oldf, newf)
			
	#=====================
	def compute_stack_of_class_averages_and_reprojections(self, iteration, move=True):
		''' create EMAN class averages in new format '''
			
		classavg = os.path.join(self.projmatchpath, "classes.%d.img" % iteration)
		classavgnew = os.path.join(self.projmatchpath, "classes_eman.%d.img" % iteration)
		classavg_precoran = os.path.join(self.projmatchpath, "classes.%d.old.img" % iteration)
		classavg_coran = os.path.join(self.projmatchpath, "classes_coran.%d.img" % iteration)
		classavg_goodMsgP = os.path.join(self.projmatchpath, "goodavgs.%d.img" % iteration)
		
		### standard EMAN class averages
		if apRecon.getComponentFromVector(self.runparams['package_params']['package'], iteration-1) == "EMAN":
			if os.path.exists(classavg) and not os.path.islink(classavg):
				for ext in ['.img','.hed']:
					oldf = classavg.replace('.img', ext)
					newf = os.path.join(self.resultspath, "proj-avgs_%s_it%.3d_vol%.3d%s" % (self.params['timestamp'], iteration, 1, ext))
					self.moveAndLink(oldf,newf,move)

			elif os.path.exists(classavgnew) and not os.path.islink(classavgnew):
				for ext in ['.img','.hed']:
					oldf = classavgnew.replace('.img', ext)
					newf = os.path.join(self.resultspath, "proj-avgs_%s_it%.3d_vol%.3d%s" % (self.params['timestamp'], iteration, 1, ext))
					self.moveAndLink(oldf,newf,move)
					
		###		spider correspondence analysis used to refine class averages
		###
		###		NOTE: THESE ARE NAMED DIFFERENTLY THAN STANDARD CLASS AVGS ... CORAN CLASSES ARE SAVED AS classes.#.img,
		###		WHEREAS EMAN CLASSES ARE SAVED AS classes.#.old.img
		###
		
		elif apRecon.getComponentFromVector(self.runparams['package_params']['package'], iteration-1) == "EMAN/SpiCoran":
			if os.path.exists(classavg_coran) and not os.path.islink(classavg_coran):
				for ext in ['.img','.hed']:
					oldf = classavg_coran.replace('.img', ext)
					newf = os.path.join(self.resultspath, "refined_proj-avgs_%s_it%.3d_vol%.3d%s" % (self.params['timestamp'], iteration, 1, ext))
					self.moveAndLink(oldf,newf,move)
			if os.path.exists(classavg_precoran) and not os.path.islink(classavg_precoran):
				for ext in ['.img','.hed']:
					oldf = classavg_precoran.replace('.img', ext)
					newf = os.path.join(self.resultspath, "proj-avgs_%s_it%.3d_vol%.3d%s" % (self.params['timestamp'], iteration, 1, ext))
					self.moveAndLink(oldf,newf,move)
			elif os.path.exists(classavgnew) and not os.path.islink(classavgnew):
				for ext in ['.img','.hed']:
					oldf = classavgnew.replace('.img', ext)
					newf = os.path.join(self.resultspath, "proj-avgs_%s_it%.3d_vol%.3d%s" % (self.params['timestamp'], iteration, 1, ext))
					self.moveAndLink(oldf,newf,move)

		### message-passing used to refine class averages			
		elif apRecon.getComponentFromVector(self.runparams['package_params']['package'], iteration-1) == "EMAN/MsgP":
			if os.path.exists(classavg) and not os.path.islink(classavg):
				for ext in ['.img','.hed']:
					oldf = classavg.replace('.img', ext)
					newf = os.path.join(self.resultspath, "proj-avgs_%s_it%.3d_vol%.3d%s" % (self.params['timestamp'], iteration, 1, ext))
					self.moveAndLink(oldf,newf,move)
			elif os.path.exists(classavgnew) and not os.path.islink(classavgnew):
				for ext in ['.img','.hed']:
					oldf = classavgnew.replace('.img', ext)
					newf = os.path.join(self.resultspath, "proj-avgs_%s_it%.3d_vol%.3d%s" % (self.params['timestamp'], iteration, 1, ext))
					self.moveAndLink(oldf,newf,move)
			if os.path.exists(classavg_goodMsgP) and not os.path.islink(classavg_goodMsgP):
				for ext in ['.img','.hed']:
					oldf = classavg_goodMsgP.replace('.img', ext)
					newf = os.path.join(self.resultspath, "refined_proj-avgs_%s_it%.3d_vol%.3d%s" % (self.params['timestamp'], iteration, 1, ext))
					self.moveAndLink(oldf,newf,move)

		return

	#=====================
	def instantiateEmanParamsData(self, iteration):
		''' fill in database entry for ApEmanRefineIterData table '''

		### get components from parameter: e.g. 'ang = 20 15 10' for iteration 2 returns 15
		package				= apRecon.getComponentFromVector(self.runparams['package_params']['package'], iteration-1)
		ang				= apRecon.getComponentFromVector(self.runparams['package_params']['ang'], iteration-1)
		lpfilter			= apRecon.getComponentFromVector(self.runparams['package_params']['lpfilter'], iteration-1)
		hpfilter			= apRecon.getComponentFromVector(self.runparams['package_params']['hpfilter'], iteration-1)
		mask				= apRecon.getComponentFromVector(self.runparams['package_params']['mask'], iteration-1)
		imask				= apRecon.getComponentFromVector(self.runparams['package_params']['imask'], iteration-1)
		pad				= apRecon.getComponentFromVector(self.runparams['package_params']['pad'], iteration-1)
		maxshift			= apRecon.getComponentFromVector(self.runparams['package_params']['maxshift'], iteration-1)
		hard				= apRecon.getComponentFromVector(self.runparams['package_params']['hard'], iteration-1)
		classkeep			= apRecon.getComponentFromVector(self.runparams['package_params']['classkeep'], iteration-1)
		classiter			= apRecon.getComponentFromVector(self.runparams['package_params']['classiter'], iteration-1)
		filt3d				= apRecon.getComponentFromVector(self.runparams['package_params']['filt3d'], iteration-1)
		shrink				= apRecon.getComponentFromVector(self.runparams['package_params']['shrink'], iteration-1)
		euler2				= apRecon.getComponentFromVector(self.runparams['package_params']['euler2'], iteration-1)
		xfiles				= apRecon.getComponentFromVector(self.runparams['package_params']['xfiles'], iteration-1)
		amask1				= apRecon.getComponentFromVector(self.runparams['package_params']['amask1'], iteration-1)
		amask2				= apRecon.getComponentFromVector(self.runparams['package_params']['amask2'], iteration-1)
		amask3				= apRecon.getComponentFromVector(self.runparams['package_params']['amask3'], iteration-1)
		median				= apRecon.getComponentFromVector(self.runparams['package_params']['median'], iteration-1)
		phasecls			= apRecon.getComponentFromVector(self.runparams['package_params']['phasecls'], iteration-1)
		fscls				= apRecon.getComponentFromVector(self.runparams['package_params']['fscls'], iteration-1)
		refine				= apRecon.getComponentFromVector(self.runparams['package_params']['refine'], iteration-1)
		goodbad				= apRecon.getComponentFromVector(self.runparams['package_params']['goodbad'], iteration-1)
		perturb				= apRecon.getComponentFromVector(self.runparams['package_params']['perturb'], iteration-1)
		msgpasskeep			= apRecon.getComponentFromVector(self.runparams['package_params']['msgpasskeep'], iteration-1)
		msgpassminp			= apRecon.getComponentFromVector(self.runparams['package_params']['msgpassminp'], iteration-1)
		
		EMANRefineParamsq = appiondata.ApEmanRefineIterData()
		EMANRefineParamsq['package']			= package
		EMANRefineParamsq['ang']			= ang
		EMANRefineParamsq['lpfilter']			= lpfilter
		EMANRefineParamsq['hpfilter']			= hpfilter
		EMANRefineParamsq['mask']			= mask
		EMANRefineParamsq['imask']			= imask
		EMANRefineParamsq['pad']			= pad
		EMANRefineParamsq['EMAN_maxshift']		= maxshift
		EMANRefineParamsq['EMAN_hard']			= hard
		EMANRefineParamsq['EMAN_classkeep']		= classkeep
		EMANRefineParamsq['EMAN_classiter']		= classiter
		EMANRefineParamsq['EMAN_filt3d']		= filt3d
		EMANRefineParamsq['EMAN_shrink']		= shrink
		EMANRefineParamsq['EMAN_euler2']		= euler2
		EMANRefineParamsq['EMAN_xfiles']		= xfiles
		EMANRefineParamsq['EMAN_amask1']		= amask1
		EMANRefineParamsq['EMAN_amask2']		= amask2
		EMANRefineParamsq['EMAN_amask3']		= amask3
		EMANRefineParamsq['EMAN_median']		= median
		EMANRefineParamsq['EMAN_phasecls']		= phasecls
		EMANRefineParamsq['EMAN_fscls']			= fscls
		EMANRefineParamsq['EMAN_refine']		= refine
		EMANRefineParamsq['EMAN_goodbad']		= goodbad
		EMANRefineParamsq['EMAN_perturb']		= perturb
		EMANRefineParamsq['MsgP_cckeep']		= msgpasskeep
		EMANRefineParamsq['MsgP_minptls']		= msgpassminp
		
		return EMANRefineParamsq
	
	#=====================
	def start(self):
		
		### database entry parameters
		package_table = 'ApEmanRefineIterData|emanParams'
		
		### set EMAN projection-matching path
		self.projmatchpath = os.path.abspath(os.path.join(self.params['rundir'], "recon"))
		### if the path does not exist, we may need to unpack the tar results
		if not os.path.isdir( self.projmatchpath ):
			tarFileName = "recon_results.tar.gz"
			resultTar = os.path.abspath(os.path.join( self.params['rundir'], tarFileName) )
			if not os.path.isfile( resultTar ):
				apDisplay.printError("Could not find %s directory or %s file." % self.projmatchpath, resultTar )
			
			### unpack the tar file
			currDir = os.getcwd()
			os.chdir(self.params['rundir'])
			command = "tar -xf %s" % tarFileName
			retcode = subprocess.call(command, stdout=subprocess.PIPE,stderr=subprocess.PIPE,  shell = True)
			os.chdir(currDir)
			if not os.path.isdir( self.projmatchpath ):
				apDisplay.printError("Failed to unpack %s to %s." % self.projmatchpath, resultTar )
			
		### determine which iterations to upload
		lastiter = self.findLastCompletedIteration()
		uploadIterations = self.verifyUploadIterations(lastiter)	
	
		### upload each iteration
		for iteration in uploadIterations:
		
			### set package parameters, as they will appear in database entries
			package_database_object = self.instantiateEmanParamsData(iteration)
			
			### move FSC file to results directory
			self.FSCExists = self.convertFSCFileForIteration(iteration)
			
			### create a stack of class averages and reprojections (optional)
			self.compute_stack_of_class_averages_and_reprojections(iteration)
				
			### create a text file with particle information
			badparticles = self.readParticleLog(iteration)
			self.createParticleDataFile(iteration, badparticles)

			### create mrc file of map for iteration and reference number
			oldvol = os.path.join(self.projmatchpath, "threed.%da.mrc" % iteration)
			newvol = os.path.join(self.resultspath, "recon_%s_it%.3d_vol001.mrc" % (self.params['timestamp'], iteration))
			if not os.path.islink(newvol):
				try:
#					shutil.move(oldvol, newvol)
					os.symlink(oldvol, newvol)
				except IOError, e:
					print e

			### make chimera snapshot of volume
			self.createChimeraVolumeSnapshot(newvol, iteration)
			
			### instantiate database objects
			self.insertRefinementRunData(iteration)
			self.insertRefinementIterationData(iteration, package_table, package_database_object)
			
		### calculate Euler jumps
		if self.runparams['numiter'] > 1:
			self.calculateEulerJumpsAndGoodBadParticles(uploadIterations)		

#=====================
if __name__ == "__main__":
	upload3D = uploadEmanProjectionMatchingRefinementScript()
	upload3D.start()
	upload3D.close()

