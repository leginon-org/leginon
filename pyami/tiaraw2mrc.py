#!/usr/bin/env python
'''
This is for converting Ceta TIA raw output to 32-bit float mrc format.
'''
print('''This converts a series of TIA raw output *.bin to mrc format''')
input_pattern= input('Enter bin file prefix prior to _001.bin, for example: ')
output_pattern=input('Enter mrc file prefix: ')

from pyami import tiaraw, mrc

import os
import sys
digits=3
test_filename = '%s_%03d.bin' % (input_pattern, 1)
if not os.path.isfile(test_filename):
	test_filename = '%s_%02d.bin' % (input_pattern, 1)
	if not os.path.isfile(test_filename):
		sys.exit('%s does not exist!' % test_filename)
	digits=2

import glob
filelist = glob.glob('%s_*.bin' % (input_pattern,))
total=len(filelist)

def read(fobj,start,shape,dtype):
		fobj.seek(start)
		datalen = shape[0]*shape[1]
		a = numpy.fromfile(fobj, dtype=dtype, count=datalen)
		a = numpy.reshape(a,shape)
		return a

for i in range(total):
	if digits==3:
		in_name='%s_%03d.bin' % (input_pattern, i+1)
	elif digits==2:
		in_name='%s_%02d.bin' % (input_pattern, i+1)
	out_name='%s_%03d.mrc' % (output_pattern, i+1)
	data = tiaraw.read(in_name)
	mrc.write(data,out_name)

