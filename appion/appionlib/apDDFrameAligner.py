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

	def setInputNumberOfFrames(self,nframes):
		self.nframes = nframes

	def getInputNumberOfFrames(self):
		return self.nframes

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
		(stdoutdata, stderrdata) = self.proc.communicate()

		# write log file
		output = stdoutdata
		self.writeLogFile(output)
		# stream stderrdata even though it is likely empty due to piping to stdout
		print stderrdata

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

	def writeLogFile(self, outbuffer):
		f = open("tmp.log", "w")
		f.write(outbuffer)
		f.close()

class MotionCorr1(DDFrameAligner):
	executable = 'dosefgpu_driftcorr'
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
		self.gain_dark_cmd = cmd
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
		return {'gpuid':'gpu', 'bin':'bin' }

	def writeLogFile(self, outbuffer):
		'''
		MotionCorr1 has its own log file. This just stream to appionlog
		'''
		print outbuffer
		apDisplay.printMsg('Real alignment log written to %s' % self.logpath)

	def setGPUid(self,gpuid):
		p = {'gpuid':gpuid}
		self.setFrameAlignOptions(p)

class MotionCorr_Purdue(MotionCorr1):
	executable = 'dosefgpu_driftcorr'
	def getValidAlignOptionMappings(self):
		opts = super(MotionCorr_Purdue,self).getValidAlignOptionMappings()
		opts.update({'nrw':'nrw', 'flp':'flp','bft':'bft' })
		return opts

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
			
class MotionCor2_UCSF(DDFrameAligner):
	def __init__(self):
		self.executable = 'motioncor2'
		DDFrameAligner.__init__(self)

	def setKV(self, kv):
		self.alignparams['kV'] = kv

	def setTotalFrames(self, totalframes):
		self.alignparams['totalframes'] = totalframes

	def setTotalDose(self, totaldose):
		self.alignparams['totaldose'] = totaldose

	def setGainYFlip(self, bool_value):
		self.alignparams['FlipGain'] = int(bool_value)

	def setGainRotate(self, int_value):
		self.alignparams['RotGain'] = int_value

	def getGainModification(self):
		return self.alignparams['FlipGain'], self.alignparams['RotGain']

	def setGainDarkCmd(self,norm_path,dark_path=None):
		'''
		If the program runs its own gain/dark correction, put in here the option
		string to add to the main command.
		'''
		cmd = ''
		if dark_path:
			apDisplay.printWarning('MotionCor2 does not handle dark reference. Assumes zero')
		if norm_path:
			cmd += " -Gain %s" % norm_path
		self.gain_dark_cmd = cmd
		apDisplay.printMsg('Gain Dark Command Option: %s' % cmd)

	def makeFrameAlignmentCommand(self):
		'''
		David Agard lab's gpu program for aligning frames using all defaults
		Dark reference select is currently unavailable, therefore this version only works for images acquired from a K2 camera in counting mode
		'''

#		print self.alignparams
#		print self.__dict__.keys()

		# Construct the command line with defaults

		cmd = '%s -InMrc %s -OutMrc %s' % (self.executable, self.framestackpath, self.aligned_sumpath)

		# binning
		if self.alignparams['FtBin'] > 1:
			cmd += ' -FtBin %d ' % self.alignparams['FtBin']

		# bfactor
		if self.alignparams['bft'] > 0:
			cmd += ' -Bft %d ' % self.alignparams['bft']

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
		patchx = self.alignparams['Patchcols']
		patchy = self.alignparams['Patchrows']
		if patchx > 0 and patchy > 0:
			cmd += ' -Patch %d %d ' % (patchx, patchy)
		elif patchx > 0 and patchy == 0:
			cmd += ' -Patch %d %d ' % (patchx, 0)
		elif patchx == 0 and patchy > 0:
			cmd += ' -Patch %d %d ' % (0, patchy)
		else: 
			pass

		# grouping
		if self.alignparams['Group']:
			cmd += ' -Group %d' % self.alignparams['Group']

		# masking
		maskcentx = self.alignparams['MaskCentcol']
		maskcenty = self.alignparams['MaskCentrow']
		if maskcentx > 0 and maskcenty > 0:
			cmd += ' -MaskCent %d %d ' % (maskcentx, maskcenty)
		elif maskcentx > 0 and maskcenty == 0:
			cmd += ' -MaskCent %d %d ' % (maskcentx, 0)
		elif maskcentx == 0 and maskcenty > 0:
			cmd += ' -MaskCent %d %d ' % (0, maskcenty)
		else: 
			pass

		masksizex = self.alignparams['MaskSizecols']
		masksizey = self.alignparams['MaskSizerows']
		if masksizex > 0 and masksizey > 0:
			cmd += ' -MaskSize %.3f %.3f ' % (masksizex, masksizey)
		elif masksizex > 0 and masksizey == 0:
			cmd += ' -MaskSize %.3f %.3f ' % (masksizex, 0)
		elif masksizex == 0 and masksizey > 0:
			cmd += ' -MaskSize %.3f %.3f ' % (0, masksizey)
		else: 
			pass

		# exposure filtering
		if self.alignparams['doseweight'] is True and self.alignparams['totaldose']:
			self.alignparams['FmDose'] = self.alignparams['totaldose'] / self.alignparams['totalframes']
			cmd += ' -PixSize %.3f ' % (self.alignparams['PixSize'])
			cmd += ' -kV %d ' % (self.alignparams['kV'])
			cmd += ' -FmDose %.3f ' % (self.alignparams['FmDose'])
		
		# serial 1, defaulted
