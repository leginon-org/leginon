PY = /home/pulokas/py24/local/include/python2.4
NUM = /home/pulokas/py24/include/python2.4/numarray

numextension.so: ../numextension.c
	gcc ../numextension.c -g -I$(PY) -I$(NUM) -lm -fpic -shared -o numextension.so

clean:
	rm -f numextension.so core
