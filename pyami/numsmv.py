#!/usr/bin/env python
import numpy

'''
Write smv format image files given the numpy array.
smv format is described in
https://strucbio.biologie.uni-konstanz.de/ccp4wiki/index.php/SMV_file_format

This only modify the size1 and size2 from the standard header.
'''

def getHeaderText(shape):
	# standard header must be 512 bytes
	text='{\nHEADER_BYTES=  512;\nBEAM_CENTER_X=0;\nBEAM_CENTER_Y=0;\nBIN=1x1;\nBYTE_ORDER=little_endian;\nDATE=Thu Jan  1 00:00:00 1970;\nDETECTOR_SN=unknown;\nDIM=2;\nDISTANCE= 850;\nOSC_RANGE=0.868;\nOSC_START=nan;\nPHI=nan;\nSIZE1=2048;\nSIZE2=2048;\nIMAGE_PEDESTAL=0;\nPIXEL_SIZE=28;\nTIME=nan;\nWAVELENGTH=0.025;\nTWOTHETA=0;\nTYPE=unsigned_short;\n}\n                                                                                                                                                                                         \n'
	size1_start=text.find('SIZE1=')+len('SIZE1=')
	size2_start=text.find('SIZE2=')+len('SIZE2=')
	# UNKNOWN which is width or height. all known smv are squares
	size1='%4d' % min(shape)
	size2='%4d' % min(shape)
	text = text[:size1_start]+size1+text[size1_start+4:]
	text = text[:size2_start]+size2+text[size2_start+4:]
	return text

def write(a, imfile=None, offset=0, header_updates={}):
	'''
	Convert array to unsigned 16 bit gray scale and save to filename.
	Format is determined from filename extension by PIL.
	'''
	if offset:
		a = a+numpy.ones(a.shape)*offset
	if a.min() < 0:
		print '%s min of %d was truncated to 0' % (imfile, a.min())
		a[a < 0] = 0
	if a.max() >= 2**16:
		print '%s max of %d was truncated to %d' % (imfile, a.max(), 2**16-1)
		a[a >= 2**16] = 2**16-1
	# known smv format are all square.
	shape = a.shape
	shape_max = max(shape)
	shape_min = min(shape)
	if shape_min != shape_max:
		print("Warning: truncate to square shape")
		crop_start = (shape_max-shape_min)/2
		if shape[0] == max(shape):
			a = a[crop_start:crop_start+shape_min,:]
		else:
			a = a[:,crop_start:crop_start+shape_min]
	# known smv files are all uint16
	a = a.astype(numpy.uint16)
	new_head = getHeaderText(a.shape)
	for k in header_updates.keys():
		v = header_updates[k]
		new_head = updateHeader(new_head,k,v)
	outf = open(imfile,'wb')
	outf.write(new_head)
	outf.write(a)
	outf.close()

def updateHeader(header, key, value):
	try:
		item_start = header.index(key)
	except ValueError:
		print('Key %s not in header' % (key,))
		return
	i = 0
	while True:
		if header[item_start+i] == ';':
			item_end = item_start+i+1
			break
		i += 1
	print(item_start, item_end)
	item_length = item_end - item_start
	item = header[item_start:item_start+item_length]
	print(item)
	allowed_length = item_length - len(key) -2 #take out '=' and ';'
	if type(value) == type(0):
		value = '%d' % value
	elif typt(value) ==type(1.2):
		value = '%5.3f' % value
	value_length = len(value)
	space_length = allowed_length - value_length
	new_item='%s=%s%s;' % (key, ' '*space_length,value)
	new_header = header.replace(item, new_item)
	print('Updating %s to %s' % (item, new_item))
	return new_header

if __name__ == '__main__':
	shape = (1000,1000)
	inset_shape = (200,200)
	a = numpy.zeros(shape)
	a[0:inset_shape[0],0:inset_shape[1]] = numpy.ones(inset_shape)
	write(a, 'test.smv')
