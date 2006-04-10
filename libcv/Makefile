
# ------------------ Compilation options ------------------------

# Loads math library.  
LIBS = -lm

# Flags for the C compiler:
#   -Wall for strict gcc warnings (requires prototypes for all functions).
#   -g to produce debug data for gdb
#   -O for optimization
CFLAGS = -Wall -g -O2

CC = gcc

# --------------------- Code modules ----------------------------

# Object files
OBJ = main.o util.o ellipsefit.o lautil.o csift.o mserutil.o mutil.c mser.o image.o match.o unionfind.o

# Definitions
DEFS = defs.h

# ------------------------ Rules --------------------------------

mser: ${OBJ}
	${CC} -o $@ ${CFLAGS} ${OBJ} ${LIBS}

# Implicit rule used by Gnu Make: $(CC) -c $(CPPFLAGS) $(CFLAGS)
${OBJ}: ${DEFS}
