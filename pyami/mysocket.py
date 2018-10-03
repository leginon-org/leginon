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
		return list(configs['my ip map'].keys())[0]  # This is o.k. because I know I only have one key.
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
		except Exception as e:
			raise LookupError(e)
	return ipaddress

def testMapping(hostname):
	try:
		this_ip = gethostbyname(hostname)
		assigned_ip = socket.gethostbyname(hostname)
		if assigned_ip == this_ip:
			return True
		else:
			e = '%s is mapped to %s in the network, not %s' % (hostname, assigned_ip, this_ip)
			raise ValueError(e)
	except Exception as e:
		raise LookupError(e)

def test():
	import testfun
	allmaps = getHostMappings()
	for host in allmaps.keys():
		module = '%s ip mapping' % (host)
		try:
			r = testMapping(host)
			testfun.printResult(module,r)
		except Exception as e:
			testfun.printResult(module,False, e)

if __name__=='__main__':
	test()
	import sys
	if sys.platform == 'win32':
		raw_input('Hit any key to quit.')
