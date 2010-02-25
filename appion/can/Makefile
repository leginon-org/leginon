
SOURCE = Adapt.cpp Node.cpp Edge.cpp
OBJECTS = Adapt.o Node.o Edge.o

BINPATH=../bin
ARCH=$(shell uname -i)
ifeq ($(ARCH),x86_64)
	EXENAME=can64.exe
else
	EXENAME=can32.exe
endif

ADAPT: ${OBJECTS}
	g++ ${OBJECTS} -o ${BINPATH}/${EXENAME} -g -O2
	chmod 777 ${BINPATH}/${EXENAME}

ADAPT.o: ${SOURCE}
	g++ -c Adapt.cpp -g -O2

Node.o: Node.cpp Node.h
	g++ -c Node.cpp -g -O2

Edge.o: Edge.cpp Edge.h
	g++ -c Edge.cpp -g -O2

clean:
	rm -fv *.o core

