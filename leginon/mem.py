#!/usr/bin/env python

import subprocess

def meminfo2dict():
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

def stats(meminfo=meminfo2dict()):
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
	used = meminfo['MemTotal'] - meminfo['MemFree']
	return used

def free():
	meminfo = meminfo2dict()
	free = meminfo['MemFree']
	return free

def total():
	meminfo = meminfo2dict()
	total = meminfo['MemTotal']
	return total

def swapused():
	meminfo = meminfo2dict()
	used = meminfo['SwapTotal'] - meminfo['SwapFree']
	return used

def swapfree():
	meminfo = meminfo2dict()
	free = meminfo['SwapFree']
	return free

def swaptotal():
	meminfo = meminfo2dict()
	total = meminfo['SwapTotal']
	return total

if __name__ == '__main__':
	print used()
