#!/usr/bin/env python

'''
affine_transform(input, matrix, offset=0.0, output_shape=None, output_type=None, output=None, order=3, mode='constant', cval=0.0, prefilter=True)

offset means:
	coordinate of input that corresponds to 0,0 in output
'''

import Mrc
import Mrcmm
import numarray
import numarray.nd_image
import numarray.linear_algebra
import dbdatakeeper
import data
import polygon
import raster
import time
import sys
import newdict
import cPickle
import os.path
import affine
import caltransformer

dbdk = dbdatakeeper.DBDataKeeper()

def memmapMRC(fileref):
	fullname = os.path.join(fileref.path, fileref.filename)
	im = Mrcmm.mrc_to_numeric(fullname)
	return im

class Image(object):
	def __init__(self, scope, camera, timestamp, fileref=None, rotation=0.0):
		self.scope = data.ScopeEMData(initializer=scope)
		self.camera = data.CameraEMData(initializer=camera)
		self.shape = self.camera['dimension']['y'], self.camera['dimension']['x']
		self.fileref = fileref
		self.timestamp = timestamp
		self.trans = caltransformer.getTransformer(scope['tem'], camera['ccdcamera'], scope['high tension'], scope['magnification'], timestamp, rotation)
		self.newStage(scope['stage position'])

	def newStage(self, stage):
		self.scope['stage position'] = stage
		self.stage = stage
		self.stagex = stage['x']
		self.stagey = stage['y']
		self.calculateStagePositions()
		self.calculateMaxDist()

	def readImage(self):
		im = self.fileref.read()
		## allow image in fileref to be garbage collected
		self.fileref.data = None
		return im
	
	def calculateStagePositions(self):
		self.bin = self.camera['binning']
		self.binx = self.bin['x']
		self.biny = self.bin['y']

		rowhalf = self.shape[0]/2.0
		colhalf = self.shape[1]/2.0
		pixelcorners = (-rowhalf,-colhalf), (-rowhalf,colhalf), (rowhalf,colhalf), (rowhalf,-colhalf)

		self.stagecorners = []
		for row,col in pixelcorners:
			pixelshift = {'row':row, 'col':col}
			newstage = self.trans.transform(pixelshift, self.stage, self.bin)
			self.stagecorners.append( (newstage['x'],newstage['y']) )
		self.stagecenter = (self.stage['x'], self.stage['y'])

	def calculateMaxDist(self):
		self.maxdist = 0.0
		for corner in self.stagecorners:
			dist = numarray.hypot(self.scope['stage position']['x']-corner[0], self.scope['stage position']['y']-corner[1])
			if dist > self.maxdist:	
				self.maxdist = 1.1 * dist

	def isClose(self, other):
		xdist = other.stagex - self.stagex
		ydist = other.stagey - self.stagey
		dist = numarray.hypot(xdist,ydist)
		if dist > (self.maxdist + other.maxdist):
			return False
		else:
			return True

