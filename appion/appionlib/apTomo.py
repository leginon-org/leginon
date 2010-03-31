import os
import time
import math
import subprocess
import shutil
import numpy
import scipy.ndimage as ndimage
try:
	from tomography import tiltcorrelator
	no_wx = False
except:
	no_wx = True
import leginon.leginondata
from pyami import arraystats, mrc, imagefun, numpil,correlator, peakfinder
from appionlib import appiondata
from leginon import libCVwrapper
try:
	import node
except:
	pass
from appionlib import apDatabase
from appionlib import apDisplay
from appionlib import apImage
from appionlib import apFile
from appionlib import apEMAN
from appionlib.apSpider import volFun

def getTiltdataList(tiltseriesdata,othertiltdata=None):
		if othertiltdata is None:
			tiltdatalist = [tiltseriesdata]
		else:
			tiltdatalist = [tiltseriesdata,othertiltdata]
			apDisplay.printMsg('Combining images from two tilt series')
		return tiltdatalist

def getExcludedImageIds(ordered_imagelist,excludelist):
	excludeids = []
	for i in excludelist:
		excludeids.append(ordered_imagelist[i].dbid)
	return excludeids

def getAlignerdata(alignerid):
	q = appiondata.ApTomoAlignerParamsData()
	alignerdata = q.direct_query(alignerid)
	return alignerdata

def getAlignmentFromDB(alignerdata,center):
	q = appiondata.ApProtomoModelData(aligner=alignerdata)
	results = q.query(results=1)
	model = results[0]
	specimen_euler = {'psi':model['psi'],'theta':model['theta'],'phi':model['phi']}
	tiltaz = model['azimuth']
	q = appiondata.ApProtomoAlignmentData(aligner=alignerdata)
	results = q.query()
	results.reverse()
	origins = []
	rotations = []
	for r in results:
		origins.append((r['shift']['x']+center['x'],r['shift']['y']+center['y']))
		rotations.append(r['rotation'])
	return specimen_euler, tiltaz, origins, rotations

def getTiltListFromAligner(alignerid):
	alignerdata = getAlignerdata(alignerid)
	q = appiondata.ApTiltsInAlignRunData(alignrun=alignerdata['alignrun'])
	results = q.query()
	for i,result in enumerate(results):
		if result['primary']:
			primkey = i
			break
	tiltdatalist = [results[primkey]['tiltseries'],]
	del results[primkey]
	for r in results:
		tiltdatalist.append(r['tiltseries'])
	return tiltdatalist

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
		imquery = leginon.leginondata.AcquisitionImageData()
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
	'''This is complex because the two start tilt images are often sorted wrong if
			just use alpha tilt.  Therefore, a fake alpha tilt value is created based
			on the tilt image collected next in time
	'''
	if not imagelist:
		apDisplay.printWarning('No images in image list.')
		return
	mrc_files = []
	imagepath = imagelist[0]['session']['image path']
	tiltseries = imagelist[0]['tilt series']
	tiltangledict = {}
	reftilts = []
	for i,imagedata in enumerate(imagelist):
		tilt = imagedata['scope']['stage position']['a']*180/3.14159
		if tilt < tiltseries['tilt start']+0.02 and tilt > tiltseries['tilt start']-0.02:
			qimage = leginon.leginondata.AcquisitionImageData()
			nextimagedata = imagelist[i+1]
			nexttilt = nextimagedata['scope']['stage position']['a']*180/3.14159
			direction = (nexttilt - tilt)
			# switch group in getCorrelationPeak not here
			tilt = tilt+0.02*direction
			reftilts.append(tilt)
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
	if len(reftilts) > 2:
		apDisplay.printError('Got too many images at the start tilt')
	refimg = tiltkeys.index(max(reftilts))
	#cut down for testing
	testing = False
	if not testing:
		return tiltkeys,ordered_imagelist,mrc_files,refimg
	else:
		print len(tiltkeys),refimg
		cut = refimg-1
		cut2 = len(tiltkeys) -refimg -1
		cutlist = ordered_imagelist[cut:-cut2]
		cuttilts = tiltkeys[cut:-cut2]
		cutfiles = mrc_files[cut:-cut2]
		refimg = refimg - cut 
		print len(cutlist),refimg
		return cuttilts,cutlist,cutfiles,refimg

