#!/usr/bin/env python
import numarray
import numarray.linear_algebra
import dbdatakeeper
import data
import gonmodel

dbdk = dbdatakeeper.DBDataKeeper()

stagetransformers = {}
def getTransformer(tem, ccd, ht, mag, timestamp, rotation=0.0):
	key = (tem.dbid,ccd.dbid,ht,mag,rotation)
	if key in stagetransformers:
		return stagetransformers[key]
	st = Transformer(tem, ccd, ht, mag, timestamp, rotation)
	stagetransformers[key] = st
	return st

class Transformer(object):
	def __init__(self, tem, ccd, ht, mag, timestamp, rotation=0.0):
		## load stage model from db
		self.xmod = self.getModelCal(tem, ccd, 'x', timestamp)
		self.ymod = self.getModelCal(tem, ccd, 'y', timestamp)
		self.xmag = self.getMagCal(tem, ccd, 'x', ht, mag, timestamp)
		self.ymag = self.getMagCal(tem, ccd, 'y', ht, mag, timestamp)
		self.stagematrixcal = self.getMatrixCal(tem, ccd, ht, mag, timestamp, 'stage position')
		self.imagematrixcal = self.getMatrixCal(tem, ccd, ht, mag, timestamp, 'image shift')
		self.rotation = rotation
		self.createMatrix()

	def rotationMatrix(self, angle):
		mat = numarray.array(
			(
				(numarray.cos(angle),-numarray.sin(angle)),
				(numarray.sin(angle), numarray.cos(angle))
			), numarray.Float32
		)
		return mat

	def createMatrix(self):
		if None in (self.xmag, self.ymag):
			self.matrix = self.stagematrixcal
		else:
			xscale = self.xmag['mean']
			yscale = self.ymag['mean']
			xang = self.xmag['angle']
			yang = self.ymag['angle']
			self.matrix = numarray.array(
				((xscale * numarray.sin(xang) , xscale * numarray.cos(xang)),
				(yscale * numarray.sin(yang) , yscale * numarray.cos(yang))), numarray.Float32
			)

		rot = self.rotationMatrix(self.rotation)
		self.matrix = numarray.matrixmultiply(self.matrix, rot)
		self.imatrix = numarray.linear_algebra.inverse(self.matrix)

	def createExtraMatrix(self):
		xscale = 0.96
		yscale = 1.0
		xang = 1.5708
		yang = -0.12
		matrix = numarray.array(
			((xscale * numarray.sin(xang) , xscale * numarray.cos(xang)),
			(yscale * numarray.sin(yang) , yscale * numarray.cos(yang))), numarray.Float32
		)

		rot = self.rotationMatrix(self.rotation)
		matrix = numarray.matrixmultiply(matrix, rot)
		imatrix = numarray.linear_algebra.inverse(matrix)
		
		return matrix

	def itransform(self, position, stage0, bin,extra=False):
		'''
		Calculate a pixel offset from the center of an image that
		corresponds to the given real world position.
		'''
		gx0 = stage0['x']
		gy0 = stage0['y']
		gx1 = position['x']
		gy1 = position['y']
		binx = bin['x']
		biny = bin['y']

		## integrate over model
		if None in (self.xmod, self.ymod):
			dgx = gx1 - gx0
			dgy = gy1 - gy0
		else:
			dgx = self.xmod.integrate(gx0,gx1)
			dgy = self.ymod.integrate(gy0,gy1)
		## rotate/scale
		if not extra:
			drow,dcol = -numarray.matrixmultiply(self.imatrix, (dgx,dgy))
		else:
			newmatrix = -numarray.matrixmultiply(self.imatrix, (dgx,dgy))
			extramatrix = self.createExtraMatrix()
			drow,dcol = numarray.matrixmultiply(newmatrix,extramatrix)

		pixelshift = {'row': drow/biny, 'col': dcol/binx}
		return pixelshift
	
	def transform(self, pixvect, stage0, bin):
		'''
		Calculate a real world position corresponding to a pixel offset
		from the center of an image.
		'''
		gx0 = stage0['x']
		gy0 = stage0['y']
		binx = bin['x']
		biny = bin['y']

		pixrow = pixvect['row'] * biny
		pixcol = pixvect['col'] * binx
	
		dgx,dgy = -numarray.matrixmultiply(self.matrix, (pixrow,pixcol))

		if None not in (self.xmod, self.ymod):
			dgx = self.xmod.predict(gx0,dgx)
			dgy = self.ymod.predict(gy0,dgy)

		return {'x':gx0+dgx, 'y':gy0+dgy}
		
	def getMagCal(self, tem, ccd, axis, ht, mag, timestamp):
		qinst = data.StageModelMagCalibrationData(magnification=mag, axis=axis)
		qinst['high tension'] = ht
		qinst['tem'] = tem
		qinst['ccdcamera'] = ccd
	
		caldatalist = dbdk.query(qinst)
	
		# get the one that was valid at timestamp
		caldata = None
		for cal in caldatalist:
			if cal.timestamp < timestamp:
				caldata = dict(cal)
				break

		if caldata is None:
			if caldatalist:
				caldata = dict(caldatalist[0])
			else:
				caldata = None
	
		return caldata
	
	def getModelCal(self, tem, ccd, axis, timestamp):
		qinst = data.StageModelCalibrationData(axis=axis)
		qinst['tem'] = tem
		qinst['ccdcamera'] = ccd
		caldatalist = dbdk.query(qinst)
	
		# get the one that was valid at timestamp
		caldata = None
		for cal in caldatalist:
			if cal.timestamp < timestamp:
				caldata = cal
				break

		if caldata is None:
			if caldatalist:
				caldata = caldatalist[0]
			else:
				return None
	
		## return it to rank 0 array
		caldata2 = {}
		caldata2['axis'] = caldata['axis']
		caldata2['period'] = caldata['period']
		caldata2['a'] = numarray.ravel(caldata['a']).copy()
		caldata2['b'] = numarray.ravel(caldata['b']).copy()
		mod = gonmodel.GonModel()
		mod.fromDict(caldata2)
		return mod

	def getMatrixCal(self, tem, ccd, ht, mag, timestamp, type):
		qinst = data.MatrixCalibrationData(type=type, magnification=mag)
		qinst['high tension'] = ht
		qinst['tem'] = tem
		qinst['ccdcamera'] = ccd
	
		caldatalist = dbdk.query(qinst)
	
		# get the one that was valid at timestamp
		caldata = None
		for cal in caldatalist:
			if cal.timestamp < timestamp:
				caldata = cal['matrix']
				break

		if caldata is None:
			if caldatalist:
				caldata = caldatalist[0]['matrix']
			else:
				caldata = None
	
		return caldata

