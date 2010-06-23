#include "cvtypes.h"

size_t sizeFromType( u08 type ) {
	switch ( type ) {
		case TYPE_U08:
		case TYPE_S08: return sizeof(s08);
		case TYPE_U16:
		case TYPE_S16: return sizeof(s16);
		case TYPE_U32:
		case TYPE_S32:
		case TYPE_F32: return sizeof(f32);
		case TYPE_U64:
		case TYPE_S64:
		case TYPE_F64: return sizeof(f64);
		case TYPE_C32: return sizeof(c32);
		case TYPE_C64: return sizeof(c64);
		default: return 0;
	}
}

/* Interconvert between signed and unsigned integer arrays, copy is made if out is NULL */

s08 *TS_08( u08 *in, u32 size, s08 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(s08)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = in[size]-S08_MAX-1;
	return out;
}

u08 *TU_08( s08 *in, u32 size, u08 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(u08)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = in[size]+S08_MAX+1;
	return out;	
}

s16 *TS_16( u16 *in, u32 size, s16 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(s16)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = in[size]-S16_MAX-1;
	return out;
}

u16 *TU_16( s16 *in, u32 size, u16 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(u16)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = in[size]+S16_MAX+1;
	return out;
}

s32 *TS_32( u32 *in, u32 size, s32 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(s32)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = in[size]-S32_MAX-1;
	return out;
}

u32 *TU_32( s32 *in, u32 size, u32 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(u32)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = in[size]+S32_MAX+1;
	return out;
}

s64 *TS_64( u64 *in, u32 size, s64 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(s64)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = in[size]-S64_MAX-1;
	return out;
}

u64 *TU_64( s64 *in, u32 size, u64 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(u64)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = in[size]+S64_MAX+1;
	return out;
}

/* Interconvert between different integer sizes with precision scaling, copy is made if out is NULL */

void *RSHIFT_32( u64 *in, u32 size, u32 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(u32)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = X64TX32(in[size]);
	return ((void *)out);
}

void *LSHIFT_32( u32 *in, u32 size, u64 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(u64)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = X32TX64(in[size]);
	return ((void *)out);
}

void *RSHIFT_48( u64 *in, u32 size, u16 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(u16)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = X64TX16(in[size]);
	return ((void *)out);
}

void *LSHIFT_48( u16 *in, u32 size, u64 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(u64)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = X16TX64(in[size]);
	return ((void *)out);
}

void *RSHIFT_56( u64 *in, u32 size, u08 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(u08)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = X64TX08(in[size]);
	return ((void *)out);
}

void *LSHIFT_56( u08 *in, u32 size, u64 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(u64)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = X08TX64(in[size]);
	return ((void *)out);
}

void *RSHIFT_16( u32 *in, u32 size, u16 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(u16)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = X32TX16(in[size]);
	return ((void *)out);
}

void *LSHIFT_16( u16 *in, u32 size, u32 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(u32)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = X16TX32(in[size]);
	return ((void *)out);
}

void *RSHIFT_24( u32 *in, u32 size, u08 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(u08)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = X32TX08(in[size]);
	return ((void *)out);
}

void *LSHIFT_24( u08 *in, u32 size, u32 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(u32)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = X08TX32(in[size]);
	return ((void *)out);
}

void *RSHIFT_08( u16 *in, u32 size, u08 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(u08)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = X16TX08(in[size]);
	return ((void *)out);
}

void *LSHIFT_08( u08 *in, u32 size, u16 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(u16)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = X08TX16(in[size]);
	return ((void *)out);
}

/* Expand an integer type into a different type with clipping */

void *EXPAND_32( u32 *in, u32 size, u64 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(u64)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = in[size];
	return ((void *)out);
	
}

void *SHRINK_32( u64 *in, u32 size, u32 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(u32)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = MIN(U32_MAX,in[size]);
	return ((void *)out);
}

void *EXPAND_48( u16 *in, u32 size, u64 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(u64)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = in[size];
	return ((void *)out);
}

void *SHRINK_48( u64 *in, u32 size, u16 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(u16)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = MIN(U16_MAX,in[size]);
	return ((void *)out);
}

void *EXPAND_56( u08 *in, u32 size, u64 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(u64)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = in[size];
	return ((void *)out);
}

void *SHRINK_56( u64 *in, u32 size, u08 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(u08)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = MIN(U08_MAX,in[size]);
	return ((void *)out);
}

void *EXPAND_16( u16 *in, u32 size, u32 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(u32)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = in[size];
	return ((void *)out);
}

void *SHRINK_16( u32 *in, u32 size, u16 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(u16)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = MIN(U16_MAX,in[size]);
	return ((void *)out);
}

void *EXPAND_24( u08 *in, u32 size, u32 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(u32)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = in[size];
	return ((void *)out);
}

void *SHRINK_24( u32 *in, u32 size, u08 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(u08)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = MIN(U08_MAX,in[size]);
	return ((void *)out);
}

void *EXPAND_08( u08 *in, u32 size, u16 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(u16)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = in[size];
	return ((void *)out);
}

void *SHRINK_08( u16 *in, u32 size, u08 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(u08)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = MIN(U08_MAX,in[size]);
	return ((void *)out);
}

/* Interconvert between integer and float arrays, copy is made if out is NULL */

f32 * F64_F32( f64 *in, u32 size, f32 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(f32)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = (f32)in[size]; 
	return out;
}

f64 * F32_F64( f32 *in, u32 size, f64 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(f64)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = in[size]; 
	return out;
}

u64 * F64_U64( f64 *in, u32 size, u64 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(u64)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = in[size];
	return out;
}

u32 * F64_U32( f64 *in, u32 size, u32 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(u32)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = in[size];
	return out;
}

u16 * F64_U16( f64 *in, u32 size, u16 *out ) {
	if ( in == NULL ) return NULL;
	if ( out == NULL ) out = malloc(sizeof(u16)*size);
	if ( out == NULL ) return NULL;
	while ( size-- ) out[size] = in[size];
	return out;
}

u08 * F64_U08( f64 *in, u32 size, u08 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(u08)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = in[size] + 0.5;
	return out;
}

s64 * F64_S64( f64 *in, u32 size, s64 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(u64)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = in[size];
	return out;
}

s32 * F64_S32( f64 *in, u32 size, s32 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(u32)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = in[size];
	return out;
}

s16 * F64_S16( f64 *in, u32 size, s16 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(u16)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = in[size];
	return out;
}

s08 * F64_S08( f64 *in, u32 size, s08 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(u08)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = in[size];
	return out;
}

u64 * F32_U64( f32 *in, u32 size, u64 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(u64)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = in[size];
	return out;
}

u32 * F32_U32( f32 *in, u32 size, u32 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(u32)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = in[size] + 0.5;
	return out;
}

u16 * F32_U16( f32 *in, u32 size, u16 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(u16)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = in[size] + 0.5;
	return out;
}

u08 * F32_U08( f32 *in, u32 size, u08 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(u08)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = in[size] + 0.5;
	return out;
}