class MontageImage(Image):
	def __init__(self, scope, camera, timestamp, rotation=0.0):
		Image.__init__(self, scope, camera, timestamp, rotation=rotation)

		self.rotation = rotation
		self.outputmatrix = self.trans.imatrix
		self.image = None
		self.inserted = 0
		self.targets = []

	def containInputs(self, inputimages):
		stagepositions = []
		for input in inputimages:
			stagepositions.extend(input.stagecorners)
		self.containStagePositions(stagepositions)

	def containStagePositions(self, stagepositions):
		## find necessary range for global space
		rows = []
		cols = []
		for stage in stagepositions:
			# find pixel position in global space
			stagepos = {'x':stage[0], 'y':stage[1]}
			pixels = self.trans.itransform(stagepos, self.stage, self.bin)
			rows.append(pixels['row'])
			cols.append(pixels['col'])
		rowmin = min(rows)
		rowmax = max(rows)
		colmin = min(cols)
		colmax = max(cols)

		## transform back to stage coordinates
		centerpixel = {'row':(rowmin+rowmax)/2.0, 'col':(colmin+colmax)/2.0}
		## update scope and camera info to contain all inputs
		self.shape = int(round(rowmax-rowmin)), int(round(colmax-colmin))
		self.camera['dimension']['x'] = self.shape[1]
		self.camera['dimension']['y'] = self.shape[0]
		newstage = self.trans.transform(centerpixel, self.stage, self.bin)
		self.newStage(newstage)

	def calculateTiles(self, tilesize):
		## figure out the final shape of global space
		rowsize = int(numarray.ceil(float(self.shape[0])/tilesize) * tilesize)
		colsize = int(numarray.ceil(float(self.shape[1])/tilesize) * tilesize)

		## make list of stage center for each tile
		print 'calculating tile positions...'
		centerpixel = rowsize/2.0-0.5, colsize/2.0-0.5
		firstpixel = tilesize/2.0-0.5
		rowi = 0
		tiles = newdict.OrderedDict()
		for row in numarray.arange(firstpixel, rowsize, tilesize):
			coli = 0
			for col in numarray.arange(firstpixel, colsize, tilesize):
				pixel = {'row':row-centerpixel[0], 'col':col-centerpixel[1]}
				newstage = self.trans.transform(pixel, self.stage, self.bin)
				tilescope = data.ScopeEMData(initializer=self.scope)
				tilescope['stage position'] = newstage
				tilecamera = data.CameraEMData(initializer=self.camera)
				tilecamera['dimension'] = {'x':tilesize, 'y':tilesize}
				args = tilescope, tilecamera, self.timestamp
				kwargs = {'rotation': self.rotation}
				tiles[(rowi,coli)] = {'args':args, 'kwargs':kwargs}
				coli += 1
			rowi += 1

		print 'Calculated %d tiles, %d rows, %d cols' % (len(tiles), rowi, coli)
		return tiles

	def needImage(self, image):
		if not self.isClose(image):
			return False
		if polygon.pointsInPolygon(image.stagecorners, self.stagecorners):
			return True
		if polygon.pointsInPolygon([image.stagecenter], self.stagecorners):
			return True
		if polygon.pointsInPolygon(self.stagecorners, image.stagecorners):
			return True
		if polygon.pointsInPolygon([self.stagecenter], image.stagecorners):
			return True
		return False

	def insertImage(self, input, target=None):
		if not self.needImage(input):
			return

		## differnce in binning requires scaling
		## assume equal x and y binning
		binscale = float(input.binx) / self.binx
		binmatrix = binscale * numarray.identity(2)

		## affine transform matrix is input matrix
		atmatrix = numarray.matrixmultiply(binmatrix, input.trans.matrix)
		atmatrix = numarray.matrixmultiply(self.outputmatrix, atmatrix)
		## affine_transform function requires the inverse matrix
		atmatrix = numarray.linear_algebra.inverse(atmatrix)

		## calculate offset position
		if target is None:
			instage = input.stage
		else:
			instage = input.trans.transform(target, input.stage, input.bin)

		pixels = self.trans.itransform(instage, self.stage, self.bin)
		pixels = (pixels['row'],pixels['col'])
		shift = pixels[0], pixels[1]
		offset = affine.affine_transform_offset(input.shape, self.shape, atmatrix, shift)

		if target is None:
			## affine transform into temporary output
			output = numarray.zeros(self.shape, numarray.Float32)

			inputarray = memmapMRC(input.fileref)

			#inputarray = splines.filter(input.fileref.filename, inputarray)
			numarray.nd_image.affine_transform(inputarray, atmatrix, offset=offset, output=output, output_shape=self.shape, mode='constant', cval=0.0, order=splineorder, prefilter=False)

			if self.image is None:
				self.image = numarray.zeros(self.shape, numarray.Float32)

			## copy temporary into final
			numarray.putmask(self.image, output, output)
			self.inserted += 1
		else:
			pix = self.shape[0]/2.0+shift[0],self.shape[1]/2.0+shift[1]
			self.targets.append(pix)


