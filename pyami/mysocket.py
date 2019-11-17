#!/usr/bin/env python
import socket

from pyami import moduleconfig

def getDefaultConfigs():
	dconfig = {}
	myname = socket.gethostname().lower()
	myaddress = socket.gethostbyname(myname)
	dconfig['my ip map'] = {myname:myaddress}
	return dconfig

try:
	configs = moduleconfig.getConfigured('pyami.cfg', package='pyami')
except:
	configs = getDefaultConfigs()

def getLoadedConfigs():
	return moduleconfig.getConfigured('pyami.cfg', package='pyami')

def getHostMappings():
	hostdict = configs['my ip map'].copy()
	if 'other ip map' in configs:
		hostdict.update(configs['other ip map'])
	return hostdict

def gethostname():
	try:
		return configs['my ip map'].keys()[0]
	except:
		KeyError('Missing "my ip map" module in pyami.cfg')

def gethostbyname(hostname):
	lower_hostname = hostname.lower()
	try:
		ipaddress = getHostMappings()[lower_hostname]
	except KeyError:
		ipaddress = None
	if not ipaddress:
		try:
			ipaddress = socket.gethostbyname(lower_hostname)
		except Exception, e:
			raise LookupError(e)
	return ipaddress

def testMapping(addr, host):
	'''
	Test that the address in pyami.cfg is mapped to the assigned hostname.
	'''
	try:
		socket_host = socket.gethostbyaddr(addr)[0]
		assigned_host = host
		if assigned_host == socket_host:
			return True
		else:
			e = '%s is mapped to %s in the network, not %s' % (addr, socket_host, assigned_host)
			raise ValueError(e)
	except socket.herror, e:
			e = '%s mapping error in socket module: %s of %s' % (addr, e, addr)
			raise ValueError(e)
	except Exception, e:
		raise LookupError(e)

def test():
	import testfun
	allmaps = getHostMappings()
	for host in allmaps.keys():
		module = '%s ip mapping' % (host)
		addr = allmaps[host]
		try:
			r = testMapping(addr, host)
			testfun.printResult(module,r)
		except Exception, e:
			testfun.printResult(module,False, e)

if __name__=='__main__':
	test()
	import sys
	if sys.platform == 'win32':
		raw_input('Hit any key to quit.')
