import os
from tomography import tiltcorrelator
import leginondata
import appionData
import node
import apDisplay
import apFile

def getFilename(tiltseriesdata):
	# determine param filename
	session_name = tiltseriesdata['session']['name']
	seriesnumber = tiltseriesdata['number']
	numberstr = '%03d' % (seriesnumber,)
	seriesname = session_name + '_' + numberstr
	return seriesname

def getImageList(tiltseriesdata):
	imquery = leginondata.AcquisitionImageData()
	imquery['tilt series'] = tiltseriesdata

	## query, but don't read image files yet, or else run out of memory
	imagelist = imquery.query(readimages=False)
	## list is reverse chronological, so reverse it
	imagelist.reverse()
	return imagelist
	
def orderImageList(imagelist):
	if not imagelist:
		apDisplay.warning('No images in image list.')
		return
	mrc_files = []
	imagepath = imagelist[0]['session']['image path']
	tiltseries = imagelist[0]['tilt series']
	tiltangledict = {}
	second_group = False 
	for imagedata in imagelist:
		tilt = imagedata['scope']['stage position']['a']*180/3.14159
		if tilt < tiltseries['tilt start']+0.01 and tilt > tiltseries['tilt start']-0.01:
			if second_group:
				direction=-tiltseries['tilt step']
			else:
				direction= tiltseries['tilt step']
				# switch group in getCorrelationPeak not here
				second_group = False
			tilt = tilt+0.001*direction
		tiltangledict[tilt] = imagedata
	tiltkeys = tiltangledict.keys()
	tiltkeys.sort()
	ordered_imagelist = []
	for key in tiltkeys:
		imagedata = tiltangledict[key]
		mrc_name = imagedata['filename'] + '.mrc'
		fullname = os.path.join(imagepath, mrc_name)
		mrc_files.append(fullname)
		ordered_imagelist.append(imagedata)
	return tiltkeys,ordered_imagelist,mrc_files

def writeOrderedImageListCorrelation(imagelist, bin):
	fakenode = node.Node('fake',imagelist[0]['session'])
	correlator = tiltcorrelator.Correlator(fakenode, 0, 4,lpf=1.5)
	allpeaks = [{'x':0.0,'y':0.0}]
	tiltseries = imagelist[0]['tilt series']
	tiltangledict = {}
	correlationpeak = {}
	second_group = False 
	for imagedata in imagelist:
		tilt = imagedata['scope']['stage position']['a']*180/3.14159
		if tilt < tiltseries['tilt start']+0.01 and tilt > tiltseries['tilt start']-0.01:
			if second_group:
				direction=-tiltseries['tilt step']
			else:
				direction= tiltseries['tilt step']
				# switch group in getCorrelationPeak not here
				second_group = False
			tilt = tilt+0.001*direction
		try:
			correlationpeak[tilt],allpeaks,second_group = getCorrelationPeak(correlator,bin, tiltseries, tilt, imagedata,allpeaks,second_group)
		except:
			raise
			break
	fakenode.die()
	return correlationpeak

def getCorrelationPeak(correlator, bin, tiltseries, tilt, imagedata,allpeaks,second_group):
	q = leginondata.TomographyPredictionData(image=imagedata)
	results = q.query()
	if len(results) > 0:
		peak = results[0]['correlation']
	else:
		raise ValueError
	start = tiltseries['tilt start']
	if tilt < start:
		peak['x']=-peak['x']
		peak['y']=-peak['y']
	if tilt < tiltseries['tilt start']+0.01 and tilt > tiltseries['tilt start']-0.01:
		correlator.correlate(imagedata, tiltcorrection=True, channel=None)
		if second_group:
			allpeaks = [{'x':0.0,'y':0.0}]
			peak = correlator.getShift(False)
			if tiltseries['tilt step'] > 0:
				return (-peak['x']/bin,peak['y']/bin),allpeaks,second_group
			else:
				return (peak['x']/bin,-peak['y']/bin),allpeaks,second_group
		else:
			second_group = True
			return None,allpeaks,second_group
	allpeaks.append(peak)
	return ((peak['x']-allpeaks[-2]['x'])/bin,-(peak['y']-allpeaks[-2]['y'])/bin),allpeaks,second_group

