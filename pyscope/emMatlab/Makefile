#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#
DIST=Makefile em.c em.h em.o em.so emTCL.so
ROOT=/home/suloway

emTCL.so: em.so emTCL.c
	gcc -g -fPIC -Xlinker -shared -I. -I$(ROOT)/include/python2.2 -L. emTCL.c em.so -o emTCL.so

em.so: em.c em.h
	gcc -g -fPIC -Xlinker -shared -I$(ROOT)/include/python2.2 -I. -Xlinker -export-dynamic -L$(ROOT)/lib/python2.2/config em.c -o em.o -lpython2.2 -lm -lutil -lpthread -ldl -lc -o em.so

clean:
	rm em.so emTCL.so
