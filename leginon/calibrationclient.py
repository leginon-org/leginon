import data
import Numeric
import LinearAlgebra
import math
import copy

class CalibrationClient(object):
	'''
	this is a component of a node that needs to use calibrations
	'''
	def __init__(self, node):
		self.node = node

	def getCalibration(self, key):
		try:
			cal = self.node.researchByDataID('calibrations')
		except:
			print 'CalibrationClient unable to use calibrations.  Is a CalibrationLibrary node running?'
			raise
		try:
			calvalue = cal.content[key]
		except KeyError:
			print '%s has not been calibrated' % (key,)
			raise
			
		return calvalue

	def setCalibration(self, key, calibration):
		newdict = {key: calibration}
		dat = data.CalibrationData('calibrations', newdict)
		self.node.publishRemote(dat)

	def magCalibrationKey(self, magnification, caltype):
		'''
		this determines the key in the main calibrations dict
		where a magnification dependent calibration is located
		'''
		return str(int(magnification)) + caltype

	def transform(self, pixelshift, scope, camera):
		'''
		pixelshift is a shift from the center of an image acquired
		under the conditions specified in scope and camera
		Implementation should return a modified scope state that induces the desired pixelshift
		'''
		raise NotImplementedError()

	def itransform(self, shift, scope, camera):
		raise NotImplementedError()

class MatrixCalibrationClient(CalibrationClient):
	def __init__(self, node):
		CalibrationClient.__init__(self, node)

	def parameter(self):
		'''
		returns a scope key for the calibrated parameter
		'''
		raise NotImplementedError()

	def setCalibration(self, magnification, measurement):
		key = self.magCalibrationKey(magnification, self.parameter())
		mat = self.measurementToMatrix(measurement)
		CalibrationClient.setCalibration(self, key, mat)

	def measurementToMatrix(self, measurement):
		'''
		convert a mesurement in pixels/[TEM parameter] to a matrix
		in [TEM parameter]/pixel
		'''
		xrow = measurement['x']['row']
		xcol = measurement['x']['col']
		yrow = measurement['y']['row']
		ycol = measurement['y']['col']
		matrix = Numeric.array([[xrow,yrow],[xcol,ycol]],Numeric.Float32)
		matrix = LinearAlgebra.inverse(matrix)
		return matrix

	def matrixAnglePixsize(self, scope, camera):
		mag = scope['magnification']
		binx = camera['binning']['x']
		biny = camera['binning']['y']
		par = self.parameter()

		key = self.magCalibrationKey(mag, par)
		matrix = self.getCalibration(key)

		xvect = matrix[:,0]
		yvect = matrix[:,1]

		xangle = math.atan2(xvect[0], xvect[1])
		xpixsize = math.hypot(xvect[0], xvect[1])
		yangle = math.atan2(yvect[0], yvect[1])
		ypixsize = math.hypot(yvect[0], yvect[1])
		ret = {}
		ret['x'] = {'angle': xangle,'pixel size': xpixsize}
		ret['y'] = {'angle': yangle,'pixel size': ypixsize}
		return ret

	def transform(self, pixelshift, scope, camera):
		'''
		Calculate a new scope state from the given pixelshift
		The input scope and camera state should refer to the image
		from which the pixelshift originates
		'''
		mag = scope['magnification']
		binx = camera['binning']['x']
		biny = camera['binning']['y']
		par = self.parameter()

		pixrow = pixelshift['row'] * biny
		pixcol = pixelshift['col'] * binx
		pixvect = (pixrow, pixcol)

		key = self.magCalibrationKey(mag, par)
		matrix = self.getCalibration(key)
		change = Numeric.matrixmultiply(matrix, pixvect)
		changex = change[0]
		changey = change[1]

		new = copy.deepcopy(scope)
		new[par]['x'] += changex
		new[par]['y'] += changey

		return new

	def itransform(self, shift, scope, camera):
		'''
		Calculate a pixel vector from an image center which 
		represents the given parameter shift.
		'''
		mag = scope['magnification']
		binx = camera['binning']['x']
		biny = camera['binning']['y']
		par = self.parameter()

		vect = (shift['x'], shift['y'])

		key = self.magCalibrationKey(mag, par)
		matrix = self.getCalibration(key)
		matrix = LinearAlgebra.inverse(matrix)

		pixvect = Numeric.matrixmultiply(matrix, vect)
		pixvect /= (biny, binx)
		return {'row':pixvect[0], 'col':pixvect[1]}