s64 * F32_S64( f32 *in, u32 size, s64 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(u64)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = in[size];
	return out;
}

s32 * F32_S32( f32 *in, u32 size, s32 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(u32)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = in[size];
	return out;
}

s16 * F32_S16( f32 *in, u32 size, s16 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(u16)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = in[size];
	return out;
}

s08 * F32_S08( f32 *in, u32 size, s08 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(u08)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = in[size];
	return out;
}

f64 * U64_F64( u64 *in, u32 size, f64 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(f64)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = in[size];
	return out;
}

f64 * S64_F64( s64 *in, u32 size, f64 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(f64)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = in[size];
	return out;
}

f32 * U64_F32( u64 *in, u32 size, f32 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(f32)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = in[size];
	return out;
}

f32 * S64_F32( s64 *in, u32 size, f32 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(f32)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = in[size];
	return out;
}

f64 * U32_F64( u32 *in, u32 size, f64 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(f64)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = in[size];
	return out;
}

f64 * S32_F64( s32 *in, u32 size, f64 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(f64)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = in[size];
	return out;
}

f32 * U32_F32( u32 *in, u32 size, f32* out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(f32)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = in[size];
	return out;
}

f32 * S32_F32( s32 *in, u32 size, f32 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(f32)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = in[size];
	return out;
}

f64 * U16_F64( u16 *in, u32 size, f64 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(f64)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = in[size];
	return out;
}

f64 * S16_F64( s16 *in, u32 size, f64 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(f64)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = in[size];
	return out;
}

f32 * U16_F32( u16 *in, u32 size, f32 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(f32)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = in[size];
	return out;
}

f32 * S16_F32( s16 *in, u32 size, f32 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(f32)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = in[size];
	return out;
}

f64 * U08_F64( u08 *in, u32 size, f64 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(f64)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = in[size];
	return out;
}

f64 * S08_F64( s08 *in, u32 size, f64 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(f64)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = in[size];
	return out;
}

f32 * U08_F32( u08 *in, u32 size, f32 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(f32)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = in[size];
	return out;
}

f32 * S08_F32( s08 *in, u32 size, f32 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(f32)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = in[size];
	return out;
}

/* Convert between complex types, copy is made if out is NULL */

c32 *C64_C32( c64 *in, u32 size, c32 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(c32)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = in[size];
	return out;
}

c64 *C32_C64( c32 *in, u32 size, c64 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(c64)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = in[size];
	return out;
}

/* Extract Real and Imaginary components of complex arrays */

f32 *GET_R_C32( c32 *in, u32 size, f32 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(f32)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = crealf(in[size]);
	return out;
}

f64 *GET_R_C64( c64 *in, u32 size, f64 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(f64)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = creal(in[size]);
	return out;
}

f32 *GET_I_C32( c32 *in, u32 size, f32 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(f32)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = cimagf(in[size]);
	return out;
}

f64 *GET_I_C64( c64 *in, u32 size, f64 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(f64)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = cimag(in[size]);
	return out;
}

c32 *SET_R_C32( f32 *in, u32 size, c32 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(c32)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = in[size] + 0*I;
	return out;
}

c64 *SET_R_C64( f64 *in, u32 size, c64 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(c64)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = in[size] + 0*I;
	return out;
}

c32 *SET_I_C32( f32 *in, u32 size, c32 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(c32)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = 0 + (in[size])*(I);
	return out;
}

c64 *SET_I_C64( f64 *in, u32 size, c64 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(c64)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = 0 + (in[size])*(I);
	return out;
}

/* Scaling Functions on float array types */

f32 *SCALE_F32( f32 *in, u32 size, f32 min, f32 max, f32 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(f32)*size);
	if ( !out ) return NULL;
	u32 k; f32 vmin=in[0], vmax=in[0];
	for(k=0;k<size;k++) vmin = MIN(vmin,in[k]);
	for(k=0;k<size;k++) vmax = MAX(vmax,in[k]);
	f32 scale = ( max - min ) / ( vmax - vmin );
	for(k=0;k<size;k++) out[k] = ( ( in[k] - vmin ) * scale ) + min;
	return out;
}

f64 *SCALE_F64( f64 *in, u32 size, f64 min, f64 max, f64 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(f64)*size);
	if ( !out ) return NULL;
	u32 k; f64 vmin=in[0], vmax=in[0];
	for(k=0;k<size;k++) vmin = MIN(vmin,in[k]);
	for(k=0;k<size;k++) vmax = MAX(vmax,in[k]);
	f64 scale = ( max - min ) / ( vmax - vmin );
	for(k=0;k<size;k++) out[k] = ( ( in[k] - vmin ) * scale ) + min;
	return out;
}

f32 *BOUND_F32( f32 *in, u32 size, f32 min, f32 max, f32 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(f32)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = BOUND(min,in[size],max);
	return out;
}

f64 *BOUND_F64( f64 *in, u32 size, f64 min, f64 max, f64 *out ) {
	if ( !in ) return NULL;
	if ( !out ) out = malloc(sizeof(f64)*size);
	if ( !out ) return NULL;
	while ( size-- ) out[size] = BOUND(min,in[size],max);
	return out;
}

/* Common functions to perform on arrays of data */

s32 MAX_S32( const s32 *in, u32 size ) {
	u32 k; s32 max = in[0];
	for(k=0;k<size;k++) max = MAX(max,in[k]);
	return max;	
}

f32 MAX_F32( const f32 *in, u32 size ) {
	u32 k; f32 max = in[0];
	for(k=0;k<size;k++) max = MAX(max,in[k]);
	return max;	
}

f64 MAX_F64( const f64 *in, u32 size ) {
	u32 k; f32 max = in[0];
	for(k=0;k<size;k++) max = MAX(max,in[k]);
	return max;	
}

f32 MAX_C32( const c32 *in, u32 size ) {
	u32 k; f32 max = crealf(in[0]);
	for(k=0;k<size;k++) max = MAX(max,crealf(in[k]));
	return max;	
}

f64 MAX_C64( const c64 *in, u32 size ) {
	u32 k; f64 max = creal(in[0]);
	for(k=0;k<size;k++) max = MAX(max,creal(in[k]));
	return max;	
}

s32 MIN_S32( const s32 *in, u32 size ) {
	u32 k; s32 min = in[0];
	for(k=0;k<size;k++) min = MIN(min,in[k]);
	return min;	
}

f32 MIN_F32( const f32 *in, u32 size ) {
	u32 k; f32 min = in[0];
	for(k=0;k<size;k++) min = MIN(min,in[k]);
	return min;	
}

f64 MIN_F64( const f64 *in, u32 size ) {
	u32 k; f64 min = in[0];
	for(k=0;k<size;k++) min = MIN(min,in[k]);
	return min;	
}

f32 MIN_C32( const c32 *in, u32 size ) {
	u32 k; f32 min = crealf(in[0]);
	for(k=0;k<size;k++) min = MIN(min,crealf(in[k]));
	return min;	
}

