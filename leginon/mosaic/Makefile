#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#
PY = /usr/include/python

mosaic.so: mosaic.c
	gcc mosaic.c -g -I$(PY) -fpic -shared -o mosaic.so

clean:
	rm -f mosaic.so core

install:
	cp mosaic.so /ami/sw/lib/python
