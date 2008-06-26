import md5
import os
import sys
import apDisplay

def md5sumfile(fname):
	"""
	Returns an md5 hash for file fname
	"""
	if not os.path.isfile(fname):
		apDisplay.printError("MD5SUM, file not found: "+fname)
	f = file(fname, 'rb')
	m = md5.new()
	while True:
		d = f.read(8096)
		if not d:
			break
		m.update(d)
	f.close()
	return m.hexdigest()

def removeStack(filename, warn=True):
	rootname = os.path.splitext(filename)[0]
	for f in (rootname+".hed", rootname+".img"):
		if os.path.isfile(f):
			if warn is True:
				apDisplay.printWarning("removing file:"+f)
			try:
				os.remove(f)
			except:
				apDisplay.printWarning('%s could not be removed' % f)

def removeFile(filename, warn=False):
	f = os.path.abspath(filename)
	if os.path.isfile(f):
		if warn is True:
			apDisplay.printWarning("removing file:"+f)
		try:
			os.remove(f)
		except:
			apDisplay.printWarning('%s could not be removed' % f)

def numImagesInStack(imgfile, boxsize=None):
	"""
	Find the number of images in an 
	IMAGIC stack based on the filesize
	"""
	if not os.path.isfile(imgfile):
		return 0
	if imgfile[-4:] == '.hed':
		numimg = int('%d' % (os.stat(imgfile)[6]/1024))
	elif imgfile[-4:] == '.img':
		hedfile = imgfile[:-4]+'.hed'
		numimg = int('%d' % (os.stat(hedfile)[6]/1024))
	elif os.path.isfile(imgfile+'.hed'):
		numimg = int('%d' % (os.stat(imgfile+'.hed')[6]/1024))
	elif imgfile[-4:] == '.spi':
		if boxsize is None:
			apDisplay.printError("boxsize is required for SPIDER stacks")
		imgmem = boxsize*(boxsize+2)*4
		numimg = int('%d' % (os.stat(imgfile)[6]/imgmem))
	else:
		apDisplay.printError("numImagesInStack() requires an IMAGIC or SPIDER stacks")
	return numimg
