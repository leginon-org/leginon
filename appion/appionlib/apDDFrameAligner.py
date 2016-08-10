#!/usr/bin/env python
from appionlib import apDisplay
import socket
import os
import subprocess

class DDFrameAligner(object):
	def __init__(self):
		self.executable = 'echo'
		self.alignparams = {}
		self.hostname = socket.gethostname().split('.')[0]

	def getExecutableName(self):
		return self.executable

	def setRunDir(self,rundir):
		'''
		Tempdir is best the same directory as the CPU gain dark correction
		if done separately.
		'''
		self.tempdir = rundir
		self.gpuid = 0
		self.hostname = 'localhost'

	def setGainDarkCmd(self,cmd):
		'''
		If the program runs its own gain/dark correction, put in here the option
		string to add to the main command.
		'''
		self.gain_dark_cmd

	def isGainDarkCorrected(self):
		'''
		Determined by getGainDarkCmd or overwritten by subclass to be True or False.
		'''
		return bool(self.gain_dark_cmd)

	def setInputFrameStackPath(self, filepath):
		'''
		The absolute path of the frame stack used as the input.
		This could be gain/dark/defect corrected if self.isGainDarkCorrected
		is True
		'''
		self.framestackpath = filepath

	def setAlignedSumPath(self,**kwargs):
		if 'gpuid' in kwargs.keys():
			self.setGpuId(kwargs['gpuid'])
		if 'hostname' in kwargs.keys():
			self.setHostname(kwargs['hostname'])
		# actual setting
		# The alignment is done in tempdir (a local directory to reduce network traffic)
		# include both hostname and gpu to identify the temp output
		self.aligned_sumpath = 'temp%s.%d_sum.mrc' % (self.hostname,self.gpuid)
		self.aligned_stackpath = 'temp%s.%d_aligned_st.mrc' % (self.hostname,self.gpuid)
		self.log = self.framestackpath[:-4]+'_Log.txt'

	def makeFrameAlignmentCommand(self):
		cmd = ' '.join([self.executable, self.framestackpath, self.aligned_sumpath])
		cmd += self.joinFrameAlignOptions(glue='-')
		cmd += ' > '+self.log
		return cmd

	def alignFrameStack(self):
		'''
		Running alignment of frame
		'''
		os.chdir(self.tempdir)

		# Construct the command line with defaults
		cmd = self.makeFrameAlignmentCommand()

		apDisplay.printMsg('Running: %s'% cmd)
		self.proc = subprocess.Popen(cmd, shell=True)
		self.proc.wait()

	def getValidAlignOptionMappings(self):
		'''
		get key-value pairs for options.  Keys are the keys in Appion params,
		Values are the keys in the program.
		'''
		return {'gpuid':'gpuid','bin':'bin'}

	def setFrameAlignOptions(self,params):
		parammaps = self.getValidAlignOptionMappings()
		for goodkey in parammaps.keys():
			if goodkey in params.keys():
				self.alignparams[parammaps[goodkey]] = params[goodkey]

	def joinFrameAlignOptions(self,glue='-'):
		cmd = ''
		for key in self.alignparams.keys():
			cmd += ' %s%s %s' % (glue,key,str(self.alignparams[key]))
		return cmd

class MotionCorr1(DDFrameAligner):
	def __init__(self):
		self.executable = 'dosefgpu_driftcorr'

	def makeFrameAlignmentCommand(self):
		cmd = '%s %s -fcs %s -dsp 0' % (self.executable, self.tempframestackpath,temp_aligned_sumpath)
		#cmd = '/emg/sw/script/motioncorr-master/bin/'+cmd
		self.modifyNumRunningAverageFrames()
		# Options
		cmd += self.joinFrameAlignOptions()

		# binning
		cmd += ' -bin %d' % (self.getNewBinning())
		# gain dark references
		cmd += gain_dark_cmd
		is_sum_with_dosefgpu =  self.isSumSubStackWithDosefgpu()
		if is_sum_with_dosefgpu:
			cmd += ' -nss %d -nes %d' % (min(self.sumframelist),max(self.sumframelist))
		else:
			# minimal sum since it needs to be redone by numpy
			cmd += ' -nss %d -nes %d' % (0,1)
		if self.save_aligned_stack:
			cmd += ' -ssc 1 -fct %s' % (temp_aligned_stackpath)
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
		
if __name__ == '__main__':
	filepath = '/Users/acheng/testdata/frames/16aug10a/rawdata/16aug10a_00001en.frames.mrc'
	params = {'bin':2,'any':1}
	makeStack = DDFrameAligner()
	makeStack.setRunDir('.')
	makeStack.setInputFrameStackPath(filepath)
	makeStack.setFrameAlignOptions(params)
	makeStack.setAlignedSumPath()
	makeStack.alignFrameStack()
