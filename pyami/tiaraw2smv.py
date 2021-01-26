#!/usr/bin/env python
'''
This is for converting Ceta TIA raw output to SMV format.
'''
print('''This converts a series of TIA raw output *.bin to smv format''')
input_pattern= input('Enter bin file prefix prior to _001.bin, for example: ')
output_pattern=input('Enter smv file prefix: ')
offset_txt = input('Data offset added to the input values. Default is based on the minimal of all input series unless the resulting offset is larger than 2000): ')
if offset_txt == '':
	offset = None
else:
	offset = int(offset_txt)
gain_txt = input('Camera Gain counts/electron (default 28 for CetaD): ')
if gain_txt == '':
	gain = 28.0
else:
	gain = float(gain)
header_dict = {'BEAMLINE': 'CETAD_TUI', 'GAIN':gain}

#-----------------------
from pyami import tiaraw, numsmv

import os
import sys
import numpy

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

def getInName(digits, input_pattern, i):
	if digits==3:
		in_name='%s_%03d.bin' % (input_pattern, i+1)
	elif digits==2:
		in_name='%s_%02d.bin' % (input_pattern, i+1)
	return in_name

if offset is None:
	# get offset and median of mins
	mins = []
	for i in range(total):
		in_name = getInName(digits, input_pattern, i)
		out_name='%s_%03d.img' % (output_pattern, i+1)
		data = tiaraw.read(in_name)
		mins.append(data.min())
	minarray = numpy.array(mins)
	min_of_mins=minarray.min()
	median_of_mins = numpy.median(minarray)
	offset = -min_of_mins
	pedestal = -min_of_mins+median_of_mins
	print("calculated offset = %.1f" % (offset+0.0))
	print("estimated pedestal median of minimal values = %.1f" % (pedestal))
	header_dict['IMAGE_PEDESTAL'] = pedestal

for i in range(total):
	in_name = getInName(digits, input_pattern, i)
	out_name='%s_%03d.img' % (output_pattern, i+1)
	data = tiaraw.read(in_name)
	numsmv.write(data,out_name, offset=offset, header_updates=header_dict)
