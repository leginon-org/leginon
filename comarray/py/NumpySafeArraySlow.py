'''
This is the slow way of getting a com safe array variant into a numpy array.
First we get a tuple, then convert to numpy array.
'''

import numpy

def call(obj, name):
	func = getattr(obj, name)
	t = func()
	return numpy.array(t)
	
def prop(obj, name):
	t = getattr(obj, name)
	return numpy.array(t)
