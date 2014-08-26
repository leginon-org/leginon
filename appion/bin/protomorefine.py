#!/usr/bin/env python

# a simple protomo2 control script

import protomo
import optparse
import sys
import glob
import os

def parseOptions():
	parser=optparse.OptionParser()
	parser.add_option('--iters', dest='iters', type='int', help='number of refinement iterations')
	parser.add_option('--i3t', dest='i3tfile', help='path to i3t file')
	parser.add_option('--param', dest='param', help='path to param file')
	parser.add_option('--tlt', dest='tlt', help='path to tlt file. Only needed for the first iteration')
	parser.add_option('--nomodel', dest='nomodel', action='store_true', default=False, help='do not model the tilt axis.')
	
	
	options, args=parser.parse_args()

	if len(args) != 0 or len(sys.argv) == 1:
		parser.print_help()
		sys.exit()
	
	return options
	
	
if __name__ == "__main__":
	options=parseOptions()
	
	seriesparam=protomo.param(options.param)	
	if options.i3tfile:
		series=protomo.series( seriesparam )
	else:
		seriesgeom=protomo.geom( options.tlt )
		options.i3tfile=options.tlt
		series=protomo.series( seriesparam, seriesgeom )

	seriesname=options.i3tfile.split('.')[0]
	iters=options.iters
	
	#figure out starting number
	start=0
	previters=glob.glob(seriesname+'*.corr')
	if len(previters) > 0:
		previters.sort()
		lastiter=previters[-1]
		start=int(lastiter.split(seriesname)[1].split('.')[0])+1
	
	
	for n in range(iters):
		print "Iteration", n
		series.align()
		basename='%s%02d' % (seriesname,(n+start))
		
		
		if options.nomodel is False:
			corrfile=basename+'.corr'
			series.corr(corrfile)
			series.fit()
		series.update()
	
		#archive results
		tiltfile=basename+'.tlt'
		geom=series.geom()
		geom.write(tiltfile)
	

	print "Done!"
