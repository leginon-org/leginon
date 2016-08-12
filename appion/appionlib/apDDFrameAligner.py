#!/usr/bin/env python
from appionlib import apDisplay
import socket
import os
import re
import subprocess

class DDFrameAligner(object):
	executable = 'cp'
	def __init__(self):
		self.alignparams = {}
		self.gain_dark_cmd = ''
		self.save_aligned_stack = True
		self.is_use_frame_aligner_sum = True

	def getExecutableName(self):
		return self.executable

	def setGainDarkCmd(self,norm_path,dark_path=None):
		'''
		If the program runs its own gain/dark correction, put in here the option
		string to add to the main command.
		'''
		cmd = ''
		self.gain_dark_cmd = cmd


	def isGainDarkCorrected(self):
		'''
		Determined by getGainDarkCmd or overwritten by subclass to be True or False.
		'''
		return bool(self.gain_dark_cmd)

	def setIsUseFrameAlignerSum(self,value):
		self.is_use_frame_aligner_sum = value

	def setSaveAlignedStack(self, value):
		self.save_aligned_stack

	def setInputFrameStackPath(self, filepath):
		'''
		The absolute path of the frame stack used as the input.
		This could be gain/dark/defect corrected if self.isGainDarkCorrected
		is True
		'''
		self.framestackpath = filepath

	def setAlignedSumPath(self, filepath):
		self.aligned_sumpath = filepath

	def setAlignedStackPath(self, filepath):
		self.aligned_stackpath = filepath

	def setLogPath(self, filepath):
		self.logpath = filepath

	def setAlignedSumFrameList(self,framelist):
		self.sumframelist = framelist
		
	def getAlignedSumFrameList(self):
		return self.sumframelist
		
	def makeFrameAlignmentCommand(self):
		cmd = ' '.join([self.executable, self.framestackpath, self.aligned_sumpath])
		cmd += self.joinFrameAlignOptions(glue='-')
		cmd += ' > '+self.logpath
		return cmd

	def alignFrameStack(self):
		'''
		Running alignment of frame
		'''
		# Construct the command line with defaults
		cmd = self.makeFrameAlignmentCommand()

		# run as subprocess
		apDisplay.printMsg('Running: %s'% cmd)
		self.proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
		self.proc.wait()

		# write log file
		output = self.proc.stdout.read()
#		f = open(self.framestackpath[:-4]+'_Log.motioncorr2.txt', "r")
#		lines = f.readlines()
#		output = ""
#		for l in lines:
#			output += l
		self.writeLogFile(output)

	def getValidAlignOptionMappings(self):
		'''
		get key-value pairs for options.  Keys are the keys in Appion params,
		Values are the keys in the program.
		'''
		return {'fakeparam':'option'}

	def setFrameAlignOptions(self,params):
		parammaps = self.getValidAlignOptionMappings()
		for goodkey in parammaps.keys():
			if goodkey in params.keys():
#				print params, params[goodkey]
				self.alignparams[parammaps[goodkey]] = params[goodkey]

	def getFrameAlignOption(self,key):
		return self.alignparams[key]

	def joinFrameAlignOptions(self,glue='-'):
		cmd = ''
		for key in self.alignparams.keys():
			cmd += ' %s%s %s' % (glue,key,str(self.alignparams[key]))
		return cmd

#	def getNewNumRunningAverageFrames(self):
#		return self.numRunningAverageFrames

	### modifying parameters

#	def setBinning(self,bin):
#		''' Camera binning of the stack '''
#		self.stack_binning = bin

#	def getBinning(self):
#		return self.stack_binning

#	def setBfactor(self,bft):
#		''' bfactor to apply to frames prior to alignment '''
#		self.bft = bft

#	def getBfactor(self):
#		return self.bft

	def writeLogFile(self, outbuffer):
		f = open("tmp.log", "w")
		f.write(outbuffer)
		f.close()

