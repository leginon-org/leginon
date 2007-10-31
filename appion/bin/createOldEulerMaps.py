#!/usr/bin/python -O

import sys, os
import apDisplay
import apEuler
import apRecon
import appionData

if __name__ == '__main__':
	for i in range(205):
		refrunid = i+1

		#check if data exists
		refrundata = apRecon.getRefineRunDataFromID(refrunid)
		if not refrundata:
			apDisplay.printWarning("db data does not exist for refrunid="+str(refrunid))
			continue

		#check if path exists
		path = refrundata['path']['path']
		if not os.path.isdir(path):
			apDisplay.printWarning("path does not exist for refrunid="+str(refrunid))
			continue
		apDisplay.printMsg("path="+str(path))

		#begin process
		apDisplay.printMsg("creating euler frequency map for refrunid="+str(refrunid))
		#print refrundata

		#get number of iterations
		numiters = apRecon.getNumIterationsFromRefineRunID(refrunid)
		apDisplay.printMsg("found "+str(numiters)+" iterations for refrunid="+str(refrunid))

		for j in range(numiters):
			iternum = int(j+1)
			apDisplay.printMsg("creating euler frequency map for iteration="+str(iternum))
			radlist, anglelist, freqlist, freqgrid = apEuler.getEulersForIteration(refrunid, iternum)
			eulerimgpath = os.path.join(path, "eulermap"+str(iternum)+".png")
			apEuler.makeImage(radlist, anglelist, freqlist, imgname=eulerimgpath)
