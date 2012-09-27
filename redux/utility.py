'''
functions useful to either client or server
'''

import itertools
import numpy

jsonmod = None
try:
	import json
	jsonmod = 'json'
except:
	try:
		import demjson
		jsonmod = 'demjson'
	except:
		pass
if jsonmod is None:
	raise ImportError('you need either need a newer version of python (>=2.6) that includes a json module, or you can install demjson for older versions of python.')

def request_to_kwargs(request):
	'''convert request string into keyword args'''
	args = request.split('&')
	key_value = itertools.imap(str.split, args, itertools.repeat('='))
	kwargs = {}
	for key,value in key_value:
		kwargs[key.strip()] = value.strip()
	return kwargs

def kwargs_to_request(**kwargs):
	'''convert keyword args to a request string'''
	args = ['%s=%s' % (key,value) for (key, value) in kwargs.items()]
	request = '&'.join(args)
	return request

## Extra things we would like to convert to JSON compatible
def json_convert(obj):
		## convert numpy types to built-in python types
		if isinstance(obj, numpy.bool_):
			return bool(obj)
		elif isinstance(obj, numpy.integer):
			return long(obj)
		elif isinstance(obj, numpy.floating):
			return float(obj)
		elif isinstance(obj, numpy.complexfloating):
			return complex(obj)
		elif isinstance(obj, numpy.dtype):
			return str(obj)
		elif isinstance(obj, numpy.ndarray):
			return obj.tolist()	
		elif isinstance(obj, buffer):
			return str(obj)
		raise ValueError('cannot convert %s' % (obj,))

## now use the conversion function in either of the two modules
if jsonmod == 'demjson':
	class ReduxJSON(demjson.JSON):
		def encode_default(self, obj, nest_level=0):
			newobj = json_convert(obj)
			return self.encode(newobj, nest_level)
	json_inst = ReduxJSON()
	json_encode = json_inst.encode

elif jsonmod == 'json':
	class ReduxJSONEncoder(json.JSONEncoder):
		def default(self, obj):
			try:
				return json_convert(obj)
			except ValueError:
				return json.JSONEncoder.default(self, obj)
	
	def json_encode(input):
			outstring = json.dumps(input, cls=ReduxJSONEncoder)
			return outstring
else:
	raise ImportError('What?')


