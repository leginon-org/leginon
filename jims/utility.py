'''
functions useful to either client or server
'''

import itertools

## Server accepts connections on this port
REDUX_PORT = 55123

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
