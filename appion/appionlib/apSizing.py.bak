#pythonlib
import os
#appion
from appionlib import appiondata
from appionlib import apDatabase
from appionlib import apParticle
from leginon import polygon

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

def getContoursFromImageTraceRun(imagedata,tracerundata):
	q = appiondata.ApContourData(image=imagedata,selectionrun=tracerundata)
	r = q.query()
	return r

def getContourPointsFromContour(contourdata):
	q = appiondata.ApContourPointData(contour=contourdata)
	pointresults = q.query()
	points = []
	for pointdata in pointresults:
		points.append((pointdata['x'],pointdata['y']))
	return points	

def makeParticleFromContour(imagedata,tracerundata,label='_trace'):
	contours = getContoursFromImageTraceRun(imagedata,tracerundata)
	peaktree = []
	for contourdata in contours:
		points = getContourPointsFromContour(contourdata)
		center = polygon.getPolygonCenter(points)
		peakdict = {'xcoord':center[0],'ycoord':center[1],'label':label,'peakarea':1}
		peaktree.append(peakdict)
	apParticle.insertParticlePeaks(peaktree, imagedata, tracerundata['name'], False)

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
