#!/usr/bin/env python
import os

from appionlib import apMatlab
from appionlib import apParam
from appionlib import apDisplay

class KSVDdenoise(object):
	def __init__(self,rundir):
		self.rundir = rundir
		self.ksvd_param_line = None
		self.stack_param_line = None
		self.matlabpaths = []
		if os.environ.has_key('MATLAB_KSVD_TOOL_PATH') and os.environ.has_key('MATLAB_DENOISE_PATH'):
			self.setHelperPaths(os.environ['MATLAB_KSVD_TOOL_PATH'],os.environ['MATLAB_DENOISE_PATH'])

		apParam.createDirectory(os.path.join(rundir,'results','mrc'))
		apParam.createDirectory(os.path.join(rundir,'results','dict'))

	def setKSVDParams(self,blocksize=8,dictsize=64,sigma=400):
		self.ksvd_param_line = '[ksvdparams] = makeKSVDparams(%d,%d,%d)\n' % (blocksize,dictsize,sigma)
		return 'DictSize%d_BlkSize%d_Sigma%d' % (dictsize,blocksize,sigma)

	def setStackParams(self,window=40,startframe=0,nframe=40,roi=((0,200),(0,200))):
		'''
		convert and set stack parameters for matlab to read
		roi = ((row_start,row_end+1),(col_start,col_end+1)) in python list index range of [row_start:row_end+1]
		'''
		# Matlab matrix first index is 1
		m_startframe = startframe+1
		#Matlab roi is (col_start,row_start,col_end,row_end) starting from 1
		m_roi = (roi[1][0]+1,roi[0][0]+1,roi[1][1],roi[0][1])
		self.stack_param_line = '[stackparams] = makeStackparams(%d,%d,%d,[%d %d %d %d])\n' % (window,m_startframe,nframe,m_roi[0],m_roi[1],m_roi[2],m_roi[3])
		return 'AvgWinLen%d_roi%d_%d_%d_%d' % (window,m_roi[0],m_roi[1],m_roi[2],m_roi[3])

	def setHelperPaths(self,lib_basepath,denoise_srcpath):
		for libname in ('ksvdbox','ompbox','imod'):
			self.matlabpaths.append(os.path.join(lib_basepath,libname))
		self.matlabpaths.append(denoise_srcpath)
		print self.matlabpaths

	def createScriptFile(self,inputdir,input_mrc):
		scriptname = 'denoise.m'
		if self.ksvd_param_line is None:
			apDisplay.Error('Must set KSVD params')
		if self.stack_param_line is None:
			apDisplay.Error('Must set Stack params')
		f = open(scriptname,'w')
		f.write('clc; close all; clear all;\n')
		allpaths =','.join(map((lambda x:"'"+x+"'"),self.matlabpaths))
		f.write('addpath(%s)\n' % allpaths)
		f.write(self.ksvd_param_line)
		f.write(self.stack_param_line)
		f.write("mrcpath = '%s'\n" % inputdir)
		f.write("mrcname = '%s'\n" % input_mrc)
		f.write("savepath = '%s'\n" % os.path.join(self.rundir,'results'))
		runline = '[out D] = KSVDDenoiseMRC(mrcpath,mrcname,savepath,stackparams,ksvdparams);\n'
		f.write(runline)
		f.close()
		return scriptname

	def setupKSVDdenoise(self,frameavg,startframe,nframe,roi):
		if nframe < frameavg + startframe:
			nframe = frameavg + startframe
		apDisplay.printMsg('********************************')
		apDisplay.printMsg('%d frames starting from frame %d will make %d frames.' % (nframe,startframe,nframe-frameavg+1))
		apDisplay.printMsg('Each resulting frame is an average of %d' % (frameavg))
		apDisplay.printMsg('********************************')
		ksvdparamstr = self.setKSVDParams()
		stackparamstr = self.setStackParams(frameavg,startframe,nframe,roi)
		return 'denoised_KSVDSingleFrame_%s_%s' % (ksvdparamstr,stackparamstr)

	def makeDenoisedStack(self,inputdir, input_mrc):
		scriptname = self.createScriptFile(inputdir,input_mrc)
		apMatlab.runMatlabScript(scriptname,xvfb=False)

if __name__=='__main__':
	d = KSVDdenoise('.')
	d.setupKSVDdenoise(5,2,7,((0,0),(200,200)))
	d.makeDenoiseStack('/ami/data15/appion/12jun18b/ddstacks/ddstack1','12jun18b_c_00032gr_00035sq_v01_00003hl_v02_00003ed_st.mrc')
