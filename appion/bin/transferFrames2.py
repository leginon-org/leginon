#!/usr/bin/env python

import os
import sys
import glob
import shutil
import subprocess
from appionlib import apDisplay
from appionlib import appionLoop2
from appionlib import apDatabase
import leginon.leginondata as leginondata
from optparse import OptionParser
import sinedon

#=====================
def transfer(src, dst, delete=True, method='rsync'):
	if method == 'mv':
		cmd = 'mv %s %s' % (src, dst)
		print cmd
		p = subprocess.Popen(cmd, shell=True)
		p.wait()
		
	elif method == 'rsync':

		'''
		Use rsync to copy the file.  The sent files are removed
		after copying.
		'''

		cmdroot = 'rsync -thvD --progress'
		if delete is True:
			cmdroot+=' --remove-sent-files '
		cmd='%s %s %s' % (cmdroot, src, dst)
		print cmd
		p = subprocess.Popen(cmd, shell=True)
		p.wait()
	
def parseOptions():
	'''
	Use OptionParser to get parameters
	'''
	parser = OptionParser()

	# options
	parser.add_option("--dryrun", dest="dryrun", default=False, action='store_true', help="Just show files that will be deleted, but do not delete them.")
	parser.add_option("--session", dest="session", type='str', help="Session name.")
	parser.add_option("--preset", dest="preset", type='str', help="Preset name.")
	parser.add_option("--origpath", dest="origpath", type='str', help="Path to the original frames.")
	parser.add_option("--destpath", dest="destpath", default=None, type='str', help="Destination path. By default, frames will be copied to the path specified in the database, but this will override that path.")
	#parser.add_option("--no-delete", dest="no-delete", default=False, action="store_true", help="Do not delete the original files after transferring")
	parser.add_option("--reverse", dest="reverse", default=False, action="store_true", help="Loop through images in reverse order")

	# parsing options
	options, args=parser.parse_args()
	
	if len(args) !=0 or len(sys.argv) == 1:
		parser.print_help()
		sys.exit()
	return options

def checkdestpath(imgdata,destination):
	try:
		session=imgdata['session']['name']
	except:
		print imgdata
	destfolder=os.path.join(destination,session,'rawdata')
	print destfolder
	if os.path.exists(destfolder):
		return destfolder
	else:
		print "Making output directory",destfolder
		os.makedirs(destfolder)
		return destfolder



if __name__ == '__main__':
	options=parseOptions()
	sinedon.setConfig('leginondata')
	if options.preset is not None:
		imgtree = apDatabase.getImagesFromDB(options.session, options.preset)
	else:
		imgtree = apDatabase.getAllImagesFromDB(self.params['sessionname'])
	print len(imgtree)

	if options.reverse is False:
		imgtree.reverse()

	### Set up dest folder
	sessionname=imgtree[0]['session']['name']
	destfolder=os.path.join(options.destpath,sessionname,'rawdata')
	if os.path.exists(destfolder):
		print "Output directory %s already exists" % (destfolder)
	else:
		print "Making output directory",destfolder
		os.makedirs(destfolder)
	
	### Transfer frames 
	for imgdata in imgtree:
		frameroot=imgdata['camera']['frames name']
		print "looking for pattern %s" % (frameroot)
		filestotransfer=glob.glob(os.path.join(options.origpath,frameroot)+'*')
		if len(filestotransfer) < 1:
			print 'Files with pattern %s not found in %s, so this image will be skipped' % (frameroot,options.origpath)
			continue
		elif len(filestotransfer) > 1:
			print 'More than one file with pattern %s found, so they will be skipped'
			continue 
		else:
			print len(filestotransfer), "files found"
		destname=imgdata['filename']+'.frames.mrc'
		destnamepath=os.path.join(destfolder,destname)
		
		print 'Transferring %s to %s' % (filestotransfer[0], destnamepath)
		if options.dryrun is False:
			transfer(filestotransfer[0],destnamepath)
			if os.path.exists(destnamepath):
				print "Transfer successful"
			else:
				print "%s %s not transferred properly\nExiting" % (filestotransfer[0],destnamepath)
				sys.exit()
		print "\n\n"
		
	print 'Done!'
