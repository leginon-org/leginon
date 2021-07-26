#/usr/bin/env python
from leginon import leginondata
filepath = raw_input('filepath ? ')

def readCtfData(filepath):
	f = open(filepath, 'r')
	lines = f.readlines()
	ctfdict = {}
	for l in lines[1:]:
		bits = l.split('\t')
		image_id = int(bits[0])
		def1 = float(bits[2])
		def2 = float(bits[3])
		avg_def = (def1+def2)/2
		print image_id, avg_def*1e6

readCtfData(filepath)
