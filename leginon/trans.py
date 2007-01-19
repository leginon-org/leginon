#!/usr/bin/env python

'''
affine_transform(input, matrix, offset=0.0, output_shape=None, output_type=None, output=None, order=3, mode='constant', cval=0.0, prefilter=True)

offset means:
	coordinate of input that corresponds to 0,0 in output

'''

import Mrc
import numarray
import numarray.nd_image
import numarray.linear_algebra
import dbdatakeeper
import data
import polygon
import raster
import time
import sys
import gonmodel
import newdict

stagetransformers = {}
def getStageTransformer(tem, ccd, ht, mag, timestamp):
	key = (tem.dbid,ccd.dbid,ht,mag,timestamp)
	if key in stagetransformers:
		return stagetransformers[key]
	st = StageTransformer(tem, ccd, ht, mag, timestamp)
	stagetransformers[key] = st
	return st

class StageTransformer(object):
	def __init__(self, tem, ccd, ht, mag, timestamp):
		## load stage model from db
		self.xmod = self.getModelCal(tem, ccd, 'x', timestamp)
		self.ymod = self.getModelCal(tem, ccd, 'y', timestamp)
		self.xmag = self.getMagCal(tem, ccd, 'x', ht, mag, timestamp)
		self.ymag = self.getMagCal(tem, ccd, 'y', ht, mag, timestamp)
		self.createMatrix()

	def createMatrix(self):
		xscale = self.xmag['mean']
		yscale = self.ymag['mean']
		xang = self.xmag['angle']
		yang = self.ymag['angle']
		self.matrix = numarray.array(
			((xscale * numarray.sin(xang) , xscale * numarray.cos(xang)),
			(yscale * numarray.sin(yang) , yscale * numarray.cos(yang))), numarray.Float32
		)
		self.imatrix = numarray.linear_algebra.inverse(self.matrix)

	def itransform(self, position, scope, camera):
		gx0 = scope['stage position']['x']
		gy0 = scope['stage position']['y']
		gx1 = position['x']
		gy1 = position['y']
		binx = camera['binning']['x']
		biny = camera['binning']['y']

		## integrate over model
		dgx = self.xmod.integrate(gx0,gx1)
		dgy = self.ymod.integrate(gy0,gy1)
		## rotate/scale
		drow,dcol = numarray.matrixmultiply(self.imatrix, (dgx,dgy))

		pixelshift = {'row': drow/biny, 'col': dcol/binx}
		return pixelshift
	
	def transform(self, pixelshift, scope, camera):
		gx0 = scope['stage position']['x']
		gy0 = scope['stage position']['y']
		binx = camera['binning']['x']
		biny = camera['binning']['y']
		pixrow = pixelshift['row'] * biny
		pixcol = pixelshift['col'] * binx
	
		gx1,gy1 = numarray.matrixmultiply(self.matrix, (pixrow,pixcol))

		dgx = self.xmod.predict(gx0,gx1)
		dgy = self.ymod.predict(gy0,gy1)
	
		newscope = data.ScopeEMData(initializer=scope)
		newscope['stage position'] = dict(scope['stage position'])
		newscope['stage position']['x'] += dgx
		newscope['stage position']['y'] += dgy
		return newscope
		
	def getMagCal(self, tem, ccd, axis, ht, mag, timestamp):
		qinst = data.StageModelMagCalibrationData(magnification=mag, axis=axis)
		qinst['high tension'] = ht
		qinst['tem'] = tem
		qinst['ccdcamera'] = ccd
	
		caldatalist = dbdk.query(qinst)
	
		# get the one that was valid at timestamp
		for cal in caldatalist:
			if cal.timestamp < timestamp:
				caldata = cal
				break
	
		caldata2 = dict(caldata)
		return caldata2
	
	def getModelCal(self, tem, ccd, axis, timestamp):
		qinst = data.StageModelCalibrationData(axis=axis)
		qinst['tem'] = tem
		qinst['ccdcamera'] = ccd
		caldatalist = dbdk.query(qinst)
	
		# get the one that was valid at timestamp
		for cal in caldatalist:
			if cal.timestamp < timestamp:
				caldata = cal
				break
	
		## return it to rank 0 array
		caldata2 = {}
		caldata2['axis'] = caldata['axis']
		caldata2['period'] = caldata['period']
		caldata2['a'] = numarray.ravel(caldata['a']).copy()
		caldata2['b'] = numarray.ravel(caldata['b']).copy()
		mod = gonmodel.GonModel()
		mod.fromDict(caldata2)
		return mod

import mrc2jpg2out
def writeJPG(a, filename, clip, quality):
	img = mrc2jpg2out.Numeric_to_Image(a, clip)
	mrc2jpg2out.write_jpeg(img, filename, quality)