f64 MIN_C64( const c64 *in, u32 size ) {
	u32 k; f64 min = creal(in[0]);
	for(k=0;k<size;k++) min = MIN(min,creal(in[k]));
	return min;	
}

f32 MEAN_S32( const s32 *in, u32 size ) {
	u32 k; f64 mean = 0;
	for(k=0;k<size;k++) mean += in[k];
	mean = mean / size;
	return (f32)mean;
}

f32 MEAN_F32( const f32 *in, u32 size ) {
	u32 k; f64 mean = 0;
	for(k=0;k<size;k++) mean += in[k];
	mean = mean / size;
	return (f32)mean;
}

f64 MEAN_F64( const f64 *in, u32 size ) {
	u32 k; f128 mean = 0;
	for(k=0;k<size;k++) mean += in[k];
	mean = mean / (f128)size;
	return ((f64)mean);
}

f64 MEAN_C32( const c32 *in, u32 size ) {
	u32 k; f64 mean = 0;
	for(k=0;k<size;k++) mean += crealf(in[k]);
	mean = mean / size;
	return (f64)mean;
}

f64 MEAN_C64( const c64 *in, u32 size ) {
	u32 k; f128 mean = 0;
	for(k=0;k<size;k++) mean += creal(in[k]);
	mean = mean / size;
	return (f64)mean;
}

f32 STDV_S32( const s32 *in, u32 size, f32 mean ) {
	u32 k; f64 stdv = 0;
	for(k=0;k<size;k++) stdv += (mean-in[k]);
	stdv = stdv / size;
	return (f32)stdv;
}

f32	STDV_F32( const f32 *in, u32 size, f32 mean ) {
	u32 k; f32 stdv = 0;
	for(k=0;k<size;k++) stdv += (mean-in[k]);
	stdv = stdv / size;
	return (f32)stdv;
}

f64	STDV_F64( const f64 *in, u32 size, f64 mean ) {
	u32 k; f64 stdv = 0;
	for(k=0;k<size;k++) stdv += pow(mean-in[k],2.0);
	stdv = stdv / (size-1);
	return sqrt(stdv);
}

f32	STDV_C32( const c32 *in, u32 size, f32 mean ) {
	u32 k; f64 stdv = 0;
	for(k=0;k<size;k++) stdv += (mean-crealf(in[k]));
	stdv = stdv / size;
	return (f64)stdv;
}

f64	STDV_C64( const c64 *in, u32 size, f64 mean ) {
	u32 k; f128 stdv = 0;
	for(k=0;k<size;k++) stdv += (mean-creal(in[k]));
	stdv = stdv / size;
	return (f64)stdv;
}

f32	* TO_F32( void *in, u32 size, u08 type, u08 flags ) {
	
	if ( in == NULL ) goto error;
	
	void *tmp = NULL, *out = NULL;
	
	u08 copy = flags & CV_COPY_DATA;
	u08 imag = flags & CV_USE_IMAGINARY;
	
	size_t msize = sizeFromType(TYPE_F32)*size;
	if ( msize == 0 ) goto error;
	
	switch ( type ) {
		case TYPE_U08:
			out = U08_F32(in,size,out);
			goto end;
		case TYPE_S08:
			out = S08_F32(in,size,out);
			goto end;
		case TYPE_U16:
			out = U16_F32(in,size,out);
			goto end;
		case TYPE_S16:
			out = S16_F32(in,size,out);
			goto end;
		case TYPE_U32:
			out = U32_F32(in,size,out);
			goto end;
		case TYPE_S32:
			out = S32_F32(in,size,out);
			goto end;
		case TYPE_U64:
			out = U64_F32(in,size,out);
			goto end;
		case TYPE_S64:
			out = S64_F32(in,size,out);
			goto end;
		case TYPE_F32:
			out = memcpy(malloc(msize),in,msize);
			goto end;
		case TYPE_F64:
			out = F64_F32(in,size,out);
			goto end;
		case TYPE_C32:
			if ( imag ) out = GET_I_C32(in,size,out);
			else        out = GET_R_C32(in,size,out);
			goto end;
		case TYPE_C64:
			if ( imag ) tmp = GET_I_C64(in,size,tmp);
			else        tmp = GET_R_C64(in,size,tmp);
			out = F64_F32(tmp,size,out);
			goto end;
		default:
			goto error;
	}
	
	end:
	if ( !out  ) goto error;
	if (  tmp  ) free(tmp);
	if ( !copy ) free(in);
	return out;
	
	error:
	if ( out ) free(out);
	if ( tmp ) free(tmp);
	return NULL;
	
}

f64	* TO_F64( void *in, u32 size, u08 type, u08 flags ) {
	
	if ( in == NULL ) goto error;
	
	void *tmp = NULL, *out = NULL;
	
	u08 copy = flags & CV_COPY_DATA;
	u08 imag = flags & CV_USE_IMAGINARY;
	
	size_t msize = sizeFromType(TYPE_F64)*size;
	if ( msize == 0 ) goto error;
	
	switch ( type ) {
		case TYPE_U08:
			out = U08_F64(in,size,out);
			goto end;
		case TYPE_S08:
			out = S08_F64(in,size,out);
			goto end;
		case TYPE_U16:
			out = U16_F64(in,size,out);
			goto end;
		case TYPE_S16:
			out = S16_F64(in,size,out);
			goto end;
		case TYPE_U32:
			out = U32_F64(in,size,out);
			goto end;
		case TYPE_S32:
			out = S32_F64(in,size,out);
			goto end;
		case TYPE_U64:
			out = U64_F64(in,size,out);
			goto end;
		case TYPE_S64:
			out = S64_F64(in,size,out);
			goto end;
		case TYPE_F32:
			out = F32_F64(in,size,out);
			goto end;
		case TYPE_F64:
			out = memcpy(malloc(msize),in,msize);
			goto end;
		case TYPE_C32:
			if ( imag ) tmp = GET_I_C32(in,size,tmp);
			else        tmp = GET_R_C32(in,size,tmp);
			out = F32_F64(tmp,size,out);
			goto end;
		case TYPE_C64:
			if ( imag ) out = GET_I_C64(in,size,out);
			else        out = GET_R_C64(in,size,out);
			goto end;
		default:
			goto error;
	}
	
	end:
	if ( !out  ) goto error;
	if (  tmp  ) free(tmp);
	if ( !copy ) free(in);
	return out;
	
	error:
	if ( out ) free(out);
	if ( tmp ) free(tmp);
	return NULL;
	
}

