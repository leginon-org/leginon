import os
import time
import subprocess
import shutil
import numpy
import scipy.ndimage as ndimage
from tomography import tiltcorrelator
import leginondata
from pyami import arraystats, mrc, imagefun, numpil,correlator, peakfinder
import appionData
import libCVwrapper
try:
	import node
except:
	pass
import apDatabase
import apDisplay
import apImage
import apFile
import apEMAN

def getFilename(tiltserieslist):
	seriesname = tiltserieslist[0]['session']['name']+'_'
	names = []
	for tiltseriesdata in tiltserieslist:
		# determine param filename
		seriesnumber = tiltseriesdata['number']
		numberstr = '%03d' % (seriesnumber,)
		names.append(numberstr)
	seriesname += '+'.join(names)
	return seriesname

def getFirstImage(tiltseries):
	tiltlist = [tiltseries,]
	imagelist = getImageList(tiltlist)
	return imagelist[0]

def getImageList(tiltserieslist):
	imagelist = []
	for tiltseriesdata in tiltserieslist:
		imquery = leginondata.AcquisitionImageData()
		imquery['tilt series'] = tiltseriesdata
		## query, but don't read image files yet, or else run out of memory
		subimagelist = imquery.query(readimages=False)
		## list is reverse chronological, so reverse it
		subimagelist.reverse()
		realist = []
		imagelist.extend(subimagelist)
	for imagedata in imagelist:
		if imagedata['label'] != 'projection':
			realist.append(imagedata)
	return realist
	
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

def getFeatureMatchTransform(ordered_imagelist, bin):
	xfname = os.path.join('/ami/data15/appion/08jun11b/tomo/tiltseries3/full3/08jun11b_003'+'.prexf')
	transformlist = []
	shape = ordered_imagelist[0]['image'].shape
	minsize = 250
	for i,imagedata in enumerate(ordered_imagelist):
		f = open(xfname, 'a')
		if i == 0:
			array1 = imagedata['image']
		array2 = imagedata['image']
		print imagedata['filename'],minsize
		resultmatrix = libCVwrapper.MatchImages(array2, array1, minsize=minsize, maxsize=0.9,  WoB=True, BoW=True)
		if abs(resultmatrix[0,0]) < 0.9 :
			resultmatrix[0,0]=1.0
			resultmatrix[1,0]=0.0
			resultmatrix[0,1]=0.0
			resultmatrix[0,0]=1.0
			shift = simpleCorrelation(array2,array1)
			resultmatrix[2,0]=shift[0]
			resultmatrix[2,1]=shift[1]
			resultmatrix[2,2]=1.0
		matrix = numpy.zeros((3,3))
		matrix[2,2] = 1.0
		matrix[0,0] = resultmatrix[1,1]
		matrix[0,1] = resultmatrix[1,0]
		matrix[1,0] = resultmatrix[0,1]
		matrix[1,1] = resultmatrix[0,0]
		matrix[2,0] = resultmatrix[2,1]-shape[1]*(1-resultmatrix[1,0]-resultmatrix[1,1])
		matrix[2,1] = resultmatrix[2,0]-shape[0]*(1-resultmatrix[0,0]-resultmatrix[0,1])
		f.write('%11.7f %11.7f %11.7f %11.7f %11.3f %11.3f\n' % (
			matrix[0,0],matrix[0,1],
			matrix[1,0],matrix[1,1],
			matrix[2,0],matrix[2,1]))
		print matrix
		transformlist.append(matrix)
		array1 = imagedata['image']
		f.close()
	return transformlist

def simpleCorrelation(array1,array2):
	c = correlator.Correlator()
	p = peakfinder.PeakFinder()
	c.setImage(0,array1)
	c.setImage(1,array2)
	shape = array1.shape
	corrimage = c.phaseCorrelate()
	p.setImage(corrimage)
	peak = peakfinder.findPixelPeak(corrimage)
	shift = [0,0]
	for i in (0,1):
		if peak['pixel peak'][i] > shape[i]/2:
			shift[i] = peak['pixel peak'][i] - shape[i]
		else:
			shift[i] = peak['pixel peak'][i]
	return shift
		
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
		qtomo = leginondata.TomographySettingsData()
		return qtomo.direct_query(settingsid)

def getTomoPixelSize(imagedata):
	imageq = leginondata.AcquisitionImageData(emtarget=imagedata['emtarget'])
	imageresults = imageq.query(readimages=False)
	for tomoimagedata in imageresults:
		if tomoimagedata['label'] != 'projection':
			predq = leginondata.TomographyPredictionData(image=tomoimagedata)
			results = predq.query(readimages=False)
			if results:
				return results[0]['pixel size']

def getTomoImageShape(imagedata):
	return (imagedata['camera']['dimension']['y'],imagedata['camera']['dimension']['x'])

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