def affine_transform_offset(inputshape, outputshape, affine_matrix, offset=(0,0)):
	'''
	calculation of affine transform offset
	for now we assume center of image
	'''
	outcenter = numarray.array(outputshape, numarray.Float32)
	outcenter.shape = (2,)
	outcenter /= 2.0
	outcenter += offset

	incenter = numarray.array(inputshape, numarray.Float32)
	incenter.shape = (2,)
	incenter /= 2.0

	outcenter2 = numarray.matrixmultiply(affine_matrix, outcenter)

	offset = incenter - outcenter2
	return offset

def getSimpleStageMatrix(scope, camera):
	queryinstance = data.MatrixCalibrationData()
	queryinstance['tem'] = scope['tem']
	queryinstance['ccdcamera'] = camera['ccdcamera']
	queryinstance['type'] = 'stage position'
	queryinstance['magnification'] = scope['magnification']
	queryinstance['high tension'] = scope['high tension']
	caldatalist = db.query(queryinstance, results=1)
	return caldatalist[0]['matrix']

class Image(object):
	def __init__(self, scope, camera, timestamp, fileref=None):
		self.scope = data.ScopeEMData(initializer=scope)
		self.camera = data.CameraEMData(initializer=camera)
		self.shape = self.camera['dimension']['y'], self.camera['dimension']['x']
		self.fileref = fileref
		self.timestamp = timestamp
		self.trans = getStageTransformer(scope['tem'], camera['ccdcamera'], scope['high tension'], scope['magnification'], timestamp)
		self.calculateCorners()
		self.calculateMaxDist()

	def readImage(self):
		im = self.fileref.read()
		## allow image in fileref to be garbage collected
		self.fileref.data = None
		return im
	
	def calculateCorners(self):
		rowhalf = self.shape[0]/2.0
		colhalf = self.shape[1]/2.0
		pixelcorners = (-rowhalf,-colhalf), (-rowhalf,colhalf), (rowhalf,colhalf), (rowhalf,-colhalf)
		self.stagecorners = []
		for row,col in pixelcorners:
			pixelshift = {'row':row, 'col':col}
			newscope = self.trans.transform(pixelshift, self.scope, self.camera)
			stage = newscope['stage position']
			self.stagecorners.append( (stage['x'],stage['y']) )

	def calculateMaxDist(self):
		self.maxdist = 0.0
		for corner in self.stagecorners:
			dist = numarray.hypot(self.scope['stage position']['x']-corner[0], self.scope['stage position']['y']-corner[1])
			if dist > self.maxdist:	
				self.maxdist = dist

	def isClose(self, other):
		xdist = other.scope['stage position']['x'] - self.scope['stage position']['x']
		ydist = other.scope['stage position']['y'] - self.scope['stage position']['y']
		dist = numarray.hypot(xdist,ydist)
		if dist > (self.maxdist + other.maxdist):
			return False
		else:
			return True
	
class OutputImage(Image):
	def __init__(self, scope, camera, timestamp, scale=1.0, rotation=0.0):
		Image.__init__(self, scope, camera, timestamp)

		self.calculateOutputMatrix(scale, rotation)

		self.image = None
		self.inserted = 0

	def calculateOutputMatrix(self, scale, rotation):
		matrix = self.trans.imatrix
		'''
		if scale is not None:
			self.scale = numarray.array(((scale, 0),(0,scale)), numarray.Float32)
			matrix = numarray.matrixmultiply(self.scale, matrix)
		else:
			self.scale = numarray.identity(2)
		if rotation is not None:
			self.rot = numarray.array( ((numarray.cos(rotation), -numarray.sin(rotation)),
			 (numarray.sin(rotation),  numarray.cos(rotation))), numarray.Float32)
			matrix = numarray.matrixmultiply(self.rot, matrix)
		else:
			self.rot = numarray.identity(2)
		'''
		self.outputmatrix = matrix

	def containInputs(self, inputimages):
		## find necessary range for global space
		rowmin = rowmax = colmin = colmax = 0
		for input in inputimages:
			for pos in input.stagecorners:
				# find pixel position in global space
				stage = {'x':pos[0], 'y':pos[1]}
				pixels = self.trans.itransform(stage, self.scope, self.camera)
				if pixels['row'] < rowmin:
					rowmin = pixels['row']
				if pixels['row'] > rowmax:
					rowmax = pixels['row']
				if pixels['col'] < colmin:
					colmin = pixels['col']
				if pixels['col'] > colmax:
					colmax = pixels['col']

		## transform back to stage coordinates
		centerpixel = {'row':(rowmin+rowmax)/2.0, 'col':(colmin+colmax)/2.0}

		## update scope and camera info to contain all inputs
		self.shape = int(round(rowmax-rowmin)), int(round(colmax-colmin))
		self.camera['dimension']['x'] = self.shape[1]
		self.camera['dimension']['y'] = self.shape[0]
		self.scope = self.trans.transform(centerpixel, self.scope, self.camera)

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
				pixel = {'row':centerpixel[0]-row, 'col':centerpixel[1]-col}
				tilescope = self.trans.transform(pixel, self.scope, self.camera)
				tilecamera = data.CameraEMData(initializer=self.camera)
				tilecamera['dimension'] = {'x':tilesize, 'y':tilesize}
				args = tilescope, tilecamera, self.timestamp
				tiles[(rowi,coli)] = args
				coli += 1
			rowi += 1
		
		print 'Calculated Tiles:', len(tiles)
		return tiles

	def needImage(self, image):
		if not self.isClose(image):
			return False
		if polygon.pointsInPolygon(image.stagecorners, self.stagecorners):
			return True
		if polygon.pointsInPolygon(self.stagecorners, image.stagecorners):
			return True
		return False

	def insertImage(self, input):
		if not self.needImage(input):
			return

		## differnce in binning requires scaling
		## assume equal x and y binning
		binscale = float(input.camera['binning']['x']) / self.camera['binning']['x']
		binmatrix = binscale * numarray.identity(2)

		## affine transform matrix is input matrix
		atmatrix = numarray.matrixmultiply(binmatrix, input.trans.matrix)
		atmatrix = numarray.matrixmultiply(atmatrix, self.outputmatrix)
		## affine_transform function requires the inverse matrix
		atmatrix = numarray.linear_algebra.inverse(atmatrix)
	
	
		## calculate offset position
		pixels = self.trans.itransform(input.scope['stage position'], self.scope, self.camera)
		## additional scale and rotation
		pixels = (pixels['row'],pixels['col'])
		'''
		pixels = numarray.matrixmultiply(self.rot, pixels)
		pixels = numarray.matrixmultiply(self.scale, pixels)
		'''

		shift = -pixels[0], -pixels[1]
		offset = affine_transform_offset(input.shape, self.shape, atmatrix, shift)

		## affine transform into temporary output
		output = numarray.zeros(self.shape, numarray.Float32)
		inputarray = input.readImage()
		numarray.nd_image.affine_transform(inputarray, atmatrix, offset=offset, output=output, output_shape=self.shape, mode='constant', cval=0.0, order=3)
	
		## copy temporary into final
		if self.image is None:
			self.image = numarray.zeros(self.shape, numarray.Float32)
		numarray.putmask(self.image, output, output)
		self.inserted += 1

