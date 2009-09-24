'''
convenience functions for displayed power spectrum
'''
import math

def getAstigmaticDefocii(params,rpixelsize, ht):
	minr = rpixelsize * min(params['a'],params['b'])
	maxz = calculateDefocus(ht,minr)
	maxr = rpixelsize * max(params['a'],params['b'])
	minz = calculateDefocus(ht,maxr)
	z0 = (maxz + minz) / 2
	zast = maxz - za
	ast_ratio = zast / z0
	if maxr == params['b']:
		params['alpha'] + math.pi / 2
	return z0, zast, ast_ratio, params['alpha']

def calculateDefocus(ht, s, Cs=2.0e-3):
		# unit is meters
	Cs = 2.0e-3
	wavelength = 3.7e-12 * 1e5 / ht
	return (Cs*wavelength**3*s**4/2+1)/(wavelength * s**2)
