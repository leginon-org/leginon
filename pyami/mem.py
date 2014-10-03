#!/usr/bin/env python

import os
import re
import subprocess

def meminfo2dict():
	if not os.path.exists('/proc/meminfo'):
		return meminfo2dictMacOSX()
	f = open('/proc/meminfo', 'r')
	lines = f.readlines()
	f.close()

	info = {}
	for line in lines:
		line = line[:-1]
		parts = line.split(':')
		key = parts[0]
		value = parts[1].strip()
		value = value.split()
		value = int(value[0])
		info[key] = value
	return info

def meminfo2dictMacOSX():
	if not os.path.exists('/usr/bin/vm_stat'):
		return None
	cmd = "/usr/bin/vm_stat"
	proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
	data = proc.stdout.readlines()
	line = data[0]
	m = re.search("page size of ([0-9]+) bytes", line)
	if not m or not m.groups():
		return None
	# want page size in kilobytes
	pagesize = int(m.groups()[0])/1024
	meminfo = {}
	for line in data:
		name,value = line.split(":")
		value = value.strip()
		if name == "Pages free":
			free = float(value)*pagesize
		if name == "Pages active":
			active = float(value)*pagesize
		if name == "Pages inactive":
			inactive = float(value)*pagesize
		if name == "Pages wired down":
			wireddown = float(value)*pagesize
	meminfo['MemTotal'] = int(free + active + inactive + wireddown)
	meminfo['MemFree'] = int(free)
	meminfo['Cached'] = 0
	meminfo['Buffers'] = 0
	meminfo['SwapTotal'] = 0
	meminfo['SwapFree']	= 0
	meminfo['MemUsed'] = int(active + inactive + wireddown)
	return meminfo
	
def stats(meminfo=meminfo2dict()):
	if meminfo is None:
		return
	total = meminfo['MemTotal']
	free = meminfo['MemFree']
	used = total - free
	buffers = meminfo['Buffers']
	cached = meminfo['Cached']
	used2 = used - buffers - cached
	free2 = free + buffers + cached
	swaptotal = meminfo['SwapTotal']
	swapfree = meminfo['SwapFree']
	swapused = swaptotal - swapfree

	print '%10d%10d%10d%10d%10d' % (total, used, free, buffers, cached)
	print '%20d%10d' % (used2, free2)
	print '%10d%10d%10d' % (swaptotal, swapused, swapfree)
	meminfo

def used():
	meminfo = meminfo2dict()
	if meminfo is None:
		return
	used = meminfo['MemTotal'] - meminfo['MemFree']
	return used

def active():
	meminfo = meminfo2dict()
	if meminfo is None:
		return
	used = meminfo['MemTotal'] - meminfo['MemFree'] - meminfo['Cached']
	return used

def free():
	meminfo = meminfo2dict()
	if meminfo is None:
		return
	free = meminfo['MemFree'] + meminfo['Cached']
	return free

def total():
	meminfo = meminfo2dict()
	if meminfo is None:
		return
	total = meminfo['MemTotal']
	return total

def swapused():
	meminfo = meminfo2dict()
	if meminfo is None:
		return
	used = meminfo['SwapTotal'] - meminfo['SwapFree']
	return used

def swapfree():
	meminfo = meminfo2dict()
	if meminfo is None:
		return
	free = meminfo['SwapFree']
	return free

def swaptotal():
	meminfo = meminfo2dict()
	if meminfo is None:
		return
	total = meminfo['SwapTotal']
	return total

multdict = {
	'b': 1,
	'kb': 1024,
	'mb': 1024*1024,
	'gb': 1024*1024*1024,
}

def procStatus(pid=None):
	if pid is None:
		pid = os.getpid()
	f = open('/proc/%d/status' % (pid,))
	statuslines = f.readlines()
	f.close()
	vm = {}
	for statusline in statuslines:
		fields = statusline.split()
		if fields[0][:2] == 'Vm':
			name = fields[0][:-1]
			value = int(fields[1])
			mult = multdict[fields[2].lower()]
			vm[name] = mult*value
	return vm

def mySize():
	status = procStatus()
	return status['VmRSS']

def test():
	mypid = os.getpid()
	print 'mypid', mypid
	print mySize()

if __name__ == '__main__':
	#print used()
	test()
