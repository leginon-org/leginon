PY = /usr/include/python

mosaic.so: mosaic.c
	gcc mosaic.c -g -I$(PY) -fpic -shared -o mosaic.so

clean:
	rm -f mosaic.so core

install:
	cp mosaic.so /ami/sw/lib/python
