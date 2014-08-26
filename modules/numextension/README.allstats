
allstats() is a replacement to these built in functions of numpy/scipy:
	min()
	max()
	mean()
	std()
Those built-in functions have the following disadvantages:
  1) Sometimes they create one or more copies of the input array.  For very
	   large arrays, this can lead to running out of memory.
	2) Sometimes they return the wrong result.  This is because intermediate
	   result buffers use the same precision as the input array, which may not
		 be enough for the final result.

allstats() is better because it calculates the statistics using a single
pass through the input array without making any copies of the array.  The
result is calculated using double precision float, so it can handle any
input type.

There are two known disadvantage of using allstats:
	1) It could be slower than the built in functions (not tested)
	2) It does not have the option of calculating along a certain axis of
     an array.  It only calculates the global stats of the array.

A test script (testallstats.py) is provided to demonstrate the difference
between allstats() and the built-in functions.  If improvements are made to
numpy/scipy, the test may demonstrate that allstats is no longer necessary.
Therefore, anytime numpy/scipy version is updated, this should be tested.
