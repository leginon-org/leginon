#!/usr/bin/env python

import sys
import math

maxprime = 12
twomult = 2**2

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
		n += 2
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
	"""
	Boxsize rules:
	(1) no prime factor greater than 11
	(2) if greater than 4^x, must be multiple of 2^x, 
	"""

	#print num
	factors = prime_factors(num)
	if num % 4 != 0:
		return False
	if num > 32 and num % 8 != 0:
		return False
	if num > 256 and num % 16 != 0:
		return False
	### get the number of powers of 4 in number
	power = int(math.floor(math.log(float(num))/math.log(4.0)))
	### check to make sure number is divisible by 2 to that power
	mod = int(2**power)
	print num, power, mod
	if num % mod != 0:
		return False
	if num > 256 and num % 16 != 0:
		return False
	if max(factors) > maxprime:
		return False
	return True

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
			
