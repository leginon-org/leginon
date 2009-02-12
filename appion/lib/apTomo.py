import os
import time
import subprocess
import numpy
import scipy.ndimage as nd
from tomography import tiltcorrelator
import leginondata
from pyami import arraystats, mrc, imagefun, numpil
import appionData
import libCVwrapper
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
		apDisplay.printWarning('No images in image list.')
		return
	mrc_files = []
	imagepath = imagelist[0]['session']['image path']
	tiltseries = imagelist[0]['tilt series']
	tiltangledict = {}
	for i,imagedata in enumerate(imagelist):
		tilt = imagedata['scope']['stage position']['a']*180/3.14159
		if tilt < tiltseries['tilt start']+0.01 and tilt > tiltseries['tilt start']-0.01:
			nextimagedata = imagelist[i+1]
			nexttilt = nextimagedata['scope']['stage position']['a']*180/3.14159
			direction = (nexttilt - tilt)
			# switch group in getCorrelationPeak not here
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

def getOrderedImageListCorrelation(imagelist, bin):
	fakenode = node.Node('fake',imagelist[0]['session'])
	correlator = tiltcorrelator.Correlator(fakenode, 0, 4,lpf=1.5)
	allpeaks = [{'x':0.0,'y':0.0}]
	tiltseries = imagelist[0]['tilt series']
	tiltangledict = {}
	correlationpeak = {}
	second_group = False 
	for i,imagedata in enumerate(imagelist):
		tilt = imagedata['scope']['stage position']['a']*180/3.14159
		if tilt < tiltseries['tilt start']+0.01 and tilt > tiltseries['tilt start']-0.01:
			nextimagedata = imagelist[i+1]
			nexttilt = nextimagedata['scope']['stage position']['a']*180/3.14159
			direction = (nexttilt - tilt)
				# switch group in getCorrelationPeak not here
			if i == 0:
				second_group = False
			tilt = tilt+0.001*direction
		try:
			correlationpeak[tilt],allpeaks,second_group = getCorrelationPeak(correlator,bin, tiltseries, tilt, imagedata,allpeaks,second_group)
		except:
			raise
			break
	fakenode.die()
	return correlationpeak

def getOrderedImageListTransform(ordered_imagelist, bin):
	transformlist = []
	shape = ordered_imagelist[0]['image'].shape
	minsize = 40
	for i,imagedata in enumerate(ordered_imagelist):
		if i == 0:
			array1 = imagedata['image']
		array2 = imagedata['image']
		print imagedata['filename'],minsize
		resultmatrix = libCVwrapper.MatchImages(array1, array2, minsize=minsize, maxsize=0.9,  WoB=True, BoW=True)
		if abs(resultmatrix[0,0]) < 0.01 and abs(resultmatrix[0,1] < 0.01):
			resultmatrix[0,0]=1.0
			resultmatrix[1,0]=0.0
			resultmatrix[0,1]=0.0
			resultmatrix[0,0]=1.0
			resultmatrix[2,0]=0.0
			resultmatrix[2,1]=0.0
			resultmatrix[2,2]=1.0
		matrix = transform
		matrix[0,0] = transform[1,1]
		matrix[0,1] = transform[1,]
		matrix[0,0] = transform[1,1]
		matrix[0,1] = -transform[1,0]
		matrix[1,0] = transform[0,1]
		matrix[1,1] = transform[0,0]
		matrix[2,0] = -transform[2,1]/bin
		matrix[2,1] = -transform[2,0]/bin
		transformlist.append(resultmatrix)
		array1 = imagedata['image']
	return transformlist
	
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
	settingsid = None
	for settings in tomosettingslist:
		if settings.timestamp < timestamp:
			settingid = settings.dbid
			break
	if settingsid is None:
		sessionq = leginondata.SessionData(user=sessiondata['user'])
		qtomo = leginondata.TomographySettingsData(session=sessiondata)
		tomosettingslist = qtomo.query()
		for settings in tomosettingslist:
			if settings.timestamp < timestamp:
				settingsid = settings.dbid
				break
	if settingsid is None:
		qtomo = leginondata.TomographySettingsData(isdefault=True)
		tomosettingslist = qtomo.query()
		for settings in tomosettingslist:
			if settings.timestamp < timestamp:
				settingsid = settings.dbid
				break
	if settingsid is None:
		if tomosettingslist:
			settingsid = tomosettingslist[0].dbid
		else:
			settingsid = None
	if settingsid:
		print settingsid
		qtomo = leginondata.TomographySettingsData()
		return qtomo.direct_query(settingsid)

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
	tomoq = appionData.ApFullTomogramData(name = name)
	results = tomoq.query()
	if not results:
		return None
	filepath = os.path.join(path,name+".rec")
	if not os.path.isfile(filepath):
		return None
	# This takes too long
	#md5sum = apFile.md5sumfile(filepath)
	#tomoq = appionData.ApFullTomogramData(md5sum = md5sum)
	#results = tomoq.query()
	#if not results:
	#	return None
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

