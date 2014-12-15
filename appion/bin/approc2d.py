#!/usr/bin/env python
from pyami import imagefun
from pyami import mrc
from pyami import imagic
import argparse #apparently optparse is being deprecated. Barf!
import os
import sys
import glob

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
		parser.add_argument( '--lp', dest='lp', type=float, metavar='FLOAT', help='Low pass filter to provided resolution. In Angstroms. ')
		parser.add_argument( '--hp', dest='hp', type=float, metavar='FLOAT', help='High pass filter to provided resolution. In Angstroms. ')
		parser.add_argument( '--apix', dest='apix', type=float, metavar='FLOAT', help='High pass filter to provided resolution. In Angstroms. ')
		parser.add_argument("--invert", dest="invert", help="Invert contrast", action='store_true', default=False )
		parser.add_argument('--first', dest='first', type=int,metavar='FLOAT', help="Operate on particles starting from the given INT. Note: particle numbers in stacks start with 0")
		parser.add_argument('--last', dest='first', type=int, metavar='FLOAT', help="Operate on particles starting from the given INT. Note: particle numbers in stacks start with 0")
		self.args=parser.parse_args()
		#print self.args
	
	def start(self):
		#Determine extension
		instacktype=os.path.splitext(self.args.in_stack)[-1]
		print instacktype
		print "Parsing header"
		if instacktype=='.mrc':
			header=mrc.readHeaderFromFile(self.args.in_stack)
		elif instacktype=='.hed' or instacktype=='.img':
			header=imagic.readImagicHeader(self.args.in_stack)
			
		print header
		nptcls=header['nz']
		print "Nptcls = ", header['nz']
		
		### First steps
		fdat=open(self.args.in_stack,'r')
		fout=open(self.args.out_stack,'wb')
		headerbytes=mrc.makeHeaderData(header)
		fout.write(headerbytes)
		
		for n in range(nptcls):
			ptcl=mrc.readDataFromFile(fdat,header,n)
			if self.args.invert is True:
				ptcl=ptcl*-1
			mrc.appendArray(ptcl,fout)
		fout.close()
		
		### Last steps
		
	
	def close(self):
		print "Done!"

if __name__ == '__main__':
	approc2d = ApProc2d()
	approc2d.start()
	approc2d.close()
	
