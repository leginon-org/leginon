#!/usr/bin/env python

import sys
import numpy
import pylab
import optparse

def parseOptions():
	parser=optparse.OptionParser()
	parser.add_option('--corr', dest='corr', help='corr file to plot')
	
	#NOTE: should use type='choice' for the following option
	parser.add_option('--plottype', dest='plottype', help='parameter to plot (cofx, cofy, coa, or rot)')

	options, args=parser.parse_args()
	
	if len(args) != 0 or len(sys.argv) == 1:
		parser.print_help()
		sys.exit()
	
	return options

if __name__=="__main__":
	options=parseOptions()
		

	corrfile=options.corr
	param=options.plottype

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

	if param=='rot':
		pylab.plot(rot)
	elif param=='cofx':
		pylab.plot(cofx)
	elif param=='cofy':
		pylab.plot(cofy)
	elif param=='coa':
		pylab.plot(coa)
	else:
		print "Please enter rot, cofx, cofy, or coa"

	pylab.show()
	print "Done!"