u08	* TO_U08( void *in, u32 size, u08 type, u08 flags ) {
	
	if ( in == NULL ) goto error;
	
	void *tmp = NULL, *out = NULL;
	
	u08 copy  = flags & CV_COPY_DATA;
	u08 imag  = flags & CV_USE_IMAGINARY;
	u08 scale = flags & CV_MAINTAIN_PRECISION;
	
	size_t msize = sizeFromType(TYPE_U08)*size;
	if ( msize == 0 ) goto error;
	
	switch ( type ) {
		case TYPE_U08:
			out = memcpy(malloc(msize),in,msize);
			goto end;
		case TYPE_S08:
			out = TU_08(in,size,out);
			goto end;
		case TYPE_U16:
			if ( scale ) out = RSHIFT_08(in,size,out);
			else         out = SHRINK_08(in,size,out);
			goto end;
		case TYPE_S16:
			tmp = TU_16(in,size,tmp);
			if ( scale ) out = RSHIFT_08(tmp,size,out);
			else         out = SHRINK_08(tmp,size,out);
			goto end;
		case TYPE_U32:
			if ( scale ) out = RSHIFT_24(in,size,out);
			else         out = SHRINK_24(in,size,out);
			goto end;
		case TYPE_S32:
			tmp = TU_32(in,size,tmp);
			if ( scale ) out = RSHIFT_24(tmp,size,out);
			else         out = SHRINK_24(tmp,size,out);
			goto end;
		case TYPE_U64:
			if ( scale ) out = RSHIFT_56(in,size,out);
			else         out = SHRINK_56(in,size,out);
			goto end;
		case TYPE_S64:
			tmp = TU_64(in,size,tmp);
			if ( scale ) out = RSHIFT_56(tmp,size,out);
			else         out = SHRINK_56(tmp,size,out);
			goto end;
		case TYPE_F32:
			if ( scale ) tmp = SCALE_F32(in,size,0,U08_MAX,tmp);
			else         tmp = BOUND_F32(in,size,0,U08_MAX,tmp);
			out = F32_U08(tmp,size,out);
			goto end;
		case TYPE_F64:
			if ( scale ) tmp = SCALE_F64(in,size,0,U08_MAX,tmp);
			else         tmp = BOUND_F64(in,size,0,U08_MAX,tmp);
			out = F64_U08(tmp,size,out);
			goto end;
		case TYPE_C32:
			if ( imag )  tmp = GET_I_C32(in,size,tmp);
			else         tmp = GET_R_C32(in,size,tmp);
			if ( scale ) tmp = SCALE_F32(tmp,size,0,U08_MAX,tmp);
			else         tmp = BOUND_F32(tmp,size,0,U08_MAX,tmp);
			out = F32_U08(tmp,size,out);
			goto end;
		case TYPE_C64:
			if ( imag )  tmp = GET_I_C64(in,size,tmp);
			else         tmp = GET_R_C64(in,size,tmp);
			if ( scale ) tmp = SCALE_F64(tmp,size,0,U08_MAX,tmp);
			else         tmp = BOUND_F64(tmp,size,0,U08_MAX,tmp);
			out = F64_U08(tmp,size,out);
			goto end;
		default:
			goto error;
	}
	
	end:
	if ( !out  ) goto error;
	if (  tmp  ) free(tmp);
	if ( !copy ) free(in);
	return out;
	
	error:
	if ( out ) free(out);
	if ( tmp ) free(tmp);
	return NULL;
	
}

s08	* TO_S08( void *in, u32 size, u08 type, u08 flags ) {
	
	if ( in == NULL ) goto error;
	
	void *tmp = NULL, *out = NULL;
	
	u08 copy  = flags & CV_COPY_DATA;
	u08 imag  = flags & CV_USE_IMAGINARY;
	u08 scale = flags & CV_MAINTAIN_PRECISION;
	
	size_t msize = sizeFromType(TYPE_S08)*size;
	if ( msize == 0 ) goto error;

	switch ( type ) {
		case TYPE_S08:
			out = memcpy(malloc(msize),in,msize);
			goto end;
		case TYPE_U08:
			out = TS_08(in,size,out);
			goto end;
		case TYPE_S16:
			if ( scale ) out = RSHIFT_08(in,size,out);
			else         out = SHRINK_08(in,size,out);
			goto end;
		case TYPE_U16:
			tmp = TS_16(in,size,tmp);
			if ( scale ) out = RSHIFT_08(tmp,size,out);
			else         out = SHRINK_08(tmp,size,out);
			goto end;
		case TYPE_S32:
			if ( scale ) out = RSHIFT_24(in,size,out);
			else         out = SHRINK_24(in,size,out);
			goto end;
		case TYPE_U32:
			tmp = TS_32(in,size,tmp);
			if ( scale ) out = RSHIFT_24(tmp,size,out);
			else         out = SHRINK_24(tmp,size,out);
			goto end;
		case TYPE_S64:
			if ( scale ) out = RSHIFT_56(in,size,out);
			else         out = SHRINK_56(in,size,out);
			goto end;
		case TYPE_U64:
			tmp = TS_64(in,size,tmp);
			if ( scale ) out = RSHIFT_56(tmp,size,out);
			else         out = SHRINK_56(tmp,size,out);
			goto end;
		case TYPE_F32:
			if ( scale ) tmp = SCALE_F32(in,size,S08_MIN,S08_MAX,tmp);
			else         tmp = BOUND_F32(in,size,S08_MIN,S08_MAX,tmp);
			out = F32_S08(tmp,size,out);
			goto end;
		case TYPE_F64:
			if ( scale ) tmp = SCALE_F64(in,size,S08_MIN,S08_MAX,tmp);
			else         tmp = BOUND_F64(in,size,S08_MIN,S08_MAX,tmp);
			out = F64_S08(tmp,size,out);
			goto end;
		case TYPE_C32:
			if ( imag )  tmp = GET_I_C32(in,size,tmp);
			else         tmp = GET_R_C32(in,size,tmp);
			if ( scale ) tmp = SCALE_F32(tmp,size,S08_MIN,S08_MAX,tmp);
			else         tmp = BOUND_F32(tmp,size,S08_MIN,S08_MAX,tmp);
			out = F32_S08(tmp,size,out);
			goto end;
		case TYPE_C64:
			if ( imag )  tmp = GET_I_C64(in,size,tmp);
			else         tmp = GET_R_C64(in,size,tmp);
			if ( scale ) tmp = SCALE_F64(tmp,size,S08_MIN,S08_MAX,tmp);
			else         tmp = BOUND_F64(tmp,size,S08_MIN,S08_MAX,tmp);
			out = F64_S08(tmp,size,out);
			goto end;
		default:
			goto error;
	}
	
	end:
	if ( !out  ) goto error;
	if (  tmp  ) free(tmp);
	if ( !copy ) free(in);
	return out;
	
	error:
	if ( out ) free(out);
	if ( tmp ) free(tmp);
	return NULL;
	
}