class InputImage(Image):
	pass


def getImageData(filename):
	q = data.AcquisitionImageData(filename=filename)
	images = dbdk.query(q, readimages=False, results=1)
	return images[0]


dbdk = dbdatakeeper.DBDataKeeper()

## exb 1-221
#exfilenames = ['07jan10c_r_00001gr_%05dexa' % i for i in range(2,222)]
exfilenames = ['07jan10c_r_00001gr_00%03dexa' % i for i in range(100,102)]

print 'reading image metadata from DB'
eximages = [getImageData(filename) for filename in exfilenames]

inputimages = []
for imdata in eximages:
	fileref = imdata.special_getitem('image', dereference=False)
	input = InputImage(imdata['scope'], imdata['camera'], imdata.timestamp, fileref)
	inputimages.append(input)

## for tiles, this is global output space
im0 = eximages[0]
timestamp = im0.timestamp
scope = im0['scope']
camera = im0['camera']
globaloutput = OutputImage(scope, camera, timestamp)
globaloutput.containInputs(inputimages)
tileargsdict = globaloutput.calculateTiles(256)

'''
print 'calculating image stats...'
min = None
max = None
mean = None
std = None
q = data.AcquisitionImageStatsData(image=eximages[0])
stats = db.query(q, results=1)[0]
sum = stats['mean']
std = stats['stdev']
for im in eximages[1:]:
	q = data.AcquisitionImageStatsData(image=im)
	stats = db.query(q, results=1)[0]
	if stats['stdev'] > std:
		std = stats['stdev']
	sum += stats['mean']
mean = sum / len(eximages)
clip = (mean-3*std, mean+3*std)
print 'clip', clip
'''

def test():
	t0 = time.time()
	tilesdone = 0
	tilestotal = len(tileargsdict)
	for tileindex,tileargs in tileargsdict.items():
		print 'TILE', tileindex
		output = OutputImage(*tileargs)
	
		for input in inputimages:
			output.insertImage(input)
		print '   inserted %d images' % (output.inserted,)
	
		f = open('outputinfo', 'a')
		r,c = tileindex
		x,y = output.scope['stage position']['x'], output.scope['stage position']['y']
		f.write('%d\t%d\t%e\t%e\n' % (r,c,x,y))
		f.close()

		Mrc.numeric_to_mrc(output.image, '%d_%d.mrc' % tileindex)

		'''
		writeJPG(output.image, '%d_%d.jpg' % tileindex, clip, 90)
		'''

		tilesdone += 1
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
		print 'Done %d of %d, Avg: %.2f tiles/sec,  Estimated time left: %02d:%02d:%02d' % (tilesdone,tilestotal,tilespersec,hrleft,minleft,secleft)

def test2():
	for input in inputimages:
		print 'input'
		globaloutput.insertImage(input)
	Mrc.numeric_to_mrc(globaloutput.image, 'global.mrc')

#import profile
test2()

