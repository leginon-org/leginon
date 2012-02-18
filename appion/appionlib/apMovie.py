import subprocess
import os

from appionlib import apDisplay

def makeflv(frameformat,framepath,moviepath,cleanup=True):
	'''
	Make flv movie from frame images. The paths should be absolute to
	avoid confusion and framepath should include a wildcard to
	gather frame images by orders such as '/data/slices*.jpg'
	'''
	apDisplay.printMsg('Putting the %s files together to flash video...' % frameformat)
	cmd = 'mencoder -nosound -mf type='+frameformat+':fps=24 -ovc lavc -lavcopts vcodec=flv -of lavf -lavfopts format=flv -o '+moviepath+' "mf://'+framepath+'"'
	proc = subprocess.Popen(cmd, shell=True)
	proc.wait()
	if cleanup:
		removeFrames(framepath)

def removeFrames(framepath):
	proc = subprocess.Popen('/bin/rm '+framepath, shell=True)
	proc.wait()
