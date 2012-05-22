import subprocess
import os

from appionlib import apDisplay

def makeflv(frameformat,framepaths_wild,moviepath,cleanup=True):
	'''
	Make flv movie from frame images. The paths should be absolute to
	avoid confusion and framepaths_wild should include a wildcard to
	gather frame images by orders such as '/data/slices*.jpg'
	'''
	if moviepath[-4:].lower() != '.flv':
		moviepath += '.flv'
	apDisplay.printMsg('Putting the %s files together to flash video...' % frameformat)
	cmd = 'mencoder -nosound -mf type='+frameformat+':fps=24 -ovc lavc -lavcopts vcodec=flv -of lavf -lavfopts format=flv -o '+moviepath+' "mf://'+framepaths_wild+'"'
	proc = subprocess.Popen(cmd, shell=True)
	proc.wait()
	if cleanup:
		removeFrames(framepaths_wild)

def makegif(frameformat,framepaths_wild,moviepath,cleanup=True):
	apDisplay.printMsg('Putting the %s files together into animated gif...' % frameformat)
	if moviepath[-4:].lower() != '.gif':
		moviepath += '.gif'
	cmd = 'convert '+framepaths_wild+ ' '+moviepath
	proc = subprocess.Popen(cmd, shell=True)
	proc.wait()
	if cleanup:
		removeFrames(framepaths_wild)

def removeFrames(framepath):
	proc = subprocess.Popen('/bin/rm '+framepath, shell=True)
	proc.wait()