def insertSubTomogram(fulltomogram,center,offsetz,dimension,path,runname,name,index,pixelsize,description):
	tomoq = appionData.ApTomogramData()
	tomoq['session'] = fulltomogram['session']
	tomoq['tiltseries'] = fulltomogram['tiltseries']
	tomoq['fulltomogram'] = fulltomogram
	tomoq['path'] = appionData.ApPathData(path=os.path.abspath(path))
	tomoq['name'] = name
	tomoq['runname'] = runname
	tomoq['number'] = index
	tomoq['center'] = center
	tomoq['offsetz'] = offsetz
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
	scale = float(size)/imshape[1]
	im = apImage.scaleImage(im,scale)	
	stats = arraystats.all(im)
	if imin is not None and imax is not None:
		range = (imin,imax)
	else:
		range = stats['mean']-3*stats['std'],stats['mean']+3*stats['std']
	numpil.write(im,jpgpath, format = 'JPEG', limits=range)

def makeMovie(filename,xsize=512):
	apDisplay.printMsg('Making movie','blue')
	mrcpath = filename
	dirpath = os.path.dirname(mrcpath)
	splitnames =  os.path.splitext(mrcpath)
	rootpath = splitnames[0]
	apDisplay.printMsg('Reading 3D recon %s' % mrcpath)
	array = mrc.read(mrcpath)
	print "image read"
	shape = array.shape
	xsize = min(xsize,shape[2])
	stats = {}
	# speed up stats calculation by projecting to axis 0 to reduce array dimension
	apDisplay.printMsg('Calculating stats...')
	slice = numpy.sum(array[:,:,:],axis=0)/shape[0]
	stats['std'] = slice.std()
	stats['mean'] = slice.mean()
	if shape[0] > shape[1]:
		renders = {'a':{'axis':0,'axisname':'z'},'b':{'axis':1,'axisname':'y'}}
	else:
		renders = {'a':{'axis':1,'axisname':'y'},'b':{'axis':0,'axisname':'z'}}
	keys = renders.keys()
	keys.sort()
	for key in keys:
		axis = renders[key]['axis']
		dimz = shape[axis]
		#generate a sequence of jpg images, each is an average of 5 slices	
		apDisplay.printMsg('Making smoothed slices...')
		for i in range(0, dimz):   
			pictpath = rootpath+'_avg%05d' % i
			ll = max(0,i - 2)
			hh = min(dimz,i + 3)
			if axis == 0:
				slice = numpy.sum(array[ll:hh,:,:],axis=axis)/(hh-ll)
			else:
				slice = numpy.sum(array[:,ll:hh,:],axis=axis)/(hh-ll)
			# adjust and shrink each image
			array2jpg(pictpath,slice,stats['mean']-8*stats['std'],stats['mean']+8*stats['std'],xsize)
		apDisplay.printMsg('Putting the jpg files together to flash video...')
		moviename = dirpath+'/minitomo%s'%key+'.flv'
		cmd = 'mencoder -nosound -mf type=jpg:fps=24 -ovc lavc -lavcopts vcodec=flv -of lavf -lavfopts format=flv -o '+moviename+' "mf://'+rootpath+'_avg*.jpg"'
		proc = subprocess.Popen(cmd, shell=True)
		proc.wait()
		os.system('rm '+rootpath+'_avg*.jpg')

def makeProjection(filename,xsize=512):
	mrcpath = filename
	dirpath = os.path.dirname(mrcpath)
	apDisplay.printMsg('Reading 3D recon %s' % mrcpath)
	array = mrc.read(mrcpath)
	shape = array.shape
	xsize = min(xsize,shape[2])
	if shape[0] > shape[1]:
		renders = {'a':{'axis':0,'axisname':'z'},'b':{'axis':1,'axisname':'y'}}
	else:
		renders = {'a':{'axis':1,'axisname':'y'},'b':{'axis':0,'axisname':'z'}}
	keys = renders.keys()
	keys.sort()
	for key in keys:
		apDisplay.printMsg('project to axis %s' % renders[key]['axisname'])
		pictpath = dirpath+'/projection'+key
		axis = renders[key]['axis']
		slice = numpy.sum(array[:,:,:],axis=axis)/(shape[axis])
		print "sum done"
		# adjust and shrink each image
		mrc.write(slice,pictpath+'.mrc')
		array2jpg(pictpath,slice,size=xsize)
