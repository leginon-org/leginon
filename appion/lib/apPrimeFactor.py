#!/usr/bin/env python

import sys

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

if __name__ == "__main__":
	if len(sys.argv) > 1:
		n = int(sys.argv[1])
		factors = prime_factors(n)
		print n, factors
	else:
		goodones = []
		for i in range(400):
			n = i+2
			factors = prime_factors(n)
			if max(factors) < 13:
				print n, factors
				goodones.append(n)
		print goodones
			
