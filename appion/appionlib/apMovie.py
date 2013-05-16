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

def makemp4(frameformat,framepaths_format,moviepath,cleanup=True):
	'''
	Make mpeg4 movie from frame images. The paths should be absolute to
	avoid confusion and framepaths_wild should include a number format to
	gather frame images by orders such as '/data/slices%05d.jpg'.  Note
	that wild card * does not work with ffmpeg
	'''
	if moviepath[-4:].lower() != '.mp4':
		moviepath += '.mp4'
	apDisplay.printMsg('Putting the %s files together to mp4...' % frameformat)
	cmd = 'ffmpeg -i %s -r 10 -b 10000 -vcodec mpeg4 %s' % (framepaths_format,moviepath)
	proc = subprocess.Popen(cmd, shell=True)
	proc.wait()
	if cleanup:
		removeFrames(framepaths_format)

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
	if '%' in framepath:
		prefix = framepath.split('%')[0]
		extension = framepath.split('.')[-1]
		framepath = prefix+'*.'+extension
	proc = subprocess.Popen('/bin/rm '+framepath, shell=True)
	proc.wait()