class MotionCorr1(DDFrameAligner):
	executable = '/Users/acheng/dosefgpu_driftcorr'
	def __init__(self):
		super(MotionCorr1,self).__init__()
		self.gain_dark_cmd = ''

	def setGainDarkCmd(self,norm_path,dark_path=None):
		'''
		If the program runs its own gain/dark correction, put in here the option
		string to add to the main command.
		'''
		cmd = ''
		if dark_path:
			cmd += " -fdr %s" % dark_path
		if norm_path:
			cmd += " -fgr %s" % norm_path
		gain_dark_cmd = cmd
		apDisplay.printMsg('Gain Dark Command Option: %s' % cmd)

	def makeFrameAlignmentCommand(self):
		cmd = '%s %s -fcs %s -dsp 0' % (self.executable, self.framestackpath, self.aligned_sumpath)
		self.modifyNumRunningAverageFrames()
		# Options
		cmd += self.joinFrameAlignOptions()

		## binning
		#cmd += ' -bin %d' % (self.getNewBinning())
		# gain dark references
		cmd += self.gain_dark_cmd
		if self.is_use_frame_aligner_sum:
			cmd += ' -nss %d -nes %d' % (min(self.sumframelist),max(self.sumframelist))
		else:
			# minimal sum since it needs to be redone by numpy
			cmd += ' -nss %d -nes %d' % (0,1)
		if self.save_aligned_stack:
			cmd += ' -ssc 1 -fct %s' % (self.aligned_stackpath)
		return cmd

	def getValidAlignOptionMappings(self):
		return {'gpuid':'gpu', 'nrw':'nrw', 'flp':'flp', 'bin':'bin' }

	def modifyNumRunningAverageFrames(self):
		'''
		modification to make Purdue motioncorr compatible with the motioncorr 1
		'''
		if 'nrw' in self.alignparams.keys():
			if self.alignparams['nrw'] <= 1:
				del self.alignparams['nrw']
		
	def modifyFlipAlongYAxis(self):
		'''
		modification to make Purdue motioncorr compatible with the motioncorr 1
		'''
		if 'flp' in self.alignparams.keys():
			if self.getNewFlipAlongYAxis() == 0:
				del self.alignparams['nrw']
			
	def setAlignedSumFrameList(self,framelist):
		self.sumframelist = framelist
		
	def getAlignedSumFrameList(self):
		return self.sumframelist

	def isSumSubStackWithDosefgpu(self):
		'''
		This funciton decides whether dosefgpu_driftcorr will be used for
		summing up ddstack.  Dosefgpu_driftcorr can only handle
		consecutive frame sum.
		'''
		framelist = self.getAlignedSumFrameList()
		# To save time, only proceed if necessary
		if framelist and framelist == range(min(framelist),min(framelist)+len(framelist)):
			self.save_aligned_stack = self.keep_stack
			return True
		# aligned_stack has to be saved to use Numpy to sum substack
		self.save_aligned_stack=True
		return False

	def writeLogFile(self, outbuffer):
		pass

class MotionCorr2_UCSF(DDFrameAligner):
	def __init__(self):
		self.executable = 'motioncorr2_ucsf'
		DDFrameAligner.__init__(self)

	def makeFrameAlignmentCommand(self, gain_dark_cmd=''):
		'''
		David Agard lab's gpu program for aligning frames using all defaults
		Dark reference select is currently unavailable, therefore this version only works for images acquired from a K2 camera in counting mode
		'''
		os.chdir(self.tempdir)
		# include both hostname and gpu to identify the temp output
		temp_aligned_sumpath = 'temp%s.%d_sum.mrc' % (self.hostname,self.gpuid)
		temp_aligned_stackpath = 'temp%s.%d_aligned_st.mrc' % (self.hostname,self.gpuid)
		print self.__dict__.keys()

		
		# Construct the command line with defaults

		cmd = 'motioncorr2_ucsf -InMrc %s -OutMrc %s' % (self.framestackpath, temp_aligned_sumpath)

		print self.alignparams
		
		# binning
		if self.alignparams['FtBin'] > 1:
