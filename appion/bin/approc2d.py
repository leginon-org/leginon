#!/usr/bin/env python

import os
import sys
import copy
import glob
from pyami import mrc
from pyami import imagic
from pyami import imagefun
from appionlib import apDisplay
from appionlib import basicScript
from appionlib.apImage import imagefilter

# XXXXX not inheriting Appion base classes because options are unique and stand alone
# basicScript is designed for this

class ApProc2d(basicScript.BasicScript):
	#=====================
	#=====================
	def setupParserOptions(self):
		self.parser.add_argument('--in', dest='infile', metavar='STRING', help='Input stack')
		self.parser.add_argument('--out', dest='outfile', metavar='STRING', help='Output stack')
		self.parser.add_argument('--lp', '--lowpass', dest='lowpass', default=None, type=float, 
			metavar='FLOAT', help='Low pass filter to provided resolution. In Angstroms. ')
		self.parser.add_argument('--hp', '--highpass', dest='highpass', default=None, type=float, 
			metavar='FLOAT', help='High pass filter to provided resolution. In Angstroms. ')
		self.parser.add_argument('--apix', dest='apix', default=1.0, type=float, 
			metavar='FLOAT', help='High pass filter to provided resolution. In Angstroms. ')
		self.parser.add_argument('--bin', dest='bin', default=1, type=int,
			metavar='INT', help="Decimate/bin by a certain factor")
		self.parser.add_argument('--invert', dest='invert', help="Invert contrast", 
			action='store_true', default=False )
		self.parser.add_argument('--first', dest='first', default=0, type=int,
			metavar='INT', help="Operate on particles starting from the given INT. Note: particle numbers in stacks start with 0")
		self.parser.add_argument('--last', dest='last', default=0, type=int, 
			metavar='INT', help="Operate on particles starting from the given INT. Note: particle numbers in stacks start with 0")
		self.parser.add_argument('--no-append', dest='append', default=None, 
			action='store_false', help="Overwrite pre-existing output stack")
		self.parser.add_argument('--append', dest='append', default=None, 
			action='store_true', help="Append to pre-existing output stack")

	#=====================
	#=====================	
	def readFileHeader(self, filename):
		#Determine extension
		if filename.endswith('.mrc'):
			header = mrc.readHeaderFromFile(filename)
		elif filename.endswith('.hed') or filename.endswith('.img'):
			header = imagic.readImagicHeader(filename)
		elif filename.endswith('.spi'):
			### to be implemented
			apDisplay.printError("SPIDER is not implemented yet")
		elif filename.endswith('.hdf'):
			### to be implemented
			apDisplay.printError("HDF is not implemented yet")
		else:
			apDisplay.printError("unknown stack type")
		return header

	#=====================
	#=====================	
	def readFileData(self, filename, header=None):
		"""
		takes any file type and returns a list of 2D arrays
		"""
		#Determine extension
		if filename.endswith('.mrc'):
			data = mrc.mmap(filename)
		elif filename.endswith('.hed') or filename.endswith('.img'):
			data = imagic.read(filename)
		elif filename.endswith('.spi'):
			### to be implemented
			apDisplay.printError("SPIDER is not implemented yet")
		elif filename.endswith('.hdf'):
			### to be implemented
			apDisplay.printError("HDF is not implemented yet")
		else:
			apDisplay.printError("unknown stack type")
		return data

	#=====================
	#=====================
	def checkExistingFile(self, inheader):		
		if not os.path.exists(self.params['outfile']):
			return 0
		### out file exists
		existheader = self.readFileHeader(self.params['outfile'])
		existNumParticles = existheader['nz']
		if self.params['append'] is None:
			if existNumParticles > 1:
				## output file is not a stack, append				
				self.params['append'] = True
			else:
				## output file is not a stack, overwrite
				self.params['append'] = False
		### display message
		if self.params['append'] is False:
			apDisplay.printWarning("Overwriting existing file, %s"%(self.params['outfile'])
			return 0		
		
		apDisplay.printMsg("Appending to existing file, %s"%(self.params['outfile'])
		## dimensions for new particles must be the same as the old
		if inheader['nx'] != existheader['nx'] or inheader['ny'] != existheader['ny']:
			apDisplay.printError("Dims for existing stack (%dx%d) is different from input stack (%dx%d)"
				%(inheader['nx'],inheader['ny'],existheader['nx'],existheader['ny']))
		
		return existNumParticles
		
	#=====================
	#=====================
	def start(self):		
		### Read input file
		inheader = self.readFileHeader(self.params['infile'])
		inputNumParticles = inheader['nz']

		# determine numParticles to add
		if self.params['last'] is None:
			self.params['last'] = inputNumParticles		
		elif self.params['last'] > inputNumParticles:
			apDisplay.printWarning("Last particle requested (%d) is larger than available particles (%d)"
				%(self.params['last'],inputNumParticles))
			self.params['last'] = inputNumParticles
		addNumParticles = self.params['last'] - self.params['first']+1

		### prepare for an existing file
		existNumParticles = self.checkExistingFile(inheader)
		self.totalParticles = existNumParticles + addNumParticles

		### write/append data
		#create header with correct number of particles after processing
		fout=open(self.params['outfile'],'rb+')

		### this should not work, because it reads the header and everything...
		indata = self.readFileData(self.params['infile'])

		outheaderbytes=mrc.makeHeaderData(outheader)
		fout=open(self.params['outfile'],'wb')
		outheader=copy.deepcopy(inheader)
		outheader['nz']=add_numParticles
		out_numParticles=0
		fout.write(outheaderbytes)

		for n in range(self.params['first'], self.params['first'] + addNumParticles):
			particle=mrc.readDataFromFile(fdat,inheader,n)
			if self.params['invert'] is True:
				particle=particle*-1
			if self.params['lowpass'] is not None:
				particle=imagefilter.lowPassFilter(particle,apix=self.params['apix'], radius=self.params['lowpass'])
			if self.params['highpass'] is not None:
				particle=imagefilter.highPassFilter2(particle, self.params['highpass'], apix=self.params['apix'])
			mrc.appendArray(particle,fout)
			out_numParticles+=1

		print "Total particles = ", out_numParticles
		fout.close()

if __name__ == '__main__':
	approc2d = ApProc2d()
	approc2d.start()
	approc2d.close()
