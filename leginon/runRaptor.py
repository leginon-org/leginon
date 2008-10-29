#!/usr/bin/env python

import subprocess

def run(inputfile, outfile, errfile):
	fout = open(outfile, 'w')
	ferr = open(errfile, 'w')
	args = ['RAPTORsim', inputfile]
	print 'starting subprocess'
	p = subprocess.Popen(args, stdout=fout, stderr=ferr)
	print 'waiting for subprocess'
	ret = p.wait()
	if ret:
		fout.write('RAPTOR failed with code: %d\n' % (ret,))
	fout.close()
	ferr.close()

if __name__ == '__main__':
	import sys
	inputfile = sys.argv[1]
	outfile = sys.argv[2]
	errfile = sys.argv[3]
	run(inputfile, outfile, errfile)
