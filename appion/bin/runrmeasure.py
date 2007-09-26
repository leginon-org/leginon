#!/usr/bin/env python

import sys, os, subprocess, glob

if len(sys.argv) !=3:
        print"""Check your arguments
Usage: runrmeasure.py apix outfile
-------------------------------------------

"""
        sys.exit()

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

f=open(resout,'w')
for intvol in intvols:
	if intvol==0:
		continue
	vol='threed.'+str(intvol)+'a.mrc'
	print 'Processing', vol
	
	rmeasure=subprocess.Popen(['rmeasure'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
	rmeasure.stdin.write(vol+'\n')
	rmeasure.stdin.write(apix+'\n')
	output=rmeasure.stdout.read()
	
	words=output.split()
	for n in range(0,len(words)):
		#print words[n],words[n+4]
		if words[n]=='Resolution' and words[n+4]=='0.5:':
			resolution=words[n+5]
			break
	print vol, resolution
	f.write('%s\t%s\n' % (vol, resolution))
f.close()
print "Done!"
