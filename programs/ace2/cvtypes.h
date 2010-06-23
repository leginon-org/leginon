#ifndef libCV_cvtypes
#define libCV_cvtypes

#include <limits.h>
#include <stdint.h>
#include <complex.h>

typedef   int8_t          bool;
typedef   int8_t           s08;
typedef   uint8_t          u08;
typedef   int16_t          s16;
typedef   uint16_t     	   u16;
typedef   int32_t          s32;
typedef   uint32_t         u32;
typedef   int64_t   	   s64;
typedef   uint64_t  	   u64; 
typedef   float            f32;
typedef   double           f64;
typedef   long double     f128;
typedef   complex float    c32;
typedef   complex double   c64;

#include "util.h"

#define MB (1<<20)

#define TYPE_NULL		0
#define TYPE_S08		1
#define TYPE_S16		2
#define TYPE_S32		3
#define TYPE_S64		4
#define TYPE_U08		5
#define TYPE_U16		6
#define TYPE_U32		7
#define TYPE_U64		8
#define TYPE_F32		9
#define TYPE_F64		10
#define TYPE_C32		11
#define TYPE_C64		12
#define DEFAULT_TYPE 	TYPE_F64

static char BOOL_STRINGS[2][7] = { "False", 
									"True" };

static char TYPE_STRINGS[14][30] = { "32 Bit Float", 
							         "8 Bit Signed Int",
							         "16 Bit Signed Int",
									 "32 Bit Signed Int",
									 "64 Bit Signed Int",
							  		 "8 Bit Unsigned Int",
							         "16 Bit Unsigned Int",
							         "32 Bit Unsigned Int",
							         "64 Bit Unsigned Int",
							         "32 Bit Float",
							         "64 Bit Float",
							         "32 Bit Complex Float",
							         "64 Bit Complex Float" };

// Flags for data types and conversion preferences

#define CV_REAL_PART			( 0 << 0 )
#define CV_IMAG_PART 			( 1 << 0 )


#define CV_COPY_DATA			( 1 << 0 )
#define CV_USE_IMAGINARY		( 1 << 1 )
#define CV_MAINTAIN_PRECISION	( 1 << 2 )


// Convenient min, max values for the types as defined in this file
#define U08_MAX  UINT8_MAX
#define U16_MAX UINT16_MAX
#define U32_MAX UINT32_MAX
#define U64_MAX UINT64_MAX
#define S08_MAX   INT8_MAX
#define S08_MIN   INT8_MIN
#define S16_MAX  INT16_MAX
#define S16_MIN  INT16_MIN
#define S32_MAX  INT32_MAX
#define S32_MIN  INT32_MIN
#define S64_MAX  INT64_MAX
#define S64_MIN  INT64_MIN

// Convenient macros for shifting integer values between types
#define X64TX08(A) (A>>56)
#define X64TX16(A) (A>>48)
#define X64TX32(A) (A>>32)

#define X32TX08(A) (A>>24)
#define X32TX16(A) (A>>16)
#define X32TX64(A) ((u64)A<<32)

#define X16TX08(A) (A>>8)
#define X16TX32(A) ((u32)A<<16)
#define X16TX64(A) ((u64)A<<48)

#define X08TX16(A) ((u16)A<<8)
#define X08TX32(A) ((u32)A<<24)
#define X08TX64(A) ((u64)A<<56)

/* Interconvert between signed and unsigned integer arrays, copy is made if out is NULL */

s08 * TS_08( u08 *in, u32 size, s08 *out );
u08 * TU_08( s08 *in, u32 size, u08 *out );
s16 * TS_16( u16 *in, u32 size, s16 *out );
u16 * TU_16( s16 *in, u32 size, u16 *out );
s32 * TS_32( u32 *in, u32 size, s32 *out );
u32 * TU_32( s32 *in, u32 size, u32 *out );
s64 * TS_64( u64 *in, u32 size, s64 *out );
u64 * TU_64( s64 *in, u32 size, u64 *out );

/* Interconvert between different integer sizes, copy is made if out is NULL */

void * RSHIFT_32( u64 *in, u32 size, u32 *out );
void * LSHIFT_32( u32 *in, u32 size, u64 *out );
void * RSHIFT_48( u64 *in, u32 size, u16 *out );
void * LSHIFT_48( u16 *in, u32 size, u64 *out );
void * RSHIFT_56( u64 *in, u32 size, u08 *out );
void * LSHIFT_56( u08 *in, u32 size, u64 *out );
void * RSHIFT_16( u32 *in, u32 size, u16 *out );
void * LSHIFT_16( u16 *in, u32 size, u32 *out );
void * RSHIFT_24( u32 *in, u32 size, u08 *out );
void * LSHIFT_24( u08 *in, u32 size, u32 *out );
void * RSHIFT_08( u16 *in, u32 size, u08 *out );
void * LSHIFT_08( u08 *in, u32 size, u16 *out );

/* Interconvert between integer and float arrays, copy is made if out is NULL */

f32 * F64_F32( f64 *in, u32 size, f32 *out );
f64 * F32_F64( f32 *in, u32 size, f64 *out );

u64 * F64_U64( f64 *in, u32 size, u64 *out );
u32 * F64_U32( f64 *in, u32 size, u32 *out );
u16 * F64_U16( f64 *in, u32 size, u16 *out );
u08 * F64_U08( f64 *in, u32 size, u08 *out );

