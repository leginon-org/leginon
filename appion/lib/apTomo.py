import os
import time
import subprocess
import numpy
from tomography import tiltcorrelator
import leginondata
from pyami import arraystats, mrc, imagefun, numpil
import appionData
try:
	import node
except:
	pass
import apDisplay
import apImage
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
		return paramsq
	return results[0]

def insertTomoAlignmentRun(sessiondata,tiltdata,leginoncorrdata,imodxcorrdata,bin,name):
	qalign = appionData.ApTomoAlignmentRunData(session=sessiondata,tiltseries=tiltdata,
			bin=bin,name=name)
	if leginoncorrdata:
		qalign['coarseLeginonParams'] = leginoncorrdata
	elif imodxcorrdata:
		qalign['coarseImodParams'] = imodxcorrdata
	results = qalign.query()
	if not results:
		qalign.insert()
		return qalign
	return results[0]

def checkExistingFullTomoData(path,name):
	filepath = os.path.join(path,name+".rec")
	if not os.path.isfile(filepath):
		return None
	md5sum = apFile.md5sumfile(filepath)
	tomoq = appionData.ApFullTomogramData(md5sum = md5sum)
	results = tomoq.query()
	if not results:
		return None
	else:
		return results[0]
	
def getFullTomoData(fulltomoId):
	return appionData.ApFullTomogramData.direct_query(fulltomoId)
	
def getTomogramData(tomoId):
	return appionData.ApTomogramData.direct_query(tomoId)
	
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

def transformParticleCenter(particle,bin,gtransform):
	#See imod manual for definition 
	# at http://bio3d.colorado.edu/imod/doc/serialalign.txt
	X = particle['xcoord']/bin
	Y = particle['ycoord']/bin
	A11 = gtransform[0]
	A12 = gtransform[1]
	A21 = gtransform[2]
	A22 = gtransform[3]
	DX = gtransform[4]
	DY = gtransform[5]
	newx = A11 * X + A12 * Y + DX
	newy = A21 * X + A22 * Y + DY
	return (newx,newy)

def insertSubTomogram(fulltomogram,center,dimension,path,runname,name,index,pixelsize,description):
	tomoq = appionData.ApTomogramData()
	tomoq['session'] = fulltomogram['session']
	tomoq['tiltseries'] = fulltomogram['tiltseries']
	tomoq['fulltomogram'] = fulltomogram
	tomoq['path'] = appionData.ApPathData(path=os.path.abspath(path))
	tomoq['name'] = name
	tomoq['runname'] = runname
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

def array2jpg(pictpath,im,imin=None,imax=None,size=512):
	jpgpath = pictpath+'.jpg'
	imshape = im.shape
	scale = float(size)/max((imshape[0],imshape[1]))
	im = apImage.scaleImage(im,scale)	
	stats = arraystats.all(im)
	if imin is not None and imax is not None:
		range = (imin,imax)
	else:
		range = stats['mean']-3*stats['std'],stats['mean']+3*stats['std']
	numpil.write(im,jpgpath, format = 'JPEG', limits=range)

def makeMovie(filename,moviesize):
	mrcpath = filename
	splitnames =  os.path.splitext(mrcpath)
	rootpath = splitnames[0]
	array = mrc.read(mrcpath)
	stats = arraystats.all(array)
	print stats
	dims = array.shape
	#dimz = dims[0]
	for axis in (0,1):
		dimz = dims[axis]
		#generate a sequence of jpg images, each is an average of 5 slices	
		for i in range(0, dimz):   
			pictpath = rootpath+'_avg%05d' % i
			ll = max(0,i - 2)
			hh = min(dimz,i + 3)
			if axis == 0:
				axisname = 'z'
				slice = numpy.sum(array[ll:hh,:,:],axis=axis)/(hh-ll)
			else:
				axisname = 'y'
				slice = numpy.sum(array[:,ll:hh,:],axis=axis)/(hh-ll)
			# adjust and shrink each image
			array2jpg(pictpath,slice,stats['mean']-3*stats['std'],stats['mean']+3*stats['std'],moviesize)
			#array2jpg(pictpath,slice,size=moviesize)
		cmd = 'mencoder -nosound -mf type=jpg:fps=24 -ovc lavc -lavcopts vcodec=flv -of lavf -lavfopts format=flv -o minitomo'+axisname+'.flv "mf://'+rootpath+'_avg*.jpg"'
		proc = subprocess.Popen(cmd, shell=True)
		proc.wait()
		os.system('rm '+rootpath+'_avg*.jpg')