u16	* TO_U16( void *in, u32 size, u08 type, u08 flags ) {
	
	void * tmp = NULL, * out = NULL;
	
	if ( in == NULL ) goto error;
	
	u08 copy  = flags & CV_COPY_DATA;
	u08 imag  = flags & CV_USE_IMAGINARY;
	u08 scale = flags & CV_MAINTAIN_PRECISION;
	
	size_t msize = sizeFromType(TYPE_U16)*size;
	if ( msize == 0 ) goto error;
	
	switch ( type ) {
		case TYPE_U08:
			if ( scale ) out = LSHIFT_08(in,size,out);
			else         out = EXPAND_08(in,size,out);
			goto end;
		case TYPE_S08:
			tmp = TU_08(in,size,tmp);
			if ( scale ) out = LSHIFT_08(tmp,size,out);
			else         out = EXPAND_08(tmp,size,out);
			goto end;
		case TYPE_U16:
			out = memcpy(malloc(msize),in,msize);
			goto end;
		case TYPE_S16:
			out = TU_16(in,size,out);
			goto end;
		case TYPE_U32:
			if ( scale ) out = RSHIFT_16(in,size,out);
			else         out = SHRINK_16(in,size,out);
			goto end;
		case TYPE_S32:
			tmp = TU_32(in,size,tmp);
			if ( scale ) out = RSHIFT_16(tmp,size,out);
			else         out = SHRINK_16(tmp,size,out);
			goto end;
		case TYPE_U64:
			if ( scale ) out = RSHIFT_48(in,size,out);
			else         out = SHRINK_48(in,size,out);
			goto end;
		case TYPE_S64:
			tmp = TU_64(in,size,tmp);
			if ( scale ) out = RSHIFT_48(tmp,size,out);
			else         out = SHRINK_48(tmp,size,out);
			goto end;
		case TYPE_F32:
			if ( scale ) tmp = SCALE_F32(in,size,0,U16_MAX,tmp);
			else         tmp = BOUND_F32(in,size,0,U16_MAX,tmp);
			out = F32_U16(tmp,size,out);
			goto end;
		case TYPE_F64:
			if ( scale ) tmp = SCALE_F64(in,size,0,U16_MAX,tmp);
			else         tmp = BOUND_F64(in,size,0,U16_MAX,tmp);
			out = F64_U16(tmp,size,out);
			goto end;
		case TYPE_C32:
			if ( imag )  tmp = GET_I_C32(in,size,tmp);
			else         tmp = GET_R_C32(in,size,tmp);
			if ( scale ) tmp = SCALE_F32(tmp,size,0,U16_MAX,tmp);
			else         tmp = BOUND_F32(tmp,size,0,U16_MAX,tmp);
			out = F32_U16(tmp,size,out);
			goto end;
		case TYPE_C64:
			if ( imag )  tmp = GET_I_C64(in,size,tmp);
			else         tmp = GET_R_C64(in,size,tmp);
			if ( scale ) tmp = SCALE_F64(tmp,size,0,U16_MAX,tmp);
			else         tmp = BOUND_F64(tmp,size,0,U16_MAX,tmp);
			out = F64_U16(tmp,size,out);
			goto end;
		default:
			goto error;
	}
	
	end:
	if ( out == NULL ) goto error;
	if ( tmp != NULL ) free(tmp);
	if ( copy == FALSE ) free(in);
	return out;
	
	error:
	if ( out != NULL ) free(out);
	if ( tmp != NULL ) free(tmp);
	return NULL;
	
}

s16	* TO_S16( void *in, u32 size, u08 type, u08 flags ) {
	
	if ( in == NULL ) goto error;
	
	void *tmp = NULL, *out = NULL;
	
	u08 copy  = flags & CV_COPY_DATA;
	u08 imag  = flags & CV_USE_IMAGINARY;
	u08 scale = flags & CV_MAINTAIN_PRECISION;
	
	size_t msize = sizeFromType(TYPE_S16)*size;
	if ( msize == 0 ) goto error;

	switch ( type ) {
		case TYPE_S08:
			if ( scale ) out = LSHIFT_08(in,size,out);
			else         out = EXPAND_08(in,size,out);
			goto end;
		case TYPE_U08:
			tmp = TS_08(in,size,tmp);
			if ( scale ) out = LSHIFT_08(tmp,size,out);
			else         out = EXPAND_08(tmp,size,out);
			goto end;
		case TYPE_S16:
			out = memcpy(malloc(msize),in,msize);
			goto end;
		case TYPE_U16:
			out = TS_16(in,size,out);
			goto end;
		case TYPE_S32:
			if ( scale ) out = RSHIFT_16(in,size,out);
			else         out = SHRINK_16(in,size,out);
			goto end;
		case TYPE_U32:
			tmp = TS_32(in,size,tmp);
			if ( scale ) out = RSHIFT_16(tmp,size,out);
			else         out = SHRINK_16(tmp,size,out);
			goto end;
		case TYPE_S64:
			if ( scale ) out = RSHIFT_48(in,size,out);
			else         out = SHRINK_48(in,size,out);
			goto end;
		case TYPE_U64:
			tmp = TS_64(in,size,tmp);
			if ( scale ) out = RSHIFT_48(tmp,size,out);
			else         out = SHRINK_48(tmp,size,out);
			goto end;
		case TYPE_F32:
			if ( scale ) tmp = SCALE_F32(in,size,S16_MIN,S16_MAX,tmp);
			else         tmp = BOUND_F32(in,size,S16_MIN,S16_MAX,tmp);
			out = F32_S16(tmp,size,out);
			goto end;
		case TYPE_F64:
			if ( scale ) tmp = SCALE_F64(in,size,S16_MIN,S16_MAX,tmp);
			else         tmp = BOUND_F64(in,size,S16_MIN,S16_MAX,tmp);
			out = F64_S16(tmp,size,out);
			goto end;
		case TYPE_C32:
			if ( imag )  tmp = GET_I_C32(in,size,tmp);
			else         tmp = GET_R_C32(in,size,tmp);
			if ( scale ) tmp = SCALE_F32(tmp,size,S16_MIN,S16_MAX,tmp);
			else         tmp = BOUND_F32(tmp,size,S16_MIN,S16_MAX,tmp);
			out = F32_S16(tmp,size,out);
			goto end;
		case TYPE_C64:
			if ( imag )  tmp = GET_I_C64(in,size,tmp);
			else         tmp = GET_R_C64(in,size,tmp);
			if ( scale ) tmp = SCALE_F64(tmp,size,S16_MIN,S16_MAX,tmp);
			else         tmp = BOUND_F64(tmp,size,S16_MIN,S16_MAX,tmp);
			out = F64_S16(tmp,size,out);
			goto end;
		default:
			goto error;
	}
	
	end:
	if ( !out  ) goto error;
	if (  tmp  ) free(tmp);
	if ( !copy ) free(in);
	return out;
	
	error:
	if ( out ) free(out);
	if ( tmp ) free(tmp);
	return NULL;
	
}