def getCorrelatorBinning(imageshape):
	origsize = max((imageshape[1],imageshape[0]))
	max_newsize = 512
	if origsize > max_newsize:
		## new size can be bigger than origsize, no binning needed
		bin = origsize / max_newsize
		remain = origsize % max_newsize
		while remain:
			bin += 1
			remain = origsize % bin
			newsize = float(origsize) / bin
		correlation_bin = bin
	else:
		correlation_bin = 1
	return correlation_bin
	
def writeTiltSeriesStack(stackdir,stackname,ordered_mrc_files):
		stackpath = os.path.join(stackdir, stackname)
		print stackpath
		if os.path.exists(stackpath):
			stheader = mrc.readHeaderFromFile(stackpath)
			stshape = stheader['shape']
			imageheader = mrc.readHeaderFromFile(ordered_mrc_files[0])
			imageshape = imageheader['shape']
			if stshape[1:] == imageshape and stshape[0] == len(ordered_mrc_files):
				apDisplay.printMsg("No need to get new stack of the tilt series")
			else:
				apImage.writeMrcStack(stackdir,stackname,order3dmrc_files, 1)
		else:
			apImage.writeMrcStack(stackdir,stackname,ordered_mrc_files, 1)

def calcRelativeShifts(globalshift):
	relativeshifts = []
	for i, shift in enumerate(globalshift):
		relativeshifts.append({'x':0.0, 'y':0.0})
		if i > 0:
			relativeshifts[i]['x'] = globalshift[i]['x'] - globalshift[i-1]['x'] 
			relativeshifts[i]['y'] = globalshift[i]['y'] - globalshift[i-1]['y']
	return relativeshifts 

def getLeginonRelativeShift(ordered_imagelist, bin, refimg):
	globalshift = getGlobalShift(ordered_imagelist, bin, refimg)
	relativeshifts = calcRelativeShifts(globalshift)
	return relativeshifts

def alignZeroShiftImages(imagedata1,imagedata2,bin):
	"""Align start-angle images for tilt series where data is collect in two halves"""
	no_wx=True
	bin = int(bin)
	if not no_wx:
		# Tilt correlator needs wx which is not available on the cluster
		# This method is consistent with the rest of leginonxcorr and will
		# revert correction channels is needed even though it is likely
		# unnecessary
		fakenode = node.Node('fake',imagedata1['session'])
		correlator = tiltcorrelator.Correlator(fakenode, 0, bin,lpf=1.5)
		for imagedata in (imagedata1,imagedata2):
			correlator.correlate(imagedata, tiltcorrection=True, channel=None)
		peak = correlator.getShift(False)
		fakenode.die()
	else:
		# phase correlation
		array1 = imagedata1['image']
		array2 = imagedata2['image']
		if bin != 1:
			array1 = imagefun.bin(array1, bin)
			array2 = imagefun.bin(array2, bin)
		shift = simpleCorrelation(array1,array2)
		peak = {'x':-shift[1]*bin,'y':shift[0]*bin}
		
	# x (row) shift on image coordinate is of opposite sign
	return {'shiftx':-peak['x'], 'shifty':peak['y']}

def peak2shift(peak, shape):
	#copied from tomography tiltcorrelator
	shift = list(peak)
	half = shape[0] / 2.0, shape[1] / 2.0
	if peak[0] > half[0]:
		shift[0] = peak[0] - shape[0]
	if peak[1] > half[1]:
		shift[1] = peak[1] - shape[1]
	return tuple(shift)

def shiftHalfSeries(zeroshift,globalshifts, refimg):
	apDisplay.printMsg("shifting images between the two tilt groups")
	for i,shift in enumerate(globalshifts[:refimg]):
		globalshifts[i]['x']=shift['x']+zeroshift['shiftx']
		globalshifts[i]['y']=shift['y']+zeroshift['shifty']
	return globalshifts