def insertSubTomoRun(sessiondata,selectionrunid,stackid,name,invert=False,subbin=1):
	if selectionrunid:
		qpick = appionData.ApSelectionRunData()
		pickdata = qpick.direct_query(selectionrunid)
	else:
		pickdata = None
	if stackid:
		qstack = appionData.ApStackData()
		stackdata = qstack.direct_query(stackid)
	else:
		stackdata = None
	qrun = appionData.ApSubTomogramRunData(session=sessiondata,
			pick=pickdata,stack=stackdata,runname=name,invert=invert,subbin=subbin)
	results = qrun.query()
	if not results:
		qrun.insert()
		return qrun
	return results[0]

def checkExistingFullTomoData(path,name):
	pathq = appionData.ApPath(name=path)
	tomoq = appionData.ApFullTomogramData(name=name,path=pathq)
	results = tomoq.query()
	if not results:
		return None
	filepath = os.path.join(path,name+".rec")
	if not os.path.isfile(filepath):
		return None
	else:
		return results[0]
	
def getFullTomoData(fulltomoId):
	return appionData.ApFullTomogramData.direct_query(fulltomoId)
	
def getTomogramData(tomoId):
	return appionData.ApTomogramData.direct_query(tomoId)
	
def insertTomo(params):
	if not params['commit']:
		apDisplay.printWarning("not commiting tomogram to database")
		return
	apDisplay.printMsg("Commiting tomogram to database")
	sessiondata = apDatabase.getSessionDataFromSessionName(params['session'])
	tiltdata = apDatabase.getTiltSeriesDataFromTiltNumAndSessionId(params['tiltseriesnumber'],sessiondata)
	runname = params['runname']
	name = params['name']
	if params['full']:
		fullbin = params['bin']
	else:
		fullbin = 1
		subbin = params['bin']
	aligndata = insertTomoAlignmentRun(sessiondata,tiltdata,None,None,fullbin,runname)
	firstimagedata = getFirstImage(tiltdata)
	path = os.path.abspath(params['rundir'])
	description = params['description']
	tiltdatalist = [tiltdata,]
	alignlist = [aligndata,]
	if params['full']:
		uploadfile = params['zprojfile']
		projectimagedata = uploadZProjection(runname,firstimagedata,uploadfile)
		return insertFullTomogram(sessiondata,tiltdatalist,alignlist,path,name,description,projectimagedata)
	else:
		projectimagedata = None
		fulltpath = params['rundir'].replace('/'+params['volume'],'')
		dummyname = 'dummy'
		dummydescription = 'fake full tomogram for subtomogram upload'
		fulltomogram = insertFullTomogram(sessiondata,tiltdatalist,alignlist,fulltpath,dummyname,dummydescription,projectimagedata)
		apix = apDatabase.getPixelSize(firstimagedata)
		tomoq = appionData.ApTomogramData()
		tomoq['session'] = sessiondata
		tomoq['tiltseries'] = tiltdata
		results = tomoq.query()
		index = len(results)+1
		pixelsize = 1e-10 * apix * params['bin']
		runname = params['volume']
		shape = map((lambda x: x * params['bin']), params['shape'])
		dimension = {'x':shape[2],'y':shape[1], 'z':shape[0]}
		subtomorundata = apTomo.insertSubTomoRun(sessiondata,
				None,None,runname,params['invert'],subbin)
		return insertSubTomogram(fulltomogram,subtomorundata,None,0,dimension,path,name,index,pixelsize,description)

def insertFullTomogram(sessiondata,tiltdatalist,alignlist,path,name,description,projectimagedata):
	tomoq = appionData.ApFullTomogramData()
	tomoq['session'] = sessiondata
	tomoq['tiltseries'] = tiltdatalist[0]
	tomoq['alignment'] = alignlist[0]
	tomoq['path'] = appionData.ApPathData(path=os.path.abspath(path))
	tomoq['name'] = name
	tomoq['description'] = description
	tomoq['zprojection'] = projectimagedata
	if len(tiltdatalist) > 1:
		idlist = []
		for align in alignlist:
			idlist.append(align.dbid)
		tomoq['combined'] = idlist
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
	X = particle['xcoord']
	Y = particle['ycoord']
	A11 = gtransform[0]
	A12 = gtransform[1]
	A21 = gtransform[2]
	A22 = gtransform[3]
	DX = gtransform[4]
	DY = gtransform[5]
	newx = A11 * X + A12 * Y + DX
	newy = A21 * X + A22 * Y + DY
	return (newx/bin,newy/bin)

def insertSubTomogram(fulltomodata,rundata,center,offsetz,dimension,path,name,index,pixelsize,description):
	tomoq = appionData.ApTomogramData(fulltomogram=fulltomodata)
	tomoq['session'] = fulltomodata['session']
	tomoq['tiltseries'] = fulltomodata['tiltseries']
	tomoq['subtomorun'] = rundata
	tomoq['path'] = appionData.ApPathData(path=os.path.abspath(path))
	tomoq['name'] = name
	tomoq['number'] = index
	tomoq['center'] = center
	# dimension is that of the original tilt images, i.e., before binning of the full tomogram
	tomoq['offsetz'] = offsetz
	tomoq['dimension'] = dimension
	# pixelsize is of the binned full and sub tomogram
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
		subprocess.Popen('rm '+rootpath+'_avg*.jpg', shell=True)

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
		pictpath = os.path.join(dirpath,'projection'+key)
		axis = renders[key]['axis']
		slice = numpy.sum(array[:,:,:],axis=axis)/(shape[axis])
		mrc.write(slice,pictpath+'.mrc')
		# adjust and shrink each image
		array2jpg(pictpath,slice,size=xsize)

