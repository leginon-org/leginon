
# ------------------ Compilation options ------------------------

# Loads math library.  
CVLIBS = -lm -lobjc -lfftw3 -lgsl -lgslcblas

# Flags for the C compiler:
#   -Wall for strict gcc warnings (requires prototypes for all functions).
#   -g to produce debug data for gdb
#   -O for optimization

CFLAGS = -O3

CC = gcc 

# --------------------- Code modules ----------------------------

# Object files

CVOBJ1= ace2.o cvtypes.o Array.o MRC.o PGM.o util.o Image.o Ellipse.o geometry.o getopts.o ctf.o
CVOBJ2= ace2correct.o cvtypes.o Array.o MRC.o PGM.o util.o Image.o Ellipse.o geometry.o getopts.o ctf.o
CVOBJ3= testf.o cvtypes.o Array.o MRC.o PGM.o util.o Image.o Ellipse.o geometry.o getopts.o ctf.o

# Definitions

CVDEFS= 

# ------------------------ Rules --------------------------------

all:	ace2 ace2correct testf

ace2: ${CVOBJ1}
	${CC} -o $@ ${CFLAGS} ${CVOBJ1} ${CVLIBS}

ace2correct: ${CVOBJ2}
	${CC} -o $@ ${CFLAGS} ${CVOBJ2} ${CVLIBS}
	
testf: ${CVOBJ3}
	${CC} -o $@ ${CFLAGS} ${CVOBJ3} ${CVLIBS}

# Implicit rule used by Gnu Make: $(CC) -c $(CPPFLAGS) $(CFLAGS)
%.o : %.m
	$(CC) -c $(CFLAGS) $< -o $@
