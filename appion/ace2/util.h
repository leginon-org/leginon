
#ifndef libcv_util
#define libcv_util

#include <sys/time.h>
#include <sys/resource.h>
#include <sys/types.h>
#include <time.h>
#include <stdlib.h>
#include <math.h>
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <stdarg.h>
#include <stddef.h>
#include <limits.h>
#include "cvtypes.h"

# define COMPILE_INFO \
  fprintf(stderr,\
 "Program: %s in source %s, Subversion revision %s,\n which was compiled on %s at %s.\n\n",\
 argv[0],__FILE__,SVN_REV,__DATE__,__TIME__)

# define CITATION \
  fprintf(stderr,\
 "Citation: %s.\nE-mail: C Yoshioka <%s>.\n\n",\
 "Ace 2",\
 "None",\
 "craigyk@scripps.edu")

#define ABS(x)			( (x) >  0  ? (x) : -(x) )
#define MAX(x,y)		( (x) > (y) ? (x) :  (y) )
#define MIN(x,y)		( (x) < (y) ? (x) :  (y) )
#define ISFINITE(x)		( !isnan(x) && !isinf(x) )
#define BOUND(x,y,z)	( MAX((x),MIN((y),(z))) )
#define SIGN(a,b)		( (b) >= 0.0 ? ABS(a) : -ABS(a) )

#define BSWAP2(A) (((((u16)(A))&0xff00)>>8)|((((u16)(A))&0x00ff)<<8))
#define BSWAP4(A) (((((u32)(A))&0xff000000)>>24)|((((u32)(A))&0x00ff0000)>>8)|((((u32)(A))&0x0000ff00)<<8)|((((u32)(A))&0x000000ff)<<24))

#define NEW(A)			(calloc(1,sizeof(A)))
#define NEWV(A,B)		(calloc(B,sizeof(A)))
#define COPYV(A,B)		(memcpy(malloc(B),A,B))
#define RENEWV(A,B,C)	(realloc(A,sizeof(B)*C))

#define CPUTIME		(getrusage(RUSAGE_SELF,&ruse),ruse.ru_utime.tv_sec+ruse.ru_stime.tv_sec+1e-6*(ruse.ru_utime.tv_usec+ruse.ru_stime.tv_usec))
static struct rusage ruse;

static u16 endian_test = 0x01;
#define IS_BIG_ENDIAN		(((u08 *)(&endian_test))[1])
#define IS_LITTLE_ENDIAN	!IS_BIG_ENDIAN

static u08 rand_seeded = 0;

#define TRUE	1
#define FALSE	0
#define PI		3.14159265358979
#define RAD		0.017453292519943295
#define DEG		57.295779513082323

#define DEBUG_LOW    0
#define DEBUG_MEDIUM 1
#define DEBUG_HIGH   2

f32  randomNumber( f32 min, f32 max);

u32  byteSwapRead(  FILE * fp, void * data, u32 number_of_elements, u32 element_size );
u32  byteSwapWrite( FILE * fp, void * data, u32 number_of_elements, u32 element_size );
u32  byteSwapBuffer( void *data, u32 number_of_elements, u32 element_size );

#endif