def getGlobalShift(ordered_imagelist, corr_bin, refimg):
	apDisplay.printMsg("getting global shift values")
	globalshifts = []
	for i, imagedata in enumerate(ordered_imagelist):
		globalshifts.append(getPredictionPeakForImage(imagedata))
	zeroshift = alignZeroShiftImages(ordered_imagelist[refimg],ordered_imagelist[refimg-1],corr_bin)
	globalshifts = shiftHalfSeries(zeroshift, globalshifts, refimg)
	return globalshifts
		
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
	peak = peakfinder.findSubpixelPeak(corrimage,lpf=1.5)
	shift = [0.0,0.0]
	for i in (0,1):
		if peak['subpixel peak'][i] > shape[i]/2:
			shift[i] = peak['subpixel peak'][i] - shape[i]
		else:
			shift[i] = peak['subpixel peak'][i]
	return shift

def getPredictionPeakForImage(imagedata):
	q = leginon.leginondata.TomographyPredictionData()
	q['image'] = imagedata
	results = q.query()
	if len(results) > 0:
		peak = results[0]['correlation']
	else:
		raise ValueError
	# x (row) shift on image coordinate is of opposite sign
	peak['x'] = - peak['x']
	return peak

def getCorrelationPeak(correlator, bin, tiltseries, tilt, imagedata,allpeaks,second_group):
	peak = getPredictionPeakForImage(imagedata)
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
	return {'x':(peak['x']-allpeaks[-2]['x'])/bin, 'y':-(peak['y']-allpeaks[-2]['y'])/bin},allpeaks,second_group

def getTomographySettings(sessiondata,tiltdata):
	'''
	search for the last tomography node settings in the order of
	from the same session, from the same user, from default
	'''
	timestamp = tiltdata.timestamp
	qtomo = leginon.leginondata.TomographySettingsData(session=sessiondata)
	tomosettingslist = qtomo.query()
	settingsid = None
	for settings in tomosettingslist:
		if settings.timestamp < timestamp:
			settingid = settings.dbid
			break
	if settingsid is None:
		sessionq = leginon.leginondata.SessionData(user=sessiondata['user'])
		qtomo = leginon.leginondata.TomographySettingsData(session=sessiondata)
		tomosettingslist = qtomo.query()
		for settings in tomosettingslist:
			if settings.timestamp < timestamp:
				settingsid = settings.dbid
				break
	if settingsid is None:
		qtomo = leginon.leginondata.TomographySettingsData(isdefault=True)
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
		qtomo = leginon.leginondata.TomographySettingsData()
		return qtomo.direct_query(settingsid)

def getTomoPixelSize(imagedata):
	imageq = leginon.leginondata.AcquisitionImageData(emtarget=imagedata['emtarget'])
	imageresults = imageq.query(readimages=False)
	for tomoimagedata in imageresults:
		if tomoimagedata['label'] != 'projection':
			predq = leginon.leginondata.TomographyPredictionData(image=tomoimagedata)
			results = predq.query(readimages=False)
			if results:
				return results[0]['pixel size']

def getTomoImageShape(imagedata):
	return (imagedata['camera']['dimension']['y'],imagedata['camera']['dimension']['x'])

def	insertImodXcorr(rotation,filtersigma1,filterradius,filtersigma2):
	paramsq = appiondata.ApImodXcorrParamsData()
	paramsq['RotationAngle'] = rotation
	paramsq['FilterSigma1'] = filtersigma1
	paramsq['FilterRadius2'] = filterradius
	paramsq['FilterSigma2'] = filtersigma2
	return publish(paramsq)

def	insertTiltsInAlignRun(alignrundata,tiltdata,settingsdata,primary=True):
	q = appiondata.ApTiltsInAlignRunData()
	q['alignrun'] = alignrundata
	q['tiltseries'] = tiltdata
	q['settings'] = settingsdata
	q['primary'] = primary
	return publish(q)

