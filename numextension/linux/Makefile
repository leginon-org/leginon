PY = /home/suloway/python-2.3.3-2/include/python2.3
NUM = /home/suloway/python-2.3.3-2/include/python2.3/Numeric

numextension.so: ../numextension.c
	gcc ../numextension.c -g -I$(PY) -I$(NUM) -fpic -shared -o numextension.so

clean:
	rm -f numextension.so core
