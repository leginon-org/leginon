#!/usr/bin/env python
'''
This script reduces the size of leginon image folder when there
are dose-weighted image presence.
This is done by shrinking unaligned image to 8x8 array that
retains mean and standard deviation of the original mrc image.
It also remove non dose weighted aligned file and replaces
it with a soft link to the dose-weighted version.
'''
import numpy
import sys
import os
import glob
from pyami import mrc

base_fake_image = numpy.array(
    [[-1.19424753,  1.4246904 , -0.93985889,  0.60135849,  0.27857971,
        -1.65301365,  1.04678336, -1.52532131],
       [-1.31055292, -1.64913688, -0.02365123,  0.66956679, -0.65988101,
         0.9513427 , -0.13423738,  0.33800944],
       [-1.1071589 ,  0.88239252,  0.10997026, -1.18640795,  0.61022063,
         0.81224024, -0.16747269,  0.00719223],
       [-0.90773998,  1.7711954 , -0.22341715,  1.77620855, -1.31179014,
         0.41032037,  0.0359722 ,  0.54127201],
       [-0.93403768, -0.68054982,  0.91282793, -0.3759068 , -0.90186899,
         0.25927322,  0.45464985,  0.45113749],
       [ 0.90185984,  0.61578781, -0.6812698 , -0.51314294,  1.5032234 ,
        -0.65909159,  2.16388489, -0.68847963],
       [-0.85829773, -2.44494674, -0.50517834,  0.6213358 ,  0.9792851 ,
         0.44794129,  0.76906529,  1.45588215],
       [ 0.43612393, -0.27890367, -0.11642871, -0.15955607, -2.52247377,
         0.62344606,  0.42410922,  1.02661867]])

def makeFakeImage(image):
	if image.std() > 0:
		fake_image = base_fake_image*image.std() + image.mean()*numpy.ones((8,8))
	else:
		fake_image = numpy.zeros((8,8))
	return fake_image

def readMrc(filepath):
	if os.path.isfile(filepath):
		if not filepath.endswith('.mrc'):
			raise ValueError('%s is not an mrc file' % filepath)
		h = mrc.readHeaderFromFile(filepath)
		if h['nz']!=1:
			raise ValueError('%s is an image stack' % filepath)
		image = mrc.read(filepath)
		if image.shape == (8,8):
			raise ValueError('%s is already at 8x8 size' % filepath)
		return image
	else:
		raise ValueError('%s does not exist' % filepath)

def runFileShrink(filepath):
	try:
		image_array = readMrc(filepath)
	except ValueError as e:
		print(e)
		print('....Bypass this file')
		return
	fake_image = makeFakeImage(image_array)
	mrc.write(fake_image, filepath)
	print('  %s is now shrunk to 8x8' % (filepath,))

def folderShrink(folderpath):
	if not os.path.isdir(folderpath):
		print('Not a directory, bypassed')
	dwmrcs = glob.glob(os.path.join(folderpath,'*DW.mrc'))
	for dw in dwmrcs:
		print('Processing %s' % dw)
		aligned = dw.replace('-DW.mrc','.mrc')
		if os.path.isfile(aligned) and not os.path.islink(aligned):
			os.remove(aligned)
			os.symlink(dw, aligned)
			print('  %s is now linked to %s' % (aligned, dw))
		raw = '-'.join(aligned.split('-')[:-1])+('.mrc')
		if os.path.isfile(raw):
			runFileShrink(raw)

if __name__=='__main__':
	if len(sys.argv) != 2:
		print('Usage: Provide a leginon image data folder name, please')
	folderShrink(sys.argv[1])
