#!/usr/bin/env python
from pyami import imagefun
from pyami import mrc
from pyami import imagic
from appionlib.apImage import imagefilter
import argparse #apparently optparse is being deprecated. Barf!
import os
import sys
import glob
import copy

#not inheriting Appion base classes because options are unique and stand alone
class ApProc2d ():
	#=====================
	
	def __init__(self):
		"""
		create parameters etc
		"""
		self.setupParserOptions()
	
	def setupParserOptions(self):
		parser=argparse.ArgumentParser()
		
		parser.add_argument( 'in_stack', metavar='STRING', help='Input stack')
		parser.add_argument( 'out_stack', metavar='STRING', help='Output stack')
		parser.add_argument( '--lp', dest='lp', default=None, type=float, metavar='FLOAT', help='Low pass filter to provided resolution. In Angstroms. ')
		parser.add_argument( '--hp', dest='hp', default=None, type=float, metavar='FLOAT', help='High pass filter to provided resolution. In Angstroms. ')
		parser.add_argument( '--apix', dest='apix', default=1.0, type=float, metavar='FLOAT', help='High pass filter to provided resolution. In Angstroms. ')
		parser.add_argument("--invert", dest="invert", help="Invert contrast", action='store_true', default=False )
		parser.add_argument('--first', dest='first', default=0, type=int,metavar='FLOAT', help="Operate on particles starting from the given INT. Note: particle numbers in stacks start with 0")
		parser.add_argument('--last', dest='last', default=0, type=int, metavar='FLOAT', help="Operate on particles starting from the given INT. Note: particle numbers in stacks start with 0")
		parser.add_argument('--no_append', dest='no_append', default=False, action='store_true', help="Overwrite preexisting output stack")
		self.args=parser.parse_args()
		#print self.args
	
	def start(self):
		#Determine extension
		instacktype=os.path.splitext(self.args.in_stack)[-1]
		print instacktype
		print "Parsing header"
		if instacktype=='.mrc':
			inheader=mrc.readHeaderFromFile(self.args.in_stack)
		elif instacktype=='.hed' or instacktype=='.img':
			inheader=imagic.readImagicHeader(self.args.in_stack)
			
		print inheader
		in_nptcls=inheader['nz']
		print "Nptcls = ", inheader['nz']
		
		### First steps
		
		# determine nptcls to add
		if self.args.last is not None:
			add_nptcls=self.args.last-self.args.first+1
		else:
			add_nptcls=in_nptcls-self.args.first

		fdat=open(self.args.in_stack,'rb')
		
		if os.path.exists(self.args.out_stack) and self.args.no_append is False:
			outheader=mrc.readHeaderFromFile(self.args.out_stack)
			out_nptcls=outheader['nz']
			outheader['nz']=out_nptcls+add_nptcls #create header with correct number of particles after processing
			fout=open(self.args.out_stack,'rb+')
		else:
			fout=open(self.args.out_stack,'wb')
			outheader=copy.deepcopy(inheader)
			outheader['nz']=add_nptcls
			out_nptcls=0
		outheaderbytes=mrc.makeHeaderData(outheader)

		fout.write(outheaderbytes)
		
			
		for n in range(self.args.first, self.args.first+add_nptcls):
			ptcl=mrc.readDataFromFile(fdat,inheader,n)
			if self.args.invert is True:
				ptcl=ptcl*-1
			if self.args.lp is not None:
				ptcl=imagefilter.lowPassFilter(ptcl,apix=self.args.apix, radius=self.args.lp)
			if self.args.hp is not None:
				ptcl=imagefilter.highPassFilter2(ptcl, self.args.hp, apix=self.args.apix)
			mrc.appendArray(ptcl,fout)
			out_nptcls+=1
		
		print "Total particles = ", out_nptcls
		fout.close()
		
		### Last steps
		
	
	def close(self):
		print "Done!"

if __name__ == '__main__':
	approc2d = ApProc2d()
	approc2d.start()
	approc2d.close()
	
