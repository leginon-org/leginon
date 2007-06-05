#!/usr/bin/env python

import sys
import mrc

f1 = open(sys.argv[1])
headerbytes = f1.read(1024)
f1.close()
h1 = mrc.parseHeader(headerbytes)

f2 = open(sys.argv[2])
headerbytes = f2.read(1024)
f2.close()
h2 = mrc.parseHeader(headerbytes)

for key in h1:
	if h1[key] != h2[key]:
		print '%s:   %s -> %s' % (key, h1[key], h2[key])

f1 = open(sys.argv[1])
f2 = open(sys.argv[2])
count = 0
while True:
	bytes1 = f1.read(4)
	bytes2 = f2.read(4)
	if bytes1 != bytes2:
		print 'bytes:  %s-%s' % (count,count+3)
	count += 4
	if not (bytes1 or bytes2):
		break
