#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#
def unique(s):
	n = len(s)
	if n == 0:
		return []

	u = {}
	try:
		for x in s:
			u[x] = 1
	except TypeError:
		del u	# move on to the next method
	else:
		return u.keys()

	try:
		t = list(s)
		t.sort()
	except TypeError:
		del t	# move on to the next method
	else:
		assert n > 0
		last = t[0]
		lasti = i = 1
		while i < n:
			if t[i] != last:
				t[lasti] = last = t[i]
				lasti += 1
			i += 1
		return t[:lasti]

	u = []
	for x in s:
		if x not in u:
			u.append(x)
	return u

