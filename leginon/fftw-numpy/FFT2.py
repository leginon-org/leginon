#!/usr/bin/env python

import Numeric, fftw, types

_fftw_cache = {}
_fftwnd_cache = {}
_rfftwnd_cache = {}

def _raw_fft(a, n=None, axis=-1, init_function=fftw.fftw_create_plan, 
		work_function=fftw.fftw, fft_cache = _fftw_cache,
	        direc = fftw.FFTW_FORWARD, init_type = fftw.FFTW_ESTIMATE):
	
	a = Numeric.asarray(a)	

	if n == None: n = a.shape[axis]	

	try:
		wsave = fft_cache[n]
	except(KeyError):
		wsave = init_function(n, direc, init_type)
		fft_cache[n] = wsave

	if a.shape[axis] != n:
		s = list(a.shape)
		if s[axis] > n:
			index = [slice(None)]*len(s)
			index[axis] = slice(0,n)
			a = a[index]
		else:	
			s[axis] = n-s[axis]
			z = Numeric.zeros(s,a.typecode())
			a = Numeric.concatenate( (a,z) , axis=axis)

	a = a.astype('D')

	if (axis not in (-1, len(a.shape))): a = Numeric.swapaxes(a, axis, -1)
	r = Numeric.zeros(a.shape,'D')

	how_many = Numeric.multiply.reduce(a.shape[0:-1])
	dist = a.shape[axis]
	work_function(wsave, how_many, a, 1, dist, r, 1, dist)
	if (axis not in (-1, len(a.shape))): r = Numeric.swapaxes(r, axis, -1)
	return r


def _raw_fftnd(a, ntup=None, axes=None, fft_cache = _fftwnd_cache,
	        workfunction = fftw.fftwnd, initfunction = fftw.fftwnd_create_plan,
	        direc = fftw.FFTW_FORWARD, init_type = fftw.FFTW_ESTIMATE):

	a = Numeric.asarray(a)
	ndim = len(a.shape)

	if axes == None:
		axes = range(ndim)

	axes = list(axes)
	if ntup == None:
		ntup = range(len(axes));
		for k in range(len(axes)):
			ntup[k] = a.shape[axes[k]]
		ntup = tuple(ntup)

	if type(ntup) is types.IntType:
		ntup = range(ntup,ntup+1)
		ntup = tuple(ntup*len(axes))

	nvec = Numeric.asarray(ntup)
	
	try:
		wsave = fft_cache[ntup]
	except(KeyError):
		wsave = initfunction(len(ntup), nvec, direc, init_type)
		fft_cache[ntup] = wsave


      # Zero pad if necessary
	for k in range(0,len(axes),1):
		if axes[k] < 0: axes[k] = axes[k]+ndim
		axis = axes[k]
		n = nvec[k]
		if a.shape[axis] != n:
			s = list(a.shape)
			if s[axis] > n:
				index = [slice(None)]*len(s)
				index[axis] = slice(0,n)
				a = a[index]
			else:	
				s[axis] = n-s[axis]
				z = Numeric.zeros(s,a.typecode())
				a = Numeric.concatenate( (a,z) , axis=axis)

	a = a.astype('D')

	needed_axes = range(ndim-len(axes),ndim)

	axes = Numeric.sort(axes).tolist()
	if (axes != needed_axes): 	# Transpose if necessary
		newaxis = []
		for k in range(ndim):
			if k not in axes:
				newaxis.append(k)
		newaxis = newaxis + axes
		a = Numeric.transpose(a,newaxis)

	r = Numeric.zeros(a.shape,'D')
	how_many = Numeric.multiply.reduce(a.shape[0:-len(axes)])
	dist = Numeric.multiply.reduce(a.shape[ndim-len(axes):ndim])
	workfunction(wsave, how_many, a, 1, dist, r, 1, dist)

	if (axes != needed_axes):       # Transpose back
		r = Numeric.transpose(r,argsort(newaxis))
			
	return r


def fft(a, n=None, axis=-1):
	return _raw_fft(a, n, axis, fftw.fftw_create_plan, fftw.fftw, _fftw_cache, fftw.FFTW_FORWARD, fftw.FFTW_ESTIMATE)
	

def ifft(a, n=None, axis=-1): 
	if n == None: n = a.shape[axis]
	return _raw_fft(a, n, axis, fftw.fftw_create_plan, fftw.fftw, _fftw_cache, fftw.FFTW_BACKWARD, fftw.FFTW_ESTIMATE)/n


def fft2d(a, s=None, axes=(-2,-1)):
	if (len(axes) != 2):
		raise ValueError, 'Incorrect axes argument for 2-D'
	return _raw_fftnd(a,s,axes)

def ifft2d(a, s=None, axes=(-2,-1)):
	if (len(axes) != 2):
		raise ValueError, 'Incorrect axes argument for 2-D'
	a = Numeric.asarray(a)
	if s == None:
		s = []
		for k in range(0,2):  s.append(a.shape[axes[k]])	
	return _raw_fftnd(a,s,axes,direc=fftw.FFTW_BACKWARD)/Numeric.product(s)

def fft3d(a, s=None, axes=(-3,-2,-1)):
	return _raw_fftnd(a,s,axes)

def ifft3d(a, s=None, axes=(-3,-2,-1)):
	if (len(axes) != 3):
		raise ValueError, 'Incorrect axes argument for 2-D'
	a = Numeric.asarray(a)
	if s == None:
		s = []
		for k in range(0,3):  s.append(a.shape[axes[k]])	
	return _raw_fftnd(a,s,axes,direc=fftw.FFTW_BACKWARD)/Numeric.product(s)

#def rfft(a, s=None, axes=(-1)):
#	return _raw_fftnd(a,s,axes,_rfftwnd_cache)

def fftnd(a, s=None, axes=None):
	return _raw_fftnd(a,s,axes)

def ifftnd(a, s=None, axes=(-3,-2,-1)):
	a = Numeric.asarray(a)
	if s == None:
		s = []
		for k in range(0,len(axes)):  s.append(a.shape[axes[k]])
	return _raw_fftnd(a,s,axes,direc=fftw.FFTW_BACKWARD)/Numeric.product(s)


def test():
	print fft( (0,1)*4 )
	print ifft( fft((0,1)*4) )
	print fft( (0,1)*4, n=16 )
	print fft( (0,1)*4, n=4 )

	print fft2d( [(0,1),(1,0)] )
#	print real_fft2d([(0,1),(1,0)] )

if __name__ == '__main__': test()