u32	* TO_U32( void *in, u32 size, u08 type, u08 flags ) {
	
	if ( in == NULL ) goto error;
	
	void *tmp = NULL, *out = NULL;
	
	u08 copy  = flags & CV_COPY_DATA;
	u08 imag  = flags & CV_USE_IMAGINARY;
	u08 scale = flags & CV_MAINTAIN_PRECISION;
	
	size_t msize = sizeFromType(TYPE_U32)*size;
	if ( msize == 0 ) goto error;

	switch ( type ) {
		case TYPE_U08:
			if ( scale ) out = LSHIFT_24(in,size,out);
			else         out = EXPAND_24(in,size,out);
			goto end;
		case TYPE_S08:
			tmp = TU_08(in,size,tmp);
			if ( scale ) out = LSHIFT_24(tmp,size,out);
			else         out = EXPAND_24(tmp,size,out);
			goto end;
		case TYPE_U16:
			if ( scale ) out = LSHIFT_16(in,size,out);
			else         out = EXPAND_16(in,size,out);
			goto end;
		case TYPE_S16:
			tmp = TU_16(in,size,tmp);
			if ( scale ) out = LSHIFT_16(tmp,size,out);
			else         out = EXPAND_16(tmp,size,out);
			goto end;
		case TYPE_U32:
			out = memcpy(malloc(msize),in,msize);
			goto end;
		case TYPE_S32:
			out = TU_32(in,size,out);
			goto end;
		case TYPE_U64:
			if ( scale ) out = RSHIFT_32(in,size,out);
			else         out = SHRINK_32(in,size,out);
			goto end;
		case TYPE_S64:
			tmp = TU_64(in,size,tmp);
			if ( scale ) out = RSHIFT_32(tmp,size,out);
			else         out = SHRINK_32(tmp,size,out);
			goto end;
		case TYPE_F32:
			if ( scale ) tmp = SCALE_F32(in,size,0,U32_MAX,tmp);
			else         tmp = BOUND_F32(in,size,0,U32_MAX,tmp);
			out = F32_U32(tmp,size,out);
			goto end;
		case TYPE_F64:
			if ( scale ) tmp = SCALE_F64(in,size,0,U32_MAX,tmp);
			else         tmp = BOUND_F64(in,size,0,U32_MAX,tmp);
			out = F64_U32(tmp,size,out);
			goto end;
		case TYPE_C32:
			if ( imag )  tmp = GET_I_C32(in,size,tmp);
			else         tmp = GET_R_C32(in,size,tmp);
			if ( scale ) tmp = SCALE_F32(tmp,size,0,U32_MAX,tmp);
			else         tmp = BOUND_F32(tmp,size,0,U32_MAX,tmp);
			out = F32_U32(tmp,size,out);
			goto end;
		case TYPE_C64:
			if ( imag )  tmp = GET_I_C64(in,size,tmp);
			else         tmp = GET_R_C64(in,size,tmp);
			if ( scale ) tmp = SCALE_F64(tmp,size,0,U32_MAX,tmp);
			else         tmp = BOUND_F64(tmp,size,0,U32_MAX,tmp);
			out = F64_U32(tmp,size,out);
			goto end;
		default:
			goto error;
	}
	
	end:
	if ( !out  ) goto error;
	if (  tmp  ) free(tmp);
	if ( !copy ) free(in);
	return out;
	
	error:
	if ( out ) free(out);
	if ( tmp ) free(tmp);
	return NULL;
	
}

s32	* TO_S32( void *in, u32 size, u08 type, u08 flags ) {
	
	if ( in == NULL ) goto error;
	
	void *tmp = NULL, *out = NULL;
	
	u08 copy  = flags & CV_COPY_DATA;
	u08 imag  = flags & CV_USE_IMAGINARY;
	u08 scale = flags & CV_MAINTAIN_PRECISION;
	
	size_t msize = sizeFromType(TYPE_S32)*size;
	if ( msize == 0 ) goto error;

	switch ( type ) {
		case TYPE_S08:
			if ( scale ) out = LSHIFT_24(in,size,out);
			else         out = EXPAND_24(in,size,out);
			goto end;
		case TYPE_U08:
			tmp = TS_08(in,size,tmp);
			if ( scale ) out = LSHIFT_24(tmp,size,out);
			else         out = EXPAND_24(tmp,size,out);
			goto end;
		case TYPE_S16:
			if ( scale ) out = LSHIFT_16(in,size,out);
			else         out = EXPAND_16(in,size,out);
			goto end;
		case TYPE_U16:
			tmp = TS_16(in,size,tmp);
			if ( scale ) out = LSHIFT_16(tmp,size,out);
			else         out = EXPAND_16(tmp,size,out);
			goto end;
		case TYPE_S32:
			out = memcpy(malloc(msize),in,msize);
			goto end;
		case TYPE_U32:
			out = TS_32(in,size,out);
			goto end;
		case TYPE_S64:
			if ( scale ) out = RSHIFT_32(in,size,out);
			else         out = SHRINK_32(in,size,out);
			goto end;
		case TYPE_U64:
			tmp = TS_64(in,size,tmp);
			if ( scale ) out = RSHIFT_32(tmp,size,out);
			else         out = SHRINK_32(tmp,size,out);
			goto end;
		case TYPE_F32:
			if ( scale ) tmp = SCALE_F32(in,size,S32_MIN,S32_MAX,tmp);
			else         tmp = BOUND_F32(in,size,S32_MIN,S32_MAX,tmp);
			out = F32_S32(tmp,size,out);
			goto end;
		case TYPE_F64:
			if ( scale ) tmp = SCALE_F64(in,size,S32_MIN,S32_MAX,tmp);
			else         tmp = BOUND_F64(in,size,S32_MIN,S32_MAX,tmp);
			out = F64_S32(tmp,size,out);
			goto end;
		case TYPE_C32:
			if ( imag )  tmp = GET_I_C32(in,size,tmp);
			else         tmp = GET_R_C32(in,size,tmp);
			if ( scale ) tmp = SCALE_F32(tmp,size,S32_MIN,S32_MAX,tmp);
			else         tmp = BOUND_F32(tmp,size,S32_MIN,S32_MAX,tmp);
			out = F32_S32(tmp,size,out);
			goto end;
		case TYPE_C64:
			if ( imag )  tmp = GET_I_C64(in,size,tmp);
			else         tmp = GET_R_C64(in,size,tmp);
			if ( scale ) tmp = SCALE_F64(tmp,size,S32_MIN,S32_MAX,tmp);
			else         tmp = BOUND_F64(tmp,size,S32_MIN,S32_MAX,tmp);
			out = F64_S32(tmp,size,out);
			goto end;
		default:
			goto error;
	}
	
	end:
	if ( !out  ) goto error;
	if (  tmp  ) free(tmp);
	if ( !copy ) free(in);
	return out;
	
	error:
	if ( out ) free(out);
	if ( tmp ) free(tmp);
	return NULL;
	
}

