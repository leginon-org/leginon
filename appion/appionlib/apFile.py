import os
import re
import sys
import time
import glob
import subprocess
import shutil
from appionlib import apDisplay
from appionlib import apRelion
from pyami import mrc
from pyami import fileutil

####
# This is a low-level file with NO database connections
# Please keep it this way
####

#===============
def md5sumfile(fname):
	"""
	Returns an md5 hash for file fname
	"""
	if not os.path.isfile(fname):
		apDisplay.printError("MD5SUM, file not found: "+fname)
	# f = file(fname, 'rb')
	f = open(fname, 'rb')
	#this next library is deprecated in python 2.6+, need to use hashlib
	# import md5
	import hashlib
	m = hashlib.md5()
	while True:
		d = f.read(8096)
		if not d:
			break
		m.update(d)
	f.close()
	return m.hexdigest()

#===============
def removeFile(filename, warn=False):
	f = os.path.abspath(filename)
	if os.path.isfile(f) or os.path.islink(f):
		if warn is True:
			apDisplay.printWarning("removing file:"+f)
			time.sleep(1)
		try:
			os.remove(f)
			return True
		except:
			apDisplay.printWarning('%s could not be removed' % f)
	return False

#===============
def removeDir(dirname, warn=True):
	dir = os.path.abspath(dirname)
	if os.path.isdir(dir):
		if warn is True:
			apDisplay.printWarning("removing directory: "+dir)
			time.sleep(1)
		try:
			shutil.rmtree(dir)
			return True
		except:
			apDisplay.printWarning('%s could not be removed' % dir)
	return False

#===============
def removeStack(filename, warn=True):
	rootname = os.path.splitext(filename)[0]
	for f in (rootname+".hed", rootname+".img", rootname+".hdf"):
		if os.path.isfile(f):
			if warn is True:
				apDisplay.printWarning("removing stack: "+f)
				time.sleep(1)
			try:
				os.remove(f)
			except:
				apDisplay.printWarning('%s could not be removed' % f)

#===============
def moveStack(filename1, filename2, warn=True):
	### replace one imagic stack with another
	rootname1 = os.path.splitext(filename1)[0]
	rootname2 = os.path.splitext(filename2)[0]
	for ext in (".hed", ".img"):
		inf = rootname1+ext
		outf = rootname2+ext
		if os.path.isfile(inf):
			if warn is True:
				apDisplay.printWarning("replacing stack file '%s' with '%s' "%(outf,inf))
				time.sleep(1)
			try:
				shutil.move(inf,outf)
			except:
				apDisplay.printWarning('%s could not be replaced with %s' % (outf,inf))

#===============
def removeFilePattern(pattern, warn=True):
	files = glob.glob(pattern)
	if warn is True:
		apDisplay.printWarning("%d files with the patterns '%s' will be removed" 
			% (len(files), pattern))
		time.sleep(3)
	removed = 0
	for fname in files:
		fullpath = os.path.abspath(fname)
		if removeFile(fullpath):
			removed+=1
	if warn is True:
		apDisplay.printMsg("Removed %d of %d files"%(removed, len(files)))
	return

#===============
def fileSize(filename, msg=False):
	"""
	return file size in bytes
	"""
	if not os.path.isfile(filename):
		return 0
	stats = os.stat(filename)
	size = stats[6]
	return size

#===============
def stackSize(filename, msg=False):
	"""
	return file size in bytes
	"""
	rootname = os.path.splitext(filename)[0]
	size = 0
	for f in (rootname+".hed", rootname+".img"):
		if not os.path.isfile(f):
			size += 0
		stats = os.stat(f)
		size += stats[6]
	return size

#===============
def getBoxSize(filename, msg=True):
	"""
	return boxsize of stack in pixels
	"""
	if not os.path.isfile(filename):
		if msg is True:
			apDisplay.printWarning("file does not exist")
		return (1,1,1)
	if filename[-4:] == '.hed' or filename[-4:] == '.img':
		root=os.path.splitext(filename)[0]
		headerfilename=root + ".hed"
		from appionlib import apImagicFile
		headerdict = apImagicFile.readImagicHeader(headerfilename)
		shape = (headerdict['rows'], headerdict['lines'], headerdict['nimg'])
		return shape
	if '.mrc' in filename[-5:]: 
		headerdict = mrc.readHeaderFromFile(filename)
		shape = headerdict['shape']
		if len(shape) == 2:
			return (shape[0], shape[1], 1)
		elif len(shape) == 3:
			return shape
	proc = subprocess.Popen("iminfo %s"%(filename), shell=True, stdout=subprocess.PIPE)
	proc.wait()
	lines = ""
	for line in proc.stdout:
		sline = line.strip()
		lines += line
		m = re.match("^Image\(s\) are ([0-9]+)x([0-9]+)x([0-9]+)", sline)	
		if m and m.groups() and len(m.groups()) > 1:
			xdim = int(m.groups()[0])
			ydim = int(m.groups()[1])
			zdim = int(m.groups()[2])
			return (xdim,ydim,zdim)
		m = re.match("^0\.\s+([0-9]+)x([0-9]+)\s+", sline)	
		if m and m.groups() and len(m.groups()) > 1:
			xdim = int(m.groups()[0])
			ydim = int(m.groups()[1])
			return (xdim,ydim,1)
		m = re.match("^0\.\s+([0-9]+)x([0-9]+)x([0-9]+)\s+", sline)	
		if m and m.groups() and len(m.groups()) > 1:
			xdim = int(m.groups()[0])
			ydim = int(m.groups()[1])
			zdim = int(m.groups()[2])
			return (xdim,ydim,zdim)
	if msg is True:
		apDisplay.printWarning("failed to get boxsize: "+lines)
	return (1,1,1)

