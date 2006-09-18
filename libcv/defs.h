
#include <stdlib.h>
#include <math.h>
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <stdarg.h>
#include <sys/time.h>
#include <sys/resource.h>
#include <sys/types.h>
#include <time.h>

#ifndef ABS
#define ABS(x)		( (x) >  0  ? (x) : -(x))
#endif
#ifndef MAX
#define MAX(x,y)	( (x) > (y) ? (x) : (y))
#endif
#ifndef MIN
#define MIN(x,y)	( (x) < (y) ? (x) : (y))
#endif
#define BOUND(x,y,z)	MAX(x,MIN(y,z))
#define SIGN(a,b)	((b) >= 0.0 ? ABS(a) : -ABS(a))
#define CPUTIME		(getrusage(RUSAGE_SELF,&ruse),ruse.ru_utime.tv_sec+ruse.ru_stime.tv_sec+1e-6*(ruse.ru_utime.tv_usec+ruse.ru_stime.tv_usec))

#define TRUE	1
#define FALSE	0
#define PI	3.14159265358979
#define RAD	0.017453292519943295
#define DEG	57.295779513082323
#define TINY	1.0e-20;
#define MACHEPS	2.22045e-16

#include "mser.h"
#include "csift.h"
#include "lautil.h"
#include "image.h"
#include "mutil.h"
#include "util.h"

struct rusage ruse;

typedef struct MatchSt {
	struct DescriptorSt *p1, *p2;
} *Match;

typedef struct PointStackSt {
	struct PointSt *items;
	int stacksize, realsize, cursor;
} *PointStack;

typedef struct PointSt {
	float row, col;
} *Point;

typedef struct EllipseSt {
	double erow, ecol, majaxis, minaxis, phi;
	double A,B,C,D,E,F;
	double minr, maxr, minc, maxc;
} *Ellipse;

