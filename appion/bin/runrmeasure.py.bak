#!/usr/bin/env python

import sys
import os
import subprocess
import glob

#===========
def getRMeasurePath():
	unames = os.uname()
	if unames[-1].find('64') >= 0:
		exename = 'rmeasure64.exe'
	else:
		exename = 'rmeasure32.exe'
	rmeasexe = subprocess.Popen("which "+exename, shell=True, stdout=subprocess.PIPE).stdout.read().strip()
	if not os.path.isfile(rmeasexe):
		rmeasexe = os.path.join(apParam.getAppionDirectory(), 'bin', exename)
	if not os.path.isfile(rmeasexe):
		apDisplay.printError(exename+" was not found at: "+apParam.getAppionDirectory())
	return rmeasexe

#===========
if __name__ == "__main__":
	if len(sys.argv) !=3:
		print "Check your arguments\nUsage: runrmeasure.py apix outfile"
		sys.exit(1)

	apix=sys.argv[1]
	resout=sys.argv[2]

	volumes=glob.glob('threed.*a.mrc')
	intvols=[]
	for vol in volumes:
		try:
			intvols.append(int(vol.split('.')[1].split('a')[0]))
		except:
			pass
	intvols.sort()


	for intvol in intvols:
		if intvol==0:
			continue
		vol='threed.'+str(intvol)+'a.mrc'
		print 'Processing', vol
		rmeasexe = getRMeasurePath()
		rmeasproc = subprocess.Popen(rmeasexe, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
		fin = rmeasproc.stdin
		fout = rmeasproc.stdout
		fin.write(vol+'\n')
		fin.write(apix+'\n')
		output = fout.read()

		resolution = None
		words=output.split()
		for n in range(0,len(words)):
			#print words[n],words[n+4]
			if words[n]=='Resolution' and words[n+4]=='0.5:':
				resolution = words[n+5]
				break
		f=open(resout, 'a')
		if resolution is None:
			print vol, "failed"
			f.write('%s\t%s\n' % (vol, "failed"))
		else:
			print vol, resolution, "A"
			f.write('%s\t%s\n' % (vol, resolution))
		f.close()
	print "Done!"
