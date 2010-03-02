
SOURCE = Adapt.cpp Node.cpp Edge.cpp
OBJECTS = Adapt.o Node.o Edge.o

#BINPATH=../bin
BINPATH=.
FLAGS=-static -O2
ARCH=$(shell uname -i)
ifeq ($(ARCH),x86_64)
	EXENAME=can64.exe
	ARCHFLAG=-m64
else
	EXENAME=can32.exe
	ARCHFLAG=-m32
endif

ADAPT: ${OBJECTS}
	g++ ${OBJECTS} -o ${BINPATH}/${EXENAME} -g ${FLAGS} ${ARCHFLAG}
	chmod 777 ${BINPATH}/${EXENAME}

Adapt.o: Adapt.cpp
	g++ -c Adapt.cpp -g ${FLAGS} ${ARCHFLAG}

Node.o: Node.cpp Node.h
	g++ -c Node.cpp -g ${FLAGS} ${ARCHFLAG}

Edge.o: Edge.cpp Edge.h
	g++ -c Edge.cpp -g ${FLAGS} ${ARCHFLAG}

clean:
	rm -fv *.o core

