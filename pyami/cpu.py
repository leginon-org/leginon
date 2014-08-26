#!/usr/bin/env python

import subprocess
ncpus = None

def count():
	global ncpus
	if ncpus:
		return ncpus
	cmd = '''cat /proc/stat |grep "^cpu[0-9]" | wc -l'''
	p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
	out,err = p.communicate()
	ncpus = int(out)
	return ncpus

if __name__ == '__main__':
	print count()
