import node
import Mrc
import xmlrpclib
import Numeric

class ImageNode(node.Node):
	def __init__(self, id, nodelocations, **kwargs):
		node.Node.__init__(self, id, nodelocations, **kwargs)
		self.start()

	def main(self):
		pass

	def defineUserInterface(self):
		nodespec = node.Node.defineUserInterface(self)

		### Acquire Bright/Dark

		ret = self.registerUIData('Image', 'binary')
		getimage = self.registerUIMethod(self.uiGetCameraImage, 'Get Camera Image', (), returnspec=ret)

		typechoices = self.registerUIData('types', 'array', default=('unsigned byte', 'short', 'float'))
		argspec = (
			self.registerUIData('MRC Type', 'string', choices=typechoices, default='short'),
			self.registerUIData('Width', 'integer', default=256),
			self.registerUIData('Height', 'integer', default=256)
		)
		getimagegrad = self.registerUIMethod(self.uiGetGradientImage, 'Get Gradient Image', argspec, returnspec=ret)


		arg = self.registerUIData('Your String', 'string', default='default string')
		ret = self.registerUIData('My String', 'string')
		changestr = self.registerUIMethod(self.uiChangeString, 'To Upper', (arg,), returnspec=ret)

		self.registerUISpec('Image Node', (getimage, getimagegrad, changestr, nodespec))

	def uiGetCameraImage(self):
		numarray = Mrc.mrc_to_numeric('test1.mrc')
		mrcstr = Mrc.numeric_to_mrcstr(numarray)
		return xmlrpclib.Binary(mrcstr)

	def gradientfun(self, row, col):
		val = 256.0 * row / self.rows
		return val

	def uiGetGradientImage(self, mrctype='short', width=256, height=256):
		if mrctype == 'unsigned byte':
			typecode = Mrc.mrcmode_typecode[0][1]
		elif mrctype == 'short':
			typecode = Mrc.mrcmode_typecode[1][1]
		elif mrctype == 'float':
			typecode = Mrc.mrcmode_typecode[2][1]

		self.rows = height
		self.cols = width

		numarray = Numeric.fromfunction(self.gradientfun, (height, width)).astype(typecode)
		Mrc.numeric_to_mrc(numarray, 'gradient.mrc')
		print 'saved gradient.mrc'
		mrcstr = Mrc.numeric_to_mrcstr(numarray)
		return xmlrpclib.Binary(mrcstr)

	def uiChangeString(self, mystring=''):
		return mystring.upper()