class ImageShiftCalibrationClient(MatrixCalibrationClient):
	def __init__(self, node):
		MatrixCalibrationClient.__init__(self, node)

	def parameter(self):
		return 'image shift'

class BeamShiftCalibrationClient(MatrixCalibrationClient):
	def __init__(self, node):
		MatrixCalibrationClient.__init__(self, node)

	def parameter(self):
		return 'beam shift'

class StageCalibrationClient(MatrixCalibrationClient):
	def __init__(self, node):
		MatrixCalibrationClient.__init__(self, node)

	def parameter(self):
		return 'stage position'


import gonmodel
class ModeledStageCalibrationClient(CalibrationClient):
	def __init__(self, node):
		CalibrationClient.__init__(self, node)

	def setMagCalibration(self, magnification, mag_dict):
		key = self.magCalibrationKey(magnification, 'modeled stage position')
		try:
			old_mag_dict = self.getCalibration(key)
			for dictkey in old_mag_dict:
				old_mag_dict[dictkey].update(mag_dict[dictkey])
		except KeyError:
			old_mag_dict = copy.deepcopy(mag_dict)

		self.setCalibration(key, old_mag_dict)

	def getMagCalibration(self, magnification):
		key = self.magCalibrationKey(magnification, 'modeled stage position')
		return self.getCalibration(key)

	def setModel(self, axis, mod_dict):
		key = axis + ' stage position model'
		self.setCalibration(key, mod_dict)

	def getModel(self, axis):
		key = axis + ' stage position model'
		return self.getCalibration(key)

	def transform(self, pixelshift, scope, camera):
		curstage = scope['stage position']

		binx = camera['binning']['x']
		biny = camera['binning']['y']
		pixrow = pixelshift['row'] * biny
		pixcol = pixelshift['col'] * binx

		## do modifications to newstage here
		xmod_dict = self.getModel('x')
		ymod_dict = self.getModel('y')
		mag_dict = self.getMagCalibration(scope['magnification'])
		delta = self.pixtix(xmod_dict, ymod_dict, mag_dict, curstage['x'], curstage['y'], pixcol, pixrow)

		newscope = copy.deepcopy(scope)
		newscope['stage position']['x'] += delta['x']
		newscope['stage position']['y'] += delta['y']
		return newscope

	def pixtix(self, xmod_dict, ymod_dict, mag_dict, gonx, gony, pixx, pixy):
		xmod = gonmodel.GonModel()
		ymod = gonmodel.GonModel()
	
		xmod.fromDict(xmod_dict)
		ymod.fromDict(ymod_dict)
	
		modavgx = mag_dict['model mean']['x']
		modavgy = mag_dict['model mean']['y']
		anglex = mag_dict['data angle']['x']
		angley = mag_dict['data angle']['y']
	
		gonx1 = xmod.rotate(anglex, pixx, pixy)
		gony1 = ymod.rotate(angley, pixx, pixy)
	
		gonx1 = gonx1 * modavgx
		gony1 = gony1 * modavgy
	
		gonx1 = xmod.predict(gonx,gonx1)
		gony1 = ymod.predict(gony,gony1)
	
		return {'x':gonx1, 'y':gony1}
	
	def pixelShift(self, ievent):
		mag = ievent.content['magnification']
		delta_row = ievent.content['row']
		delta_col = ievent.content['column']

		current = self.getStagePosition()
		print 'current before delta', current
		curx = current['stage position']['x']
		cury = current['stage position']['y']

		xmodfile = self.modfilename('x')
		ymodfile = self.modfilename('y')
		magfile = self.magfilename(mag)

		deltagon = self.pixtix(xmodfile,ymodfile,magfile,curx,cury,delta_col,delta_row)

		current['stage position']['x'] += deltagon['x']
		current['stage position']['y'] += deltagon['y']
		print 'current after delta', current

		stagedata = data.EMData('scope', current)
		self.publishRemote(stagedata)