def insertTomoAlignmentRun(sessiondata,leginoncorrdata,imodxcorrdata,protomorundata,bin,name,path,description=None):
	pathq = appiondata.ApPathData(path=os.path.abspath(path))
	qalign = appiondata.ApTomoAlignmentRunData(session=sessiondata,
			bin=bin,name=name, path=pathq)
	if leginoncorrdata:
		qalign['coarseLeginonParams'] = leginoncorrdata
	if imodxcorrdata:
		qalign['coarseImodParams'] = imodxcorrdata
	if protomorundata:
		qalign['fineProtomoParams'] = protomorundata
	results = qalign.query()
	if not results:
		qalign['description'] = description
		qalign.insert()
		return qalign
	return results[0]

def insertAlignerParams(alignrundata,params,protomodata=None,refineparamsdata=None,goodrefineparamsdata=None,imagedata=None):
	# protomoaligner parameters
	alignerq = appiondata.ApTomoAlignerParamsData()
	alignerq['alignrun'] = alignrundata
	alignerq['description'] = params['description']
	if alignrundata['fineProtomoParams']:
		alignerq['protomo'] = protomodata
		alignerq['refine cycle'] = refineparamsdata
		alignerq['good cycle'] = goodrefineparamsdata
		alignerq['good start'] = params['goodstart']
		alignerq['good end'] = params['goodend']
	alignerdata = publish(alignerq)
	return alignerdata

def publish(q):
	results = q.query()
	if not results:
		q.insert()
		return q
	return results[0]

def insertSubTomoRun(sessiondata,selectionrunid,stackid,name,invert=False,subbin=1):
	if selectionrunid:
		qpick = appiondata.ApSelectionRunData()
		pickdata = qpick.direct_query(selectionrunid)
	else:
		pickdata = None
	if stackid:
		qstack = appiondata.ApStackData()
		stackdata = qstack.direct_query(stackid)
	else:
		stackdata = None
	qrun = appiondata.ApSubTomogramRunData(session=sessiondata,
			pick=pickdata,stack=stackdata,runname=name,invert=invert,subbin=subbin)
	return publish(qrun)

def insertFullTomoRun(sessiondata,path,runname,method,imageidlist=''):
	runq = appiondata.ApFullTomogramRunData()
	runq['session'] = sessiondata
	runq['path'] = appiondata.ApPathData(path=os.path.abspath(path))
	runq['runname'] = runname
	runq['method'] = method
	runq['excluded'] = imageidlist
	return publish(runq)

def checkExistingFullTomoData(path,name):
	pathq = appiondata.ApPath(path=path)
	runq = appiondata.ApFullTomogramRunData(pathq) 
	tomoq = appiondata.ApFullTomogramData(name=name, reconrun=runq)
	results = tomoq.query()
	if not results:
		return None
	filepath = os.path.join(path,name+".rec")
	if not os.path.isfile(filepath):
		return None
	else:
		return results[0]

def getFullTomoData(fulltomoId):
	return appiondata.ApFullTomogramData.direct_query(fulltomoId)

def getTomogramData(tomoId):
	return appiondata.ApTomogramData.direct_query(tomoId)

def uploadTomo(params):
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
	alignrun = insertTomoAlignmentRun(sessiondata,tiltdata,None,None,None,fullbin,runname,params['aligndir'],'manual alignment from upload')
	alignerdata = apProTomo.insertAlignerParams(alignrun,params)
	firstimagedata = getFirstImage(tiltdata)
	path = os.path.abspath(params['rundir'])
	description = params['description']
	if params['full']:
		thickness = params['shape'][0] * fullbin
		uploadfile = params['zprojfile']
		projectimagedata = uploadZProjection(runname,firstimagedata,uploadfile)
		fullrundata = insertFullTomoRun(sessiondata,path,runname,'upload')
		return insertFullTomogram(sessiondata,tiltdata,alignerdata,fullrundata,name,description,projectimagedata,thickness,fullbin)
	else:
		projectimagedata = None
		fulltpath = params['rundir'].replace('/'+params['volume'],'')
		dummyname = 'dummy'
		dummydescription = 'fake full tomogram for subtomogram upload'
		thickness = params['shape'][0] * subbin
		fullrundata = insertFullTomoRun(sessiondata,fullpath,runname,'upload')
		fulltomogram = insertFullTomogram(sessiondata,tiltdata,alignerdata,fullrundata,dummyname,dummydescription,projectimagedata,thickness,fullbin)
		apix = apDatabase.getPixelSize(firstimagedata)
		tomoq = appiondata.ApTomogramData()
		tomoq['session'] = sessiondata
		tomoq['tiltseries'] = tiltdata
		results = tomoq.query()
		index = len(results)+1
		pixelsize = 1e-10 * apix * subbin
		runname = params['volume']
		shape = map((lambda x: x * subbin), params['shape'])
		dimension = {'x':shape[2],'y':shape[1], 'z':shape[0]}
		subtomorundata = insertSubTomoRun(sessiondata,
				None,None,runname,params['invert'],subbin)
		return insertSubTomogram(fulltomogram,subtomorundata,None,0,dimension,path,name,index,pixelsize,description)

