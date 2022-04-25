#!/usr/bin/env python

#python
import sys
import os
import time
import numpy
# appion
import sinedon.directq
from appionlib import apEMAN
from appionlib import apFile
from appionlib import apDisplay
from appionlib import apStack
from appionlib import apImage
from appionlib import apImagicFile
from appionlib import apProject

#===============
def makeStackMeanPlot(stackid, gridpoints=16):
	if gridpoints > 30:
		apDisplay.printError("Too large of a grid")
	apDisplay.printMsg("creating Stack Mean Plot montage for stackid: "+str(stackid))
	t0 = time.time()
	### big stacks are too slow
	boxsize = apStack.getStackBoxsize(stackid)
	bin = 1
	if boxsize is not None:
		while boxsize/bin > 128:
			bin+=1
	apDisplay.printMsg("binning stack by "+str(bin))
	stackdata = apStack.getOnlyStackData(stackid, msg=False)
	stackpath = stackdata['path']['path']
	stackfile = os.path.join(stackpath, stackdata['name'])
	# if no stackfile, likely virtual stack
	if not os.path.isfile(stackfile):
		apDisplay.printMsg("possible virtual stack, searching for original stack")
		vstackdata = apStack.getVirtualStackParticlesFromId(stackid)
		partdatas = vstackdata['particles']
		stackfile = vstackdata['filename']
		stackdata = apStack.getOnlyStackData(vstackdata['stackid'], msg=False)
	# otherwise get stack info
	else:
		# get stats from stack:
		sqlcmd = "SELECT " + \
			"particleNumber, mean, stdev " + \
			"FROM ApStackParticleData " + \
			"WHERE `REF|ApStackData|stack` = %i"%(stackid)
		partdatas = sinedon.directq.complexMysqlQuery('appiondata',sqlcmd)
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
	apDisplay.printMsg(str(limits))

	### create particle bins
	partlists = {}
	for i in range(gridpoints):
		for j in range(gridpoints):
			key = ("%02dx%02d"%(i,j))
			partlists[key] = []

	### sort particles into bins
	for partdata in partdatas:
		key = meanStdevToKey(partdata['mean'], partdata['stdev'], limits, gridpoints)
		partnum = int(partdata['particleNumber'])
		partlists[key].append(partnum)

	printPlot(partlists, gridpoints)

	### createStackAverages
	keys = partlists.keys()
	keys.sort()
	count = 0
	backs = "\b\b\b\b\b\b\b\b\b\b\b"
	montagestack = os.path.join(stackpath,"montage"+str(stackid)+".hed")
	apFile.removeStack(montagestack)
	mystack = []
	for key in keys:
		count += 1
		sys.stderr.write(backs+backs+backs+backs)
		sys.stderr.write("% 3d of % 3d, %s: % 6d"%(count, len(keys), key, len(partlists[key])))
		avgimg = averageSubStack(partlists[key], stackfile, bin)
		if avgimg is not False:
			avgimg = numpy.fliplr(avgimg)
			mystack.append(avgimg)
	apImagicFile.writeImagic(mystack, montagestack)
	sys.stderr.write("\n")
	assemblePngs(keys, str(stackid), montagestack)
	apDisplay.printMsg("/bin/mv -v montage"+str(stackid)+".??? "+stackpath)
	apDisplay.printMsg("finished in "+apDisplay.timeString(time.time()-t0))

#===============
def averageSubStack(partlist, stackfile, bin=1):
	if len(partlist) > 300:
		partlist = partlist[:300]
	boxsize = apImagicFile.getBoxsize(stackfile)
	if len(partlist) == 0:
		binboxsize = boxsize/bin
		blank = numpy.ones((binboxsize, binboxsize), dtype=numpy.float32)
		return blank
	if not os.path.isfile(stackfile):
		apDisplay.printWarning("could not find stack, "+stackfile)
		return False
	partdatalist = apImagicFile.readParticleListFromStack(stackfile, partlist, boxsize, msg=False)
	partdataarray = numpy.asarray(partdatalist)
	finaldata = partdataarray.mean(0)
	if bin > 1:
		finaldata = apImage.binImg(finaldata, bin)
	return finaldata

#===============
def assemblePngs(keys, tag, montagestack):
	apDisplay.printMsg("assembling pngs into montage")
	# get path from montagestack
	stackpath = os.path.dirname(os.path.abspath(montagestack))

	montagecmd = "montage -geometry +4+4 "
	montagestackdata = apImagicFile.readImagic(montagestack)
	for i,key in enumerate(keys):
		if i % 20 == 0:
			sys.stderr.write(".")
		pngfile = key+".png"
		array = montagestackdata['images'][i]
		apImage.arrayToPng(array, pngfile, normalize=True, msg=False)
		#proccmd = "proc2d "+montagestack+" "+pngfile+" first="+str(i)+" last="+str(i)
		#apEMAN.executeEmanCmd(proccmd, verbose=False, showcmd=False)
		montagecmd += pngfile+" "
	apDisplay.printMsg("montaging")
	montagefile = os.path.join(stackpath,"montage"+tag+".png")
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
		apDisplay.printMsg(outstr)

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
	print "Usage: apStackMeanPlot.py <stackid> <#points> <projectid>"
	if len(sys.argv) > 1:
		stackid = int(sys.argv[1])
	else:
		#stackid=1279
		stackid=1291
	if len(sys.argv) > 2:
		gridpoints = int(sys.argv[2])
	else:
		gridpoints=16
	if len(sys.argv) > 3:
		projectid = int(sys.argv[3])
	else:
		projectid=None
	### setup correct database after we have read the project id
	if projectid is not None:
		apDisplay.printWarning("Using split database")
		# use a project database
		newdbname = apProject.getAppionDBFromProjectId(projectid)
		import sinedon
		sinedon.setConfig('appiondata', db=newdbname)
		apDisplay.printColor("Connected to database: '"+newdbname+"'", "green")

	makeStackMeanPlot(stackid, gridpoints)



