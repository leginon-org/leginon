#!/usr/bin/env python
'''
This is a test of numextension.allstats() and demonstrates why it is
necessary.  Future changes to numpy/scipy may change the behavior of this
demonstration, and make allstats unncessary.
'''

import numpy
import numextension
import os

print 'Demonstration of how allstats is better:'
print ''

a = 500 * numpy.ones((1000,1000), dtype=numpy.float32)
print 'Here is a type float32 array where all elements are set to 500.0:'
print a
print ''

numpy_mean = a.mean()
allstats_result = numextension.allstats(a, mean=True)
allstats_mean = allstats_result['mean']
print 'mean calculated by numpy:  %s' % (numpy_mean,)
print 'mean calculated by allstats:  %s' % (allstats_mean,)
print ''

pid = os.getpid()

print 'Now we will test the memory usage issue.'
print 'You should begin monitoring the memory usage of this process (pid=%d).' % (pid,)
print 'For example, in another terminal, run this:'
print '    top -d 0.5 -b -p %d | grep %d' % (pid,pid)
raw_input('Hit enter to create a large array in memory...')

a = numpy.ones((200, 1024, 1024), dtype=numpy.int16)
memsize = a.size * a.itemsize
megs = memsize / 1024.0 / 1024.0

print 'You should see an increase in memory usage of about %d MB.' % (megs,)
print 'While monitoring the memory usage, hit enter to calculate standard'
print 'deviation on this array using allstats()'
raw_input('Hit enter now...')

numextension.allstats(a, std=True)

print 'You should have noticed cpu go to 100%, but almost no increase in memory.'
raw_input('Hit enter again to calculate standard deviation with numpy.std()...')

a.std()

print 'You should have noticed a significant increase in memory usage.'
