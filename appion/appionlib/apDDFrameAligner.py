#!/usr/bin/env python
from appionlib import apDisplay
import socket
import os
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

		apDisplay.printMsg('Running: %s'% cmd)
		self.proc = subprocess.Popen(cmd, shell=True)
		self.proc.wait()

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
				self.alignparams[parammaps[goodkey]] = params[goodkey]

	def getFrameAlignOption(self,key):
		return self.alignparams[key]

	def joinFrameAlignOptions(self,glue='-'):
		cmd = ''
		for key in self.alignparams.keys():
			cmd += ' %s%s %s' % (glue,key,str(self.alignparams[key]))
		return cmd

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
			
if __name__ == '__main__':
	filepath = '/Users/acheng/testdata/frames/16aug10a/rawdata/16aug10a_00001en.frames.mrc'
	params = {'bin':2,'any':1}
	makeStack = DDFrameAligner()
	makeStack.setRunDir('.')
	makeStack.setInputFrameStackPath(filepath)
	makeStack.setFrameAlignOptions(params)
	makeStack.setAlignedSumPath()
	makeStack.alignFrameStack()