#===============
def numImagesInStack(imgfile, boxsize=None):
	"""
	Find the number of images in a stack:
	IMAGIC: based on the filesize
	RELION: based on lines in star file
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
	elif imgfile.endswith(".star"):
		return len(apRelion.starParticleArray(imgfile))
	elif 'mrc' in imgfile[-4:]:
		numimg = mrc.readHeaderFromFile(imgfile)['nz']
	else:
		apDisplay.printError("numImagesInStack() requires an IMAGIC, SPIDER, or RELION stack (or .mrc[s]...)")
	return numimg

def safeSymLink(source, destination):
	''' create new symbolic link only if the destination is not a file'''
	if (os.path.isfile(destination) and not os.path.islink(destination)):
		apDisplay.printWarning('destination is a non-linked file, linking from %s to %s not performed' % (source,destination))
		return False
	else:
		if (os.path.islink(destination)):
			os.remove(destination)
		os.symlink(source,destination)
	return True

def safeCopy(source, destination):
	''' copy from source only if the destination is not a file'''
	if (os.path.isfile(destination) and not os.path.islink(destination)):
		apDisplay.printWarning('destination is a non-linked file, copying from %s to %s not performed' % (source,destination))
		return False
	else:
		if (os.path.islink(destination)):
			os.remove(destination)
		shutil.copy(source,destination)
	return True

def replaceUniqueLinePatternInTxtFile(filepath,search_string,new_linetext):
	infile = open(filepath,'r')
	lines = infile.readlines()
	infile.close()
	if new_linetext[-1] != '\n':
		new_linetext += '\n'
	newlines = []
	for line in lines:
		if search_string in line:
			apDisplay.printWarning('%s will be replaced by %s in %s' % (line[:-1],new_linetext[:-1],filepath))
			newline = new_linetext
		else:
			newline = line
		newlines.append(newline)
	tmppath = filepath+'.tmp'
	outfile = open(filepath+'.tmp','w')
	outfile.writelines(newlines)
	outfile.close()
	shutil.move(tmppath,filepath)


def getMrcFileShape(mrcpath):
	header = mrc.readHeaderFromFile(mrcpath)
	return header['shape']

def rsync(from_path, to_dir, remove_sent=False, delay=0):
	'''
	perform rsync with from_path and to under to_dir.
	Can impose a delay before execution.
	'''
	if not to_dir:
		return
	fileutil.mkdirs(to_dir)
	cmd = makeRsyncCommand(from_path, to_dir, remove_sent)
	print(cmd)
	time.sleep(delay)
	proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
	(output, error) = proc.communicate()

def makeRsyncCommand(from_path, to_dir, remove_sent=False):
	#rsync command handles both file and directory
	remove_sent_text = ''
	if remove_sent:
		# remove-sent-files flag
		remove_sent_text = '--remove-sent-files '
	cmd = 'rsync -av %s%s %s' % (remove_sent_text, from_path, to_dir)
	return cmd

def compress_and_rsync(from_path, to_dir, remove_sent=False, delay=0):
	'''
	compress file at from_path to be put under to_dir. from_path can be
	a directory and this will compress files in there to a subdirectory of
	the same basename.
	'''
	time.sleep(delay)

	if os.path.isdir(from_path):
		basename = os.path.basename(from_path)
		wild_card = '/*'
		#bzip2 command need to modify from_path to allow directory
		bzip2_from_path = from_path+wild_card
		rsync_from_path = from_path
	else:
		bzip2_from_path = from_path
		rsync_from_path = from_path+'.bz2'
	# bzip2 only compresses file, not directory
	cmd = 'pbzip2 -k -p1 %s' % (bzip2_from_path)
	if to_dir:
		rsync_cmd = makeRsyncCommand(rsync_from_path, to_dir, remove_sent)
		cmd += '; '+rsync_cmd	
	print(cmd)
	proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
	(output, error) = proc.communicate()

####
# This is a low-level file with NO database connections
# Please keep it this way
####


