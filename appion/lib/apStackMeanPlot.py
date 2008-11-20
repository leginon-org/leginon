#!/usr/bin/env python

import sys
import os
import time
import apEMAN
import apFile
import apDisplay
import apStack


#===============
def makeStackMeanPlot(stackid, gridpoints=20):
	t0 = time.time()
	stackdata = apStack.getOnlyStackData(stackid, msg=False)
	stackfile = os.path.join(stackdata['path']['path'], stackdata['name'])
	partdatas = apStack.getStackParticlesFromId(stackid, msg=False)
	#check only first 100 particles for now
	#partdatas = partdatas[:500]
	apFile.removeFile("montage"+str(stackid)+".png")

	### find limits
	limits = {'minmean': 1e12, 'maxmean': -1e12, 'minstdev': 1e12, 'maxstdev': -1e12,}
	for partdata in partdatas:
		if partdata['mean'] is None:
			continue
		mean = partdata['mean']
		stdev = partdata['stdev']
		if mean < limits['minmean']:
			limits['minmean'] = mean
		if mean > limits['maxmean']:
			limits['maxmean'] = mean
		if stdev < limits['minstdev']:
			limits['minstdev'] = stdev
		if stdev > limits['maxstdev']:
			limits['maxstdev'] = stdev
	if limits['minmean'] > 1e11:
		apDisplay.printWarning("particles have no mean values in database")
		return
	print limits

	### create particle bins
	partlists = {}
	for i in range(gridpoints):
		for j in range(gridpoints):
			key = ("%02dx%02d"%(i,j))
			partlists[key] = []

	### sort paritcles into bins
	for partdata in partdatas:
		key = meanStdevToKey(partdata['mean'], partdata['stdev'], limits, gridpoints)
		partnum = int(partdata['particleNumber']-1)
		partlists[key].append(partnum)

	printPlot(partlists, gridpoints)

	### createStackAverages
	keys = partlists.keys()
	keys.sort()
	count = 0
	backs = "\b\b\b\b\b\b\b\b\b\b\b"
	montagestack = "montage.hed"
	apFile.removeStack(montagestack)
	for key in keys:
		count += 1
		sys.stderr.write(backs+backs+backs+backs)
		sys.stderr.write("% 3d of % 3d, %s: % 6d"%(count, len(keys), key, len(partlists[key])))
		averageSubStack(partlists[key], stackfile, montagestack)
	print ""
	assemblePngs(keys, str(stackid), montagestack)
	print "mv montage"+str(stackid)+".png "+stackdata['path']['path']
	apDisplay.printMsg("finished in "+apDisplay.timeString(time.time()-t0))

#===============
def averageSubStack(partlist, stackfile, filename):
	if len(partlist) == 0:
		emancmd = ( "proc2d "+stackfile+" "+filename+" first=0 last=0 mask=1" )
		apEMAN.executeEmanCmd(emancmd, verbose=False, showcmd=False)
		return False
	if not os.path.isfile(stackfile):
		apDisplay.printWarning("could not create stack average, "+filename)
		return False
	listfile = "temp.lst"
	f = open(listfile, "w")
	count = 0
	#for partnum in partlist:
	while(count < len(partlist) and count < 500):
		partnum = partlist[count]
		count += 1
		f.write(str(partnum)+"\n")
	f.close()
	emancmd = ( "proc2d "+stackfile+" "+filename+" list="+listfile+" average" )
	apEMAN.executeEmanCmd(emancmd, verbose=False, showcmd=False)
	return True

#===============
def assemblePngs(keys, tag, montagestack):
	apDisplay.printMsg("assembling pngs into montage")
	montagecmd = "montage -geometry +4+4 "
	for i,key in enumerate(keys):
		if i % 20 == 0:
			sys.stderr.write(".")
		pngfile = key+".png"
		proccmd = "proc2d "+montagestack+" "+pngfile+" first="+str(i)+" last="+str(i)
		apEMAN.executeEmanCmd(proccmd, verbose=False, showcmd=False)
		montagecmd += pngfile+" "
	apDisplay.printMsg("montaging")
	montagefile = "montage"+tag+".png"
	montagecmd += montagefile
	apEMAN.executeEmanCmd(montagecmd, verbose=True)
	#rotatecmd = "mogrify -rotate 180 -flop "+montagefile
	#apEMAN.executeEmanCmd(rotatecmd, verbose=False)
	for key in keys:
		apFile.removeFile(key+".png")
	if not os.path.isfile(montagefile):
		apDisplay.printWarning("failed to create montage file")

#===============
def printPlot(partlists, gridpoints):
	for i in range(gridpoints):
		outstr = "%02d: "%(i)
		for j in range(gridpoints):
			if j % 2 == 0:
				key = ("%02dx%02d"%(i,j))
				outstr += "% 5d "%(len(partlists[key]))
		print outstr

#===============
def meanStdevToKey(mean, stdev, limits, gridpoints):
	if mean == limits['maxmean']:
		x = gridpoints-1
	else:
		x = int(gridpoints*(mean - limits['minmean'])/(limits['maxmean'] - limits['minmean']))
	if stdev == limits['minstdev']:
		y = gridpoints-1
	else:
		y = int(gridpoints*(limits['maxstdev'] - stdev)/(limits['maxstdev'] - limits['minstdev']))
	#print mean, stdev, x, y
	return ("%02dx%02d"%(y,x))

#===============
#===============
#===============
if __name__ == "__main__":
	if len(sys.argv) > 1:
		stackid = int(sys.argv[1])
	else:
		#stackid=1279
		stackid=1291
	makeStackMeanPlot(stackid)


