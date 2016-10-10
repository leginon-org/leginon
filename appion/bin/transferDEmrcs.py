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


imageclasses = [
	leginondata.AcquisitionImageData,
	leginondata.DarkImageData,
	leginondata.BrightImageData,
	leginondata.NormImageData,
]

#imageclasses = [leginondata.AcquisitionImageData]

#=====================
def transfer(src, dst, delete=True):
	'''
	Use rsync to copy the file.  The sent files are removed
	after copying.
	'''
	
	cmdroot = 'rsync -rlptDvh --progress'
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
	parser.add_option("--source", dest="source",
		help="Path that contains the frame mrc stacks", metavar="PATH")
	parser.add_option("--destination", dest="destination",
		help="Parent path into which to transfer the frames", metavar="PATH", default='')
	parser.add_option("--nopause", dest="nopause", action='store_true', default=False, help="By default, if the script finds a frame stack that doesn't have a corresponding leginon image, it will pause for user input unless this option is specified")
	parser.add_option("--dryrun", dest="dryrun", action='store_true', default=False, help="Loop through frames and show procedures, but do not actually tranfer frames")

	# parsing options
	options, args=parser.parse_args()
	
	if len(args) !=0 or len(sys.argv) == 1:
		parser.print_help()
		sys.exit()
	return options

def queryFramesName(framesname):
	qccd = leginondata.InstrumentData(hostname='ddd-pc')
	qcam = leginondata.CameraEMData(ccdcamera=qccd)
	qcam['frames name'] = framesname
	for cls in imageclasses:
		qim = cls(camera=qcam)
		results = qim.query()
		if results:
			if len(results) > 1:
				# fix for issue #3967. Not to work on the aligned images
				for r in results:
					if r['camera']['align frames']:
						continue
					return r
			else:
				# If there is just one, transfer regardlessly.
				return results[0]
	return None

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
	sourceframepath=os.path.join(options.source,'*.mrc')
	rawframes=glob.glob(sourceframepath)
	rawframes.sort()
	
	for n,origframestackpath in enumerate(rawframes):
	
		origframestack=os.path.split(origframestackpath)[-1]
		print "Searching for", origframestack
		frameprefix= origframestack[0:14]
		imgdata=queryFramesName(frameprefix)
		if (imgdata is None) and (options.nopause is False):
			print "No leginon image found for ", origframestack
			yorn=None
			while (yorn!='y' and yorn!='n'):
				yorn=raw_input('Continue? y or n : ')
				yorn=yorn.lower()
				if yorn[0]=='n':
					print "Exiting"
					sys.exit()
			if yorn=='y':
				continue
		elif (imgdata is None) and (options.nopause is True):
			print "Skipping frame stack", origframestack
			continue
	
		destfolder=checkdestpath(imgdata,options.destination)
		newname=imgdata['filename']+'.frames.mrc'
		#print newname
		destpath=os.path.join(destfolder,newname)
		print "Transferring\n",origframestackpath,'to\n',destpath
		if options.dryrun is False:
			transfer(origframestackpath,destpath)
		else:
			print "Skipping transfer in dryrun mode"
		print "Image complete"
		print len(rawframes)-(n+1),'frame stacks remaining\n'

	print "Done!"
	
	
