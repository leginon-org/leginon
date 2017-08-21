#!/usr/bin/env python

# a simple protomo2 control script for reconstructing a volume after alignment refinement

import protomo
import optparse
import sys
import glob
import os

def parseOptions():
	parser=optparse.OptionParser()
	parser.add_option('--param', dest='param', help= 'Param file')
	parser.add_option('--map', dest='map', help= 'Output map name, e.g. series1.img')

	options, args=parser.parse_args()
	
	if len(args) != 0 or len(sys.argv) == 1:
		parser.print_help()
		sys.exit()
	
	return options


if __name__=='__main__':

	options=parseOptions()
	
	param=protomo.param(options.param)
	series=protomo.series(param)
	series.mapfile(options.map)
	
	print "Done!"
