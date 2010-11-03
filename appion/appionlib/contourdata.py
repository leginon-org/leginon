
import sinedon
import leginondata

class ApContour(sinedon.Data):
	def typemap(cls):
		return sinedon.Data.typemap() + (
			('name', str),
			('image', leginondata.AcquisitionImageData),
			('x', float),
			('y', float),
			('version', int),
			('method', str),
			('particleType', str),
			('runID', str),
		)
	typemap = classmethod(typemap)

class ApContourPoint(sinedon.Data):
	def typemap(cls):
		return sinedon.Data.typemap() + (
			('contour', ApContour),
			('x', float),
			('y', float),
		)
	typemap = classmethod(typemap)