def insertFullTomogram(sessiondata,tiltdata,aligner,fullrundata,name,description,projectimagedata,thickness,bin=1):
	tomoq = appiondata.ApFullTomogramData()
	tomoq['session'] = sessiondata
	tomoq['tiltseries'] = tiltdata
	tomoq['aligner'] = aligner
	tomoq['reconrun'] = fullrundata
	tomoq['name'] = name
	tomoq['description'] = description
	tomoq['zprojection'] = projectimagedata
	tomoq['thickness'] = thickness
	tomoq['bin'] = bin
	return publish(tomoq)

def getLastVolumeIndex(fulltomodata):
	tomoq = appiondata.ApTomogramData(fulltomogram=fulltomodata)
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
	tomoq = appiondata.ApTomogramData(fulltomogram=fulltomodata)
	tomoq['session'] = fulltomodata['session']
	tomoq['tiltseries'] = fulltomodata['tiltseries']
	tomoq['subtomorun'] = rundata
	tomoq['path'] = appiondata.ApPathData(path=os.path.abspath(path))
	tomoq['name'] = name
	tomoq['number'] = index
	tomoq['center'] = center
	# offsetz is in pixel of the full tomogram
	tomoq['offsetz'] = offsetz
	# dimension is that of the original tilt images, i.e., before binning of the full tomogram
	tomoq['dimension'] = dimension
	# pixelsize is of the full_bin * sub_bin tomogram
	tomoq['pixelsize'] = pixelsize
	tomoq['description'] = description
	filepath = os.path.join(path,name+".rec")
	tomoq['md5sum'] = apFile.md5sumfile(filepath)
	return publish(tomoq)

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

def makeAlignStackMovie(filename,xsize=512):
	apDisplay.printMsg('Making movie','blue')
	mrcpath = filename
	dirpath = os.path.dirname(mrcpath)
	splitnames =  os.path.splitext(mrcpath)
	rootpath = splitnames[0]
	alignsplit = rootpath.split('-')
	if len(alignsplit) > 1:
		key = alignsplit[-1]
	else:
		key = ''
	print 'dirpath',dirpath
	print 'key',key
	apDisplay.printMsg('Reading align stack %s' % mrcpath)
	array = mrc.read(mrcpath)
	shape = array.shape
	xsize = min(xsize,shape[2])
	stats = {}
	# speed up stats calculation by projecting to axis 0 to reduce array dimension
	apDisplay.printMsg('Calculating stats...')
	slice = numpy.sum(array[:,:,:],axis=0)/shape[0]
	stats['std'] = slice.std()
	stats['mean'] = slice.mean()
	axis = 0
	dimz = shape[0]
	#generate a sequence of jpg images
	apDisplay.printMsg('Making slices...')
	for i in range(0, dimz):
		pictpath1 = rootpath+'_slice%05d' % i
		pictpath2 = rootpath+'_slice%05d' % (2*dimz-i)
		slice = array[i,:,:]
		stats['mean'] = slice.mean()
		# adjust and shrink each image
		array2jpg(pictpath1,slice,stats['mean']-6*stats['std'],stats['mean']+6*stats['std'],xsize)
		array2jpg(pictpath2,slice,stats['mean']-6*stats['std'],stats['mean']+6*stats['std'],xsize)
	apDisplay.printMsg('Putting the jpg files together to flash video...')
	moviename = dirpath+'/minialign'+key+'.flv'
	print 'moviename',moviename
	cmd = 'mencoder -nosound -mf type=jpg:fps=24 -ovc lavc -lavcopts vcodec=flv -of lavf -lavfopts format=flv -o '+moviename+' "mf://'+rootpath+'_slice*.jpg"'
	proc = subprocess.Popen(cmd, shell=True)
	proc.wait()
	proc = subprocess.Popen('rm '+rootpath+'_slice*.jpg', shell=True)
	proc.wait()

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
		proc = subprocess.Popen('rm '+rootpath+'_avg*.jpg', shell=True)
		proc.wait()