def getImageData(filename_or_id):
	print 'getImageData(%s)' % (filename_or_id,)
	if isinstance(filename_or_id, basestring):
		q = data.AcquisitionImageData(filename=filename_or_id)
		images = dbdk.query(q, readimages=False, results=1)
		if images:
			return images[0]
		else:
			raise RuntimeError('%s does not exist' % (filename_or_id,))
	else:
		im = dbdk.direct_query(data.AcquisitionImageData, filename_or_id, readimages=False)
		return im

def createTargetInputs(targetimages):
	targetinputs = []
	for id, target in targetimages:
		imdata = getImageData(id)
		fileref = imdata.special_getitem('image', dereference=False)
		input = Image(imdata['scope'], imdata['camera'], imdata.timestamp, fileref)
		targetinputs.append((input, target))
	return targetinputs

def targetStagePositions(targetinputs):
	stagepositions = []
	for input in targetinputs:
		inputim = input[0]
		target = input[1]
		stage = inputim.trans.transform(target, inputim.stage, inputim.bin)
		stagepositions.append(stage)
	return stagepositions

def longEdgeAngle(left_target, right_target, output):
	# angle from column axis
	# assumes all targets from same mag

	# find stage positions of targets
	stagepos = []
	for input in (left_target, right_target):
		inputim = input[0]
		target = input[1]
		stage = inputim.trans.transform(target, inputim.stage, inputim.bin)
		stagepos.append(stage)
	edgevectx = stagepos[1]['x'] - stagepos[0]['x']
	edgevecty = stagepos[1]['y'] - stagepos[0]['y']

	## angle from horizontal axis, defined by first two corners
	horizx = output.stagecorners[1][0] - output.stagecorners[0][0]
	horizy = output.stagecorners[1][1] - output.stagecorners[0][1]

	edgeangle = numarray.arctan2(edgevecty, edgevectx)
	horizangle = numarray.arctan2(horizy, horizx)
	
	return edgeangle - horizangle

def createInputs(images, cachefile=None):
	inputimages = []
	for imdata in images:
		fileref = imdata.special_getitem('image', dereference=False)
		print 'Creating Image:', imdata['filename']
		input = Image(imdata['scope'], imdata['camera'], imdata.timestamp, fileref)
		inputimages.append(input)
	if cachefile is not None:
		f = open(cachefile, 'w')
		cPickle.dump(inputimages, f, cPickle.HIGHEST_PROTOCOL)
		f.close()
	return inputimages

def readInputs(cachefile):
	print 'reading inputs info'
	f = open(cachefile, 'r')
	inputimages = cPickle.load(f)
	f.close()
	return inputimages

def createGlobalOutput(imdata, angle=0.0, bin=1):
	print 'creating global image space'
	timestamp = imdata.timestamp
	scope = data.ScopeEMData(initializer=imdata['scope'])
	camera = data.CameraEMData(initializer=imdata['camera'])
	binning = {'x':camera['binning']['x']*bin, 'y':camera['binning']['y']*bin}
	camera['binning'] = binning
	globaloutput = MontageImage(scope, camera, timestamp, rotation=angle)
	return globaloutput

def readTileInfo():
	print 'reading tile info'
	f = open('tiles', 'r')
	tiles = cPickle.load(f)
	f.close()
	print 'done'
	return tiles

def storeTileInfo(tiledict):
	f = open('tiles', 'w')
	cPickle.dump(tiledict, f, cPickle.HIGHEST_PROTOCOL)
	f.close()

def markTarget(im, target):
	size = 4
	r1 = int(target[0]-size)
	r2 = int(target[0]+size)
	c1 = int(target[1]-size)
	c2 = int(target[1]+size)
	im[r1:r2, c1:c2] -= 3000