u64	* TO_U64( void *in, u32 size, u08 type, u08 flags ) {
	
	if ( in == NULL ) goto error;
	
	void *tmp = NULL, *out = NULL;
	
	u08 copy  = flags & CV_COPY_DATA;
	u08 imag  = flags & CV_USE_IMAGINARY;
	u08 scale = flags & CV_MAINTAIN_PRECISION;
	
	size_t msize = sizeFromType(TYPE_U64)*size;
	if ( msize == 0 ) goto error;

	switch ( type ) {
		case TYPE_U08:
			if ( scale ) out = LSHIFT_56(in,size,out);
			else         out = EXPAND_56(in,size,out);
			goto end;
		case TYPE_S08:
			tmp = TU_08(in,size,tmp);
			if ( scale ) out = LSHIFT_56(tmp,size,out);
			else         out = EXPAND_56(tmp,size,out);
			goto end;
		case TYPE_U16:
			if ( scale ) out = LSHIFT_48(in,size,out);
			else         out = EXPAND_48(in,size,out);
			goto end;
		case TYPE_S16:
			tmp = TU_16(in,size,tmp);
			if ( scale ) out = LSHIFT_48(tmp,size,out);
			else         out = EXPAND_48(tmp,size,out);
			goto end;
		case TYPE_U32:
			if ( scale ) out = LSHIFT_32(in,size,out);
			else         out = EXPAND_32(in,size,out);
			goto end;
		case TYPE_S32:
			tmp = TU_32(in,size,tmp);
			if ( scale ) out = LSHIFT_32(tmp,size,out);
			else         out = EXPAND_32(tmp,size,out);
			goto end;
		case TYPE_U64:
			out = memcpy(malloc(msize),in,msize);
			goto end;
		case TYPE_S64:
			out = TU_64(in,size,out);
			goto end;
		case TYPE_F32:
			if ( scale ) tmp = SCALE_F32(in,size,0,U64_MAX,tmp);
			else         tmp = BOUND_F32(in,size,0,U64_MAX,tmp);
			out = F32_U64(tmp,size,out);
			goto end;
		case TYPE_F64:
			if ( scale ) tmp = SCALE_F64(in,size,0,U64_MAX,tmp);
			else         tmp = BOUND_F64(in,size,0,U64_MAX,tmp);
			out = F64_U64(tmp,size,out);
			goto end;
		case TYPE_C32:
			if ( imag )  tmp = GET_I_C32(in,size,tmp);
			else         tmp = GET_R_C32(in,size,tmp);
			if ( scale ) tmp = SCALE_F32(tmp,size,0,U64_MAX,tmp);
			else         tmp = BOUND_F32(tmp,size,0,U64_MAX,tmp);
			out = F32_U64(tmp,size,out);
			goto end;
		case TYPE_C64:
			if ( imag )  tmp = GET_I_C64(in,size,tmp);
			else         tmp = GET_R_C64(in,size,tmp);
			if ( scale ) tmp = SCALE_F64(tmp,size,0,U64_MAX,tmp);
			else         tmp = BOUND_F64(tmp,size,0,U64_MAX,tmp);
			out = F64_U64(tmp,size,out);
			goto end;
		default:
			goto error;
	}
	
	end:
	if ( !out  ) goto error;
	if (  tmp  ) free(tmp);
	if ( !copy ) free(in);
	return out;
	
	error:
	if ( out ) free(out);
	if ( tmp ) free(tmp);
	return NULL;
	
}

s64	* TO_S64( void *in, u32 size, u08 type, u08 flags ) {
	
	if ( in == NULL ) goto error;
	
	void *tmp = NULL, *out = NULL;
	
	u08 copy  = flags & CV_COPY_DATA;
	u08 imag  = flags & CV_USE_IMAGINARY;
	u08 scale = flags & CV_MAINTAIN_PRECISION;
	
	size_t msize = sizeFromType(TYPE_S64)*size;
	if ( msize == 0 ) goto error;

	switch ( type ) {
		case TYPE_S08:
			if ( scale ) out = LSHIFT_56(in,size,out);
			else         out = EXPAND_56(in,size,out);
			goto end;
		case TYPE_U08:
			tmp = TS_08(in,size,tmp);
			if ( scale ) out = LSHIFT_56(tmp,size,out);
			else         out = EXPAND_56(tmp,size,out);
			goto end;
		case TYPE_S16:
			if ( scale ) out = LSHIFT_48(in,size,out);
			else         out = EXPAND_48(in,size,out);
			goto end;
		case TYPE_U16:
			tmp = TS_16(in,size,tmp);
			if ( scale ) out = LSHIFT_48(tmp,size,out);
			else         out = EXPAND_48(tmp,size,out);
			goto end;
		case TYPE_S32:
			if ( scale ) out = LSHIFT_32(in,size,out);
			else         out = EXPAND_32(in,size,out);
			goto end;
		case TYPE_U32:
			tmp = TS_32(in,size,tmp);
			if ( scale ) out = LSHIFT_32(tmp,size,out);
			else         out = EXPAND_32(tmp,size,out);
			goto end;
		case TYPE_S64:
			out = memcpy(malloc(msize),in,msize);
			goto end;
		case TYPE_U64:
			out = TS_64(in,size,out);
			goto end;
		case TYPE_F32:
			if ( scale ) tmp = SCALE_F32(in,size,S64_MIN,S64_MAX,tmp);
			else         tmp = BOUND_F32(in,size,S64_MIN,S64_MAX,tmp);
			out = F32_S64(tmp,size,out);
			goto end;
		case TYPE_F64:
			if ( scale ) tmp = SCALE_F64(in,size,S64_MIN,S64_MAX,tmp);
			else         tmp = BOUND_F64(in,size,S64_MIN,S64_MAX,tmp);
			out = F64_S64(tmp,size,out);
			goto end;
		case TYPE_C32:
			if ( imag )  tmp = GET_I_C32(in,size,tmp);
			else         tmp = GET_R_C32(in,size,tmp);
			if ( scale ) tmp = SCALE_F32(tmp,size,S64_MIN,S64_MAX,tmp);
			else         tmp = BOUND_F32(tmp,size,S64_MIN,S64_MAX,tmp);
			out = F32_S64(tmp,size,out);
			goto end;
		case TYPE_C64:
			if ( imag )  tmp = GET_I_C64(in,size,tmp);
			else         tmp = GET_R_C64(in,size,tmp);
			if ( scale ) tmp = SCALE_F64(tmp,size,S64_MIN,S64_MAX,tmp);
			else         tmp = BOUND_F64(tmp,size,S64_MIN,S64_MAX,tmp);
			out = F64_S64(tmp,size,out);
			goto end;
		default:
			goto error;
	}
	
	end:
	if ( !out  ) goto error;
	if (  tmp  ) free(tmp);
	if ( !copy ) free(in);
	return out;
	
	error:
	if ( out ) free(out);
	if ( tmp ) free(tmp);
	return NULL;
	
}

