
# ------------------ Compilation options ------------------------

# Loads math library.  
LIBS = -lm

# Flags for the C compiler:
#   -Wall for strict gcc warnings (requires prototypes for all functions).
#   -g to produce debug data for gdb
#   -O for optimization
CFLAGS = -Wall -g -O3

CC = gcc

# --------------------- Code modules ----------------------------

# Object files
OBJ = main.o geometry.o lautil.o mutil.o util.o image.o mser.o unionfind.o csift.o match.o

# Definitions

# ------------------------ Rules --------------------------------

mser: ${OBJ}
	${CC} -o $@ ${CFLAGS} ${OBJ} ${LIBS}

# Implicit rule used by Gnu Make: $(CC) -c $(CPPFLAGS) $(CFLAGS)
${OBJ}: ${DEFS}