def createSingleImage(inputimages, globaloutput, outfilename, outformat):
	n = len(inputimages)
	for i,input in enumerate(inputimages):
		print 'inserting %d of %d' % (i+1,n)
		globaloutput.insertImage(input)
	'''
	if targetinputs:
		for input,target in targetinputs:
			globaloutput.insertImage(input, target)
		print 'inserted %s targets' % (len(globaloutput.targets),)
	for target in globaloutput.targets:
		print 'T', target
		markTarget(globaloutput.image, target)
	'''
	Mrc.numeric_to_mrc(globaloutput.image, outfilename)

def createTiles(inputs, tiledict, tilesize, row1=None, row2=None, col1=None, col2=None):
	blank = numarray.zeros((tilesize,tilesize), numarray.Float32)

	if None in (row1,row2,col1,col2):
		tileindices = tiledict.keys()
	else:
		tileindices = []
		for rowi in range(row1, row2+1):
			for coli in range(col1, col2+1):
				tileindices.append((rowi,coli))

	f = open('outputinfo', 'w')
	f.close()

	tilestotal = len(tileindices)
	t0 = time.time()
	for i,tileindex in enumerate(tileindices):
			tileargs = tiledict[tileindex]
			print 'Creating tile:', tileindex
			output = MontageImage(*tileargs['args'], **tileargs['kwargs'])
		
			for input in inputs:
				output.insertImage(input)
			print '   Inserted %d images' % (output.inserted,)
			if output.inserted:
				outim = output.image
			else:
				outim = blank
		
			f = open('outputinfo', 'a')
			r,c = tileindex
			x,y = output.scope['stage position']['x'], output.scope['stage position']['y']
			f.write('%d\t%d\t%e\t%e\n' % (r,c,x,y))
			f.close()
	
			Mrc.numeric_to_mrc(outim, '%d_%d.mrc' % tileindex)
	
			'''
			jpeg.save(output.image, clip[0], clip[1], '%d_%d.jpg' % tileindex, 90)
			'''
	
			tilesdone = i+1
			tilesleft = tilestotal - tilesdone
			elapsed = time.time() - t0
			tilespersec = tilesdone / elapsed
	
			secleft = tilesleft * tilespersec
			hrleft = secleft / 3600.0
			hrleft = int(hrleft)
			secleft = secleft - hrleft * 3600.0
			minleft = secleft / 60.0
			minleft = int(minleft)
			secleft = secleft - minleft * 60.0
			secleft = int(secleft)
			print '   Done %d of %d, Avg: %.2f tiles/sec,  Estimated time left: %02d:%02d:%02d' % (tilesdone,tilestotal,tilespersec,hrleft,minleft,secleft)

########## End of classes and functions...
########## Now the script!