def makeProjection(filename,xsize=512):
	mrcpath = filename
	dirpath = os.path.dirname(mrcpath)
	apDisplay.printMsg('Reading 3D recon %s' % mrcpath)
	array = mrc.read(mrcpath)
	shape = array.shape
	xsize = min(xsize,shape[2])
	# default for full tomogram is XZY
	if shape[0] > shape[1]:
		renders = {'a':{'axis':0,'axisname':'z'},'b':{'axis':1,'axisname':'y'},'c':{'axis':2,'axisname':'x'}}
	else:
		renders = {'a':{'axis':1,'axisname':'y'},'b':{'axis':0,'axisname':'z'},'c':{'axis':2,'axisname':'x'}}
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
	presetdata = leginon.leginondata.PresetData(initializer=initialimagedata['preset'])
	presetdata['name']='Zproj'
	imagedata = leginon.leginondata.AcquisitionImageData(initializer=initialimagedata)
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
	return publish(imagedata)

def getSubvolumeInfo(subtomorundata):
	tomoq = appiondata.ApTomogramData(subtomorun=subtomorundata)
	results = tomoq.query(results=1)
	if results:
		tomo = results[0]
		subbin = subtomorundata['subbin']
		fullq = appiondata.ApFullTomogramData()
		fulltomogram = tomo['fulltomogram']
		if fulltomogram['alignrun'] is  None:
			# new data has no alignrun
			fullbin = tomo['fulltomogram']['aligner']['alignrun']['bin']
		else:
			# old data has no aligner
			fullbin = tomo['fulltomogram']['alignrun']['bin']
		totalbin = subbin * fullbin
		shape = (tomo['dimension']['z']/totalbin,tomo['dimension']['y']/totalbin,tomo['dimension']['x']/totalbin)
		pixelsize = tomo['pixelsize']
		return shape,totalbin,pixelsize
	else:
		return None, 1,None

def getSubTomogramData(subtomorundata,stackpdata):
	pdata = stackpdata['particle']
	tomoq = appiondata.ApTomogramData(subtomorun=subtomorundata,center=pdata)
	results = tomoq.query()
	if results:
		tomo = results[0]
		return tomo

def getTomoVolume(tomodata):
		path = tomodata['path']['path']
		name = tomodata['name']+'.rec'
		apDisplay.printMsg("Loading subtomogram %s" %name)
		volume = mrc.read(os.path.join(path,name))
		return volume

def getParticleCenterZProfile(subvolume,shift,halfwidth,bgwidth):
	shape = subvolume.shape
	ystart = max(0,int(shape[1]/2.0 - shift['y'] - halfwidth))
	xstart = max(0,int(shape[1]/2.0 - shift['x'] - halfwidth))
	yend = min(shape[1],ystart + 2 * halfwidth + 1)
	xend = min(shape[2],xstart + 2 * halfwidth + 1)
	array = subvolume[:,ystart:yend,xstart:xend]
	xavg = numpy.sum(array,axis=2)/(2*halfwidth+1)
	xyavg = numpy.sum(xavg,axis=1)/(2*halfwidth+1)
	background = numpy.sum(xyavg[:bgwidth])/bgwidth
	background += numpy.sum(xyavg[-bgwidth:])/bgwidth
	background = background / 2
	vmax = xyavg.max()
	return (xyavg - background) / (vmax-background)

