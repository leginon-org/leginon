
import leginonconfig
import sinedon.newdict
import sinedon.data
import os
from pyami import weakattr
import leginondata

Data = sinedon.data.Data

class EpuGridSquareData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('name', str),
			('time_string', str),
			('version', int),
			('image', AcquisitionImageData),
		)
	typemap = classmethod(typemap)

class EpuHoleFoilData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('name', str),
			('time_string', str),
			('version', int),
			('image', AcquisitionImageData),
			('grid_square', GridSquareData),
		)
	typemap = classmethod(typemap)

class EpuEnData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('name', str),
			('time_string', str),
			('version', int),
			('image', AcquisitionImageData),
			('hole_foil', EpuHoleFoilData),
		)
	typemap = classmethod(typemap)