s64 * F64_S64( f64 *in, u32 size, s64 *out );
s32 * F64_S32( f64 *in, u32 size, s32 *out );
s16 * F64_S16( f64 *in, u32 size, s16 *out );
s08 * F64_S08( f64 *in, u32 size, s08 *out );

u64 * F32_U64( f32 *in, u32 size, u64 *out );
u32 * F32_U32( f32 *in, u32 size, u32 *out );
u16 * F32_U16( f32 *in, u32 size, u16 *out );
u08 * F32_U08( f32 *in, u32 size, u08 *out );

s64 * F32_S64( f32 *in, u32 size, s64 *out );
s32 * F32_S32( f32 *in, u32 size, s32 *out );
s16 * F32_S16( f32 *in, u32 size, s16 *out );
s08 * F32_S08( f32 *in, u32 size, s08 *out );

f64 * U64_F64( u64 *in, u32 size, f64 *out );
f64 * S64_F64( s64 *in, u32 size, f64 *out );

f32 * U64_F32( u64 *in, u32 size, f32 *out );
f32 * S64_F32( s64 *in, u32 size, f32 *out );

f64 * U32_F64( u32 *in, u32 size, f64 *out );
f64 * S32_F64( s32 *in, u32 size, f64 *out );

f32 * U32_F32( u32 *in, u32 size, f32 *out );
f32 * S32_F32( s32 *in, u32 size, f32 *out );

f64 * U16_F64( u16 *in, u32 size, f64 *out );
f64 * S16_F64( s16 *in, u32 size, f64 *out );

f32 * U16_F32( u16 *in, u32 size, f32 *out );
f32 * S16_F32( s16 *in, u32 size, f32 *out );

f64 * U08_F64( u08 *in, u32 size, f64 *out );
f64 * S08_F64( s08 *in, u32 size, f64 *out );

f32 * U08_F32( u08 *in, u32 size, f32 *out );
f32 * S08_F32( s08 *in, u32 size, f32 *out );

/* Convert between complex types, copy is made if out is NULL */

c32 * C64_C32( c64 *in, u32 size, c32 *out );
c64 * C32_C64( c32 *in, u32 size, c64 *out );

/* Extract and set real and imaginary components of complex arrays, copy is made if out is NULL */

f32 * GET_R_C32( c32 *in, u32 size, f32 *out );
f32 * GET_I_C32( c32 *in, u32 size, f32 *out );

f64 * GET_R_C64( c64 *in, u32 size, f64 *out );
f64 * GET_I_C64( c64 *in, u32 size, f64 *out );

c32 * SET_R_C32( f32 *in, u32 size, c32 *out );
c64 * SET_R_C64( f64 *in, u32 size, c64 *out );

c32 * SET_I_C32( f32 *in, u32 size, c32 *out );
c64 * SET_I_C64( f64 *in, u32 size, c64 *out );

/* Scaling Functions on float array types, copy is made if out is NULL */

f32 * SCALE_F32( f32 *in, u32 size, f32 min, f32 max, f32 *out );
f64 * SCALE_F64( f64 *in, u32 size, f64 min, f64 max, f64 *out );

/* Common functions to perform on arrays of data */

s32 MAX_S32( const s32 *in, u32 size );
f32 MAX_F32( const f32 *in, u32 size );
f64 MAX_F64( const f64 *in, u32 size );
f32 MAX_C32( const c32 *in, u32 size );
f64 MAX_C64( const c64 *in, u32 size );

s32 MIN_S32( const s32 *in, u32 size );
f32 MIN_F32( const f32 *in, u32 size );
f64 MIN_F64( const f64 *in, u32 size );
f32 MIN_C32( const c32 *in, u32 size );
f64 MIN_C64( const c64 *in, u32 size );

f32 MEAN_S32( const s32 *in, u32 size );
f32 MEAN_F32( const f32 *in, u32 size );
f64 MEAN_F64( const f64 *in, u32 size );
f64 MEAN_C32( const c32 *in, u32 size );
f64 MEAN_C64( const c64 *in, u32 size );

f32 STDV_S32( const s32 *in, u32 size, f32 mean );
f32 STDV_F32( const f32 *in, u32 size, f32 mean );
f64 STDV_F64( const f64 *in, u32 size, f64 mean );
f32 STDV_C32( const c32 *in, u32 size, f32 mean );
f64 STDV_C64( const c64 *in, u32 size, f64 mean );

/* Functions to convert to specified types from any of the other types */

f32 * TO_F32( void *in, u32 size, u08 type, u08 flags );
f64 * TO_F64( void *in, u32 size, u08 type, u08 flags );
u08 * TO_U08( void *in, u32 size, u08 type, u08 flags );
s08 * TO_S08( void *in, u32 size, u08 type, u08 flags );
u16 * TO_U16( void *in, u32 size, u08 type, u08 flags );
s16 * TO_S16( void *in, u32 size, u08 type, u08 flags );
u32 * TO_U32( void *in, u32 size, u08 type, u08 flags );
s32 * TO_S32( void *in, u32 size, u08 type, u08 flags );
u64 * TO_U64( void *in, u32 size, u08 type, u08 flags );
s64 * TO_S64( void *in, u32 size, u08 type, u08 flags );
c32 * TO_C32( void *in, u32 size, u08 type, u08 flags );
c64 * TO_C64( void *in, u32 size, u08 type, u08 flags );

void * TO_TYPE( void *in, u32 size, u08 type, u08 totype, u08 flags );

/* Functions which deal with multi-dimensional array type */

size_t sizeFromType( u08 type );

#endif
