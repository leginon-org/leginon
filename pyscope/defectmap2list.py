#!/usr/bin/env python

import numpy
import scipy.ndimage as ndimage
from pyami import mrc

class DefectMapper(object):
	def __init__(self):
		self.linerows = None
		self.linecols = None
		self.points = []
		self.defect_array = None

	def readDefectMap(self,gain_map_path):
		'''
		Read Defect mrc map. The defects have a value of zero.
		'''
		a = mrc.read(gain_map_path)
		self.defect_array = numpy.where(a==0,1,0)

	def makeFakeDefectMap(self,shape):
		a = numpy.ones(shape)
		a[0,:] = 0
		a[200,300] = 0
		a[400,0] = 0
		self.defect_array = numpy.where(a==0,1,0)

	def scaleMap(self,scale):
		self.defect_array = ndimage.interpolation.zoom(self.defect_array,zoom=scale,order=0)

	def cropMap(self,offset,dimension):
		self.defect_array = self.defect_array[offset['y']:dimension['y']+offset['y'], offset['x']:dimension['x']+offset['x']]

	def getLineDefects(self):
		'''
		Find Defects that takes up the whole line
		'''
		self.linerows=self.__getLineIndices(0)
		self.linecols=self.__getLineIndices(1)
		
	def __getLineIndices(self,axis):
		'''
		Quick line defect determination.
		'''
		other_axis=1-axis
		row_length = self.defect_array.shape[axis]
		# collapse the other axis
		row_sum = numpy.sum(self.defect_array,other_axis)
		# find lines with 60% of the pixels are defects
		lines = numpy.where(row_sum>0.4*row_length,True,False)
		line_row_numbers = numpy.where(lines)[0]
		return list(line_row_numbers)

	def getDefects(self):
		# Point defects are those not in any line defects
		point_defect_array = self.defect_array.copy()
		self.getLineDefects()
		# Remove line defects from point_defect_array
		for row in self.linerows:
			point_defect_array[row,:] = 0
		for col in self.linecols:
			point_defect_array[:,col] = 0
		is_point_array = numpy.where(point_defect_array==1,True,False)
		points = numpy.where(is_point_array)
		if points[0].shape[0]:
			for i in range(points[0].shape[0]):
				# points is a tuple of two arrays of rows and cols.
				# The length of each array is the number of points
				# point = (col,row)
				self.points.append((points[1][i],points[0][i]))

if __name__=='__main__':
	app = DefectMapper()
	app.readDefectMap('refs/defect.mrc')
	app.scaleMap({'x':512,'y':512})
	app.cropMap(offset={'x':0,'y':0},dimension={'x':512,'y':512})
	app.getDefects()
	print 'bad rows:',app.linerows
	print 'bad cols:',app.linecols
	print 'bad pixels:',app.points