#			self.setBinning(self.alignparams['FtBin'])
			cmd += ' -FtBin %d ' % self.stack_binning

		# bfactor
		if self.alignparams['Bft'] > 0:
#			self.setBfactor(self.alignparams['Bft']) 
			cmd += ' -Bft %d ' % self.bft

		# frame truncation
		if self.alignparams['Throw'] > 0:
			cmd += ' -Throw %d' % self.alignparams['Throw']
		if self.alignparams['Trunc'] > 0:
			cmd += ' -Trunc %d' % self.alignparams['Trunc']

		# convergence parameters
		if self.alignparams['Iter'] > 0:
			cmd += ' -Iter %d' % self.alignparams['Iter']
		if self.alignparams['Tol']:
			cmd += ' -Tol %.3f' % self.alignparams['Tol']

		# patches
		patchx = int(self.alignparams['Patch'].split(",")[0])
		patchy = int(self.alignparams['Patch'].split(",")[1])
		if patchx > 0 and patchy > 0:
			cmd += ' -Patch %s %s ' % (patchx, patchy)
		elif patchx > 0 and patchy == 0:
			cmd += ' -Patch %s %s ' % (patchx, 0)
		elif patchx == 0 and patchy > 0:
			cmd += ' -Patch %s %s ' % (0, patchy)
		else: 
			pass

		# masking
		maskcentx = int(self.alignparams['MaskCent'].split(",")[0])
		maskcenty = int(self.alignparams['MaskCent'].split(",")[1])
		if maskcentx > 0 and maskcenty > 0:
			cmd += ' -MaskCent %s %s ' % (maskcentx, maskcenty)
		elif maskcentx > 0 and maskcenty == 0:
			cmd += ' -MaskCent %s %s ' % (maskcentx, 0)
		elif maskcentx == 0 and maskcenty > 0:
			cmd += ' -MaskCent %s %s ' % (0, maskcenty)
		else: 
			pass

		masksizex = int(self.alignparams['MaskSize'].split(",")[0])
		masksizey = int(self.alignparams['MaskSize'].split(",")[1])
		if masksizex > 0 and masksizey > 0:
			cmd += ' -MaskSize %s %s ' % (masksizex, masksizey)
		elif masksizex > 0 and masksizey == 0:
			cmd += ' -MaskSize %s %s ' % (masksizex, 0)
		elif masksizex == 0 and masksizey > 0:
			cmd += ' -MaskSize %s %s ' % (0, masksizey)
		else: 
			pass

		# exposure filtering
		if self.alignparams['doseweight'] is True:
			cmd += ' -PixSize %.3f ' % (self.alignparams['PixSize'])
			cmd += ' -kV %d ' % (self.alignparams['kV'])
			cmd += ' -FmDose %.3f ' % (self.alignparams['FmDose'])
		
		
		# gain dark references
		cmd += gain_dark_cmd

		# GPU ID
		cmd += ' Gpu %d' % self.gpuid

		return cmd

		"""

		if os.path.isfile(temp_aligned_sumpath):
			# successful alignment
			if self.tempdir != self.rundir:
				if os.path.isfile(temp_log):
					shutil.move(temp_log,self.framestackpath[:-4]+'_Log.txt')
					apDisplay.printMsg('Copying result for %s from %s to %s' % (self.image['filename'],self.tempdir,self.rundir))
			if not is_sum_with_dosefgpu:
				self.sumSubStackWithNumpy(temp_aligned_stackpath,temp_aligned_sumpath)
			shutil.move(temp_aligned_sumpath,self.aligned_sumpath)
			if self.keep_stack:
				shutil.move(temp_aligned_stackpath,self.aligned_stackpath)
			else:
				apFile.removeFile(temp_aligned_stackpath)
				apFile.removeFile(self.aligned_stackpath)
		else:
			if self.tempdir != self.rundir:
				# Move the Log to permanent location for future inspection
				if os.path.isfile(temp_log):
					shutil.move(self.tempframestackpath[:-4]+'_Log.txt',self.framestackpath[:-4]+'_Log.txt')
			apDisplay.printWarning('dosefgpu_driftcorr FAILED: \n%s not created.' % os.path.basename(temp_aligned_sumpath))
			#apDisplay.printError('If this happens consistently on an image, hide it in myamiweb viewer and continue with others' )
		os.chdir(self.rundir)

		"""

	def getValidAlignOptionMappings(self):
		return {
			'gpuid':'Gpu', 
			'nrw':'Group', 
			'flp':'flp', 
			'bin':'FtBin', 
			"bft":"Bft",
			"apix":"PixSize",
			"Iter":"Iter",
			"Patch":"Patch",
			"MaskCent":"MaskCent",
			"MaskSize":"MaskSize",
			"kV":"kV",
			"FmDose":"FmDose",
			"Tol":"Tol",
			"kv":"kV",
			"Trunc":"Trunc",
			"Throw":"Throw",
			"Crop":"Crop",
			"FmRef":"FmRef",
			"doseweight":"doseweight",
			"totalframes":"totalframes"
			}

	def modifyFlipAlongYAxis(self):
		'''
		modification to make Purdue motioncorr compatible with the motioncorr 1
		'''
		if 'flp' in self.alignparams.keys():
			if self.getNewFlipAlongYAxis() == 0:
				del self.alignparams['nrw']
			
	def setAlignedSumFrameList(self,framelist):
		self.sumframelist = framelist
		
	def getAlignedSumFrameList(self):
		return self.sumframelist
	
	def writeLogFile(self, outbuffer):
		''' 
		takes output log buffer from running frame aligner 
		will write motioncorr2 log file and standard log file that is readable by appion image viewer (motioncorr1 format)
		'''

		### motioncorr2 format
		log2 = self.framestackpath[:-4]+'_Log.motioncorr2.txt'
		f = open(log2, "w")
		f.write(outbuffer)
		f.close()

		### this is unnecessary, need to figure out how to convert outbuffer from subprocess PIPE to readable format
		f = open(log2, "r")
		outbuffer = f.readlines()
		f.close()

		### parse motioncorr2 output
		shifts = []
		for l in outbuffer: 
			m = re.match("...... Frame", l)
			if m:
				shx = float(l[26:].split()[0])
				shy = float(l[26:].split()[1])
				shifts.append([shx, shy])

		### convert motioncorr2 output to motioncorr1 format
		shifts_adjusted = []
		midval = len(shifts)/2
		midshx = shifts[midval][0]
		midshy = shifts[midval][1]
		for l in shifts:
			shxa = l[0] - midshx
			shya = l[0] - midshy
			shifts_adjusted.append([shxa, shya])

		### motioncorr1 format, needs conversion from motioncorr2 format
		log = self.framestackpath[:-4]+'_Log.txt'
                f = open(log,"w")
		f.write("Sum Frame #%.3d - #%.3d (Reference Frame #%.3d):\n" % (0, self.alignparams['totalframes'], self.alignparams['totalframes']/2))
		for i in range(self.alignparams['totalframes']):
	                f.write("......Add Frame #%.3d with xy shift: %.5f %.5f\n" % (i, shifts_adjusted[i][0], shifts_adjusted[i][1]))
                f.close()
		


		
if __name__ == '__main__':
	filepath = '/Users/acheng/testdata/frames/16aug10a/rawdata/16aug10a_00001en.frames.mrc'
	params = {'bin':2,'any':1}
	makeStack = DDFrameAligner()
	makeStack.setRunDir('.')
	makeStack.setInputFrameStackPath(filepath)
	makeStack.setFrameAlignOptions(params)
	makeStack.setAlignedSumPath()
	makeStack.alignFrameStack()