def uploadZProjection(runname,initialimagedata,uploadfile):
	presetdata = leginondata.PresetData(initializer=initialimagedata['preset'])
	presetdata['name']='Zproj'
	imagedata = leginondata.AcquisitionImageData(initializer=initialimagedata)
	basename = os.path.basename(uploadfile)
	splitname = os.path.splitext(basename)
	names = splitname[0].split('_zproject')
	projectionname = names[0]+'_'+runname+'_zproject'
	imagedata['filename']=projectionname
	imagedata['label'] = 'projection'
	imagedata['preset'] = presetdata
	newimgfilepath = os.path.join(imagedata['session']['image path'],projectionname)
	apDisplay.printMsg("Copying original image to a new location: "+newimgfilepath)
	shutil.copyfile(uploadfile, newimgfilepath)
	image = mrc.read(newimgfilepath)
	imagedata['image'] = image
	results = imagedata.query()
	if not results:
		imagedata.insert()
		return imagedata
	return imagedata[0]

def getSubvolumeShape(subtomorundata):
	tomoq = appionData.ApTomogramData(subtomorun=subtomorundata)
	results = tomoq.query(results=1)
	if results:
		tomo = results[0]
		shape = (tomo['dimension']['z'],tomo['dimension']['y'],tomo['dimension']['x'])
		return shape

def getFullZSubvolume(subtomorundata,stackpdata):
	pdata = stackpdata['particle']
	tomoq = appionData.ApTomogramData(subtomorun=subtomorundata,center=pdata)
	results = tomoq.query()
	if results:
		tomo = results[0]
		print tomo['center']['xcoord']
		if tomo['center']['xcoord'] < 800 or tomo['center']['xcoord'] > 1150:
			return None
		if tomo['center']['ycoord'] < 800 or tomo['center']['ycoord'] > 1250:
			return None
		path = tomo['path']['path']
		name = tomo['name']+'.rec'
		print name
		volume = mrc.read(os.path.join(path,name))
		return volume

def getParticleCenterZProfile(subvolume,shift,halfwidth):
	shape = subvolume.shape
	ystart = max(0,int(shape[1]/2.0 - shift['y'] - halfwidth))
	xstart = max(0,int(shape[1]/2.0 - shift['x'] - halfwidth))
	yend = min(shape[1],ystart + 2 * halfwidth + 1)
	xend = min(shape[2],xstart + 2 * halfwidth + 1)
	array = subvolume[:,ystart:yend,xstart:xend]
	xavg = numpy.sum(array,axis=2)/(2*halfwidth+1)
	xyavg = numpy.sum(xavg,axis=1)/(2*halfwidth+1)
	bgwidth = 35
	background = numpy.sum(xyavg[:bgwidth])/bgwidth
	background += numpy.sum(xyavg[-bgwidth:])/bgwidth
	background = background / 2
	vmax = xyavg.max()
	return (xyavg - background) / (vmax-background)

def transformTomo(a,package,alignpdata,zshift=0.0):
	shift = (alignpdata['xshift'],alignpdata['yshift'],zshift)
	angle = alignpdata['rotation']
	mirror = alignpdata['mirror']
	print shift,angle,mirror
	if package == 'Xmipp':
		return xmippTransformTomo(a,angle,shift,mirror,2)
	elif package == 'Spider':
		return xmippTransformTomo(a,angle,shift,mirror,2)

def xmippTransformTomo(a,rot=0,shift=(0,0,0), mirror=False, order=2):
	"""
		similar to apImage.xmippTransform but on 3D volume and rotate on the
		xy plane
	"""
	b = a
	shiftxyz = (shift[2],shift[1],shift[0])
	b = ndimage.shift(b, shift=shiftxyz, mode='reflect', order=order)
	if mirror is True:
		b = numpy.fliplr(b)
	b = ndimage.shift(b, shift=(0,-0.5,-0.5), mode='wrap',order=order)
	b = ndimage.rotate(b, angle=-1*rot, axes=(2,1), reshape=False, order=order)
	b = ndimage.shift(b, shift=(0, 0.5, 0.5), mode='wrap',order=order)
	return b
	

def gaussianCenter(array):
	X = numpy.arange(array.size)
	#ignore negative shadow
	array = numpy.where(array < 0, 0,array)
	return numpy.sum(X*array)/numpy.sum(array)

def modifyVolume(volpath,bin=1,invert=False):
	volpathtemp = volpath+".tmp.mrc"
	if invert:
		multfactor = -1.0
	else:
		multfactor = 1.0
	lpcmd = ('proc3d %s %s shrink=%d mult=%e' % (volpath,volpathtemp,bin,multfactor))
	apDisplay.printMsg("modifying 3d volume with EMAN")
	apEMAN.executeEmanCmd(lpcmd)
	if os.path.exists(volpathtemp):
		shutil.move(volpathtemp,volpath)
