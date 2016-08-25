/*----------------------------------------------------------------------------*
*
*  coretypedefs.c  -  intrinsic data types
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "coretypedefs.h"


/* variables */

enum {
  IdentUint8,
  IdentUint16,
  IdentUint32,
  IdentUint64,
  IdentInt8,
  IdentInt16,
  IdentInt32,
  IdentInt64,
  IdentReal32,
  IdentReal64,
  IdentImag32,
  IdentImag64,
  IdentCmplx32,
  IdentCmplx64,
  IdentBit,
  IdentBit2,
  IdentRGB,
  IdentReal,
  IdentImag,
  IdentCmplx,
  IdentEnd
};

const char *TypeIdentTab[] = {
  [ IdentUint8   ] = TypeIdentUint8,
  [ IdentUint16  ] = TypeIdentUint16,
  [ IdentUint32  ] = TypeIdentUint32,
  [ IdentUint64  ] = TypeIdentUint64,
  [ IdentInt8    ] = TypeIdentInt8,
  [ IdentInt16   ] = TypeIdentInt16,
  [ IdentInt32   ] = TypeIdentInt32,
  [ IdentInt64   ] = TypeIdentInt64,
  [ IdentReal32  ] = TypeIdentReal32,
  [ IdentReal64  ] = TypeIdentReal64,
  [ IdentImag32  ] = TypeIdentImag32,
  [ IdentImag64  ] = TypeIdentImag64,
  [ IdentCmplx32 ] = TypeIdentCmplx32,
  [ IdentCmplx64 ] = TypeIdentCmplx64,
  [ IdentBit     ] = TypeIdentBit,
  [ IdentBit2    ] = TypeIdentBit2,
  [ IdentRGB     ] = TypeIdentRGB,
  [ IdentReal    ] = TypeIdentReal,
  [ IdentImag    ] = TypeIdentImag,
  [ IdentCmplx   ] = TypeIdentCmplx,
  [ IdentEnd     ] = NULL
};

const Type TypeCodeTab[] = {
  [ IdentUint8   ] = TypeUint8,
  [ IdentUint16  ] = TypeUint16,
  [ IdentUint32  ] = TypeUint32,
  [ IdentUint64  ] = TypeUint64,
  [ IdentInt8    ] = TypeInt8,
  [ IdentInt16   ] = TypeInt16,
  [ IdentInt32   ] = TypeInt32,
  [ IdentInt64   ] = TypeInt64,
  [ IdentReal32  ] = TypeReal32,
  [ IdentReal64  ] = TypeReal64,
  [ IdentImag32  ] = TypeImag32,
  [ IdentImag64  ] = TypeImag64,
  [ IdentCmplx32 ] = TypeCmplx32,
  [ IdentCmplx64 ] = TypeCmplx64,
  [ IdentBit     ] = TypeBit,
  [ IdentBit2    ] = TypeBit2,
  [ IdentRGB     ] = TypeRGB,
  [ IdentReal    ] = TypeReal,
  [ IdentImag    ] = TypeImag,
  [ IdentCmplx   ] = TypeCmplx,
  [ IdentEnd     ] = 0
};


/* functions */

extern const char *TypeIdent
                   (Type type)

{

  if ( !type ) {
    return TypeIdentUndef;
  }

  Size i = IdentEnd;

  while ( i-- ) {

    if ( type == TypeCodeTab[i] ) {
      return TypeIdentTab[i];
    }

  }

  return "unknown";

}
