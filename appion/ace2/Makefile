
# ------------------ Compilation options ------------------------

# Loads math library.  
CVLIBS = -lm -lobjc -lfftw3 -lgsl -lgslcblas

# Flags for the C compiler:
#   -Wall for strict gcc warnings (requires prototypes for all functions).
#   -g to produce debug data for gdb
#   -O for optimization

BINPATH=../bin
CC = gcc 
SVNDEF := -D'SVN_REV="$(shell svnversion -n .)"'
CFLAGS := -O3 ${SVNDEF}


# --------------------- Code modules ----------------------------

# Object files

CVOBJ=  cvtypes.o Array.o MRC.o PGM.o util.o Image.o Ellipse.o geometry.o getopts.o ctf.o

# Definitions

CVDEFS= 

# ------------------------ Rules --------------------------------

all: ace2 ace2correct testf

ace2: ${CVOBJ} ace2.o
	${CC} -o $(BINPATH)/$@.exe ${CFLAGS} ace2.o ${CVOBJ} ${CVLIBS}

ace2correct: ${CVOBJ} ace2correct.o
	${CC} -o $(BINPATH)/$@.exe ${CFLAGS} ace2correct.o ${CVOBJ} ${CVLIBS}
	
testf: ${CVOBJ} testf.o
	${CC} -o $@.exe ${CFLAGS} testf.o ${CVOBJ} ${CVLIBS}

# Implicit rule used by Gnu Make: $(CC) -c $(CPPFLAGS) $(CFLAGS)
%.o : %.m
	$(CC) -c $(CFLAGS) $< -o $@

clean:
	echo ""
	rm -fv *~
	rm -fv *.o *.a
