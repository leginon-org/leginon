/*----------------------------------------------------------------------------*
*
*  coretypedefs.h  -  intrinsic data types
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef coretypedefs_h_
#define coretypedefs_h_

#include "defs.h"


/* macros */

#define TypeGetSize( code )      ( code & TypeMaskSize )

#define TypeGetBits( code )      ( ( code & TypeMaskBits ) >> 8 )

#define TypeGetCount( code )     ( ( code & TypeMaskCount ) >> 12 )

#define TypeSetBits( bits )      ( ( bits << 8 ) & TypeMaskBits )

#define TypeSetCount( count )    ( ( count << 12 ) & TypeMaskCount )

#define TypePack( count, bits )  ( TypeSetCount( count ) | TypeSetBits( bits ) | ( ( ( count * bits + 7 ) / 8 ) & TypeMaskSize ) )

#define TypeIsNumeric( code )    ( code & TypeMaskNum )

#define TypeIsReal( code )       ( !( code & TypeMaskImag ) )

#define TypeIsImag( code )       ( ( code & TypeMaskNum ) == TypeMaskImag )

#define TypeIsCmplx( code )      ( ( code & TypeMaskNum ) == ( TypeMaskReal | TypeMaskImag ) )


/* types */

typedef enum {
  TypeMaskSize  = 0x0000ff,
  TypeMaskSign  = 0x100000,
  TypeMaskInt   = 0x200000,
  TypeMaskReal  = 0x400000,
  TypeMaskImag  = 0x800000,
  TypeMaskNum   = TypeMaskInt | TypeMaskReal | TypeMaskImag,
  TypeMaskBits  = 0x000f00,
  TypeMaskCount = 0x0ff000,
  TypeMaskClass = 0xffff00,
  TypeMask      = 0xffffff,
  TypeUint8   = sizeof( uint8_t   ) | TypeSetCount( 1 ) | TypeMaskInt,
  TypeUint16  = sizeof( uint16_t  ) | TypeSetCount( 1 ) | TypeMaskInt,
  TypeUint32  = sizeof( uint32_t  ) | TypeSetCount( 1 ) | TypeMaskInt,
  TypeUint64  = sizeof( uint64_t  ) | TypeSetCount( 1 ) | TypeMaskInt,
  TypeInt8    = sizeof( int8_t    ) | TypeSetCount( 1 ) | TypeMaskSign | TypeMaskInt,
  TypeInt16   = sizeof( int16_t   ) | TypeSetCount( 1 ) | TypeMaskSign | TypeMaskInt,
  TypeInt32   = sizeof( int32_t   ) | TypeSetCount( 1 ) | TypeMaskSign | TypeMaskInt,
  TypeInt64   = sizeof( int64_t   ) | TypeSetCount( 1 ) | TypeMaskSign | TypeMaskInt,
  TypeReal32  = sizeof( Real32    ) | TypeSetCount( 1 ) | TypeMaskSign | TypeMaskReal,
  TypeReal64  = sizeof( Real64    ) | TypeSetCount( 1 ) | TypeMaskSign | TypeMaskReal,
  TypeImag32  = sizeof( Real32    ) | TypeSetCount( 1 ) | TypeMaskSign | TypeMaskImag,
  TypeImag64  = sizeof( Real64    ) | TypeSetCount( 1 ) | TypeMaskSign | TypeMaskImag,
  TypeCmplx32 = 2*sizeof( Real32  ) | TypeSetCount( 2 ) | TypeMaskSign | TypeMaskReal | TypeMaskImag,
  TypeCmplx64 = 2*sizeof( Real64  ) | TypeSetCount( 2 ) | TypeMaskSign | TypeMaskReal | TypeMaskImag,
  TypeBit    = TypePack( 8, 1 ),
  TypeBit2   = TypePack( 4, 2 ),
  TypeRGB    = TypePack( 3, 8 ),
  TypeUndef  = 0
} Type;


/* macros */

#define TypeIdentUndef    "undefined"
#define TypeIdentUint8    "uint8"
#define TypeIdentUint16   "uint16"
#define TypeIdentUint32   "uint32"
#define TypeIdentUint64   "uint64"
#define TypeIdentInt8     "int8"
#define TypeIdentInt16    "int16"
#define TypeIdentInt32    "int32"
#define TypeIdentInt64    "int64"
#define TypeIdentReal32   "real32"
#define TypeIdentReal64   "real64"
#define TypeIdentImag32   "imag32"
#define TypeIdentImag64   "imag64"
#define TypeIdentCmplx32  "complex32"
#define TypeIdentCmplx64  "complex64"
#define TypeIdentBit      "bit"
#define TypeIdentBit2     "bit2"
#define TypeIdentRGB      "rgb"

#define TypeIdentReal     "real"
#define TypeIdentImag     "imag"
#define TypeIdentCmplx    "complex"


/* must be in sync with defs.h */

#if IndexBits == 32
  #define TypeIndex       TypeInt32
#elif IndexBits == 64
  #define TypeIndex       TypeInt64
#endif

#if SizeBits == 32
  #define TypeSize        TypeUint32
#elif SizeBits == 64
  #define TypeSize        TypeUint64
#endif

#if OffsetBits == 32
  #define TypeOffset      TypeInt32
#elif SizeBits == 64
  #define TypeOffset      TypeInt64
#endif

#if CoordBits == 32
  #define TypeCoord       TypeReal32
#elif CoordBits == 64
  #define TypeCoord       TypeReal64
#endif

#if RealBits == 32
  #define TypeReal        TypeReal32
#elif RealBits == 64
  #define TypeReal        TypeReal64
#endif

#if ImagBits == 32
  #define TypeImag        TypeImag32
#elif ImagBits == 64
  #define TypeImag        TypeImag64
#endif

#if RealBits != ImagBits
  #error RealBits != ImagBits
#endif

#if RealBits == 32
  #define TypeCmplx       TypeCmplx32
#elif RealBits == 64
  #define TypeCmplx       TypeCmplx64
#endif


/* variables */

extern const char *TypeIdentTab[];

extern const Type TypeCodeTab[];


/* prototypes */

extern const char *TypeIdent
                   (Type type);


#endif
