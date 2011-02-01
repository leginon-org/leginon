#pythonlib
import os
#appion
from appionlib import appiondata
from appionlib import apDatabase

def getContourPickerDataFileName(sessionname,contourid):
	q = appiondata.ApSelectionRunData()
	rundata = q.direct_query(contourid)
	if rundata:
		contourrunpath = rundata['path']['path']
		datafilepath = os.path.join(contourrunpath,'contourpickerData-'+sessionname+'.txt')
		if os.path.isfile(datafilepath):
			return datafilepath
	return False

def getImagePixelSizeFromContourId(contourid):
	# This returns pixelsize in Angstrom
	q = appiondata.ApSelectionRunData()
	rundata = q.direct_query(contourid)
	q = appiondata.ApContourData(selectionrun=rundata)
	r = q.query(results=1)
	lastimagedata = r[0]['image']
	apix = apDatabase.getPixelSize(lastimagedata)
	return apix


def analyzeArea(contourid):
	return []

def commitSizingRun(params, method=None):
	q = appiondata.ApSelectionRunData()
	tracerundata = q.direct_query(params['contourid'])
	pathq = appiondata.ApPathData()
	pathq['path'] = params['rundir']

	q = q.direct_query(params['contourid'])
	q = appiondata.ApSizingRunData()
	q['name'] = params['runname']
	q['tracerun'] = tracerundata
	q['path'] = pathq
	q['method'] = method
	q.insert()
	return q

def commitSizingResults(rundata,areas):
	return
