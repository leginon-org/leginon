#!/usr/bin/env python
import socket

from pyami import moduleconfig
configs = moduleconfig.getConfigured('mysocket.cfg', package='pyami')

def getHostMappings():
	hostdict = configs['my map'].copy()
	hostdict.update(configs['others'])
	return hostdict

def gethostname():
	try:
		return configs['my map'].keys()[0]
	except:
		KeyError('Missing "my map" module in mysocket.cfg')

def gethostbyname(hostname):
	try:
		return getHostMappings()[hostname]
	except:
		return socket.gethostbyname(hostname)

def testMapping(hostname):
	from pyami import testfun
	module = '%s ip mapping' % (hostname)
	try:
		this_ip = gethostbyname(hostname)
		assigned_ip = socket.gethostbyname(hostname)
		if assigned_ip == this_ip:
			testfun.printResult(module,True)
		else:
			e = '%s is mapped to %s in the network, not %s' % (hostname, assigned_ip, this_ip)
			testfun.printResult(module,False, e)
	except Exception, e:
		testfun.printResult(module,False, e)

def test():
	allmaps = getHostMappings()
	for host in allmaps.keys():
		testMapping(host)

if __name__=='__main__':
	test()
	import sys
	if sys.platform == 'win32':
		raw_input('Hit any key to quit.')