def transformTomo(a,name,package,alignpdata,zshift=0.0,bin=1):
	shift = (alignpdata['xshift']/bin,alignpdata['yshift']/bin,zshift)
	angle = alignpdata['rotation']
	mirror = alignpdata['mirror']
	print 'shift= (%.2f, %.2f)' % shift, 'rotate=%.1 deg' % (angle,), 'upside-down=',mirror
	"""
		zoom the array by 2 to get better interpretation of noisy volume and then
		use numpy affine transform to rotate and shift. prefilter should be False to 
		faithfully regenerate features in the sections.  In addition, zoom order need
		to be one to prevent filtering effect while affine transform order should be
		more than 2 for better interpretation of the rotation.
	"""
	scale = 2.0
	### order=1 copies values
	b = ndimage.zoom(a,scale,mode='nearest',prefilter=False,order=1)
	shape = b.shape
	center = map((lambda x: x / 2), list(b.shape))
	shift2 = map((lambda x: x * scale), list(shift))
	inboxtuple = list(a.shape)
	inboxtuple.reverse()
	if mirror is True:
		mvalue = -1
	else:
		mvalue = 1
	rot = angle * math.pi / 180.0
	rotationaffine = numpy.matrix([[1,0,0,0],[0,math.cos(rot),-math.sin(rot),0],[0,math.sin(rot),math.cos(rot),0],[0,0,0,1]])
	shiftaffine = numpy.matrix([[1,0,0,shift2[2]],[0,1,0,shift2[1]],[0,0,1,shift2[0]],[0,0,0,1]])
	centeraffine = numpy.matrix([[1,0,0,0],[0,1,0,center[1]],[0,0,1,center[2]],[0,0,0,1]])
	mirroraffine = numpy.matrix([[mvalue,0,0,0],[0,1,0,0],[0,0,mvalue,0],[0,0,0,1]])
	if package == 'Xmipp':
		totalaffine = xmippAffineTransform(rotationaffine, shiftaffine, mirroraffine, centeraffine)
	elif package == 'Spider':
		totalaffine = spiderAffineTransform(rotationaffine, shiftaffine, mirroraffine, centeraffine)
	totalshift = (totalaffine[0,3],totalaffine[1,3],totalaffine[2,3])
	b = ndimage.affine_transform(b, totalaffine[:-1,:-1], offset=totalshift, mode='wrap', order=3, prefilter=False)
	c = ndimage.zoom(b,1.0/scale,mode='nearest',prefilter=False,order=1)
	return c

def xmippAffineTransform(rotationaffine, shiftaffine, mirroraffine, centeraffine):
	return shiftaffine.I * mirroraffine * centeraffine * rotationaffine.I * centeraffine.I
def spiderAffineTransform(rotationaffine, shiftaffine, mirroraffine, centeraffine):
	return centeraffine * rotationaffine.I * centeraffine.I * shiftaffine.I * centeraffine * mirroraffine * centeraffine.I

#=========================
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

def insertTomoAverageRun(runname,rundir,subtomorundata,stackdata,halfwidth,description):
	tomoaq = appiondata.ApTomoAverageRunData()
	tomoaq['path'] = appiondata.ApPathData(path=os.path.abspath(rundir))
	tomoaq['runname'] = runname
	tomoaq['subtomorun'] = subtomorundata
	tomoaq['stack'] = stackdata
	tomoaq['xyhalfwidth'] = halfwidth
	tomoaq.query()
	results = tomoaq.query()
	if not results:
		tomoaq['description'] = description
		tomoaq.insert()
		return tomoaq
	return results[0]

def insertTomoAvgParticle(avgrundata,subvolumedata,alignp,shiftz):
	tomoaq = appiondata.ApTomoAvgParticleData()
	tomoaq['avgrun'] = avgrundata
	tomoaq['subtomo'] = subvolumedata
	tomoaq['aligned particle'] = alignp
	tomoaq['z shift'] = shiftz
	return publish(tomoaq)

