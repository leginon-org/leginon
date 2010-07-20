#!/usr/bin/python

import numpy
from numpy import random
import time
import math
from appionlib import apDisplay


def getArea(i, j, k):
	a = j - i
	b = k - i
	area = abs(a[0]*b[1] - a[1]*b[0])
	return float(area)


def tiltang(picks1, picks2, arealim=1000.0, maxtri=10000, speed=30.0):
	leng = picks1.shape[0]
	choo = leng*(leng-1)*(leng-2)/6
	arealimsq = float(arealim**2)

	#counting variables
	datadict = {
	 'badarea': 0,
	 'badlen': 0,
	 'posstri': choo,
	 'numtri': 0,
	 'tottri': 0,
	 'sum': 0,
	 'sumsq': 0,
	 'wtot': 0,
	 'wsum': 0,
	 'wsqtot': 0,
	 'wsumsq': 0,
	}

	apDisplay.printMsg("%d picks, %d operations, %s"
		%(leng, choo, apDisplay.timeString(choo*speed*1e-6)))
	t0 = time.time()
	for i in range(leng):
		for j in range(i+1, leng):
			for k in range(j+1, leng):
				datadict['tottri'] += 1
				area1 = getArea(picks1[i,:], picks1[j,:], picks1[k,:])
				if area1 < arealim:
					datadict['badarea'] += 1
					continue
				area2 = getArea(picks2[i,:], picks2[j,:], picks2[k,:])
				if area2 < arealim:
					datadict['badarea'] += 1
					continue
				ratio = area2 / area1
				if area1 > area2:
					theta = math.acos(area2 / area1)
				else:
					theta = -1.0*math.acos(area1 / area2)
				weight = float(area1 + area2) / (arealim + 500.0)
				datadict['numtri'] += 1
				datadict['sum'] +=    theta
				datadict['sumsq'] +=  theta**2
				datadict['wtot'] +=   weight
				datadict['wsqtot'] += weight**2
				datadict['wsum'] +=   theta*weight
				datadict['wsumsq'] += theta**2*weight
				if datadict['numtri'] > maxtri:
					break

	if datadict['numtri'] < 1:
		apDisplay.printWarning("No triangles could be made from the picks")
		return datadict

	#time stats
	#print choo
	datadict['time'] = time.time()-t0
	datadict['speed'] = datadict['time']/float(datadict['tottri'])*1.0e6
	apDisplay.printMsg(apDisplay.timeString(datadict['time'])+" "+str(datadict['speed'])+" ns/oper")

	#post-analysis
	datadict['theta'] = datadict['sum'] / datadict['numtri']*180.0/math.pi
	datadict['wtheta'] = datadict['wsum'] / datadict['wtot']*180.0/math.pi
	top = datadict['numtri']*datadict['sumsq'] - datadict['sum']*datadict['sum'];
	if( top < 0.001 ) :
		datadict['thetadev'] = 0
	else:
		datadict['thetadev'] = math.sqrt( top / (datadict['numtri'] * (datadict['numtri'] - 1.0)) )
	datadict['thetadev'] *= 180.0/math.pi

	wtop = datadict['wsumsq']*datadict['wtot'] - datadict['wsum']*datadict['wsum']
	wbot = datadict['wtot']*datadict['wtot'] - datadict['wsqtot']
	datadict['wthetadev'] = math.sqrt(wtop/wbot);
	datadict['wthetadev'] *= 180.0/math.pi

	#print datadict
	return datadict


if __name__ == '__main__':
	leng = 350
	picks1 = random.random_integers(0, 1024, (leng,2))
	picks2 = random.random_integers(0, 1024, (leng,2))
	tiltang(picks1, picks2)


