#!/usr/bin/env python

import sys
import numpy
import pylab
import optparse

def parseOptions():
	parser=optparse.OptionParser()
	parser.add_option('--corr', dest='corr', help='corr file to plot')
	
	options, args=parser.parse_args()
	
	if len(args) != 0 or len(sys.argv) == 1:
		parser.print_help()
		sys.exit()
	
	return options

if __name__=="__main__":
	options=parseOptions()
		

	corrfile=options.corr

	f=open(corrfile,'r')
	lines=f.readlines()
	f.close()

	rot=[]
	cofx=[]
	cofy=[]
	coa=[]
	for line in lines:
		words=line.split()
		rot.append(float(words[1]))
		cofx.append(float(words[2]))
		cofy.append(float(words[3]))
		coa.append(float(words[4]))

#	pylab.figure(figsize=(10,14))
	pylab.figure()
	pylab.subplot(221)
	pylab.plot(rot)
	pylab.title("rot")
	
	pylab.subplot(222)	
	pylab.plot(cofx)
	pylab.title('cofx')
	
	pylab.subplot(223)
	pylab.plot(cofy)
	pylab.title('cofy')
	
	pylab.subplot(224)
	pylab.plot(coa)
	pylab.title('coa')
	
	pylab.show()
	print "Done!"
