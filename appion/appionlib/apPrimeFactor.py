#!/usr/bin/env python

import sys

maxprime = 12
twomult = 2**1

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
def getAllPrimes(maxn=1028):
	goodones = []
	n = 2
	while n < maxn:
		if isGoodPrime(n):
			#print n, factors
			goodones.append(n)
		n += 1
	return goodones

#====================
def getAllEvenPrimes(maxn=1028):
	goodones = []
	n = 2
	while n < maxn:
		if isGoodPrime(n):
			#print n, factors
			goodones.append(n)
		n += 2
	return goodones

#====================
def getNextEvenPrime(num=400):
	goodones = []
	n = num
	while not isGoodStack(n) and n < 10000:
		n += 1
	return n

#====================
def getPrevEvenPrime(num=400):
	goodones = []
	n = num
	while not isGoodStack(n) and n > 1:
		n -= 1
	return n

#====================
def getPrimeLimits(num=4):
	prev = getPrevEvenPrime(num)
	next = getNextEvenPrime(num)
	return (prev, next)

#====================
def isGoodPrime(num=4):
	#print num
	factors = prime_factors(num)
	if max(factors) < maxprime:
		return True
	return False

#====================
def isGoodStack(num=4):
	if num % twomult != 0:
		return False
	return isGoodPrime(num)

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
			