#		cmd += ' Serial 1'
		
		# gain dark references
		cmd += self.gain_dark_cmd

		# gain gemetry modification
		cmd += ' -FlipGain %d ' % self.alignparams['FlipGain']
		cmd += ' -RotGain %d ' % self.alignparams['RotGain']

		# GPU ID
		cmd += ' -Gpu %s' % self.alignparams['Gpu'].replace(","," ")

		return cmd

	def getValidAlignOptionMappings(self):
		return {
			'gpuids':'Gpu', 
			'nrw':'Group', 
			'flp':'flp', 
			'bin':'FtBin', 
			"Bft":"bft",
			"apix":"PixSize",
			"Iter":"Iter",
			"Patchrows":"Patchrows",
			"Patchcols":"Patchcols",
			"MaskCentrow":"MaskCentrow",
			"MaskCentcol":"MaskCentcol",
			"MaskSizerows":"MaskSizerows",
			"MaskSizecols":"MaskSizecols",
			"kV":"kV",
			"Tol":"Tol",
			"kv":"kV",
			"startframe":"Throw",
			"Crop":"Crop",
			"FmRef":"FmRef",
			"doseweight":"doseweight",
			"totalframes":"totalframes"
			}

#	def modifyFlipAlongYAxis(self):
#		'''
#		modification to make Purdue motioncorr compatible with the motioncorr 1
#		'''
#		if 'flp' in self.alignparams.keys():
#			if self.getNewFlipAlongYAxis() == 0:
#				del self.alignparams['nrw']
			
	def setAlignedSumFrameList(self,framelist):
		self.sumframelist = framelist
		total_frames = self.getInputNumberOfFrames()
		self.alignparams['Trunc'] = total_frames - self.sumframelist[-1] - 1
		
	def getAlignedSumFrameList(self):
		return self.sumframelist
	
	def writeLogFile(self, outbuffer):
		''' 
		takes output log buffer from running frame aligner 
		will write motioncor2 log file and standard log file that is readable by appion image viewer (motioncorr1 format)
		'''

		### motioncor2 format
		log2 = self.framestackpath[:-4]+'_Log.motioncor2.txt'
		f = open(log2, "w")
		f.write(outbuffer)
		f.close()

		### this is unnecessary, need to figure out how to convert outbuffer from subprocess PIPE to readable format
		f = open(log2, "r")
			
		outbuffer = f.readlines()
		f.close()

		### parse motioncor2 output
		temp = []
		found = False
		for line in outbuffer:
			if "Full-frame alignment shift" in line or found:
				temp.append(line)
				found = True
		shifts = []
		
		for l in temp: 
			m = re.match("...... Frame", l)
			if m:
				shx = float(l.split()[-2])
				shy = float(l.split()[-1])
				shifts.append([shx, shy])

		### convert motioncorr2 output to motioncorr1 format
		binning = 1.0
		if 'FtBin' in self.alignparams.keys():
			binning = self.alignparams['FtBin']
		shifts_adjusted = []
		midval = len(shifts)/2
		midshx = shifts[midval][0]
		midshy = shifts[midval][1]
		for l in shifts:
			# convert to the convention used in motioncorr
			# so that shift is in pixels of the aligned image.
			shxa = -(l[0] - midshx) / binning
			shya = -(l[1] - midshy) / binning
			shifts_adjusted.append([shxa, shya])

		### motioncorr1 format, needs conversion from motioncorr2 format
		log = self.framestackpath[:-4]+'_Log.txt'
                f = open(log,"w")
		f.write("Sum Frame #%.3d - #%.3d (Reference Frame #%.3d):\n" % (0, self.alignparams['totalframes'], self.alignparams['totalframes']/2))
		for i in range(self.alignparams['totalframes']-self.alignparams['Throw']-self.alignparams['Trunc']):
	                f.write("......Add Frame #%.3d with xy shift: %.5f %.5f\n" % (i+self.alignparams['Throw'], shifts_adjusted[i][0], shifts_adjusted[i][1]))
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