if __name__ == '__main__':
	from optparse import OptionParser
	import stitchparser
	import profile
	
	parser = OptionParser()

	parser.add_option('-i', '--input-list', action='store', type='string', dest='infilename', help="read the file containing list of input images")
	parser.add_option('-x', '--stitch-xml', action='store', type='string', dest='xmlfilename', help="read the XML stitch file for list of input images")
	parser.add_option('-I', '--input-cache', action='store', type='string', dest='incache', help="read the file containing image cache")
	parser.add_option('-o', '--output-mrc', action='store', type='string', dest='outfilename', help="write the resulting image to an MRC file")
	parser.add_option('-t', '--tile-size', action='store', type='int', dest='tilesize', help="generate tiles from the output image with the specified tile size")
	parser.add_option('-b', '--bin', action='store', type='float', dest='bin', help="apply the additional binning factor to the output")
	parser.add_option('-d', '--output-definition', action='store', type='string', dest='outdef', help="use the given image as the space to transform into")
	parser.add_option('-s', '--spline-order', action='store', type='int', dest='splineorder', help="use the given spline order for affine transforms")
	parser.add_option('-f', '--output-format-order', action='store', type='string', dest='outformat', help="jpeg or mrc")

	(options, args) = parser.parse_args()

	badargs = False
	if options.infilename is None and options.incache is None and options.xmlfilename is None:
		print 'You must specify either an input file list (-i) or an input cache (-I) or an XML file (-x).'
		badargs = True

	if options.outfilename is None and options.tilesize is None:
		print 'You must specify either an output MRC filename (-o) for a single output file'
		print '   or a tile size (-t) if you want to generate tiles'
		badargs = True

	if badargs:
		sys.exit()


	############## Set up inputs ################
	if options.xmlfilename is not None or options.infilename is not None:
		if options.xmlfilename is not None:
			info = stitchparser.parse(options.xmlfilename)
			filenames = info['images']
			print 'FILENAMES', filenames

		if options.infilename is not None:
			f = open(options.infilename, 'r')
			filenames = f.readlines()
			f.close()
			filenames = [filename[:-1] for filename in filenames]

			## database has filenames without the mrc extension
			filenames = map(os.path.basename, filenames)
			filenames = [filename[:-4] for filename in filenames]
	
		print 'reading image metadata'
		images1 = [getImageData(filename) for filename in filenames]
		images = []
		for image in images1:
			if image['filename'][-2:] != 'gr':
				images.append(image)
			else:
				print 'rejecting', image['filename']
		print 'creating input image objects'
		inputimages = createInputs(images, options.incache)
	elif options.incache is not None:
		print 'reading input image objects'
		inputimages = readInputs(options.incache)

	############# Set up output image
	if options.outdef is None:
		fname = inputimages[0].fileref.filename[:-4]
	else:
		fname = options.outdef
	outim = getImageData(fname)

	if options.bin is None:
		bin = 1.0
	else:
		bin = options.bin

	tempoutput = createGlobalOutput(outim, 0.0, bin=bin)

	## rotate to section edge
	if False:
		angle = longEdgeAngle(targetinputs[2], targetinputs[1], tempoutput)
		globaloutput = createGlobalOutput(outim, angle, bin=bin)
	else:
		globaloutput = tempoutput
	
	#### set output boundaries and center
	globaloutput.containInputs(inputimages)

	print 'Output shape:', globaloutput.shape

	############## Set up targtets for rotat##############
	'''
	targetimages = (
		(301393, {'row':-111,'col':-237}),
		(301393, {'row':-150,'col':-44}),
		(301393, {'row':132,'col':-82}),
		(301396, {'row':91,'col':248}),
	)
	#### Target stuff
	print 'creating input target objects'
	targetinputs = createTargetInputs(targetimages)
	longedge = targetinputs[3], targetinputs[2]
	targetstages = targetStagePositions(targetinputs)
	globaloutput.containStagePositions(targetstages)
	'''
	
	############ create outputs and save ###############
	if options.splineorder is None:
		splineorder = 1
	else:
		splineorder = options.splineorder

	if options.tilesize is not None:
		tilesize = options.tilesize
		print 'calc tiles'
		tiledict = globaloutput.calculateTiles(tilesize)
		#storeTileInfo(tiledict)
		createTiles(inputimages, tiledict, tilesize)
	elif options.outfilename is not None:
		createSingleImage(inputimages, globaloutput, options.outfilename, options.outformat)
		#profile.run('createSingleImage(inputimages, globaloutput, options.outfilename, options.outformat)')
		
	#tiledict = readTileInfo()
	
	############# Image stats ############
	'''
	print 'calculating image stats...'
	min = None
	max = None
	mean = None
	std = None
	q = data.AcquisitionImageStatsData(image=images[0])
	stats = db.query(q, results=1)[0]
	sum = stats['mean']
	std = stats['stdev']
	for im in images[1:]:
		q = data.AcquisitionImageStatsData(image=im)
		stats = db.query(q, results=1)[0]
		if stats['stdev'] > std:
			std = stats['stdev']
		sum += stats['mean']
	mean = sum / len(images)
	clip = (mean-3*std, mean+3*std)
	print 'clip', clip
	'''
