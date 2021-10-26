#/usr/bin/env python
import math
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
		imagedata = leginondata.AcquisitionImageData().direct_query(image_id)
		alpha = imagedata['scope']['stage position']['a']*180.0/math.pi
		alpha_degrees = round(alpha,1)
		if abs(float(alpha_degrees)) < 0.5:
			def0 = avg_def
		avg_def = avg_def - def0
		if alpha_degrees not in ctfdict:
			ctfdict[alpha_degrees] = []
		ctfdict[alpha_degrees].append(avg_def)
	alpha_keys = ctfdict.keys()
	alpha_keys.sort()
	for k in alpha_keys:
		ctfdict[k] = sum(ctfdict[k])/float(len(ctfdict[k]))
	return ctfdict

print readCtfData(filepath)
