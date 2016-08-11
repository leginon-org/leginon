/*----------------------------------------------------------------------------*
*
*  defs.h  -  common definitions
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef defs_h_
#define defs_h_

#include "config.h"
#include <float.h>
#include <inttypes.h>
#include <limits.h>
#include <stddef.h>
#include <stdint.h>
#ifdef COMPLEX
#include <complex.h>
#endif


/* boolean type */

typedef unsigned char Bool;

enum {
  False = 0,
  True = !False
};


/* index type, signed integer */

#if SIZE_MAX == UINT32_MAX

typedef int32_t Index;
#define IndexMin INT32_MIN
#define IndexMax INT32_MAX
#define IndexBits (32)
#define IndexD PRId32
#define IndexX PRIx32

#elif SIZE_MAX == UINT64_MAX

typedef int64_t Index;
#define IndexMin INT64_MIN
#define IndexMax INT64_MAX
#define IndexBits (64)
#define IndexD PRId64
#define IndexX PRIx64

#endif


/* size and offsets, unsigned integer */

#if SIZE_MAX == UINT32_MAX

typedef size_t Size;
#define SizeMin (0)
#define SizeMax SIZE_MAX
#define SizeBits (32)
#define SizeU PRIu32
#define SizeX PRIx32

#elif SIZE_MAX == UINT64_MAX

typedef size_t Size;
#define SizeMin (0)
#define SizeMax SIZE_MAX
#define SizeBits (64)
#define SizeU PRIu64
#define SizeX PRIx64

#endif


/* file size and file offsets, signed integer (and equivalent unsigned) */

#if OFFSETBITS == 32

typedef int32_t Offset;
#define OffsetMin INT32_MIN
#define OffsetMax INT32_MAX
#define OffsetBits (32)
#define OffsetD PRId32
#define OffsetX PRIx32

#define OffsetMaxSize OffsetMax

#elif OFFSETBITS == 64

typedef int64_t Offset;
#define OffsetMin INT64_MIN
#define OffsetMax INT64_MAX
#define OffsetBits (64)
#define OffsetD PRId64
#define OffsetX PRIx64

#if SIZE_MAX == UINT32_MAX
#define OffsetMaxSize ((Offset)UINT32_MAX)
#elif SIZE_MAX == UINT64_MAX
#define OffsetMaxSize OffsetMax
#endif

#endif


/* floating point types */

typedef float Real32;
#define Real32Min FLT_MIN
#define Real32Max FLT_MAX
#define Real32EPS FLT_EPSILON
#define Real32E "e"
#define Real32F "f"
#define Real32G "g"
#define Real32S "f"

typedef double Real64;
#define Real64Min DBL_MIN
#define Real64Max DBL_MAX
#define Real64EPS DBL_EPSILON
#define Real64E "e"
#define Real64F "f"
#define Real64G "g"
#define Real64S "lf"

#define CmplxI _Complex_I
#ifdef IMAGINARY
#define ImagI _Imaginary_I
#else
#define ImagI _Complex_I
#endif

#ifdef IMAGINARY
typedef float _Imaginary Imag32;
#endif
#define Imag32Min (FLT_MIN*ImagI)
#define Imag32Max (FLT_MAX*ImagI)
#define Imag32EPS (FLT_EPSILON*ImagI)
#define Imag32E "e"
#define Imag32F "f"
#define Imag32G "g"
#define Imag32S "f"

#ifdef IMAGINARY
typedef double _Imaginary Imag64;
#endif
#define Imag64Min (DBL_MIN*ImagI)
#define Imag64Max (DBL_MAX*ImagI)
#define Imag64EPS (DBL_EPSILON*ImagI)
#define Imag64E "e"
#define Imag64F "f"
#define Imag64G "g"
#define Imag64S "lf"

#ifdef COMPLEX

typedef float _Complex Cmplx32;
typedef double _Complex Cmplx64;
#undef I

#else

typedef union {
  float array[2];
  float _Complex cmplx;
} Cmplx32;
typedef union {
  double array[2];
  double _Complex cmplx;
} Cmplx64;
#define complex _Complex

#endif


 /* type for coordinates etc. */

typedef double Coord;
#define CoordMin DBL_MIN
#define CoordMax DBL_MAX
#define CoordEPS DBL_EPSILON
#define CoordBits (64)
#define CoordE "e"
#define CoordF "f"
#define CoordG "g"
#define CoordS "lf"


/* types for image data */

#if REALBITS == 32

typedef Real32 Real;
#define RealMin Real32Min
#define RealMax Real32Max
#define RealEPS Real32EPS
#define RealBits (32)
#define RealE Real32E
#define RealF Real32F
#define RealG Real32G
#define RealS Real32S

#ifdef IMAGINARY
typedef Imag32 Imag;
#else
typedef Real32 Imag;
#endif
#define ImagMin Imag32Min
#define ImagMax Imag32Max
#define ImagEPS Imag32EPS
#define ImagBits (32)
#define ImagE Real32E
#define ImagF Real32F
#define ImagG Real32G
#define ImagS Real32S

typedef Cmplx32 Cmplx;

#elif REALBITS == 64

typedef Real64 Real;
#define RealMin Real64Min
#define RealMax Real64Max
#define RealEPS Real64EPS
#define RealBits (64)
#define RealE Real64E
#define RealF Real64F
#define RealG Real64G
#define RealS Real64S

#ifdef IMAGINARY
typedef Imag64 Imag;
#else
typedef Real64 Imag;
#endif
#define ImagMin Imag64Min
#define ImagMax Imag64Max
#define ImagEPS Imag64EPS
#define ImagBits (64)
#define ImagE Real64E
#define ImagF Real64F
#define ImagG Real64G
#define ImagS Real64S

typedef Cmplx64 Cmplx;

#endif


/* date and time */

typedef struct {
  uint32_t date;
  uint32_t time;
} Time;


/* exception status */

typedef uint32_t Status;

enum {
  E_NONE = 0
};


/* include after type definitions */

#include "coreconfig.h"


#endif
