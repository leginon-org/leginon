from xmlrpclib import *
import cStringIO
import Image
import Mrc
try:
	import numarray as Numeric
except:
	import Numeric
import types

try:
	import radix64

	def decode(self, data):
		self.data = radix64.decode(data)

	def encode(self, out):
		out.write("<value><base64>\n")
		e = radix64.encode(self.data)
		out.write(e)
		out.write("</base64></value>\n")

	Binary.decode = decode
	Binary.encode = encode
except ImportError:
	pass

def dump_Numeric_array(self, value, write):
	self.dump_instance(Binary(Mrc.numeric_to_mrcstr(value)), write)

def dump_instance(self, value, write):
	if value.__class__ == Image.Image:
		stream = cStringIO.StringIO()
		value.save(stream, 'jpeg')
		value = xmlrpclib.Binary(stream.getvalue())
		stream.close()
		self.dump_instance(Binary(value), write)
	else:
		self.dump_instance(value, write)

Marshaller.dispatch[Numeric.ArrayType] = dump_Numeric_array
Marshaller.dispatch[types.InstanceType] = dump_instance

