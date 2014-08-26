

SOURCE = Adapt.cpp Node.cpp Edge.cpp
OBJECTS = Adapt.o Node.o Edge.o

ADAPT: ${OBJECTS}
	g++ ${OBJECTS} -o CAN -g -O2 -fopenmp

ADAPT.o: ${SOURCE}
	g++ -c Adapt.cpp -g -O2 -fopenmp

Node.o: Node.cpp Node.h
	g++ -c Node.cpp -g -O2 -fopenmp

Edge.o: Edge.cpp Edge.h
	g++ -c Edge.cpp -g -O2 -fopenmp

clean:
	-rm -f *.o core