c32	* TO_C32( void *in, u32 size, u08 type, u08 flags ) {
	
	if ( in == NULL ) goto error;
	
	void *tmp = NULL, *out = NULL;
	
	u08 copy  = flags & CV_COPY_DATA;
	u08 imag  = flags & CV_USE_IMAGINARY;
	u08 scale = flags & CV_MAINTAIN_PRECISION;
	
	size_t msize = sizeFromType(TYPE_C32)*size;
	if ( msize == 0 ) goto error;

	switch ( type ) {
		case TYPE_U08:
			tmp = U08_F32(in,size,tmp);
			if ( imag ) out = SET_I_C32(tmp,size,out);
			else        out = SET_R_C32(tmp,size,out);
			goto end;
		case TYPE_S08:
			tmp = S08_F32(in,size,tmp);
			if ( imag )  out = SET_I_C32(tmp,size,out);
			else         out = SET_R_C32(tmp,size,out);
			goto end;
		case TYPE_U16:
			tmp = U16_F32(in,size,tmp);
			if ( imag )  out = SET_I_C32(tmp,size,out);
			else         out = SET_R_C32(tmp,size,out);
			goto end;
		case TYPE_S16:
			tmp = S16_F32(in,size,tmp);
			if ( imag )  out = SET_I_C32(tmp,size,out);
			else         out = SET_R_C32(tmp,size,out);
			goto end;
		case TYPE_U32:
			tmp = U32_F32(in,size,tmp);
			if ( imag )  out = SET_I_C32(tmp,size,out);
			else         out = SET_R_C32(tmp,size,out);
			goto end;
		case TYPE_S32:
			tmp = S32_F32(in,size,tmp);
			if ( imag )  out = SET_I_C32(tmp,size,out);
			else         out = SET_R_C32(tmp,size,out);
			goto end;
		case TYPE_U64:
			tmp = U64_F32(in,size,tmp);
			if ( imag )  out = SET_I_C32(tmp,size,out);
			else         out = SET_R_C32(tmp,size,out);
			goto end;
		case TYPE_S64:
			tmp = S64_F32(in,size,tmp);
			if ( imag )  out = SET_I_C32(tmp,size,out);
			else         out = SET_R_C32(tmp,size,out);
			goto end;
		case TYPE_F32:
			if ( imag )  out = SET_I_C32(in,size,out);
			else         out = SET_R_C32(in,size,out);
			goto end;
		case TYPE_F64:
			tmp = F64_F32(in,size,tmp);
			if ( imag )  out = SET_I_C32(tmp,size,out);
			else         out = SET_R_C32(tmp,size,out);
			goto end;
		case TYPE_C32:
			out = memcpy(malloc(msize),in,msize);
			goto end;
		case TYPE_C64:
			out = C64_C32(in,size,out);
			goto end;
		default:
			goto error;
	}
	
	end:
	if ( !out  ) goto error;
	if ( tmp   ) free(tmp);
	if ( !copy ) free(in);
	return out;
	
	error:
	if ( out ) free(out);
	if ( tmp ) free(tmp);
	return NULL;
	
}

c64	* TO_C64( void *in, u32 size, u08 type, u08 flags ) {
	
	if ( in == NULL ) goto error;
	
	void *tmp = NULL, *out = NULL;
	
	u08 copy  = flags & CV_COPY_DATA;
	u08 imag  = flags & CV_USE_IMAGINARY;
	u08 scale = flags & CV_MAINTAIN_PRECISION;
	
	size_t msize = sizeFromType(TYPE_C64)*size;
	if ( msize == 0 ) goto error;

	switch ( type ) {
		case TYPE_U08:
			tmp = U08_F64(in,size,tmp);
			if ( imag ) out = SET_I_C64(tmp,size,out);
			else        out = SET_R_C64(tmp,size,out);
			goto end;
		case TYPE_S08:
			tmp = S08_F64(in,size,tmp);
			if ( imag )  out = SET_I_C64(tmp,size,out);
			else         out = SET_R_C64(tmp,size,out);
			goto end;
		case TYPE_U16:
			tmp = U16_F64(in,size,tmp);
			if ( imag )  out = SET_I_C64(tmp,size,out);
			else         out = SET_R_C64(tmp,size,out);
			goto end;
		case TYPE_S16:
			tmp = S16_F64(in,size,tmp);
			if ( imag )  out = SET_I_C64(tmp,size,out);
			else         out = SET_R_C64(tmp,size,out);
			goto end;
		case TYPE_U32:
			tmp = U32_F64(in,size,tmp);
			if ( imag )  out = SET_I_C64(tmp,size,out);
			else         out = SET_R_C64(tmp,size,out);
			goto end;
		case TYPE_S32:
			tmp = S32_F64(in,size,tmp);
			if ( imag )  out = SET_I_C64(tmp,size,out);
			else         out = SET_R_C64(tmp,size,out);
			goto end;
		case TYPE_U64:
			tmp = U64_F64(in,size,tmp);
			if ( imag )  out = SET_I_C64(tmp,size,out);
			else         out = SET_R_C64(tmp,size,out);
			goto end;
		case TYPE_S64:
			tmp = S64_F64(in,size,tmp);
			if ( imag )  out = SET_I_C64(tmp,size,out);
			else         out = SET_R_C64(tmp,size,out);
			goto end;
		case TYPE_F32:
			tmp = F32_F64(in,size,tmp);
			if ( imag )  out = SET_I_C64(tmp,size,out);
			else         out = SET_R_C64(tmp,size,out);
			goto end;
		case TYPE_F64:
			if ( imag )  out = SET_I_C64(in,size,out);
			else         out = SET_R_C64(in,size,out);
			goto end;
		case TYPE_C32:
			out = C32_C64(in,size,out);	
			goto end;
		case TYPE_C64:
			out = memcpy(malloc(msize),in,msize);
			goto end;
		default:
			goto error;
	}
	
	end:
	if ( !out  ) goto error;
	if (  tmp  ) free(tmp);
	if ( !copy ) free(in);
	return out;
	
	error:
	if ( out ) free(out);
	if ( tmp ) free(tmp);
	return NULL;
	
}

void * TO_TYPE( void *in, u32 size, u08 type, u08 totype, u08 flags ) {
	
	void *out = NULL;
	
	if ( !in || !size ) goto error;
	
	if ( !sizeFromType(  type) ) goto error;
	if ( !sizeFromType(totype) ) goto error;

	switch ( totype ) {
		case TYPE_U08:
			out = TO_U08(in,size,type,flags);
			goto end;
		case TYPE_S08:
			out = TO_S08(in,size,type,flags);
			goto end;
		case TYPE_U16:
			out = TO_U16(in,size,type,flags);
			goto end;			
		case TYPE_S16:
			out = TO_S16(in,size,type,flags);
			goto end;
		case TYPE_U32:
			out = TO_U32(in,size,type,flags);
			goto end;
		case TYPE_S32:
			out = TO_S32(in,size,type,flags);
			goto end;
		case TYPE_U64:
			out = TO_U64(in,size,type,flags);
			goto end;
		case TYPE_S64:
			out = TO_S64(in,size,type,flags);
			goto end;
		case TYPE_F32:
			out = TO_F32(in,size,type,flags);
			goto end;
		case TYPE_F64:
			out = TO_F64(in,size,type,flags);
			goto end;
		case TYPE_C32:
			out = TO_C32(in,size,type,flags);
			goto end;
		case TYPE_C64:
			out = TO_C64(in,size,type,flags);
			goto end;
		default:
			goto error;
	}
	
	end: 
	if ( !out ) goto error;
	return out;
	
	error:
	if ( out ) free( out );
	return NULL;
	
}
