import node
import Mrc
import xmlrpclib

class ImageNode(node.Node):
	def __init__(self, id, nodelocations):
		node.Node.__init__(self, id, nodelocations)
		self.start()

	def main(self):
		pass

	def defineUserInterface(self):
		nodespec = node.Node.defineUserInterface(self)

		### Acquire Bright/Dark
		ret = self.registerUIData('Image', 'binary')
		getimage = self.registerUIMethod(self.uiGetImage, 'Get Image', (), returnspec=ret)

		arg = self.registerUIData('Your String', 'string', default='default string')
		ret = self.registerUIData('My String', 'string')
		changestr = self.registerUIMethod(self.uiChangeString, 'To Upper', (arg,), returnspec=ret)

		self.registerUISpec('Image Node', (getimage, changestr, nodespec))

	def uiGetImage(self):
		numarray = Mrc.mrc_to_numeric('test1.mrc')
		mrcstr = Mrc.numeric_to_mrcstr(numarray)
		return xmlrpclib.Binary(mrcstr)

	def uiChangeString(self, mystring=''):
		return mystring.upper()
