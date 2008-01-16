#!/usr/bin/python -O

import sys, os
import apDisplay
import apEuler
import apRecon
import appionData

if __name__ == '__main__':
	refrunid = 243

	#check if data exists
	refrundata = apRecon.getRefineRunDataFromID(refrunid)
	if not refrundata:
		apDisplay.printWarning("db data does not exist for refrunid="+str(refrunid))
		sys.exit(1)

	#check if path exists
	path = refrundata['path']['path']
	print path
	if not os.path.isdir(path):
		apDisplay.printWarning("path does not exist for refrunid="+str(refrunid))
		sys.exit(1)
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
		apEuler.createEulerImages(refrunid, iternum, path=path)
