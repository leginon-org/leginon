#!/usr/bin/env python

import sys

#====================
def prime_factors(n):
	""" Return the prime factors of the given number. """
	# < 1 is a special case
	if n <= 1:
		return [1]
	factors = []
	lastresult = n
	while True:
		if lastresult == 1:
			break
		c = 2
		while True:
			if lastresult % c == 0:
				break
			c += 1
		factors.append(c)
		lastresult /= c
	return factors

#====================
def getAllPrimes(maxn=400):
	goodones = []
	n = 2
	while True:
		factors = prime_factors(n)
		if max(factors) < 13:
			print n, factors
			goodones.append(n)
			if (n > maxn):
				break
		n += 1
	return goodones

#====================
def getNextPrime(num=400):
	goodones = []
	n = num
	while not isGoodPrime(n) and n < 10000:
		n += 1
	return n

#====================
def getPrevPrime(num=400):
	goodones = []
	n = num
	while not isGoodPrime(n) and n > 1:
		n -= 1
	return n

#====================
def getPrimeLimits(num=4):
	prev = getPrevPrime(num)
	next = getNextPrime(num)
	return (prev, next)

#====================
def isGoodPrime(num=4):
	print num
	factors = prime_factors(num)
	if max(factors) < 13:
		return True
	return False

#====================
if __name__ == "__main__":
	if len(sys.argv) > 1:
		n = int(sys.argv[1])
		factors = prime_factors(n)
		print n, factors
		prev, next = getPrimeLimits(n)
		print "Use %d or %d instead"%(prev,next)
	else:
		print getAllPrimes()
			