def getTomographySettings(sessiondata,tiltdata):
	'''
	search for the last tomography node settings in the order of
	from the same session, from the same user, from default
	''' 
	timestamp = tiltdata.timestamp
	qtomo = leginondata.TomographySettingsData(session=sessiondata)
	tomosettingslist = qtomo.query()
	settingsdata = None
	for settings in tomosettingslist:
		if settings.timestamp < timestamp:
			settingsdata = dict(settings)
			break
	if settingsdata is None:
		sessionq = leginondata.SessionData(user=sessiondata['user'])
		qtomo = leginondata.TomographySettingsData(session=sessiondata)
		tomosettingslist = qtomo.query()
		for settings in tomosettingslist:
			if settings.timestamp < timestamp:
				settingsdata = dict(settings)
				break
	if settingsdata is None:
		qtomo = leginondata.TomographySettingsData(isdefault=True)
		tomosettingslist = qtomo.query()
		for settings in tomosettingslist:
			if settings.timestamp < timestamp:
				settingsdata = dict(settings)
				break
	if settingsdata is None:
		if tomosettingslist:
			settingsdata = dict(tomosettingslist[0])
		else:
			settingsdata = None
	return settingsdata

def getTomoPixelSize(imagedata):
	predq = leginondata.TomographyPredictionData(image=imagedata)
	results = predq.query(readimages=False)
	if results:
		print results[0]['pixel size']
		return results[0]['pixel size']

def	insertImodXcorr(rotation,filtersigma1,filterradius,filtersigma2):
			paramsq = appionData.ApImodXcorrParamsData()		
			paramsq['RotationAngle'] = rotation
			paramsq['FilterSigma1'] = filtersigma1
			paramsq['FilterRadius2'] = filterradius
			paramsq['FilterSigma2'] = filtersigma2
			results = paramsq.query()
			if not results:
				paramsq.insert()
			results = paramsq.query()
			return results[0]

def insertTomoAlignmentRun(sessiondata,tiltdata,leginoncorrdata,imodxcorrdata,bin):
	qalign = appionData.ApTomoAlignmentRunData(session=sessiondata,tiltseries=tiltdata,
		coarseLeginonParams=leginoncorrdata,coarseImodParams=imodxcorrdata,bin=bin)
	results = qalign.query()
	if not results:
		qalign.insert()
		results = qalign.query()
	return results[0]

def checkExistingFullTomoData(path,name):
	filepath = os.path.join(path,name+".rec")
	md5sum = apFile.md5sumfile(filepath)
	tomoq = appionData.ApFullTomogramData(md5sum = md5sum)
	results = tomoq.query()
	if not results:
		return None
	else:
		return results[0]
	
def insertFullTomogram(sessiondata,tiltdata,alignrun,path,name,description):
	tomoq = appionData.ApFullTomogramData()
	tomoq['session'] = sessiondata
	tomoq['tiltseries'] = tiltdata
	tomoq['alignment'] = alignrun
	tomoq['path'] = appionData.ApPathData(path=os.path.abspath(path))
	tomoq['name'] = name
	tomoq['description'] = description
	filepath = os.path.join(path,name+".rec")
	tomoq['md5sum'] = apFile.md5sumfile(filepath)
	tomoq.query()
	results = tomoq.query()
	if not results:
		tomoq.insert()
		return tomoq
	return results[0]

def getLastVolumeIndex(fulltomodata):
	tomoq = appionData.ApTomogramData(fulltomogram=fulltomodata)
	results = tomoq.query()
	if results:
		return results[0]['number']
	else:
		return 0

def insertSubTomogram(fulltomogram,center,dimension,path,name,index,pixelsize,description):
	tomoq = appionData.ApTomogramData()
	tomoq['session'] = fulltomogram['session']
	tomoq['tiltseries'] = fulltomogram['tiltseries']
	tomoq['fulltomogram'] = fulltomogram
	tomoq['path'] = appionData.ApPathData(path=os.path.abspath(path))
	tomoq['name'] = name
	tomoq['number'] = index
	tomoq['center'] = center
	tomoq['dimension'] = dimension
	tomoq['pixelsize'] = pixelsize
	tomoq['description'] = description
	filepath = os.path.join(path,name+".rec")
	tomoq['md5sum'] = apFile.md5sumfile(filepath)
	results = tomoq.query()	
	if not results:
		tomoq.insert()
		return tomoq
	return results[0]