def test():
	import datetime
	# hole transformer
	qhole = data.AcquisitionImageData(filename='07mar29b_00010gr_00012sq_v02_00011hl')
	images = dbdk.query(qhole, readimages=False)
	im = images[0]
	hlscope = im['scope']
	hlcamera = im['camera']
	hltrans = getTransformer(hlscope['tem'], hlcamera['ccdcamera'], hlscope['high tension'], hlscope['magnification'], im.timestamp)

	# square transformer
	qsq = data.AcquisitionImageData(filename='07mar29b_00010gr_00012sq')
	images = dbdk.query(qsq, readimages=False)
	im= images[0]
	sqscope = im['scope']
	sqcamera = im['camera']
	sqtrans = getTransformer(sqscope['tem'], sqcamera['ccdcamera'], sqscope['high tension'], sqscope['magnification'], datetime.datetime(2007,4,10,0,0,0))


	## get stage position of target on hole image
	bin = hlcamera['binning']
	stage0 = hlscope['stage position']
	pixvect = {'row': 0, 'col':0}
	stage = hltrans.transform(pixvect, stage0, bin)
	print 'STAGE', stage

	## get pixel position of stage position on square image
	bin = sqcamera['binning']
	stage0 = sqscope['stage position']
	pix = sqtrans.itransform(stage, stage0, bin)
	print 'PIX', pix



if __name__ == '__main__':
	test()
